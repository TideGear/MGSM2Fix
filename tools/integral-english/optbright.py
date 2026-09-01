#!/usr/bin/env python
"""Option -> SCREEN: put USA's brightness paragraph into Integral's option stage.

USA draws this paragraph as one 232x70 texture, `sc_text`, that Integral's DAR
does not contain and Integral's overlay never names.  Integral draws it as font
text bound from the option stage's GCL chain (`opt.c`'s
`for (i = 0; i < 31; i++) fEC4[i].string = GCL_GetString(GCL_NextStr())`), so
the port is a text port, not an art port:

    chain[13..16]  the four paragraph lines
    chain[24]      "Press the O button to return to the option"
    chain[27]      "screen."          (was a colon USA never shows)

All six strings come verbatim off USA's own `sc_text`, including the O-button
sentence - USA has the English for it, it simply does not display those two rows
on this screen.  Nothing is translated or reworded; USA's own line breaks are
kept.

Why no VRAM work is needed, despite `c_width = (rect.w * 4) / 12` implying a
42-character limit: `put_hankaku_4bpp` returns each glyph's own advance, so
ASCII is proportional, and the wrap test in `font_print_string` compares
*pixels* against `kcb->width` (252 px at the default 21-character budget).
Measured off USA's texture these lines render 222, 226, 224, 31, 227 and 37 px,
so every one fits the default 64-unit lane with ~25 px to spare.  `max_width` is
read `lbu` (verified in both retail's and our overlay at 0x800C3598), so the
255 px ceiling is the same bound.

The chain delta is held at exactly zero by padding "game." with trailing spaces,
so no container size field moves and nothing after chain[27] shifts.  (A large
negative shift has crashed the script before - see the preope notes.)

usage: optbright.py            (reads work/, writes work/ and the two PPFs)
"""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gclparse import parse_script, containers_over, be16, be32
from gcldec import chain_at

BASE   = 'work/int1_stage.dir'            # retail, the PPF's base image
SHIP   = 'work/int1_stage_opt11.dir'      # what the deployed option PPF contains
OVL    = 'D:/mgsbuild/d/obj/option.bin'   # the rebuilt option overlay
OUT    = 'work/int1_stage_bright.dir'

# STAGE.DIR LBA per disc.  No Integral disc image is on disk, so these were
# solved from the originally deployed option PPF and proved by re-encoding the
# retail->SHIP diff and reproducing that PPF byte for byte, on all 2610 of its
# records, for both discs.  cross_check() below repeats that whenever the PPF on
# disk still holds exactly the SHIP diff; once this script has overwritten it,
# the record counts differ and the check is skipped rather than faked.
DISCS  = [(0, 136654, 'INTEGRAL_disc1_en_option.ppf'),
          (1, 105178, 'INTEGRAL_disc2_en_option.ppf')]
BASELINE = 'work/option_ppf_baseline_disc%d.ppf'   # the SHIP-state PPF, for revert
HDR    = 24                               # mode 2 form 1
MODS   = 'D:/Steam/SteamApps/common/MGS1/mods/INTEGRAL/INTEGRAL'
DESC   = b'MGS Integral: option screen text'

CIRCLE = b'\x90\x1b'    # the font's O glyph, mixed with ASCII exactly as
                        # int1_en.exe already does: "Press \x90\x1b to zoom in,"

# USA's words, re-wrapped.  USA's own line breaks cannot be used: they run 41-43
# characters, and Integral's half-width Latin glyphs are wider than the font
# USA's texture was authored with.  Measured on screen, a 41-character line
# renders 239 px against a hard limit of 240 - `buf_width = kcb->width - 12`,
# since opt.c passes flag 0 so FONT_NO_KINSOKU is clear - and 43 characters would
# exceed both that and the u8 `max_width`.  Over the limit `font_print_string`
# wraps inside the 20-row band: the continuation lands on the CLUT row and runs
# ~1.4 KB past the heap buffer, which is what corrupted the palettes and froze
# the game on the first attempt.
#
# So: paragraphs rejoined and re-wrapped to 36 characters, words untouched, in
# the same 4 + 2 line shape USA uses.  At the measured 5.83 px/char that is
# ~210 px, ~30 px of headroom.  Same reasoning as the preope recaps.
TEXT = {
    13: b'Adjust the monitor brightness so the',
    14: b'gray scale below the green line',
    15: b'cannot be seen, for the appropriate',
    16: b'brightness to play this game.',
    24: b'Press the ' + CIRCLE + b' button to return to the',
    27: b'option screen.',
}
PAD_INDEX = 27          # absorbs the delta with trailing spaces - it must be the
                        # shortest line, since padding widens max_width too
WRAP_LIMIT = 240        # px, buf_width
PX_ASCII   = 6.0        # conservative: measured 5.83 px/char over 41 characters
PX_ZENKAKU = 12.0       # font_get_glyph_width returns 12 for anything non-hankaku


def pad(x, a=2048): return (x + a - 1) // a * a


def ents(d):
    h = struct.unpack('<I', d[:4])[0]; o = []
    for p in range(4, h + 12, 12):
        n = d[p:p+8].rstrip(b'\x00')
        if n: o.append((n.decode('latin1'), struct.unpack('<I', d[p+8:p+12])[0]))
    return o


def stage_geom(d, name):
    """-> (stage_base, stage_span, tags, payload_offsets)"""
    base = dict(ents(d))[name] * 2048
    ver, _p, sect = struct.unpack('<BBh', d[base:base+4])
    tags, p = [], base + 4
    while True:
        tid, mode, ext, sz = struct.unpack('<HBBi', d[p:p+8])
        if mode == 0: break
        tags.append([tid, mode, ext, sz, p + 4]); p += 8   # p+4 = the size field
    off, offs = 2048, {}
    for k, t in enumerate(tags):
        if chr(t[1]) == 'c' and chr(t[2]) in 'klhg': continue
        offs[k] = base + off; off += pad(t[3])
    assert off == sect * 2048, 'stage layout mismatch: %d vs %d' % (off, sect * 2048)
    return base, sect * 2048, tags, offs


def diff_records(a, b):
    """ppfgen's record split: runs of differing bytes, cut at 2048 boundaries."""
    out, i = [], 0
    while i < len(a):
        if b[i] != a[i]:
            j = i
            while j < len(a) and b[j] != a[j]: j += 1
            out.append((i, b[i:j])); i = j
        else: i += 1
    recs = []
    for fo, data in out:
        p = 0
        while p < len(data):
            end = ((fo + p) // 2048 + 1) * 2048
            n = min(len(data) - p, end - (fo + p))
            recs.append((fo + p, data[p:p+n])); p += n
    return recs


def read_ppf(path):
    d = open(path, 'rb').read()
    assert d[:5] == b'PPF30', d[:8]
    p, out = 1084 if d[57] else 60, []
    while p < len(d):
        off = struct.unpack_from('<Q', d, p)[0]; p += 8
        n = d[p]; p += 1
        out.append((off, d[p:p+n])); p += n
        if d[58]: p += n
    return out


def cross_check(recs, ppf, lba):
    """If the PPF on disk still holds exactly `recs`, prove `lba` against every
    one of its records.  Returns None when it holds something else (i.e. this
    script has already written it), so a stale file cannot silently validate."""
    if len(recs) != len(ppf):
        return None
    for (fo, dd), (o, pd) in zip(recs, ppf):
        if (lba + fo // 2048) * 2352 + HDR + (fo % 2048) != o or dd != pd:
            raise AssertionError('geometry disagrees at file offset 0x%X' % fo)
    return len(recs)


def build_ppf(recs, lba, desc, version):
    """60-byte header: magic(5) version(1) description(50) then the image-type,
    blockcheck, undo and diz flags - the layout read_ppf above parses."""
    out = bytearray(b'PPF30')
    out += bytes([version])
    out += desc.ljust(50, b'\x00')
    out += bytes([0, 0, 0, 0])
    for fo, data in recs:
        p = 0
        while p < len(data):                           # a record length is one byte
            n = min(255, len(data) - p)
            out += struct.pack('<Q', (lba + (fo + p) // 2048) * 2352 + HDR + ((fo + p) % 2048))
            out += bytes([n]) + data[p:p+n]; p += n
    return bytes(out)


def main():
    retail = open(BASE, 'rb').read()
    buf    = bytearray(open(SHIP, 'rb').read())
    assert len(buf) == len(retail), 'STAGE.DIR size changed'

    # --- the SHIP-state PPF is the revert path, so write it out first; it is also
    # what proves the geometry whenever the file on disk still matches it
    ship = diff_records(retail, bytes(buf))
    lbas, version = {}, 2
    for disc, lba, name in DISCS:
        path = os.path.join(MODS, str(disc), name)
        raw = open(path, 'rb').read()
        version = raw[5]
        lbas[disc] = lba
        base_ppf = build_ppf(ship, lba, DESC, version)
        open(BASELINE % (disc + 1), 'wb').write(base_ppf)
        n = cross_check(ship, read_ppf(path), lba)
        if n is not None:
            assert base_ppf == raw, 'round-trip of the deployed PPF for disc %d differs' % (disc + 1)
            print('disc %d: lba=%-7d deployed PPF still the SHIP state - reproduced exactly (%d records)'
                  % (disc + 1, lba, n))
        else:
            print('disc %d: lba=%-7d deployed PPF already rewritten by this script; '
                  'baseline saved to %s' % (disc + 1, lba, BASELINE % (disc + 1)))

    base, span, tags, offs = stage_geom(buf, 'option')
    print('option stage: base 0x%X, %d sectors' % (base, span // 2048))

    # --- 1. the rebuilt overlay
    ovl = open(OVL, 'rb').read()
    old = tags[0][3]
    assert pad(len(ovl)) == pad(old), \
        'overlay %d -> %d crosses a sector boundary; the stage would have to move' % (old, len(ovl))
    assert len(ovl) <= 26624, 'overlay past retail footprint (limit 2 in the preope notes)'
    if len(ovl) < old:
        buf[offs[0]+len(ovl):offs[0]+old] = b'\x00' * (old - len(ovl))
    buf[offs[0]:offs[0]+len(ovl)] = ovl
    struct.pack_into('<i', buf, tags[0][4], len(ovl))
    print('overlay: %d -> %d bytes (pad %d, headroom %d)'
          % (old, len(ovl), pad(len(ovl)), 26624 - len(ovl)))

    # --- 2. the chain
    scr = offs[6]
    cs  = scr + 0x1B8
    root, slen = parse_script(buf, scr + 0x172)
    recs = chain_at(buf, cs)
    span0 = sum(2 + r[1] for r in recs)
    assert len(recs) == 31, 'expected 31 records, got %d' % len(recs)

    need = {k: len(v) + 1 for k, v in TEXT.items()}          # payload + NUL
    delta = sum(need[k] - recs[k][1] for k in TEXT)
    grow  = -delta                                           # absorbed by PAD_INDEX
    assert grow >= 0, 'chain would have to grow by %d; containers need adjusting' % -grow
    TEXT[PAD_INDEX] = TEXT[PAD_INDEX] + b' ' * grow
    print('chain: deltas %+d, padding [%d] with %d spaces -> net 0'
          % (delta, PAD_INDEX, grow))

    # Every line must render inside buf_width or font_print_string wraps into
    # the CLUT row and past the heap buffer.  Trailing padding counts.
    for k, t in sorted(TEXT.items()):
        px = 0.0
        i = 0
        while i < len(t):
            if t[i] >= 0x81: px += PX_ZENKAKU; i += 2
            else:            px += PX_ASCII;   i += 1
        assert px <= WRAP_LIMIT - 16, \
            'record %d estimates %.0f px, too close to the %d px wrap limit' % (k, px, WRAP_LIMIT)
        print('   [%2d] %2d bytes  ~%3.0f px of %d' % (k, len(t), px, WRAP_LIMIT))

    out = bytearray()
    for k, (p, L, pl) in enumerate(recs):
        t = TEXT.get(k, pl)
        assert len(t) + 1 <= 255, 'record %d too long' % k
        out += bytes([0x07, len(t) + 1]) + t + b'\x00'
    D = len(out) - span0
    assert D == 0, 'chain delta %+d; container sizes would need adjusting' % D
    buf[cs:cs+span0] = bytes(out)

    # --- 3. verify the script still parses and the records read back
    root2, s2 = parse_script(buf, scr + 0x172)
    r2 = chain_at(buf, cs)
    assert s2 == slen and len(r2) == len(recs), 'script re-parse changed shape'
    assert root2.kids[0].end == scr + 0x172 + s2, 'script tree end moved'
    for k in sorted(TEXT):
        got = bytes(r2[k][2])
        assert got == TEXT[k], 'record %d readback %r' % (k, got)
    for k in (3, 7, 12):                                     # already-shipped edits survive
        assert bytes(r2[k][2]) == bytes(recs[k][2]), 'record %d disturbed' % k
    print('verify: script length %d unchanged, 31 records, all payloads read back' % s2)
    for k in sorted(TEXT):
        b = bytes(r2[k][2])
        # the O glyph is 0x90 0x1B, which no console codepage can print
        show = ''.join(chr(c) if 32 <= c < 127 else '<%02X>' % c for c in b)
        print('   [%2d] %2d bytes  %s' % (k, len(b), show))

    open(OUT, 'wb').write(bytes(buf))
    print('wrote %s' % OUT)

    # --- 4. the PPFs
    new_recs = diff_records(retail, bytes(buf))
    print('diff vs retail: %d records, %d bytes' % (len(new_recs), sum(len(d) for _, d in new_recs)))
    for disc, _l, name in DISCS:
        p = os.path.join(MODS, str(disc), name)
        blob = build_ppf(new_recs, lbas[disc], DESC, version)
        open(p, 'wb').write(blob)
        print('disc %d -> %s (%d bytes)' % (disc + 1, p, len(blob)))


if __name__ == '__main__':
    main()
