# Integral English text

Tooling that ports English text from **MGS1 (USA)** into **MGS Integral**
(Japanese), emitting PPF patches for the Ketchup mod loader. Nothing is
translated: every English string is copied from the USA disc, and only page
counts and line breaks change.

## What ships

| Patch | Contents |
|---|---|
| `en_items` | item descriptions |
| `en_menu`, `en_menu2` | menu strings |
| `en_option` | `screen brightness setup`, `key configuration setup`, `use directional buttons to test` |
| `en_preope` | Previous Operations: Metal Gear (12 pages), Metal Gear 2 (19 pages) |

`en_menu3` is disabled — it crashes with `GCL:WRONG CODE` walking a RAM buffer,
cause never found.

## Building

Needs the decompilation at `D:\mgsbuild\d` (branch `integral-english-text`,
see `decomp-overlay-changes.patch`) and disc images in `discs/`.

    cd D:/mgsbuild/d/build
    py build.py --psyq_path D:/mgsbuild/psyq --variant main_exe
    ninja -f build.ninja ../obj/preope.bin ../obj/option.bin

    py preope_both.py          # builds the stage
    py preope_ppf.py discs/int1.bin out/INTEGRAL_disc1_en_preope.ppf

**Always check the overlay entry point after touching `preope.c`:**

    grep -m1 "  NewPreviousOperation" obj/asm_preope_lhs.map    # must be 800C4DA4

The disc's main executable is never rebuilt, so it calls that address directly.
`preope_reserved()` in `preope.c` is padding that holds it in place — retune it
if the code ahead of it changes. Measured cost with this psyq compiler: 12 bytes
overhead plus 8 per `volatile_global = n + k;` statement, or 12 for a wide
constant, which gives 4-byte granularity.

## The three limits

Each of these produces the *same* symptom — a black text area with the page
counter still drawn — which is why they took so long to separate.

1. **The GCL argument chain has a size ceiling between 9,567 and 10,304 bytes.**
   Both recaps' text needs 10,304; each alone needs ~9,5xx. Proven by padding
   the chain with records past the last one the game reads, leaving the read
   text known-good: still black. So it is size, not content or record count.
2. **The overlay loads at a fixed address and must stay within retail's 13
   sectors** (24,911 bytes, region ends 0x800C9358). Growing it to 31,500 to
   hold text in `.rodata` broke *both* recaps, including the one whose chain was
   untouched.
3. **The script chunk itself grows freely** — 14 sectors in use. Verified by
   declaring it 2,048 bytes longer with the chain unchanged.

Hence the design: Metal Gear in the chain, Metal Gear 2 in the script chunk past
the end of the script, located by pointer from `field_394[0].string`.

`MG2_RECAP_OFFSET` in `preope.c` is **hardcoded to 22029**, which assumes the
chain is exactly +737 bytes over retail (Metal Gear wrapped at 45 characters,
12 pages). `preope_both.py` asserts it. Change the wrapping and both must move.

## Things that do not work

- **Text in the overlay's `.rodata`** — breaks limit 2.
- **Blanking the now-unread Japanese recap records** to reclaim chain space — an
  8,055-byte negative shift crashed the script at `set map` with no exception.
  Every chain edit that has worked moved things by at most +780.
- **Stage relocation into DUMMY3M.DAT does work** — verified by relocating a
  working build byte-for-byte unchanged. It is used here (90 sectors).
- **`-O1` on the recap files makes the overlay bigger**, not smaller.

## Wrap width

`c_width = (rect.w * 4) / 12` suggests a 42-character limit, but that assumes
12-pixel glyphs. The font is proportional and English is narrower: 45-character
lines render complete (verified in game on Metal Gear page 11/12). Shipped as
Metal Gear 45 / 12 pages, Metal Gear 2 42 / 19 pages.

## Not tested

Disc 2 in game (its `preope` stage is byte-identical to disc 1's, so the same
build is used); the option submenus (SCREEN, KEY CONFIG, VIBRATION TEST), which
use the VRAM columns this changes; and the `f924[12]` fix, which corrects a real
out-of-bounds write but was not what fixed the EXIT freeze.

## Briefing menu (`brf` stage)

The briefing's videos, subtitles and character bios are **already English in
Integral** - only the menu chrome is Japanese. Those labels are not text: they
are PCX textures drawn as textured quads (`b_select.c`, `brf_800C983C` ->
`DG_GetTexture`), which is why no ASCII label exists in STAGE.DIR, the
executable or BRF.DAT.

`GV_StrCode` (source/libgv/strcode.c, verified against its own doc examples)
maps resource names to archive ids: the labels are **`br_s00`-`br_s15`**, the
detailed-information submenu. The four `FILE 00`-`FILE 03` labels are different
textures, not yet located.

`pcx4.py` decodes/encodes the format: standard PCX, 1 bit/pixel x 4 planes,
128-byte header, RLE where `code > 0xC0` means a run of `code - 0xC0`. Note the
RLE stream is **row-wide** - `PcxInflate4` decodes `stride * nplanes` bytes as
one stream, so runs cross plane boundaries.

Three things must be right or the game breaks:

1. **VRAM coordinates.** Each PCX carries its own destination in a `PCXINFO`
   block at offset 74 (stamp 12345): `px, py, cx, cy`. USA's differ completely
   from Integral's - using them uploads labels over the FILE menu and over
   whatever the briefing video's timestamp draws from. Keep Integral's.
2. **Slot dimensions.** The draw quads are hardcoded to Integral's original
   label sizes (confirmed by on-screen width ratios matching Integral's texture
   widths, not USA's). Anything wider overflows into the neighbouring texture's
   VRAM and garbles it. Fit each image to Integral's `w x h`.
3. **4-byte alignment.** Every archive entry's size is a multiple of 4, padded
   with trailing zeros. Emitting an unaligned entry misaligns everything after
   it and the loader takes a wild jump (seen as `pc: 30824000`).

Palette and `n_colors` must come from the USA artwork, which uses up to 16
indices where Integral uses 5.

**Known imperfection:** labels whose English is far longer than the Japanese
(`人質` -> `hostages`, `核兵器` -> `nuclear weapons`) are squeezed into narrow
quads and render small. Fixing that needs the quad constants, which live in the
undecompiled `brf` asm (`asm/overlays/brf/*.s`, raw `dw` opcode dumps).

### Matching USA label sizing: not possible from the texture side

Tested and ruled out. The 16 labels were placed at USA's exact native
dimensions in free VRAM (page-aligned, no overlaps) and still rendered at
Integral's proportions - `hostages` small, `the terrorists' armament` large.
Had the quad been `tex->w/h`, USA-sized textures would have drawn USA-sized.
So the draw rect is a hardcoded constant, and only patching
`asm/overlays/brf/*.s` (raw `dw` opcode dumps) can change it.

Two constraints learned the hard way while trying:

- **Texture pages.** At 4bpp a page is 64 VRAM units wide and a texture must
  fit inside one: `(px % 64) + ceil(w / 4) <= 64`. Every Integral label obeys
  this. Straddling a boundary makes the U coordinate wrap and every label
  collapses into one cluster on screen.
- **Occupancy needs real colour depth.** The `brf` archive is not uniformly
  4bpp; the large background panels are deeper. Computing free VRAM as
  `ceil(w / 4)` for all 51 textures underestimates their footprint, and labels
  packed into "free" space land on the background art and show through it.
