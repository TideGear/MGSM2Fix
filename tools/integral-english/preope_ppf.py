#!/usr/bin/env python
"""Emit the PPF that parks the grown `preope` stage in DUMMY3M.DAT and repoints
STAGE.DIR at it.  Nothing the game reads is overwritten: DUMMY3M.DAT is 27 MB of
zero-filled padding that does not appear in the executable's file-name table."""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from iso import Disc

DESC = b'MGS Integral: English Previous Operations'
# PPF3's description field is exactly 50 bytes, and `ljust` only pads - it never
# truncates. A longer string shifts every record offset, and the loader then
# writes at garbage addresses until the game dies. Cost 306 MB of log to find.
assert len(DESC) <= 50, 'PPF3 description field is 50 bytes'

stage = open('work/preope_en.bin', 'rb').read()
disc_p, out_p = sys.argv[1], sys.argv[2]
disc = Disc(disc_p)
files = {n.upper(): (l, s) for n, l, s, d in disc.walk() if not d}
sd_lba = files['/MGS/STAGE.DIR;1'][0]
du_lba, du_size = files['/DUMMY3M.DAT;1']
offset = du_lba - sd_lba
need = len(stage) // 2048
assert need * 2048 == len(stage)
assert need < du_size // 2048, 'stage does not fit in DUMMY3M.DAT'
print('%s: STAGE.DIR lba=%d  DUMMY3M lba=%d (%d sectors)  -> entry offset %d, %d sectors used'
      % (os.path.basename(disc_p), sd_lba, du_lba, du_size // 2048, offset, need))

f = open(disc_p, 'rb')
def img(lba, within): return lba * 2352 + disc.hdr + within

writes = []   # (image_offset, bytes)

# 1. the stage itself - DUMMY3M is all zeros, so only non-zero runs need writing
blank = 0
for s in range(need):
    page = stage[s*2048:(s+1)*2048]
    f.seek(img(du_lba + s, 0))
    cur = f.read(2048)
    assert cur == bytes(2048), 'DUMMY3M sector %d is not blank' % s
    lo, hi = 0, 2048
    while lo < hi and not page[lo]: lo += 1
    while hi > lo and not page[hi-1]: hi -= 1
    if lo < hi: writes.append((img(du_lba + s, lo), page[lo:hi]))
    blank += 2048 - (hi - lo)
print('   %d of %d stage bytes are leading/trailing zero in their sector and need no record' % (blank, len(stage)))

# 2. repoint the STAGE.DIR entry
sd = open('work/int1_stage.dir', 'rb').read()
hsz = struct.unpack('<I', sd[:4])[0]
ent = None
for p in range(4, hsz + 12, 12):
    if sd[p:p+8].rstrip(b'\x00') == b'preope': ent = p; break
assert ent is not None
old = struct.unpack('<I', sd[ent+8:ent+12])[0]
print('   STAGE.DIR preope entry at file offset %d: sector %d -> %d' % (ent, old, offset))
f.seek(img(sd_lba + ent // 2048, ent % 2048 + 8))
assert f.read(4) == struct.pack('<I', old), 'STAGE.DIR entry does not match retail'
writes.append((img(sd_lba + ent // 2048, ent % 2048 + 8), struct.pack('<I', offset)))

out = bytearray(b'PPF30' + bytes([2])
                + DESC.ljust(50, b'\x00') + bytes(4))
n = 0
for off, data in writes:
    for k in range(0, len(data), 255):
        c = data[k:k+255]
        out += struct.pack('<Q', off + k) + bytes([len(c)]) + c
        n += 1
os.makedirs(os.path.dirname(out_p) or '.', exist_ok=True)
open(out_p, 'wb').write(bytes(out))
print('   -> %s  (%d records, %d bytes)' % (out_p, n, len(out)))
