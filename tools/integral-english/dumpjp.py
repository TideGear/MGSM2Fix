"""Dump every Japanese line on the Integral discs, exactly as the game draws it.

This is the 100%-fidelity dump: each line is rendered from the game's OWN glyph
bitmaps, so there is no recognition step and nothing to get wrong. Text output
can only ever be as complete as the glyph identification (87% today, see
`COVERAGE.md`); the images are complete now.

    py dumpjp.py                      everything, to work/jpdump/
    py dumpjp.py --source RADIO.DAT   one source only
    py dumpjp.py --lines-per-page 30 --scale 2

Output, per source file and per disc:

    work/jpdump/<disc>_<source>.pdf      paginated images of every line
    work/jpdump/<disc>_<source>/*.png    the same pages as PNGs
    work/jpdump/index.tsv                one row per line: where it is, its
                                         codes, and the partial text decode

WHERE THE GLYPHS COME FROM

Bank 0 (kana, punctuation and the game's common kanji) is `font.res`, found by
signature in the stage archive. Bank 1 is per-block, and the block carries it:

* a `.gcx` script ends with a font blob - `parse_gcx` reads it as `font` - and
  `0x9A01 + i` indexes it.
* a `RADIO.DAT` fragment carries its own, and finding the fragment a string
  belongs to is `radiomap.py`'s job - read its docstring before touching any
  of this. The short version: the fragment list comes from parsing each
  candidate sector's record list (`menu_gcl_exec_block_800478B4`) and is
  checked against the 192 fragment extents the game's own radio codes declare.

An earlier version of this file inferred the base with a heuristic and was
wrong for 93% of strings while reporting "100.000% attributed"; the dump it
produced was a neat 2,763-page document full of wrong glyphs. The measure that
catches that is the number of DISTINCT bitmaps the text lookups produce - a
Japanese font has a couple of thousand, and the heuristic produced 91,834.
`radiomap.py` prints that number; check it, not the share of strings that got
an answer.
"""
import argparse
import bisect
import collections
import io
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

import abst_build
import jptext
import mainsweep
import portio
import radiomap
import rendertext
import vr_sweep
from audit_text import game_text
from iso import Disc
from portio import INTEGRAL_IMAGES
from vrlib import chunk_index
from workdir import GAME, WORK

CONTAINER = GAME + '/windata/dlc/dlc_japan.bin'
CODE = re.compile(r'<([0-9A-F]{4})>')
GLYPH, N = 36, 12
BLANK = Image.new('L', (N, N), 0)


def cell(raw):
    im = Image.new('L', (N, N))
    for y in range(N):
        bits = int.from_bytes(raw[y*3:y*3+3], 'big')
        for x in range(N):
            im.putpixel((x, y), ((bits >> (22 - 2*x)) & 3) * 85)
    return im


class Fonts(object):
    """bank 0 from font.res, bank 1 handed in per block"""

    def __init__(self, stage_dir):
        self.data, self.at = rendertext.font_res(stage_dir)
        self.cache = {}

    def bank0(self, code):
        if code in self.cache:
            return self.cache[code]
        try:
            im = rendertext.glyph(self.data, self.at, code)
        except Exception:
            im = None
        self.cache[code] = im
        return im

    def bank1(self, blob, i):
        raw = blob[i*GLYPH:(i+1)*GLYPH]
        return cell(raw) if len(raw) == GLYPH else None


def render_line(text, fonts, blob):
    """the line as the game draws it; `#N` and `|` start a new row"""
    rows, cur = [], []
    parts = re.split(r'(<[0-9A-F]{4}>|#N|\|)', text)
    for part in parts:
        if not part:
            continue
        if part in ('#N', '|'):
            rows.append(cur); cur = []
            continue
        m = CODE.fullmatch(part)
        if not m:
            for chx in part:
                cur.append(('ascii', chx))
            continue
        code = int(m.group(1), 16) & ~0x6000
        if 0x9600 <= code < 0x9A00 and blob is not None:
            cur.append(('g', fonts.bank1(blob, code - 0x9601)))
        elif code >= 0x9A00 and blob is not None:
            cur.append(('g', fonts.bank1(blob, code - 0x9A01)))
        else:
            cur.append(('g', fonts.bank0(code)))
    rows.append(cur)
    rows = [r for r in rows if r]
    if not rows:
        return None
    w = max(sum(N for _ in r) for r in rows)
    im = Image.new('L', (max(w, N), N * len(rows)), 0)
    d = ImageDraw.Draw(im)
    for ri, r in enumerate(rows):
        x = 0
        for kind, v in r:
            if kind == 'g':
                if v is not None:
                    im.paste(v, (x, ri * N))
                else:
                    d.rectangle([x + 1, ri*N + 1, x + N - 2, ri*N + N - 2], outline=110)
            else:
                d.text((x + 2, ri * N + 1), v, fill=255)
            x += N
    return im


def collect(disc_ix, scope='unported'):
    """(source, key, offset, text, blob) for every in-scope Japanese line.

    scope='unported' keeps only Japanese with no USA counterpart, which is what
    a translation would start from: `RADIO.DAT`'s commentary region, the
    `DEMO.DAT`/`VOX.DAT` pockets (already USA-subtracted by `jplist`) and the
    stage archives' Integral-only screens. It drops `RADIO.DAT`'s story-codec
    region, whose Japanese is a subtitle track for conversations USA ships in
    English. scope='all' keeps everything."""
    STORY_END = 0x042C54C          # the story codec ends, the commentary begins
    COMMENTARY_END = 0x0AAC050
    out = []
    want = 'disc%d' % (disc_ix + 1)
    with io.open(WORK + '/japanese-inventory.tsv', encoding='utf-8') as fh:
        fh.readline()
        rows = [l.rstrip(chr(10)).split(chr(9)) for l in fh]
    rows = [f for f in rows if len(f) >= 7 and f[0] == want]
    m = radiomap.build(disc_ix, verbose=False)
    for f in rows:
        src, off, text = f[1], int(f[2], 16), f[6]
        if src == 'RADIO.DAT':
            if scope == 'unported' and not (STORY_END <= off < COMMENTARY_END):
                continue
            at = m['base_of'].get(off)
            blob = radiomap.blob_of(m, off)
            out.append((src, 'base%07X' % (at[0] if at else 0), off, text, blob))
        elif src in ('DEMO.DAT', 'VOX.DAT'):
            out.append((src, src, off, text, None))
        elif src.startswith('STAGE.DIR/'):
            out.append(('STAGE.DIR', src.split('/')[1], off, text, None))
    return out

def stage_blobs(disc_ix):
    """stage name -> its .gcx font blob, for bank 1 in the stage archives"""
    sd = open('%s/int%d_stage.dir' % (WORK, disc_ix + 1), 'rb').read()
    out = {}
    for name in portio.entries(sd):
        try:
            tags, payloads, offsets = portio.stage(sd, name)
            chunk = payloads[chunk_index(tags)]
        except Exception:
            continue
        cf = [(chr(t[2]) if t[2] != 0xFF else '?', t[3]) for t in tags if t[1] == ord('c')]
        for ext, off in cf:
            if ext != 'g':
                continue
            try:
                g, _ = abst_build.parse_gcx(chunk, off)
            except Exception:
                continue
            if g['font']:
                out.setdefault(name, g['font'])
                break
    return out


def text_with_bank1(text, blob, stage=None):
    """decode, resolving bank-1 codes through the block font + shape table.

    This is what lets the text output grow toward 100% on its own: every glyph
    named in `glyphs-to-identify.tsv` resolves here from that moment on, in
    every block that reuses the same bitmap."""
    if blob is None:
        return jptext.decode(text, stage)
    out = text
    for c in set(CODE.findall(text)):
        v = int(c, 16) & ~0x6000
        i = None
        if 0x9600 <= v < 0x9A00:
            i = v - 0x9601
        elif v >= 0x9A00:
            i = v - 0x9A01
        if i is None:
            continue
        raw = blob[i*GLYPH:(i+1)*GLYPH]
        if len(raw) != GLYPH:
            continue
        ch = jptext.char_for_shape(raw)
        if ch:
            out = out.replace('<%s>' % c, ch)
    return jptext.decode(out, stage)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=WORK + '/jpdump')
    ap.add_argument('--source', help='only this source file')
    ap.add_argument('--lines-per-page', type=int, default=28)
    ap.add_argument('--scale', type=int, default=2)
    ap.add_argument('--discs', default='1,2,vr')
    ap.add_argument('--limit', type=int, default=0, help='stop after N lines (a smoke test)')
    ap.add_argument('--scope', choices=('unported', 'all'), default='unported',
                    help='unported (default) keeps only Japanese that USA has no counterpart for; see collect()')
    ap.add_argument('--png', action='store_true',
                    help='also write every page as PNG (thousands of files; PDF only by default)')
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    index = io.open(args.out + '/index.tsv', 'w', encoding='utf-8', newline='')
    index.write('disc\tsource\tgroup\toffset\tpage\trow\tpartial_text\tcodes\n')
    total = 0
    for disc_ix in (0, 1):
        if str(disc_ix + 1) not in args.discs.split(','):
            continue
        fonts = Fonts('%s/int%d_stage.dir' % (WORK, disc_ix + 1))
        blobs = stage_blobs(disc_ix)
        lines = collect(disc_ix, args.scope)
        if args.source:
            lines = [l for l in lines if l[0] == args.source]
        if args.limit:
            lines = lines[:args.limit]
        bysrc = collections.defaultdict(list)
        for src, key, off, text, blob in lines:
            bysrc[src].append((key, off, text, blob))
        for src, items in sorted(bysrc.items()):
            pages, page, row = [], None, 0
            H = N * 3 * args.scale
            pdfname = '%s/disc%d_%s' % (args.out, disc_ix + 1, src.replace('.', '_'))
            os.makedirs(pdfname, exist_ok=True)
            plain = io.open(pdfname + '.txt', 'w', encoding='utf-8', newline='')
            plain.write('# %s, disc %d - every line, in file order, decoded.\n'
                        '# A blank line separates conversations.\n\n'
                        % (src, disc_ix + 1))
            last_key = None
            for key, off, text, blob in items:
                use = blob if blob is not None else blobs.get(key)
                im = render_line(text, fonts, use)
                if im is None:
                    continue
                if page is None or row >= args.lines_per_page:
                    if page is not None:
                        pages.append(page)
                    page = Image.new('L', (1100, args.lines_per_page * H), 0)
                    row = 0
                big = im.resize((im.width * args.scale, im.height * args.scale), Image.NEAREST)
                page.paste(big.crop((0, 0, min(big.width, 1000), big.height)), (90, row * H))
                ImageDraw.Draw(page).text((4, row * H + 4), '%d' % (total + 1), fill=170)
                said = text_with_bank1(text, use,
                                       key if src == 'STAGE.DIR' else None)
                if key != last_key:
                    if last_key is not None:
                        plain.write('\n')
                    plain.write('--- %s ---\n' % key)
                    last_key = key
                plain.write('%s\n' % said.replace('#N', '\n'))
                index.write('%s\t%s\t%s\t0x%X\t%d\t%d\t%s\t%s\n'
                            % ('disc%d' % (disc_ix + 1), src, key, off,
                               len(pages) + 1, row + 1,
                               said.replace('\t', ' '), text))
                row += 1
                total += 1
            if page is not None:
                pages.append(page)
            plain.close()
            if not pages:
                continue
            inv = [p.point(lambda v: 255 - v) for p in pages]
            inv[0].save(pdfname + '.pdf', save_all=True, append_images=inv[1:], resolution=150.0)
            if args.png:
                for i, pg in enumerate(inv):
                    pg.save('%s/page%04d.png' % (pdfname, i + 1))
            print('disc%d %-12s %6d line(s), %4d page(s) -> %s.pdf'
                  % (disc_ix + 1, src, len(items), len(pages), pdfname), flush=True)
    index.close()
    print()
    print('%d line(s) dumped; index -> %s/index.tsv' % (total, args.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
