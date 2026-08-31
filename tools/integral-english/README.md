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
| `en_brf` | briefing menu labels (20 PCX textures + quad constants) |

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

    py brf_widen.py            # VRAM placement for the briefing labels
    py brf_build.py            # quad patches + texture swap
    py reloc_ppf.py brf work/brf_en.bin 128 discs/int1.bin out/INTEGRAL_disc1_en_brf.ppf

**Check the overlay entry point after touching `preope.c`:**

    grep -m1 "  NewPreviousOperation" obj/asm_preope_lhs.map    # 800C4DA4

`preope_reserved()` in `preope.c` is padding that holds it there. **It is
probably unnecessary** — see the audit below. It is kept only because preope
took ~30 build/test cycles to get working and the change has not been tested.
Padding cost with this psyq compiler: 12 bytes overhead plus 8 per
`volatile_global = n + k;` statement, or 12 for a wide constant, giving 4-byte
granularity.

## The three limits

Each of these produces the *same* symptom — a black text area with the page
counter still drawn — which is why they took so long to separate.

1. **Both recaps' text in the GCL chain fails somewhere between 9,567 and
   10,304 bytes.** Both together need 10,304; each alone needs ~9,5xx. Proven
   by padding the chain with records past the last one the game reads, leaving
   the read text known-good: still black. So it is size, not content or record
   count. The *mechanism* is not a parser limit — see the audit below.
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
  working build byte-for-byte unchanged. Used for preope (90 sectors) and brf
  (139 sectors).
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
Integral** — only the menu chrome is Japanese. Those labels are PCX textures
drawn as textured quads, which is why no ASCII label exists in STAGE.DIR, the
executable or BRF.DAT.

`GV_StrCode` maps resource names to archive ids. All 20 labels exist in both
archives under the same id, one to one:

| id | Integral | USA |
|---|---|---|
| `br_s00` | 潜入方法 | infiltration method |
| `br_s01` | タイムリミット | time limit |
| `br_s02` | 作戦責任者 | person in charge of the operation |
| `br_s03` | サポート要員 | support crew |
| `br_s04` | ロイ キャンベル | Roy Campbell |
| `br_s05` | メリル | Meryl |
| `br_s06` | Dr. ナオミ | Dr. Naomi |
| `br_s07` | 人質 | hostages |
| `br_s08` | 核兵器 | nuclear weapons |
| `br_s09` | テロリストの要求 | the terrorists' demand |
| `br_s10` | 遺伝子強化 | genetic strengthening |
| `br_s11` | テロリストの兵装 | the terrorists' armament |
| `br_s12` | 次世代特殊部隊 | next-generation special force unit |
| `br_s13` | 全員賛同の理由 | the reason for unanimous approval |
| `br_s14` | FOX HOUND部隊 | unit FOX-HOUND |
| `br_s15` | リキッド スネーク | Liquid Snake |
| `br_f00`–`br_f03` | FILE 00–03 | mission description / operation outline / operation member / detailed information |

### The texture is stretched to the quad

`source/overlays/brf/onoda/brf/b_select.c` is decompiled and settles the model
that cost the most time here:

    void brf_800C983C(int prim, int tex_id, POLY_FT4 *poly, int xl, int yt, int xr, int yb, ...)
    {
        brf_800C97CC(prim, poly, xl, yt, xr, yb, abe);   /* setXY4(poly, xl,yt, xr,yb) */
        tex = DG_GetTexture(tex_id);
        poly->u0 = tex->off_x;  poly->u1 = tex->off_x + tex->w + 1;   /* whole texture */

The screen rect is a **hardcoded quad** and the UVs span the **whole texture**,
so **rendered size is the quad's, and texture size does not affect it at all**.
A label draws at its true size only when its canvas equals its quad. That is
why an earlier attempt — dropping USA's native-size textures into free VRAM —
changed nothing on screen, and it is the reason to prefer padding over scaling:
padding a canvas out to the quad keeps the art 1:1, scaling distorts it.

It also dissolves the shared-register problem *for the art*. Several labels
share one `xr` immediate, so they share a quad — but they need not be the same
width: size the shared quad to the group's largest member and pad the smaller
ones with the palette's black entry, and each still renders at its own true
size.

That is not enough once the **selection highlight** is considered, because the
highlight follows the quad. `br_s06` (Dr. Naomi, 52 px) shares `xr` with
`br_s02` (112 px), so its highlight ran 60 px past its text; `br_s09` shares
with `br_s11` and ran 8 px over. USA gives each its own `xr`.

Un-sharing needs one spare instruction slot per argument block and there is
none — **except** that the rewritten positioner overwrites all four poly `y`
values every frame, which makes the GetResources `yt`/`yb` dead for every
`br_sNN`. Their loads are the spare slots. All four rows are unconditional, so
the positioner always runs and the `y` really is always replaced:

    br_s02  800C9EF8  addiu t0, zero, 138   ; its own xr
                      addiu s5, zero, 78    ; and leaves br_s06's xr in s5
                      sw t0,16 / sw t0,20 / sw t0,24 / sw s1,28 / nop
    br_s09  800CA134  addiu s4, zero, 146
    br_s11  800CA1C8  addiu t0, zero, 154   ; no longer reads s4
                      sw t0,16 / sw t0,20 / sw t0,24 / sw s1,28 / nop

All 15 label quad widths then equal USA's exactly, and every canvas equals its
own art with no group padding.

### The three quad families

Found by disassembling the 38 `brf_800C983C` call sites in `GetResources`
(`asm/overlays/brf/brf_800C99C0.s`) and reading the resource-name string loaded
before each one. Args are `a3=xl, 16(sp)=yt, 20(sp)=xr, 24(sp)=yb, 28(sp)=abe,
32(sp)=orient`.

**A — full quad** (`br_s02 s04 s06 s07 s08 s09 s11 s12 s14`): `xl=26` plus real
`yt/xr/yb` immediates. Width and height both patchable. Shared immediates:

    800C9EFC = 86    br_s02.xr, br_s06.xr
    800CA038 = -7    br_s06.yt, br_s09.yt
    800CA040 = 6     br_s06.yb, br_s09.yb
    800CA134 = 122   br_s09.xr, br_s11.xr

**B — indented rows** (`br_s01 s03 s05 s10 s13 s15`): `xl=46`, `yt=yb=0`, one
unique `xr`. `xr - xl` equals the Integral texture width exactly for all six.
Width patchable, height not — see below.

### Height: take it from the texture's own V coordinates

`brf_800C69B4` drew every `br_sNN` into a quad of one hardcoded height
(`addiu v1, a2, 13`). **The selection highlight follows that quad**, so a fixed
height gives a fixed highlight — measured by diffing screenshots that differ
only in which row is selected:

    fixed quad   mine 24, 24, 24 ...                          (uniform)
    USA          5, 6, 7, 9, 10, 11, 12, 13, 14, 23, 24       (per row)

USA varies because it sizes each box to its own label: `above + below + 5`
equals that label's texture height, exactly, for all 16.

The exact per-label height is already in the poly, and the positioner never
touches it. `brf_800C983C` sets `v0 = tex->off_y` and
`v2 = tex->off_y + tex->h + 1`, and `tex->h` is height−1, so **`v2 - v0` is the
texture height**. Unlike the poly's `y`, the UVs are stable across frames, so
reading them cannot accumulate.

Reading it costs four instructions, and the function has them: its x
normalisation is entirely redundant, because `setXY4` already leaves `x2 == x0`
and `x1 == x3`. The two `lh` and the two `sh` that copy x are dead:

    lbu  a0, 29(v0)      v2
    lbu  a1, 13(v0)      v0
    subu v1, a0, a1      v1 = texture height
    addu v1, a2, v1      v1 = y + height
    sh a2,10 / a2,18 / v1,26 / v1,34

The quad is now the texture height per label — the same rule USA uses — so the
highlight matches without approximation, and every canvas is USA's art at USA's
size with no padding, scaling or squashing.

Two earlier approximations are gone with it: a fixed 20-row quad (which made
the highlight uniform) and `advance - 6` (which left it 0–3 rows tall). Measured
before the fix: highlight 14.0 game px against USA's 11.0, both with their top
2.0 px above the ink — the tops already agreed, only the height was over.

### The vertical rule

The rule left of the submenu items is **poly 26** (the first `br_line2`), found
by scanning every poly-x store for the rule's x: `x0/x2 = 19`, `x1/x3 = 23`.
Not `br_line1` (poly 25) — that one is a *horizontal* rule, and the code that
writes it only sets x, reading and writing y back unchanged.

Integral sizes it centred, from a hardcoded 20 per item — its **original** row
advance:

    v1   = (20n - 7) / 2
    s0   = -41 - v1            the list's starting y
    rule = [s0 - 2, v1 - 38]   length = 2*v1 + 5 = 20n - 2

Verified: that predicts 17 game px for the one-item operation-outline submenu
and 57 for the three-item operation-member one; measured 16.8 and 56.8.

USA's rule is structurally different — its code is a top-anchored animated
reveal (`y0/y1 = -55`, `y2/y3 = a3 - 55`, x ramped by a timer) rather than a
centred bar — and measures 12.6 and 62.8 for the same two submenus, i.e. it
grows ~25 per item against Integral's 20, in the opposite direction on each.

Only the outline case is safely correctable: the bottom constant is independent
of the row start, so shortening it moves the rule without moving any text.
`800C6F3C  -38 -> -43` gives `2*v1` = 12 game px against USA's 12.6.

**Still different: the operation-member rule**, 6 game px shorter than USA's.
Its length is not written by the outline block (the only `-38` in the range),
nor by the second poly-26 block at `800C7508`, which animates x and preserves
y. Matching it means porting USA's formula, which is shaped differently and
whose Integral counterpart also feeds the row start — so it was left alone
rather than reshaped blind.

### Horizontal: USA's relative layout does not fit Integral

Integral's vertical rule sits 20 game px right of USA's (measured 2101 vs 1921,
180 display px at 9 px per game px) while its label `xl` constants are only
16–17 right. So the labels sit ~4 px left of USA's label-to-rule offset — but
closing that gap does not fit:

    USA       rule at  0,  xl 10  ->  the terrorists' armament (128) ends 138   22 px margin
    Integral  rule at 20,  xl 30  ->                               ends 158   touching the edge

The panel spans -160..160, so `xl = USA's xl + 20` puts the final `t` on the
screen edge. Integral keeps its native `xl`; the 4 px offset stays and the text
stays on screen. The rule is not a poly either game writes and the `DG_PRIM`
world matrix is set in undecompiled asm, so moving it was not available.

That also exposed a pre-existing overflow: Integral's indents were sized for
the narrower Japanese art, and USA's `genetic strengthening` (120 px) at
family B's `xl` 46 ends at **166**, off screen — `the reason for unanimous
approval` at 162. Each family's `xl` is now clamped so its widest member ends
by 156; family B goes 46 -> 36.

### Read USA's constants; measure only to find discrepancies

USA reworked the row positioner. It takes the box extents as stack arguments —

    subu v1, a2, v1        top    = y - arg4   (16(sp))
    addiu a0, a0, 5
    addu  a0, a2, a0       bottom = y + arg5 + 5  (20(sp))

— where Integral hardcodes 13. **Every USA box height (`above + below + 5`)
equals that label's texture height exactly**, which is both how USA renders each
row at its own size and a self-check that the extraction is right.

The call structure is identical in both games, so USA's constants transfer.
`rowargs.py` simulates registers over an overlay and reports each call's
arguments; `quadscan.py` does the same for the label draws, labelling calls by
the resource-name string; `brf_widen` diffs the two overlays and emits the patch
lists, so the build follows the discs rather than any hardcoded number.

| | s00 | s01 | s02 | s03 | s04 | s05 | s06 | s07 | s08 | s09 | s10 | s11 | s12 | s13 | s14 | s15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Integral adv | 20 | 20 | 20 | 20 | 20 | 20 | 20 | 17 | 17 | 17 | 17 | 17 | 17 | 17 | 17 | 17 |
| USA adv | 20 | 20 | **27** | 17 | 17 | 17 | 17 | 16 | 16 | 16 | 16 | 16 | **26** | **26** | 16 | 16 |
| USA xl | — | 29 | 10 | 29 | 10 | 29 | 10 | 10 | 10 | 10 | 29 | 10 | 10 | 29 | 10 | 29 |
| Integral xl | — | 46 | 26 | 46 | 26 | 46 | 26 | 26 | 26 | 26 | 46 | 26 | 26 | 46 | 26 | 46 |

**Horizontal.** Integral's whole panel sits 20 game px right of USA's — the
vertical rule measures x 2101 vs 1921, 180 display px at 9 px per game px (the
scale is 2160/240, not the 8.75 an ink-width estimate suggests). The `xl`
constants differ by only 16–17, so the labels sat ~4 px left of where USA has
them relative to their own rule. Setting `xl = USA's xl + 20` places them
exactly; `xr` follows because the canvas is `xl + USA's width`. The rule itself
is not a poly either game writes — it is panel art — so it cannot be moved.

**Traps, all of which produced a wrong answer first:**

- A `jal` takes arguments from its **delay slot**. Scanning only backwards
  mis-attributes them by one call: that first put `br_s12`'s advance at
  `800C7228`, which is really `br_s10`'s.
- `br_s08`'s advance is `addu a3, a1, zero` — it reuses its own poly index 17
  as the advance, so it needs a replaced instruction, not an edited immediate.
- `br_s02`'s advance is `ori a3, s6, 10` = `17 | 10` = **27**. A simulator that
  handles only addiu/addu reports it as inherited and invites a guess of 20.
- Writing `$zero` in the simulator corrupts every later value; MIPS discards
  those writes.

Estimating from screenshots gave 28 for `br_s12` and 28 for `br_s02`; the
binaries say 26 and 20→27, and that **every** single-line advance was off by
1–3 as well. Measure to locate a discrepancy, then read the disc for the value.

**Known residual.** USA's box top is `y - above` with `above` 2–4 per label;
Integral's is `y`, so rows sit 2–4 px lower than USA's relative to the rule.
Fixing it means making the box `[y-4, y+H]` and placing each label's art at
canvas row `4 - above`. The positioner has a free slot for it — `sh a0, 8(v0)`
writes x0 back unchanged — but the highlight box (`brf_800C6930`) derives its
own geometry from the same `base_y` and would need the matching shift, so this
is untested and deliberately not applied.

### Constraints that must all hold### Constraints that must all hold### Constraints that must all hold

`pcx4.py` decodes/encodes the format: standard PCX, 1bpp × 4 planes, 128-byte
header, RLE where `code > 0xC0` is a run of `code - 0xC0`. The RLE stream is
**row-wide** — `PcxInflate4` decodes `stride * nplanes` bytes as one stream, so
runs cross plane boundaries.

1. **Width must be a multiple of 4.** `DG_LoadInitPcx` does `w /= 2` then
   `tex->dim.w = w / 2`, and `PcxInflate4`'s inner loop ends early when the
   remaining byte count is not a multiple of 4.
2. **Keep Integral's `px/py/cx/cy`.** USA's differ completely; using them
   uploads labels over the FILE menu and over the video timestamp.
3. **4-byte alignment.** Every archive entry size must be a multiple of 4. An
   unaligned entry misaligns everything after it and the loader takes a wild
   jump (seen as `pc: 30824000`).
4. **The U coordinate must not overflow.** `DG_SetTexture` keeps
   `off_x = (px % 64) * (16 / bpp)` in **texels**, and `brf_800C983C` sets
   `poly->u1 = off_x + w + 1` into a `u_char`. So the real limit is
   `(px % 64) * (16 / bpp) + w + 1 <= 255`, which is stricter than the
   unit-wise page test and supersedes it. Over 255 the U wraps and the quad
   samples across the whole page as vertical stripes.

   The V axis has the same limit: `off_y = py % 256`, `poly->v2 = off_y + h`,
   which also keeps a texture inside one 256-row tpage half. `br_s14` broke on
   it when the row height went to 20 (`239 + 20 = 259`).

   The U form was the navigation-order garble. `br_s09`/`br_s11` at `(928, …)` 128
   wide gave `128 + 128 + 1 = 257`; the unit test `(928 % 64) + 32 <= 64`
   passed because 32 + 32 = 64 exactly. They were the only two labels over the
   limit and the only two that garbled. Moving them to `px = 896` (`off_x = 0`)
   fixes it. Max across the build is now 249.
5. **Occupancy needs real colour depth.** The archive is 47 textures at 4bpp and
   4 at 8bpp; VRAM units are `ceil(w * bpp / 16)`, not `ceil(w / 4)`.
6. **CLUTs are on a 16-unit stride** and every label's is exclusive, so raising
   `n_colors` from Integral's 5 to USA's 16 fits exactly. Palette and
   `n_colors` must come from the USA artwork.

`brf_build.py` asserts every quad equals its texture, plus 1–5 above. That
assert caught a real bug: `brf_quads_all.json` had recorded `br_s12`'s `yb` at
`800CA214`, which is actually its `xl` (`addiu a3,zero,26`) — the patch had been
moving br_s12's left edge, and both immediates being 26 hid it.

## Audit against the decomp

Findings from re-checking the shipped work against the decompiled source.

**The overlay entry point does not need pinning.** Every overlay carries its
entry address in its own header: `obj/preope.bin` word[1] is `800C4DA4`,
`obj/option.bin` word[1] is `800C93A8`, and the build writes it. Nothing else
references either address — an exhaustive search of `int1.exe`, `STAGE.DIR`,
`BRF.DAT`, `DEMO.DAT` and `RADIO.DAT` for the literal word and for genuine
`lui`+`addiu` pairs finds only the overlay headers themselves. The one apparent
hit in `int1.exe` forms `800B4DA4`, a different address.

`opt.c` proves it empirically: our changes moved `NewOption` +100 bytes from
retail's `800C9344` to `800C93A8`, the header followed, and the option screen
works in game. So the documented reason for `preope_reserved()` is wrong, and
the −152-byte shift that once killed the host process had some other cause. The
padding is retained untested; removing it would free ~100 bytes in an overlay
that has a hard size limit.

**"GCL chain size ceiling" names a symptom, not a mechanism.** `libgcl/parse.c`
imposes no limit on the number or total size of chain records — records are read
in place by pointer, `argbuffer[32]` holds command arguments only, and the
1-byte length field caps a single record at 255 bytes, which nothing here
approaches. The stage buffer is `GV_GetMaxFreeMemory(GV_NORMAL_MEMORY)`, so a
memory interaction is the likely mechanism; our `Work` also grew 14,336 bytes
(184 → 248 entries × 224). The 9,567–10,304 threshold is real and reproducible,
but its cause is still unidentified.

**Leaving the GCL cursor short is safe.** Replacing MG2's 152
`GCL_GetString(GCL_NextStr())` calls with a blob walk leaves `next_str_ptr` 152
records behind. `preope.c` reads the chain in only three places (lines 810, 819,
829), all before that point, and the interpreter tracks its own `commandline_p`,
so nothing downstream is affected.

**`option_char_width()` is dead code.** It returns 24 for entries 4 and 5, but
`font_set_kcb` clamps: `w2 = (rect.w * 4) / (c_skip + 12)` = 21 for a 64-word
column, and `if (width > 0 && width <= w2)` fails, so `c_width` stays 21. Those
two lines render correctly anyway — `font_get_buffer_size` gives a 252-pixel
buffer and the proportional font fits 23–24 English characters in far less.
Harmless, but the comment claims an effect it does not have.

**Verified correct.** `f924[8]` → `[12]` is a genuine fix: `f920` is tested
against 11 and used to index `f924`, so retail wrote four ints past the end into
`kcb[0]`. `dword_800C3218` entry 12's `num = 1` really does centre
(`rect.x = x - max_width / 2`). Both `opt.c` and `preope.c` are fully decompiled
with no `INCLUDE_ASM`, so growing their `Work` structs is safe. The
45-character wrap is consistent with the formula, not just with testing.

**Stale comment.** `option_column_x`'s comment says entry 12's texture sits "at
832"; the code assigns `option_column_x[1]` = 896. The layout is sound — entry
12 occupies x 896–1021 at y 256–276 and column 3 starts at y 277 — but the
number in the comment is wrong.

**Fixed.** `preope.c` compared the string terminator against a literal 0x00 byte
embedded in the source rather than the `'\0'` escape, which made the whole file
binary to `grep` and `diff`. psyq compiled it identically (`obj/preope.bin` is
byte-for-byte the same before and after, entry still at `800C4DA4`), but any
tool that re-saved the file would have silently dropped the byte.

## Achievements

Per upstream (nuggs), the `DisableRAM` + `DisableCDROM` combination in
`MGSM2Fix.ini` will work for suppressing achievements. There is no dedicated
option. Untested here.
