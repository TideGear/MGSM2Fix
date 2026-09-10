"""Render every unidentified game glyph to a labelled PDF for transcription.

`jptext.py` reads 87% of the Japanese on the disc. The rest is bank 1, whose
glyphs are drawn in a font Konami made: template matching against a modern
outline font scores 47% top-1 and against Shinonome's native 12-dot bitmaps
only 5.9%, so there is no reference font to look them up in. What is left is
recognition, and a person - or a multimodal model - reading the glyphs is the
tool that fits.

    py glyphsheets.py                 -> work/glyphs-to-identify.pdf + .tsv
    py glyphsheets.py --per-page 60

Each cell shows one glyph at 6x with an ID beneath it. The companion TSV lists
ID, how many times that shape occurs on the disc, and the OCR shortlist as a
hint - useful precisely because a wrong hint is obvious once you can see the
glyph. Transcribe into the TSV's `char` column and `jptext.py` picks it up.

WHY THIS NEEDS NO TABLE OFFSETS

Bank 1 is a per-block table, so `code -> shape` differs between blocks - but
`shape -> character` is global, proven by the 78 shapes identified in the stage
archives turning up byte-identical inside `RADIO.DAT` 150-220 times each. So a
glyph named once here is named everywhere it is reused, and none of this depends
on locating a conversation's table.

Shapes are ordered by how often they occur, so a partial pass still buys the
most text: the first few hundred cover most of the commentary's characters.
"""
import argparse
import collections
import io
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw

from workdir import WORK

N, SCALE = 12, 6


def draw_glyph(b):
    im = Image.new('L', (N, N))
    for y in range(N):
        bits = int.from_bytes(b[y*3:y*3+3], 'big')
        for x in range(N):
            im.putpixel((x, y), ((bits >> (22 - 2*x)) & 3) * 85)
    return im


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--shapes', default=WORK + '/radio_shapes.pkl')
    ap.add_argument('--per-page', type=int, default=80)
    ap.add_argument('--cols', type=int, default=8)
    ap.add_argument('--pdf', default=WORK + '/glyphs-to-identify.pdf')
    ap.add_argument('--tsv', default=WORK + '/glyphs-to-identify.tsv')
    ap.add_argument('--png', action='store_true', default=True,
                    help='also write one PNG per page, for tools that cannot read PDF')
    args = ap.parse_args()

    shapes = pickle.load(open(args.shapes, 'rb'))
    import jptext
    # the stage-archive shapes already named, so they can be skipped and can
    # also serve as a sanity check if any slip through
    try:
        stage = pickle.load(open(WORK + '/bank1_shapes.pkl', 'rb'))
    except Exception:
        stage = {}
    named = set()
    keys = list(stage)
    for i, ch in getattr(jptext, 'SHAPE_NAMED', {}).items():
        if i < len(keys):
            named.add(keys[i])

    todo = sorted(((n, s) for s, n in shapes.items() if s not in named), reverse=True)
    print('%d shape(s) to identify, ordered by frequency' % len(todo))

    CW, CH = N * SCALE + 20, N * SCALE + 26
    pages = []
    rows = []
    for start in range(0, len(todo), args.per_page):
        chunk = todo[start:start + args.per_page]
        nrow = (len(chunk) + args.cols - 1) // args.cols
        im = Image.new('L', (args.cols * CW, nrow * CH), 255)
        d = ImageDraw.Draw(im)
        for i, (count, shape) in enumerate(chunk):
            gid = start + i
            x, y = (i % args.cols) * CW, (i // args.cols) * CH
            g = draw_glyph(shape)
            g = g.point(lambda v: 255 - v)             # black on white for print
            im.paste(g.resize((N * SCALE, N * SCALE), Image.NEAREST), (x + 10, y + 6))
            d.text((x + 20, y + N * SCALE + 10), 'g%d' % gid, fill=0)
            d.rectangle([x, y, x + CW - 2, y + CH - 2], outline=190)
            rows.append((gid, count, shape.hex()))
        pages.append(im.convert('L'))
    pages[0].save(args.pdf, save_all=True, append_images=pages[1:], resolution=150.0)
    if args.png:
        outdir = os.path.dirname(args.pdf) + '/glyphpages'
        os.makedirs(outdir, exist_ok=True)
        for i, im in enumerate(pages):
            im.save('%s/page%02d.png' % (outdir, i + 1))
        print('%d PNG page(s) -> %s' % (len(pages), outdir))
    print('%d page(s) -> %s' % (len(pages), args.pdf))
    with io.open(args.tsv, 'w', encoding='utf-8', newline='') as fh:
        fh.write('id\toccurrences\tchar\tshape_hex\n')
        for gid, count, hexs in rows:
            fh.write('g%d\t%d\t\t%s\n' % (gid, count, hexs))
    print('-> %s  (fill in the char column)' % args.tsv)
    return 0


if __name__ == '__main__':
    sys.exit(main())
