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
| `en_brf` | briefing menu labels (20 PCX textures, quads, USA's row arithmetic and `above`) |

`en_menu3` is disabled — it crashes with `GCL:WRONG CODE` walking a RAM buffer,
cause never found.

## Gotchas

Everything below cost at least one broken build. Sections further down have the
detail; this is the index.

### Diagnosing a freeze or crash — do these two things first

1. **Compare the rebuilt overlay's size with retail's, and check whether the
   diff touches `f924`.** Size is cheap insurance; `f924` is the mechanism.
   Growing `f924` past retail's 8 is a genuine freeze (see Overlays below).
2. **Bisect against a stock run before theorising.** Move the PPF aside and
   confirm the fault is even ours; then split it (overlay vs chain, then edit
   by edit). Every mechanism I reasoned my way to without doing this — an
   uninitialised array, the font atlas, a struct overrun — was wrong.
3. **A freeze leaves no trace in `MGSM2Fix.log`.** The last lines are always
   the periodic `check_write_mgs_savedata`, identical to a clean exit, so the
   log cannot tell you a freeze happened or where.
4. Symptoms mislead about *locality*: an overlay 32 bytes too large froze only
   the EXIT row, which looks exactly like a bug in the EXIT row.

### Overlays

- **Keep an overlay at or under retail's byte count** — but as insurance, not
  because it is the mechanism. The `+108` / `+32` / `+0` bisection that produced
  this rule was **confounded**: the commit that reached +0 also reverted
  `f924[12]` to `[8]`, and that is the real freeze. Overlays load into the BSS
  tail at `StageCharacterEntries` with ~118 KB of headroom (the largest stage
  overlay on the disc is 143,856 bytes against option's 25,842), so +32 bytes
  cannot plausibly overflow it. The padded sector slot (26,624) is not a limit
  either.
- **Do not "fix" retail's quirks — `f924` above all.** It is indexed
  `f924[work->f920]` and the cursor states run to 11, so states 8..11 read and
  write `kcb[0]`'s first bytes. Retail depends on what it finds there: enlarging
  the array to 12 redirects those reads to freshly-zeroed slots and changes which
  branch each state takes, which is the EXIT-row hang. Leave it at 8.
  The retail key-config init likewise writes `f2AFC[7..16]` past a 4-entry array;
  that one *is* inert (it stores literal 0 into already-zeroed memory, and
  entering KEY CONFIG re-stamps all 17 of `f2B0C[0..16]`), so growing `f2AFC` is
  safe where growing `f924` is not. Know which is which before you touch either.
- A struct field change shifts every later offset, so the recompiled overlay
  differs from retail in ~20 KB of bytes. That is normal, not a red flag.
- `build/*.matching.bin` is byte-identical to retail, so **the decomp is
  trustworthy** — any misbehaviour in a rebuild comes from your own edits.
- `FAIL: does not match target hash` from `build.py` is *expected* for the
  overlays we deliberately modify (`option`, `preope`).
- Overlays carry their own entry address in their header; entry points do **not**
  need pinning.
- Work areas are `GV_NewActor(EXEC_LEVEL, sizeof(Work))`, so growing `Work` is
  safe for the allocation — but not for the size limit above.

### Font and text rendering

- **`c_width = (rect.w * 4) / 12` implies 12 px per character, but the ASCII
  font is proportional.** This one formula caused two separate broken builds:
  an unnecessary font-atlas repack, and lines wrapped at the wrong width.
  Compute real widths from `font.res` (`glyph_widths()` in `optbright.py`).
- **The wrap limit is `kcb->width - 12`, not `kcb->width`** —
  `font_print_string` subtracts 12 unless `FONT_NO_KINSOKU` is set, and opt.c
  passes flag 0. So 240 px at the default 21-character budget, not 252.
- **`max_width` is one byte**, loaded `lbu`, so 255 px is a hard ceiling. The
  decomp declares it `char`; PSY-Q's plain `char` is unsigned and retail emits
  `lbu`, which is why it works.
- **Wrapping is not cosmetic — it smashes the heap.** The continuation is drawn
  18 rows down inside a 20-row band, so it lands on the CLUT row at band+20
  (multicoloured pixel noise) and keeps writing ~1.4 KB past the
  `row * height + 32` buffer. Visible result: doubled overlapping lines and
  wrecked palettes; real result: a freeze on the next screen that allocates.
- **Never size lines off USA's art — and compare like with like.** The glyph
  widths are in fact *identical* between the builds (measured ink-to-ink on
  matching Previous Operations pages: 261 vs 261, 306 vs 306). An earlier note
  here claimed Integral's were wider, from comparing a *computed advance* against
  a *measured ink extent* — different quantities. Compute advances from
  `font.res` (`glyph_widths()` in `optbright.py`) or measure ink on both screens
  in one pass, never one against the other.
- Trailing-space padding widens `max_width` too, so **pad only the shortest
  line** when balancing chain lengths.
- Zenkaku (2-byte) glyphs cost a flat 12 px. `90 1B` is ○ and `90 18` is ✕,
  mixed inline with ASCII — precedent already shipping in `int1_en.exe`
  (`Press \x90\x1b to zoom in,`).
- `font.res` is not addressable by tag id — it lives in the `init` stage and is
  found by signature (`>II 392, 2306`). Table 1 is 96 big-endian words for
  ASCII 32..127; width is bits 27:24.
- Text visibility is the font **CLUT colour**, and all 31 entries are reset to 0
  before the per-state switch — so lighting an entry in a new state is safe, and
  blanking one is just omission.
- All entries are printed once at init and drawn every frame; their positions
  are read from `dword_800C3218` at print time.
- For these option entries the ink lands at exactly the table's x and
  **table y + 16**. Calibrating that offset against *kanji* gave +15 and put
  everything 1 px low.

### The GCL text chain

- Records are `07 <len> <payload> 00`, starting at script+0x1B8.
- **Fix container sizes with `gclparse.containers_over`**, not the hardcoded
  offsets an older note lists — it finds every enclosing size field.
- **Keeping the chain delta at exactly zero avoids container arithmetic
  entirely.** Prefer it: a −8,055-byte shift crashed the script at `set map`
  with no exception, and every edit that has ever worked moved things by at
  most +780.
- Empty records (payload = a single NUL) render zero-width and are harmless —
  USA ships 24 of them.
- `GCL_GetString` returns a pointer *into* the chain; the text is read in place,
  so there is no separate string table to update.

### Textures and quads

- **The texture is stretched to a hardcoded quad**, and `SetPacketTexture`'s UVs
  span the whole texture, so changing texture size alone does nothing. The
  selection highlight follows the same quad.
- A label's height is already in the poly: `v2 - v0`.
- `off_x + w` and `off_y + h` must both be ≤ 255 (`u_char` UVs); overflow shows
  as vertical striping.
- PCX here is 4-plane 1bpp with row-wide RLE, `PCXINFO` at offset 74 (stamp
  12345), width a multiple of 4, CLUTs on a 16-unit stride.
- Many polys have **two writers** — a settled layout block and an animated
  reveal dispatched from a jump table — and which one wins varies per submenu.
- To find version-exclusive art, **diff the two builds' DARs**: that is how
  USA's `sc_text` turned up as the only texture Integral's option stage lacks.
- **A quad constant is settled only by a like-for-like screenshot after
  deploying — not by copying USA's, not by deriving it.** USA draws `sc_text` at
  `y0 = 2`; the same constant here landed 12 rows high. The measurement-derived
  `y0 = 14` was right and an adversarial review talked me out of it. The two
  builds' draw environments differ in a way neither the decomp nor USA's binary
  shows. Deploy, shoot both, diff.
- **Pin every build input; a step that reads "whatever is deployed" will one day
  read its own output.** Moving that output aside is not a fix — it drops
  whatever the *previous* deployed file contributed. And re-run the static
  checks on the build you actually deploy, not the one before it.

### Reading disassembly

- USA's brf/option overlay base is **0x800C5970**, Integral's **0x800C3208**.
  Match functions by call count, never by address.
- A `jal` takes arguments from its **delay slot** too; scanning only backwards
  mis-attributes them by one call.
- **Never write `$zero`** in a register simulator — MIPS discards it, and a
  simulator that doesn't corrupts everything downstream.
- A linear simulation cannot be trusted on a **conditionally-assigned
  register**; look for every write before believing one.
- Resource ids are `GV_StrCode` hashes computed at runtime from strings in
  `.rodata`, so they are **not** immediates in the code — grep the overlay for
  the name instead.

### Measuring from screenshots

- Scale is **9 display px per game px** (2160/240) with a 480 px x offset.
  Verify it against something with a known texture row — the brightness screen's
  green line is `sc_back_l` row 92, i.e. game y 100.
- **Measure against the user's shots of both games, per submenu, before
  concluding anything is exact.** The briefing rows were believed within 1 px;
  against the user's USA shots they were 4 / 1 / 12 rows off per submenu, and
  the shots also showed the "highlight" function being patched was a different
  feature entirely. Use a fixed element (the FILE column) as the framing
  control, exclude the rule from the label band, and compare highlighted to
  highlighted.
- Measure **ink centroids, not band tops**: a highlighted row's glow moves a
  threshold's idea of where ink starts by 2–3 px, the same size as the effects
  being chased.

### PPFs and deployment

- Ketchup loads every PPF in `mods/INTEGRAL/INTEGRAL/{0,1}`; the log line
  `[Ketchup] base path is mods\INTEGRAL\INTEGRAL\0` confirms it picked them up.
  Keep patches in separate files so they can be disabled individually.
- Our PPFs carry **no undo data** and no Integral disc image is on disk, so
  `ppfgen.py`'s LBA lookup is unusable. Recover the mapping from a deployed PPF
  and prove it on every record (`optbright.py` does this). Disc 1 is LBA
  136654, disc 2 is 105178, both mode 2 form 1 (24-byte sector header).
- A PPF record's length is **one byte**, so split runs at 255 bytes *and* at
  2048-byte sector boundaries.
- Regenerating a PPF in place destroys the reference you were verifying
  against — save a baseline copy first; it is also your revert path.

### Toolchain and environment

- Build with `PSYQ_SDK=D:/mgsbuild/psyq` from `D:/mgsbuild/d/build`
  (`py build.py`). The SDK path default in `build.py` is wrong for this machine.
- `obj/option.bin` is the modified overlay; `build/option.matching.bin` is the
  pristine one.
- **Do not author Python through shell heredocs.** Escapes get eaten — `\x00`
  became a literal NUL byte in a source file twice, and a `str.replace` silently
  matched nothing. Write files with an editor tool.
- The console is cp1252: printing a 0x90 byte raises `UnicodeEncodeError`.
  Escape non-ASCII before printing.
- `MGSM2Fix.log` contains `exceptions are enabled` for every script VM it hooks,
  so a log filter must not grep for `exception`.

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
12-pixel glyphs; the font is proportional. Compute real widths from `font.res`
(`glyph_widths()` in `optbright.py`) — see the Gotchas.

Previous Operations no longer wraps at all: it uses USA's own line breaks
verbatim (to 54 characters), because the recap draws each line as two sprites
totalling 384 px. The option screen is the tight one at 240 px, which is why
the brightness paragraph is re-wrapped to 36.

## Not ported yet: the KEY CONFIG screen

**The Master Collection intercepts KEY CONFIG with its own UI, so porting these
is invisible there.** It is recorded here for a future patch aimed at raw PSX
disc images, where the in-game screen *is* what you see — and it is still
Japanese.

Eight `option` DAR textures need USA's art. All are 4bpp; sizes differ because
the Japanese and English labels differ, so this is the same job as the 20
briefing labels (swap the art, place it in VRAM, keep the quad equal to the
texture — see the briefing section):

| texture | Integral | USA | USA VRAM | USA CLUT | colours | reads |
|---------|----------|-----|----------|----------|---------|-------|
| `key_button`  | 88x12  | 88x13  | (128,492) | (1008,234) | 15 | ボタンタイプ → button type |
| `key_sykan`   | 88x12  | 112x13 | (80,480)  | (928,234)  | 16 | シュカンモード → first person view |
| `key_syukan`  | 60x7   | 88x10  | (208,480) | (960,234)  | 16 | |
| `key_normal`  | 52x6   | 40x10  | (175,492) | (992,235)  | 11 | NORMAL → normal |
| `key_reverse` | 64x6   | 44x6   | (11,504)  | (768,236)  | 10 | REVERSE → reverse |
| `key_action`  | 64x7   | 32x8   | (175,502) | (976,235)  | 11 | アクションボタン → action |
| `key_buki`    | 44x7   | 44x7   | (0,504)   | (896,235)  | 12 | ブキボタン → weapon (same size, 287 px differ) |
| `key_hohuku`  | 52x7   | 28x8   | (120,256) | (1008,235) | 10 | |

Everything else on that screen is already pixel-identical: `key_option`,
`key_symbol`, `key_a`, `key_b`, `key_c` byte-for-byte, and `key_back_l`,
`key_back_r`, `key_pad` identical once rendered (their indices differ, their
colours do not).

Note `key_normal` and `key_reverse` are already Latin in Integral, but in a
bolder all-caps face; porting them changes the style to USA's lowercase.

## Also not matched: the brightness grey ramp

`sc_back_r`'s greys are uniformly **7 levels darker** than USA's
(72/64/56/48/40 against 79/71/63/55/47), which moves 40% of that half's pixels
by delta 7, plus ~68 pixels of real element difference; `sc_back_l` differs in
550 pixels. Invisible in normal use, but this is a brightness *calibration*
screen, so the ramp values are arguably the content. Both are straight art
swaps if it ever matters.

## Not tested

Disc 2 in game — its `preope` stage is byte-identical to disc 1's and its option
stage produced an identical PPF record set, so the same builds are used and both
discs' PPFs are generated together.

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

### The `above` offset: read back from the texture's VRAM row

USA's box is `[y - above, y + below + 5]` with a per-label `above` of 2, 3 or 4
(its positioner's fifth argument; `rowargs.py` extracts all 16). Ours was
`[y, y + h]`, so every label sat `above` rows low relative to its row anchor —
and, worse, the row anchors themselves were not USA's (next section), which is
why an earlier pass measured "9 of 16 exact" and concluded the shift was not
worth fixing. Measured against the user's USA shots, no label was exact.

`above` is not derivable from the poly, and the positioner has no slot for a
table lookup — but it already reads the poly's `v0`, which is the texture's
VRAM row (`off_y = py % 256`), and **we choose `py`**. So the builder places
each `br_sNN` at `py % 8 == above` and the positioner reads it back:

    lbu  a0, 29(v0)      v2
    lbu  a1, 13(v0)      v0 = py % 256
    subu v1, a0, a1      h = texture height
    andi a1, a1, 7       above
    subu a0, a2, a1      top    = y - above
    addu v1, a0, v1      bottom = top + h        (== y + below + 5)
    sh a0,10 / a0,18 / v1,26 / v1,34

Ten of the eleven slots, `a2` intact for the `y + advance` return. Box height
is unchanged, so the selection glow (which follows the quad) is unchanged. The
placement constraint moved 15 of the 16 labels in VRAM; `brf_build.py` asserts
`py % 8 == USA_ABOVE[tid]` for every label after the rebuild.

### Where each list starts: USA's arithmetic, not Integral's

Both builds centre a submenu's list on the total height of its items, from
different formulas. Measured from the user's shots (left FILE column identical
in every pair, so the framing is the same), the right column sat **4 rows high
in operation outline, 1 row low in operation member and 12 rows high in
detailed information** once `above` was accounted for. The item count `n` is a
runtime variable (briefing flags at `work+128/136/144/164/176/184`), so the
constants had to become USA's formulas, not USA's values:

    outline    s0 = -41 - (20n - 15) / 2        Integral: (20n - 7)     800C6EEC  -7 -> -15
    member     s0 = -21 - (20n -  5) / 2        Integral: (20n - 7)     800C6FE4  -7 -> -5
    detailed   s0 =   9 - (16n + 10d - 11) / 2  Integral: ~((17n-4)/2)  800C7100  22-word rewrite

`d` is the number of two-line labels (1, or 2 once `br_s13` unlocks); the
rewrite fits in the block's own three `nop`s and drops the redundant signed
halving (the value is always positive). For the user's save (n = 1 / 3 / 6)
all three now compute exactly USA's `-43 / -48 / -38`.

**Still different:** USA's member block has a second branch — with 4 or 5
items it switches `br_s03..s06` to a 17-row advance, `br_s02` to 27, and
`s0 = -21 - (17n - 2) / 2`. Integral's advances are fixed immediates with no
free register to make them conditional, so once Meryl / support crew unlock
the member rows will sit 4 rows apart from USA's. Everything else follows `n`.

### The rule constants are USA's own

With each submenu's half-height `v` now USA's, the rule needs no compensation:
top `s0 - 4` (Integral drew `s0 - 2`), bottoms `v - 36`, `v - 16`, `v + 14` —
USA's immediates verbatim. The earlier `-43` / `-12` were corrections for the
different `v`; the lengths already matched (12.8 / 62.8 / 102.8 game px) and
only the tops move with the rows.

### `brf_800C6930` is not the selection highlight

It was patched as one (box `[y, y+5]`, bar `[y+5, y+6]`), on the belief that
USA's `above` was the label's. It is not: the function positions two
untextured polys per **flag-gated item** — (27,28) `br_s01`, (29,30) `br_s03`,
(31,32) `br_s05`, (33,34) `br_s10`, (35,36) `br_s13`, (37,38) `br_s15` — drawn
only while that item's flag is 1, at that item's row, coloured 0x46/0x50/0x4B.
Integral draws box `[y-4, y+10]` and bar `[y+10, y+11]`; USA's version
(`800C910C`) takes a fifth argument `K` and draws bar `[y+3, y+4]`, box
`[y-K, y+3]`, with `K = 10` except `br_s03`'s site (18) and `br_s13`'s (14).
The function is rewritten to USA's geometry, deriving `K` from the box poly
index in `a2`, in the twelve dead x-copy slots. **Unverified in game**: the
user's save has none of those flags set, so nothing draws them yet. The real
selection glow follows the label quad and already measured identical to USA on
every highlighted label (top/bottom gaps to the text equal within 0.3 px).

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

All three rules now use USA's constants; see "The rule constants are USA's
own" above. (An earlier version compensated for Integral's different `v` with
`-43` / `-12`; those are gone.)

### Horizontal: move the whole group, not just the labels

Integral's submenu sits **20 game px right of USA's**. The FILE column already
measures pixel-identical to USA, so both games share the actor origin — which
means this is genuinely different chrome, and USA's `xl` values are the target
rather than an offset from Integral's.

Moving the labels alone never worked: it either broke the label-to-rule gap or
pushed `the terrorists' armament` (128 px) off the 160 px edge. The rule has to
move with them, and every x involved is an immediate:

    800C6F28   s6  19 -> -1     vertical rule left    (polys 26 / 40 / 42)
    800C6F38   s5  23 ->  3     vertical rule right
    800C6F18   s4  addu s4,a3,zero -> addiu s4,zero,0
                               connector right end   (polys 25 / 39 / 41)
    label xl        26 -> 10, 46 -> 29   (USA's values)
    800C7674/76A4   26 -> 10             br_s00's animated x

**The layout block is not the last word on x.** Every rule and connector is
rewritten by an animated reveal (`x = 11p - K`) dispatched from the jump table
at `800C74C0`, and for the *outline* submenu that block is still active once
settled — so it won, and that rule stayed at game x 20, sitting inside
`infiltration method`, while the others followed `s6`/`s5` to 0. The animated
constants need the same shift:

    800C73A0  -46 -> -66   p25 connector right end
    800C7424  -24 -> -44   p39 connector right end
    800C745C  -46 -> -66   p41 connector right end
    800C74FC  -47 -> -67   p26 outline  rule x0/x2
    800C7508  -43 -> -63   p26 outline  rule x1/x3
    800C7580  -25 -> -45   p40 member   rule x0/x2
    800C7584  -21 -> -41   p40 member   rule x1/x3
    800C75B8  -47 -> -67   p42 detailed rule x0/x2
    800C75C4  -43 -> -63   p42 detailed rule x1/x3

The connectors' **left** ends (`-46` and `-24`, separate immediates) anchor to
the FILE column and stay. Lesson: after moving anything in this menu, check for
a second writer — the settled frame and the reveal animation set the same fields
from different code, and which one wins varies by submenu.

`s4` is `addu s4, a3, zero` — it reuses `br_s00`'s **advance** of 20 as an x
coordinate, so it needs a real load rather than an edited immediate, and `a3`
must keep its 20. The connectors' left ends (`-46` at `800C6F14`, `-24` at
`800C700C`) are anchored to the FILE column and stay put.

At USA's `xl` nothing overflows (family A 10 + 128 = 138, family B 29 + 120 =
149), so the earlier right-edge clamp is gone and both families sit at USA's
real indent. An assertion keeps it that way.

### Constraints that must all hold

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

## Option → SCREEN (brightness) screen

Ported by `optbright.py`. The two builds draw this paragraph by **completely
different mechanisms**, which is why no amount of searching USA for the English
text worked at first.

**USA draws it as one texture.** `option`'s DAR carries `sc_text`
(`GV_StrCode` 0x2FBD), 232x70, 4bpp, VRAM (512,256) — a single image holding
six pre-rendered lines:

    Adjust the monitor brightness so the gray
    scale below the green line cannot be seen,
    for the appropriate brightness to play this
    game.
    Press the O button to return to the option
    screen.

Integral's `option` DAR has **no** `sc_text` and Integral's option overlay does
not contain the string `sc_text` at all, so there is no code to draw it. The
resource-name strings in the two overlays differ exactly here: USA has
`sc_text`, Integral instead has `int_op_language1/1_w/2/3/3_w`.

**Integral draws it as font text from the GCL chain.** `opt.c:2750` binds every
KCB entry from the chain in order:

    for (i = 0; i < 31; i++)
        work->fEC4[i].string = GCL_GetString(GCL_NextStr());

`GCL_GetString` returns a pointer *into the chain* (`libgcl/parse.c:193`), so
the text is inline in the option stage's 0xFF chunk, chain at +0x1B8. The
brightness lines are:

| record | glyphs | `dword_800C3218` x,y | content |
|--------|--------|----------------------|---------|
| 13 | 20 | 36, 110 | line 1 |
| 14 | 20 | 36, 125 | line 2 |
| 15 | 20 | 36, 140 | line 3 |
| 16 | 19 | 36, 155 | line 4 |
| 24 | 18 | 36, 175 | `○ボタンでオプション画面に戻ります。` |
| 27 |  1 | 110, 300 | the parked colon — USA shows none |

The 15 px row pitch and the 20 px gap before record 24 match the screenshot
exactly (measured 65 px from line 1 to the ○ line; the table gives 175-110=65),
which is what identifies the records without a glyph table. Record 24's first
glyph is `901B` (○); record 25 is the same sentence without `○ボタンで`, used
by another submenu.

### Why the fifth line is not simply "no English counterpart"

Integral shows five lines; USA shows four. It is tempting to treat
`○ボタンでオプション画面に戻ります。` as Japanese-only and leave it, but it is
**not** — lines 5-6 of `sc_text` are its English counterpart, authored by
Konami. So this line can be ported without translating anything; it is only
USA's *option* screen that does not display those two rows of the texture.

### What the port needed — and the VRAM analysis that was wrong

**No VRAM work at all.** That is worth stating plainly because the first plan
here was a font-atlas repack, and it was built on a false premise. The formula
in `option_800C339C` / `font_get_buffer_size`,
`c_width = (rect.w * 4) / (c_skip + 12)`, reads like 12 px per character, which
makes a 42-character line need a 128-unit lane, which collides with the next
column, which forces a repack. Every step of that follows from the 12.

The 12 is only the *cell* size used to size the buffer. `put_hankaku_4bpp`
returns each glyph's own advance, so ASCII is **proportional**, and the wrap
test in `font_print_string` compares pixels:

    if (next_width > 0 && (x + dx + next_width + kcb->c_skip - 1) >= buf_width)

against `buf_width`, which is `kcb->width` = `(c_skip + 12) * c_width - c_skip`
= 252 px at the default 21-character budget, **less 12** — `font_print_string`
does `if (!(kcb->flag & FONT_NO_KINSOKU)) buf_width -= 12;` and opt.c passes
flag 0. So the real limit is **240 px**, and `option_char_width` can stay at its
default for all six lines: no lane, column or band moves.

The same bound shows up independently: `rect.w = kcb->max_width` and
`max_width` is a single byte, loaded `lbu` at 0x800C3598 in both retail's
overlay and ours, so 255 px is the engine's own hard ceiling for an option line
and the 240 px wrap sits inside it.

**USA's line breaks cannot be used verbatim, and this cost a broken build.**
USA's lines are 41-43 characters, and its `sc_text` renders them in 222-227 px —
so they look like they fit. They do not: Integral's half-width Latin glyphs are
wider than the font that texture was authored with. Measured on screen from our
own build, `"Adjust the monitor brightness so the gray"` — 41 characters —
renders **239 px**, one pixel inside the limit, and the 42- and 43-character
lines wrapped.

What a wrap does here is worth knowing, because it is not a cosmetic failure.
The continuation is drawn 18 rows down (`l_skip + 12`) inside a band that is
only 20 rows tall, so it lands on the CLUT row that sits at band + 20 — the
multicoloured pixel noise — and it keeps writing past `row * height + 32`
= 2,592 bytes of `GV_AllocMemory`, about 1.4 KB into the heap. The visible
result was overlapping doubled lines and corrupted palettes; the real result was
a heap smash that **froze the game** when a later screen allocated.

So the paragraphs are rejoined and re-wrapped to 36 characters, words untouched,
keeping USA's 4 + 2 line shape. Longest line measured 209 px, ~31 px of margin.
This is the same conclusion the preope recaps reached for the same reason, and
`integral-preope-three-limits` had already recorded the half of it that matters
most — that the formula's 12 px per character is not the font's real metric.
It does *not* say English fits USA's wrapping; measure our renderer, not USA's
art.

What the port actually changes:

1. `dword_800C3218` entries 13-16, 24 and 27 → x 43, y 118, 130, 142, 154, 166,
   178. USA's paragraph has a **12-row** line pitch with its first ink row at
   screen y 134 and ink left at x 43; measured on our own build, these entries
   put their ink at exactly the table's x and 16 rows below its y, so the table
   values are USA's positions less that offset. (The first attempt used +15 and
   x 42, from a calibration against *kanji*; the screenshot then measured ink at
   x 42 / y 135, which is where the 1 px corrections come from.)
2. Entry 27 — a colon USA never shows, previously parked at y=300 — takes the
   second line of USA's own wrapping. Its colour call moves from `case 5` (the
   vibration screen) to `case 7` (this screen). Colours are reset for all 31
   entries before that switch, so dropping it from case 5 blanks the colon
   there, which is what USA shows.
3. Records 13-16, 24 and 27 get USA's words on the 36-character wrap. The ○ is
   the font's own glyph `90 1B` mixed with ASCII, exactly as `int1_en.exe`
   already ships (`Press \x90\x1b to zoom in,`), and it costs 12 px rather than
   ~6, since `font_get_glyph_width` returns 12 for anything non-hankaku.
4. The chain delta is held at **exactly zero** by padding record 27 with 15
   trailing spaces, so no container size field moves and nothing after it
   shifts. A large negative shift has crashed this script before. The padding
   goes on the *shortest* line, because trailing spaces widen `max_width` too —
   padding a near-limit line would push it into a wrap.
5. The font atlas is retail's again — `option_column_x` gone, entry 12 back to a
   64-word rect, `option_char_width` deleted. Against `font.res` the three
   ported strings measure 174, 142 and 137 px in a 240 px lane, so none of that
   widening was ever needed, and removing it is most of what got the overlay
   back to retail's size.

### The overlay must not exceed retail's byte count

This is the hardest-won constraint in the whole stage, and it is not about
sectors. `option`'s overlay loads at a fixed address, so **one byte past
retail's 25,842 corrupts whatever follows it** — and the symptom is a freeze on
an option row that has nothing to do with the edit. Measured, by bisecting one
build at a time against a stock run:

| overlay | vs retail | KEY CONFIG row | EXIT row |
|---------|-----------|----------------|----------|
| 25,950  | +108      | freeze         | freeze   |
| 25,874  | +32       | ok             | freeze   |
| 25,842  | **+0**    | ok             | ok       |

The 26,624-byte padded slot is *not* the limit and is far too generous to
protect you; `optbright.py` asserts against retail's actual size, read from the
base image. Note how badly this misleads: at +32 only EXIT broke, which looks
exactly like a bug in the EXIT row. The earlier option work grew `f924[8]` to
`[12]` chasing that freeze, and that change — plus `option_char_width`, entry
12's 128-word rect and the column move — is *what pushed the overlay over*.
Growing a struct or adding a helper to fix an option-screen freeze is very
likely to cause one.

So before theorising about any option-screen freeze: **compare the overlay's
size with retail's.** Then bisect against a stock run. Both were skipped here,
at the cost of a dozen relaunches.

`f924` is back at retail's `[8]` for the same reason. Retail reads *and writes*
past its end into `kcb[0]` because the cursor states run to 11; retail tolerates
that, and correcting it costs 16 bytes of struct plus every offset after it.
Leave retail's quirks alone unless there is evidence they hurt.

**Superseded: the texture route shipped, and the paragraph is now pixel-exact.**
Everything above about the 240 px wrap and the 36-character re-wrap describes the
*font* path, which is still what the option screen's other entries use — but the
brightness paragraph is no longer one of them. See "The sc_text texture port"
below. The rest of this section is kept because the font limits it documents are
real and still bound every other entry on the screen.

For the record, the reasons this route was first rejected were both wrong. "No
spare poly" — the screen submenu's `POLY_FT4 field_5D4[4]` / `int f2AFC[4]` grow
to 5 harmlessly (see below), and the real bound was `GM_MakePrim`'s pack count,
not the arrays. "USA's runtime moves the quad" — it does not; USA's `sc_text`
string is referenced exactly once in its overlay and there is no second writer to
that poly. The apparent movement was my own coordinate-system error.

## The sc_text texture port

USA draws the brightness paragraph as **one 232x70 4bpp texture**, `sc_text`, on
a quad - never with the font. Integral had no such texture and no code naming it.
Porting it makes the paragraph pixel-exact, because it is USA's own artwork on
USA's own quad: USA's line breaks, USA's glyph rendering, all six lines, none of
the font path's limits. Built by `optsctext.py`.

| | |
|---|---|
| overlay | 25,830 bytes |
| DAR | 121,680 -> 125,856, 56 -> 57 entries |
| stage | 75 -> 77 sectors, relocated to **DUMMY3M idx 384** |
| sc_text | VRAM (512,256), CLUT (1008,237) |
| key_pad | moved (512,256) -> (512,326), which is what USA does |
| quad | `Init_Res(work, GV_StrCode("sc_text"), po, -121, 14, 111, 60, 0, 0)` — texture cropped to rows 0..45 |

### The three things that would have shipped as bugs

**`brf` is also relocated into DUMMY3M**, at idx 128..266, next to `preope`'s
0..89. The obvious slot - 90, just past preope - would have overwritten 40
sectors of the shipped briefing stage. Worse, a blankness check would have
*passed*, because PPFs are applied by the loader at runtime and never written
back, so the image on disk shows all 13,501 DUMMY3M sectors as zero. Occupancy
has to be composited from the deployed PPFs; `optsctext.py` does that and asserts
disjointness. Slot 384 leaves brf 256 sectors of growth room.

**`menu.ppf` writes chain records 4 and 5** ("screen brightness setup", "key
configuration setup") into the option stage. After relocation those writes land
on a stage the game no longer reads, so both labels would have silently reverted
to Japanese. The relocated image is therefore built from a **composite** of
retail plus the deployed *non-option* PPFs' STAGE.DIR writes plus a **pinned**
copy of the last font-text option build (`work/fonttext_disc{1,2}_option.ppf`,
`CHAIN_PPF`), and `verify()` asserts the 8 records in `EXPECT_CHAIN` (3/7 blank,
4/5/12/26 English, 13/24 English) before emitting.

**Never let the builder consume its own previous output** — this shipped as a
bug on 2026-09-02. Once the sc_text PPF was deployed, `composite()`'s "every
deployed PPF" included it, and its entry repoint would send the walk out of the
file; my workaround was to move the deployed option PPF aside before rebuilding.
That silently dropped the font-text PPF's 1,519 bytes of chain edits, so records
3/7/12/13-16/24/26 reverted to retail Japanese: "use directional buttons to
test" came back as `振動テスト...` with a garbled glyph (the user caught it). The
static record check had been run on the *previous* build, not the one deployed.
Now the input is pinned, any write to the entry pointer is a hard error, and the
record assert runs on every build.

**The quad's y: the two engines do not place the same constant in the same
place.** USA's own call is `(-121, 2, 111, 72)`. Deployed here, that rendered the
paragraph exactly **12 rows above** USA's on-screen position — measured `dy -12`
on all four lines with `dx 0`, i.e. horizontally pixel-identical, vertically
shifted. The measurement-derived `y0 = 14` (which an adversarial review had
talked me out of in favour of "just copy USA") turned out to be correct. Lesson:
neither copying USA's constant nor deriving one from a screenshot settles a quad
position — **only a like-for-like screenshot comparison after deploying does**,
because the two builds' draw environments evidently differ. One shot, measured,
fixed it.

**USA shows four lines; the texture has six.** Rows 47–69 (the ○-button
sentence) never appear on USA's screen, so the texture is cropped to rows 0..45
in the DAR (line 4 ends at row 45, row 46 is blank). Data-only, keeps the quad
1:1, and the crop is asserted to decode round-trip.

### Why the fifth quad rides the existing loop

Two ways to add it. Appending a `POLY_FT4` to the end of `Work` and copying it
explicitly leaves every existing field offset alone - but it needs a per-frame
40-byte struct copy, and measured **+156 bytes against 92 reclaimed**. Growing
`field_5D4[4]`/`f2AFC[4]` to 5 lets the existing copy loop carry it for nothing:
**-12**. The real allocation bound was neither array but `GM_MakePrim`'s pack
count for `field_2C`, 4 -> 5, which is heap.

Growing `f2AFC` shifts which `f2B0C` slots retail's key-config init overrun
zeroes, from `[3..12]` to `[2..11]`. That is inert, twice over: those writes
store literal `0` into memory `GV_NewActor` has already zeroed, and entering KEY
CONFIG sets **all 17** of `f2B0C[0..16]` before the screen draws. The
`f924` -> `kcb[0]` overrun relationship also survives, because `field_5D4` shifts
`f924` and `kcb` together.

### A correction on the overlay size limit

The Gotchas section says the option overlay must not exceed retail's 25,842
bytes, from a `+108` / `+32` / `+0` bisection. **That bisection was confounded**:
the commit that took it to +0 also reverted `f924[12]` to `[8]`, and *that* is a
real freeze mechanism - retail indexes `f924[work->f920]` with cursor states up
to 11, so states 8..11 read and write `kcb[0]`'s first bytes, and enlarging the
array redirects those reads to zeroed slots and changes which branch each state
takes. Meanwhile overlays load into the BSS tail at `StageCharacterEntries` with
roughly 118 KB of headroom - the largest stage overlay on the disc is 143,856
bytes against option's 25,842 - so +32 bytes cannot plausibly overflow anything.
Treat "stay at or under retail" as cheap insurance rather than the mechanism, and
treat **any** change to `f924` as the thing to be afraid of.

### Verification before deploying

`optsctext.py` asserts, and these all passed: a loader-style DAR walk consuming
exactly 57 entries with `remaining` hitting 0 and every entry 4-aligned; UV fit
(`off_x` 0 + 232 <= 255, `off_y` 0 + 70 <= 255, 58 units from a 64-aligned x so a
single tpage); DUMMY3M disjointness against the composited PPF map plus a
blankness read of all 78 target sectors on both discs; the STAGE.DIR entry
reading retail's 27,136 before being repointed. Then, end to end on **both**
discs: applying the emitted PPF to the disc image in `dlc_japan.bin` resolves
`option` to DUMMY3M idx 384 and reads the 78-sector block back byte-identical,
with exactly one record outside the slot (the entry repoint).

Verified in game 2026-09-02: the four paragraph lines occupy screenshot rows
1215-1286, 1323-1385, 1431-1502 and 1557-1601 in both the USA shot and ours —
pixel-identical placement — and the vibration-test help line is English again.

### Reverting

`work/backup_before_sctext/` holds all 12 PPFs from before this change, and
`fonttext_disc{1,2}_option.ppf` in that folder is specifically the previous
font-text option build. Copy those two back over
`mods/INTEGRAL/INTEGRAL/{0,1}/INTEGRAL_disc{1,2}_en_option.ppf` and the
brightness screen returns to the re-wrapped font text, which is positionally
exact but not pixel-exact.

Re-running the builder after deployment needs nothing moved aside: `composite()`
skips the deployed option PPF by name (it is this script's own output) and
takes the chain edits from `CHAIN_PPF` instead.

### Building and deploying

`optbright.py` needs `work/int1_stage.dir` (retail), `work/int1_stage_opt11.dir`
(whatever the deployed option PPF currently contains) and a rebuilt
`D:/mgsbuild/d/obj/option.bin`, and it rewrites both discs' option PPFs in
place.

No Integral disc image is on disk, so the STAGE.DIR LBA cannot be looked up the
way `ppfgen.py` does it. Instead the script **recovers the geometry from the
deployed PPF and proves it**: it solves `lba` from the first record, checks that
mapping against all 2,610 shipped records, and then re-encodes that same diff
and requires it to reproduce the shipped file byte for byte before writing
anything. Disc 1 is LBA 136654, disc 2 is 105178, both mode 2 form 1
(24-byte sector header).

### Dead ends, recorded so they are not repeated

`sc_back_l` and `sc_back_r` (160x224 4bpp, VRAM (80,256) and (208,256)) are the
full-screen background halves and are **textless in both builds** — they hold
the grey ramp, the green line, the 57/49/41/33/24/16/8/0 numbers and the grid.
Decoding and rendering both confirmed it.

The English paragraph is not ASCII anywhere: not in `us1.exe` (a PS-X EXE whose
SDK strings *are* greppable, so ASCII would have been found), `us1_stage.dir`,
`us1_brf.dat`, `us1_radio.dat`, `windata/alldata.bin` or either
`windata/dlc/dlc_*.bin`. `grep` on `alldata.bin` does find "screen brightness
setup" and "use directional buttons to test" twice each, which proves the search
was working. A delta-pattern search (invariant under any uniform additive
offset) and UTF-16/high-bit/XOR/0x81-padded variants all found nothing either.
The one `Adjust` hit in `us1_stage.dir` at 0x29915A2 is a false positive inside
a symbol map (`GM_ConfigMotionAdjust`); the two `monitor` hits are the source
filename `monitor1.c` in `s08b`/`s08br`.

USA's option chain really does have the paragraph slots empty. Its whole 680-byte
0xFF chunk holds 28 records of which only four are non-empty — `[4] screen
brightness setup`, `[5] key configuration setup`, `[12]` and `[26] use
directional buttons to test` — with `07 01 00` (a bare terminator) for the
rest, including 13-16.

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
