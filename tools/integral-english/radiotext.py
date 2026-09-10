"""Pull every subtitle out of RADIO.DAT by walking the game's own records.

    py radiotext.py                     what it finds, and the checks
    py radiotext.py --disc 2
    py radiotext.py --dump out.txt      every line, in file order

WHY NOT `japanese-inventory.tsv`

`jplist`'s scanner looks for runs of glyph codes and **ends a run at any code
it does not recognise**, so the code is dropped and the text after it starts a
new row. Two ranges it does not recognise carry real text: `0x91xx` (bank 0's
second kanji page, of which only four characters were ever identified) and
`0x97xx` (bank 1 above index 255 - the commentary's font blobs hold up to 441
glyphs and the codes run straight on into it). Measured over the commentary,
the inventory holds **85.2%** of the glyph instances; the visible symptom is
「無限バンダナは制作チーム内では昆」, where the 布 of 昆布 is a `0x9106` and the run stops
on it.

The fix is not a better scanner. The game knows exactly where its text is, so
walk what it walks.

THE GRAMMAR, FROM menu/radiomes.c

A block is `[marker][BE16 totalSize][records]`, ending at `+totalSize+1` or on
a 0 byte; a record is `FF <code> <BE16 size> <payload>` and the next one is at
`+size+2` (`menu_gcl_exec_block_800478B4`). The payloads that matter:

* **TALK** (`radio_anim_with_subtitles_800471AC`) - three BE16 words
  (chara, image, unk), then the subtitle to the end of the record.
* **IF** (`radio_if_80047514`) - a GCL value, then a nested block; then
  `FF 12 <value><block>` for each ELSEIF and `FF 11 <block>` for ELSE.
* **SWITCH** (`radio_switch_800475B8`) - a GCL value, then `21 <BE16 case>
  <block>` repeated, `22 <block>` for default, a 0 byte to end. Note the case
  marker is a bare byte here, *not* preceded by FF.
* **RANDSWITCH** (`radio_randSwitch_80047660`) - a BE16 (not a GCL value),
  then `31 <BE16 weight><block>` repeated, 0 to end.

GCL value sizes are `GCL_GetNextValue` (libgcl/parse.c), which is what
`gclparse.parse_values` already implements.
"""
import argparse
import collections
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jptext
import radiomap
from workdir import WORK

GLYPH = 36
TALK, IF, ELSE, ELSEIF = 0x01, 0x10, 0x11, 0x12
SWITCH, CASE, DEFAULT, RANDSWITCH, RANDCASE = 0x20, 0x21, 0x22, 0x30, 0x31


def be16(d, p):
    return (d[p] << 8) | d[p + 1]


def value_end(d, p):
    """one GCL value at p -> the offset just past it (GCL_GetNextValue)"""
    t = d[p]
    if t & 0xF0 == 0x10:                 # GCL_VAR
        return p + 4
    if t == 0x00:
        return p + 1
    if t == 0x01:
        return p + 3                     # SHORT
    if t in (0x02, 0x03, 0x04):
        return p + 2                     # BYTE/CHAR/BOOL
    if t in (0x06, 0x08):
        return p + 3                     # STRID/PROCID
    if t == 0x07:
        return p + 2 + d[p + 1]          # STRING
    if t in (0x09, 0x0A):
        return p + 5                     # INT/SYMBOL
    if t == 0x20:
        return p + 2                     # ARRAY
    if t == 0x30:
        return p + 1 + d[p + 1]          # EXPR
    if t == 0x40:
        return p + 1 + be16(d, p + 1)    # ARG
    if t == 0x50:
        return p + 2 + d[p + 2]          # OPTION
    raise ValueError('value opcode %02X at 0x%X' % (t, p))


def block_end(d, p):
    return p + 1 + be16(d, p + 1)


def walk(d, s, limit, emit, depth=0, stats=None):
    """every TALK payload in the block at `s` and everything nested in it"""
    if depth > 24:
        return
    recs, _ = radiomap.walk_block(d, s, limit)
    for pos, code, size in recs:
        payload, rend = pos + 4, pos + size + 2
        if stats is not None:
            stats[radiomap.RDCODE[code]] += 1
        try:
            if code == TALK:
                emit(payload + 6, rend, depth)
            elif code == IF:
                p = value_end(d, payload)
                while p < rend:
                    walk(d, p, rend, emit, depth + 1, stats)
                    p = block_end(d, p)
                    if p + 1 >= rend or d[p] != 0xFF:
                        break
                    c = d[p + 1]
                    p += 2
                    if c == ELSEIF:
                        p = value_end(d, p)
                    elif c != ELSE:
                        break
            elif code in (SWITCH, RANDSWITCH):
                p = payload + 2 if code == RANDSWITCH else value_end(d, payload)
                while p < rend and d[p]:
                    c = d[p]
                    p += 1
                    if c in (CASE, RANDCASE):
                        p += 2
                    elif c != DEFAULT:
                        break
                    walk(d, p, rend, emit, depth + 1, stats)
                    if c == DEFAULT:
                        break
                    p = block_end(d, p)
        except (ValueError, IndexError):
            if stats is not None:
                stats['!' + radiomap.RDCODE[code]] += 1


def blobs(m):
    """fragment start -> its font blob, bounded by the NEXT fragment.

    Bounding matters: a commentary blob holds 224-441 glyphs and the codes
    reach index 511, so an unbounded slice reads the next fragment's bytes and
    renders plausible-looking wrong kanji.
    """
    frags = m['frags']
    starts = sorted(frags)
    out = {}
    for i, f in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else len(m['radio'])
        out[f] = m['radio'][frags[f]:nxt]
    return out


def subtitles(m):
    """(fragment, offset, raw bytes) for every subtitle on the disc"""
    radio, frags = m['radio'], m['frags']
    starts = sorted(frags)
    out = []
    stats = collections.Counter()
    for i, f in enumerate(starts):
        base = frags[f]
        got = []
        walk(radio, f + 8, base, lambda a, b, dep: got.append((a, b)), 0, stats)
        for a, b in got:
            out.append((f, a, bytes(radio[a:b])))
    return out, stats


def render(raw, blob):
    """subtitle bytes -> text, resolving bank 1 through the fragment's font"""
    out, p = [], 0
    while p < len(raw):
        b = raw[p]
        if b < 0x80:
            out.append(chr(b) if 0x20 <= b < 0x7F else
                       ('\n' if b == 0x0A else ''))
            p += 1
            continue
        if p + 1 >= len(raw):
            break
        v = ((b << 8) | raw[p + 1]) & ~0x6000
        p += 2
        if 0x9600 <= v < 0x9A00 and blob is not None:
            i = radiomap.bank1_index(v) * GLYPH
            g = blob[i:i + GLYPH]
            ch = jptext.char_for_shape(g) if len(g) == GLYPH else None
            out.append(ch or '⟪%04X⟫' % v)
        else:
            out.append(jptext.glyph_char(v) or '⟪%04X⟫' % v)
    return ''.join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--disc', type=int, default=1, choices=(1, 2))
    ap.add_argument('--dump', help='write every line here, in file order')
    args = ap.parse_args()

    jptext.load_shape_table()
    m = radiomap.build(args.disc - 1, verbose=False)
    radio, frags = m['radio'], m['frags']
    subs, stats = subtitles(m)
    print('records walked:', ', '.join('%s %d' % kv for kv in stats.most_common()))
    print('subtitles found: %d' % len(subs))

    codes = unknown = 0
    fonts = blobs(m)
    fh = io.open(args.dump, 'w', encoding='utf-8', newline='') if args.dump else None
    last = None
    for f, a, raw in subs:
        txt = render(raw, fonts[f])
        for _ in re.finditer(r'⟪[0-9A-F]{4}⟫', txt):
            unknown += 1
        codes += sum(1 for i in range(0, len(raw) - 1)
                     if raw[i] >= 0x80 and (i == 0 or raw[i-1] < 0x80 or True)) * 0
        if fh:
            if f != last:
                fh.write('\n--- fragment 0x%07X ---\n' % f)
                last = f
            fh.write(txt.rstrip() + '\n')
    if fh:
        fh.close()
        print('-> %s' % args.dump)
    print('unresolved glyph codes in the text: %d' % unknown)
    return 0


if __name__ == '__main__':
    sys.exit(main())
