#!/usr/bin/env python
"""Previous Operations with MGS1 (USA)'s exact pagination, line breaks and
character counts.

Two corrections over what shipped before:

**The source was wrong.** `work/us1_stage.dir` is the *European* PSX stage file,
not the USA one - its recap reads "mercenary. He was feared", the USA disc reads
"mercenary who was feared", and only the European container has the former. The
USA text comes out of the Master Collection's own SLUS_005.94 image; see
`integral-english-source-discs`. Everything else we ported (the option chain,
`sc_text`, all 20 briefing textures) is byte-identical between the two releases,
so this is the only text that was mis-sourced.

**USA lays out 7 lines per page, not 8.** Easy to miscount off a screenshot; the
proof is that MG1 page 5 starts at chain record 4 + 4*7 = 32, which is
"warhead-equipped two-legged walking tank. It" - the first line of the 5/13 shot.
MG1 is 90 lines over 13 pages (last page 6), MG2 is 133 over 19 (exactly full).

Integral's engine draws **8** slots a page (`field_464[PAGE_COUNT * 8]`,
`(page-1)*8 + index`, and `i < 8` loops in four draw passes). Rather than
retarget all of that to 7 - `pre_met2.c` alone has a dozen `i < 8` loops, most
of which are not line loops - every page carries USA's 7 lines followed by one
blank. USA's page breaks are then reproduced exactly and no draw loop is
touched: MG1 needs 13*8 = 104 slots for 13 pages of 7+1, and MG2 needs
19*8 = 152 for 19 of 7+1, which is exactly what the existing arrays hold.
So the decomp change is only `PAGE_COUNT 12 -> 13` in `pre_met1.c` plus
`field_714[13 * 8]` and `j < 13` in `preope.c`. `pre_met2.c` is untouched.

Line width is not a constraint here even though USA runs to 54 characters:
`pre_met1.c`/`pre_met2.c` never read `max_width` (whose byte would cap at
255 px). They hardcode two sprites a line, `field_1F0 = 256` at x and
`field_1FC = 128` at x+256, so a line draws to 384 px. USA's widest is 309.

Architecture is unchanged and proven: MG1's lines are GCL chain records, MG2's
are NUL-terminated strings in the script chunk past the end of the script, found
by pointer at `MG2_RECAP_OFFSET` from the first chain record's payload. Both
recaps in the chain hit a size threshold that has never been explained.

usage: preope_usa.py            (reads work/, writes work/ and the two PPFs)
"""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gclparse import parse_script, containers_over, be16, be32

BASE_STAGE = 'work/preope_en.bin'          # last known-good stage, same layout
USA        = 'work/usa1_stage.dir'         # the real USA PSX stage file
OVL        = 'D:/mgsbuild/d/obj/preope.bin'
OUT        = 'work/preope_usa.bin'
JP         = 'D:/Steam/SteamApps/common/MGS1/windata/dlc/dlc_japan.bin'
MODS       = 'D:/Steam/SteamApps/common/MGS1/mods/INTEGRAL/INTEGRAL'
DESC       = b'MGS Integral: English Previous Operations'

# Integral discs inside dlc_japan.bin, read from their own ISO filesystems.
# The STAGE.DIR LBAs independently match the ones solved from the deployed
# option PPF, which is what proves the geometry.
DISCS = [dict(disc=0, img=0x0,        boot='SLPM_862.47', sd=136654, du=292330,
              ppf='INTEGRAL_disc1_en_preope.ppf'),
         dict(disc=1, img=0x2AE54800, boot='SLPM_862.48', sd=105178, du=303436,
              ppf='INTEGRAL_disc2_en_preope.ppf')]
HDR = 24                                   # mode 2 form 1

LINES_PER_PAGE = 7                         # USA's
SLOTS_PER_PAGE = 8                         # Integral's engine
MG1_PAGES, MG2_PAGES = 13, 19
MG1_SRC = (4, 94)                          # USA chain records: MG1 body
MG2_SRC = (95, 228)                        # ... and MG2 body
SCRIPT_NO_BLOB = 22469                     # script length in BASE_STAGE, blob excluded
MG2_RECAP_OFFSET_OLD = 22029               # what BASE_STAGE was built with


def pad(x, a=2048): return (x + a - 1) // a * a


def ents(d):
    h = struct.unpack('<I', d[:4])[0]; o = []
    for p in range(4, h + 12, 12):
        n = d[p:p+8].rstrip(b'\x00')
        if n: o.append((n.decode('latin1'), struct.unpack('<I', d[p+8:p+12])[0], p))
    return o


def stage_of(d, name):
    base = [s for n, s, _p in ents(d) if n == name][0] * 2048
    ver, _p, sect = struct.unpack('<BBh', d[base:base+4])
    tags, p = [], base + 4
    while True:
        tid, mode, ext, sz = struct.unpack('<HBBi', d[p:p+8])
        if mode == 0: break
        tags.append([tid, mode, ext, sz, p + 4]); p += 8
    return base, sect, tags


def chain_records(d, at):
    p, out = at, []
    while p < len(d) and d[p] == 7:
        n = d[p+1]
        if n == 0: break
        out.append(d[p+2:p+2+n]); p += 2 + n
    return out, p


def rec(text):
    """A new chain record from bare text: 07, length-with-NUL, text, NUL."""
    return bytes([7, len(text) + 1]) + text + bytes(1)


def raw(payload):
    """Re-emit an existing record unchanged.  chain_records() hands back the
    payload *including* its terminating NUL, so this must not add another -
    doing so silently grew every preserved record by a byte."""
    return bytes([7, len(payload)]) + payload


def paginate(lines):
    """USA's 7 lines a page, each page padded to the engine's 8 slots."""
    out = []
    for i in range(0, len(lines), LINES_PER_PAGE):
        page = lines[i:i+LINES_PER_PAGE]
        out += page + [b''] * (SLOTS_PER_PAGE - len(page))
    return out


def main():
    # ---- USA's text, verbatim: no rewrapping, no rejoining
    usa = open(USA, 'rb').read()
    ub, _s, utags = stage_of(usa, 'preope')
    uscr = ub + 2048 + pad(utags[0][3]) + pad(utags[1][3])
    urecs, _e = chain_records(usa, uscr + 0x1B8)
    assert b'mercenary who was feared' in b''.join(urecs), \
        '%s is not the USA text - the European stage file reads "He was feared"' % USA
    mg1 = [urecs[i].rstrip(bytes(1)) for i in range(*MG1_SRC)]
    mg2 = [urecs[i].rstrip(bytes(1)) for i in range(*MG2_SRC)]
    assert (len(mg1), len(mg2)) == (90, 133), (len(mg1), len(mg2))
    s1, s2 = paginate(mg1), paginate(mg2)
    assert len(s1) == MG1_PAGES * SLOTS_PER_PAGE, len(s1)
    assert len(s2) == MG2_PAGES * SLOTS_PER_PAGE, len(s2)
    print('USA text: MG1 %d lines -> %d pages -> %d slots;  MG2 %d -> %d -> %d'
          % (len(mg1), MG1_PAGES, len(s1), len(mg2), MG2_PAGES, len(s2)))
    print('  longest line %d chars' % max(len(b) for b in mg1 + mg2))

    # ---- the base stage
    st = bytearray(open(BASE_STAGE, 'rb').read())
    ver, _p, sect = struct.unpack('<BBh', st[:4])
    tags = [list(struct.unpack('<HBBi', st[4+8*k:12+8*k])) + [4+8*k+4] for k in range(9)]
    scr = 2048 + pad(tags[0][3]) + pad(tags[1][3])
    cs = scr + 0x1B8
    old, chain_end = chain_records(st, cs)
    old_len = chain_end - cs
    print('base stage: %d sectors, script chunk %d, chain %d records / %d bytes'
          % (sect, tags[6][3], len(old), old_len))

    # ---- the overlay (same size, so nothing in the stage moves)
    ovl = open(OVL, 'rb').read()
    assert len(ovl) == tags[0][3], \
        'overlay %d != %d; the stage layout would change' % (len(ovl), tags[0][3])
    st[2048:2048+len(ovl)] = ovl

    # ---- new chain: the 4 preope.c strings, MG1's slots, then everything after
    # the old MG1 block untouched (Integral records the GCL script still reads)
    head = old[:4]
    tail = old[4 + 12 * SLOTS_PER_PAGE:]          # base stage had MG1 at 12 pages
    new_chain = b''.join(raw(r) for r in head) \
              + b''.join(rec(b) for b in s1) \
              + b''.join(raw(r) for r in tail)
    D = len(new_chain) - old_len
    print('chain: %d -> %d bytes (D=%+d), %d -> %d records'
          % (old_len, len(new_chain), D, len(old), len(head) + len(s1) + len(tail)))

    root, slen = parse_script(st, scr + 0x172)
    cov = containers_over(root, cs, cs + old_len)

    # ---- reassemble the script chunk: preamble, chain, the rest of the script,
    # then MG2's blob at the end
    blob = b''.join(b + bytes(1) for b in s2)
    script = bytes(st[scr:cs]) + new_chain \
           + bytes(st[cs+old_len:scr+SCRIPT_NO_BLOB]) + blob
    new_chunk = len(script)
    assert pad(new_chunk) == pad(tags[6][3]), \
        'chunk %d -> %d crosses a sector boundary; the sound chunks would move' \
        % (tags[6][3], new_chunk)
    st[scr:scr+pad(tags[6][3])] = script + bytes(pad(tags[6][3]) - new_chunk)
    struct.pack_into('<i', st, tags[6][4], new_chunk)
    print('script chunk: %d -> %d (both pad to %d, no chunk shifts)'
          % (tags[6][3], new_chunk, pad(new_chunk)))

    # ---- container size fields enclosing the chain
    for c in cov:
        o = c.size_at
        if c.size_bits == 32: struct.pack_into('>I', st, o, be32(st, o) + D)
        else:                 struct.pack_into('>H', st, o, be16(st, o) + D)

    # ---- verify: script re-parses, records read back, blob is where the
    # overlay's MG2_RECAP_OFFSET says it is
    root2, s2len = parse_script(st, scr + 0x172)
    assert s2len == slen + D, 'script length %d != %d' % (s2len, slen + D)
    got, end2 = chain_records(st, cs)
    assert len(got) == len(head) + len(s1) + len(tail)
    for k, b in enumerate(s1):
        assert got[4+k].rstrip(bytes(1)) == b, 'MG1 slot %d readback' % k
    want_off = MG2_RECAP_OFFSET_OLD + D
    blob_at = (cs + 2) - 2 + want_off
    q, read = blob_at, []
    for _ in range(len(s2)):
        e = st.index(bytes(1), q); read.append(bytes(st[q:e])); q = e + 1
    assert read == s2, 'blob readback differs'
    assert q == scr + new_chunk, 'blob ends at %d, chunk ends at %d' % (q - scr, new_chunk)
    print('verify: script %d -> %d, %d records, MG1 and all %d blob strings read back'
          % (slen, s2len, len(got), len(read)))
    print('  MG2_RECAP_OFFSET must be %d  (preope.c currently: %s)'
          % (want_off, 'OK' if want_off == 22042 else 'MISMATCH - edit preope.c'))
    assert want_off == 22042, 'preope.c has MG2_RECAP_OFFSET 22042; layout wants %d' % want_off

    tot = 2048 + sum(pad(tags[k][3]) for k in (0, 1)) + pad(new_chunk) \
        + pad(tags[7][3]) + pad(tags[8][3])
    assert tot == sect * 2048, 'stage span %d != %d sectors' % (tot, sect)
    open(OUT, 'wb').write(bytes(st))
    print('wrote %s (%d bytes, %d sectors)' % (OUT, len(st), sect))
    emit(bytes(st))


def emit(stage):
    """Park the stage in DUMMY3M.DAT and repoint STAGE.DIR's preope entry.

    Verified against the Integral disc images inside dlc_japan.bin rather than a
    standalone .bin, since no disc image is on disk. PPF offsets are relative to
    each disc image's own start, so the container base is subtracted.
    """
    sd_file = open('work/int1_stage.dir', 'rb').read()
    entp = [p for n, _s, p in ents(sd_file) if n == 'preope'][0]
    old_sector = struct.unpack('<I', sd_file[entp+8:entp+12])[0]
    need = len(stage) // 2048
    assert need * 2048 == len(stage)
    f = open(JP, 'rb')
    for D in DISCS:
        img, sd, du = D['img'], D['sd'], D['du']
        def at(lba, within): return (lba + within // 2048) * 2352 + HDR + within % 2048
        writes = []
        blank = 0
        for s in range(need):
            page = stage[s*2048:(s+1)*2048]
            f.seek(img + at(du + s, 0))
            assert f.read(2048) == bytes(2048), 'DUMMY3M sector %d not blank on disc %d' % (s, D['disc']+1)
            lo, hi = 0, 2048
            while lo < hi and not page[lo]: lo += 1
            while hi > lo and not page[hi-1]: hi -= 1
            if lo < hi: writes.append((at(du + s, lo), page[lo:hi]))
            blank += 2048 - (hi - lo)
        off = at(sd + entp // 2048, entp % 2048 + 8)
        f.seek(img + off)
        assert f.read(4) == struct.pack('<I', old_sector), \
            'STAGE.DIR preope entry does not match retail on disc %d' % (D['disc']+1)
        writes.append((off, struct.pack('<I', du - sd)))
        out = bytearray(b'PPF30' + bytes([2]) + DESC.ljust(50, b'\x00') + bytes(4))
        n = 0
        for o, data in writes:
            for k in range(0, len(data), 255):
                c = data[k:k+255]
                out += struct.pack('<Q', o + k) + bytes([len(c)]) + c; n += 1
        p = os.path.join(MODS, str(D['disc']), D['ppf'])
        open(p, 'wb').write(bytes(out))
        print('disc %d (%s): preope sector %d -> %d, %d zero bytes skipped, %d records'
              % (D['disc']+1, D['boot'], old_sector, du - sd, blank, n))
        print('   -> %s (%d bytes)' % (p, len(out)))


if __name__ == '__main__':
    main()
