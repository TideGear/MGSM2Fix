"""End-to-end static check of the USA brightness fix.

Takes the 426 bytes out of the SHIPPED binary, puts them at the offset the
shipped table names, over the collection's OWN unpatched data, and decodes the
texture that results. Nothing here trusts the build tools' intent.
"""
import re, struct, sys, io
sys.path.insert(0, r'C:/Users/Tideg/My Drive/Development/MGSM2Fix/tools/integral-english')
import pcx4
from optsctext import ents, dar_entries, pad, SC_TEXT

ASI = (r'C:/Users/Tideg/AppData/Roaming/Vortex/metalgearsolidmc/'
       r'mods/MGSM2Fix-5-3-6-0-1774482213/MGSM2Fix64.asi')
HDR, SIZE, PAY_OFF = 24, 5852, 0x1064
DISCS = [(1, 'work/usa1_stage.dir', 132344, 0x165A4790, 0xF12F8000),
         (2, 'work/usa2_stage.dir', 100801, 0x11EE3E40, None)]

# --- the patch bytes, and the offsets, straight out of the header the build used
hdr = io.open(r'C:/Users/Tideg/My Drive/Development/MGSM2Fix/src/mgs1.h',
              encoding='utf-8', newline='').read().replace('\r\n', '\n')
i = hdr.index('MGS1_BrightnessTextData[426] = {')
want = bytes(int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{2}),', hdr[i:hdr.index('};', i)]))
assert len(want) == 426
entries = re.findall(r'\{(\d+), "(\w+)", (\d), 0x([0-9A-Fa-f]+)ull, data,', hdr)
assert len(entries) == 2, entries
print('shipped table: %s' % [(int(t), v, int(d), '0x%s' % o.upper()) for t, v, d, o in entries])

asi = open(ASI, 'rb').read()
at = asi.find(want)
assert at >= 0, 'the 426 bytes are not in the shipped binary'
data = asi[at:at + 426]
print('shipped binary: 426 bytes at 0x%X, %s the table in the header'
      % (at, 'identical to' if data == want else 'DIFFERENT from'))
print()


def image_off(lba, fo):
    return (lba + fo // 2048) * 2352 + HDR + fo % 2048


for no, path, lba, off_expect, alldata_base in DISCS:
    d = bytearray(open(path, 'rb').read())
    sec = {n: v for n, v, _p in ents(bytes(d))}['option']
    base = sec * 2048
    tags, p = [], base + 4
    while True:
        tid, mode, ext, sz = struct.unpack('<HBBi', d[p:p + 8])
        if mode == 0:
            break
        tags.append((tid, chr(mode), chr(ext) if 32 <= ext < 127 else '?', sz)); p += 8
    FILE = [k for k, t in enumerate(tags) if not (t[1] == 'c' and t[2] in 'klhg')]
    off, payoff = 2048, {}
    for k in FILE:
        payoff[k] = off
        off += pad(tags[k][3])

    q, dar_pay = 0, None
    for tid, ext, blob in dar_entries(bytes(d[base + payoff[1]: base + payoff[1] + tags[1][3]])):
        if tid == SC_TEXT:
            dar_pay = q + 8
        q += 8 + len(blob)
    fo = sec * 2048 + payoff[1] + dar_pay + PAY_OFF
    got_off = image_off(lba, fo)
    entry = [e for e in entries if int(e[2]) == no - 1][0]
    print('disc %d: fo %d -> image 0x%08X; shipped table says 0x%s  ->  %s'
          % (no, fo, got_off, entry[3].upper(),
             'MATCH' if got_off == int(entry[3], 16) else 'MISMATCH'))
    assert got_off == int(entry[3], 16)
    assert got_off == off_expect

    if alldata_base is not None:
        f = open('D:/Steam/SteamApps/common/MGS1/windata/alldata.bin', 'rb')
        f.seek(alldata_base + got_off)
        assert f.read(426) == bytes(d[fo:fo + 426]), 'alldata.bin disagrees with the dump'
        print('        the collection\'s own alldata.bin holds those same pre-patch bytes')

    # apply, then decode
    d[fo:fo + 426] = data
    payload = bytes(d[base + payoff[1] + dar_pay: base + payoff[1] + dar_pay + SIZE])
    w, h, pal, rows = pcx4.decode(payload)
    prof = [sum(1 for x in range(2, 227) if rows[y][x] not in (12, 0, 11, 5)) for y in range(h)]
    starts = [y for y in range(h) if prof[y] and (y == 0 or not prof[y - 1])]
    bar = (rows[0].count(0), rows[1].count(0))
    orig = pcx4.decode(open('work/usa_sc_text.pcx', 'rb').read())[3]
    assert (w, h) == (232, 70), (w, h)
    assert starts == [0, 12, 24, 38], starts
    assert min(bar) > 150, bar
    assert rows[:46] == [list(r) for r in orig[:46]], 'a kept row changed'
    assert all(prof[y] == 0 for y in range(46, h)), 'ink below the four lines'
    print('        patched texture: %dx%d, lines at %s, (8,8,8) filler %d/%d px,'
          ' rows 0..45 identical to the game\'s own, nothing below' % (w, h, starts, bar[0], bar[1]))
print()
print('OK on both disks.')
