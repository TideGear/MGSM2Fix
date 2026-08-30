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
