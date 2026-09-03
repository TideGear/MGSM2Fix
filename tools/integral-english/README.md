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
| `en_savemsg` | memory-card messages (`datasave.c` save/load caption tables in the executable) |

`en_menu3` is disabled — it crashes the title stage with `GCL:WRONG CODE`. See
"Why `en_menu3` crashes" below; diagnosed 2026-09-03, not yet rebuilt.

## Scope: what this port changes, and what it deliberately keeps

**Verbatim USA text, placed where USA places it. Everything else stays as
Integral shipped it.** Integral is the later release and its non-text
differences may be deliberate; they are kept unless they are text, a
translation, or the positioning of text and its chrome (rules, connectors,
highlight boxes that frame the text). Decided 2026-09-02, after the unlocked
briefing comparison surfaced differences that are real but not text:

| Kept from Integral | What it is |
|---|---|
| "watched" dimming colour RGB (70, 80, 75) | USA dims flagged items, connectors and FILE boxes to (90, 105, 95); Integral's `brf_800C6634` uses (70, 80, 75), 30 immediates 1:1. Only visible once items are flagged. |
| `br_back_l` right-edge seam | 154 stencil-mask bits differ along texture x 155–159; every other briefing texture is pixel-identical (palettes differ only in unused entries). |
| vertical rule brightness, FILE-box interiors, a few collage rows | Integral's rule renders ~201 grey against USA's 166, box interiors 24–32 against 0. Not attributed; the background fade (`(frame-28)*8`, identical in both) is not the cause. Nothing the port touched. |
| 1P MODE's twenty-one explanation pages (Japanese) | An Integral-only mode: USA has no 1P MODE, and Integral ships no English for the pages, so there is nothing to port and no translation is made. See "1P MODE" under Unlocks. |

So "pixel-identical to USA" for this project means: every glyph and every
piece of chrome that positions text lands on the same pixels; brightness and
art that Integral changed on its own are not chased.

### Audit against the rule (2026-09-02)

Every deployed change was re-checked against the scope rule. Findings:

- **Record 6 of the option chain (the EXIT row's help line, タイトル画面に
  戻ります。) had two corrupted bytes** — an `'e'` and a space from an English
  string, written at the wrong offset by an early font-text build and carried
  forward by the pinned chain input. On screen it read タ¥トル¨面に戻ります。.
  A text bug of the port. `optsctext.py` now restores every record the port
  does not own from retail and asserts it (`PORTED_RECORDS`).
- **Record 7, the colon Integral's Japanese help lines use (字幕設定：オン,
  サウンド設定：ステレオ …), had been blanked** to avoid an overlap on the
  vibration-test row. That removed Japanese text with no English counterpart —
  against the rule. Restored; the overlap is prevented instead by entry 27 no
  longer being lit in that state, and record 27's padding absorbs the byte.
- **Record 3, the vibration-test row's own label (振動テスト, lit with the
  sentence in state 5), stays blank — decided 2026-09-02.** Integral's line was
  振動テスト：方向キー左右で振動します。, i.e. the row's name plus a sentence
  that USA's `use directional buttons to test` already covers; the label adds
  nothing the English does not say, so USA's line alone, centred, is kept.
- Everything else is text, or the geometry that positions text: labels, rows,
  rules, connectors, highlight boxes, paragraph texture, pagination. Nothing
  changed a colour, blend or background texture.

Verified in game 2026-09-02 on all eight option rows: the four Japanese help
lines read 字幕設定：オン, 字幕言語設定：英語, サウンド設定：ステレオ, 振動設定：オン
with their colons; EXIT reads タイトル画面に戻ります。 cleanly; the three English
lines are unchanged.

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

- **A PPF record aimed at the executable must not cross a 2048-byte payload
  boundary.** Ketchup mirrors executable writes into RAM byte by byte with
  `sector = k / 2352; pos = k % 2352; if (pos >= 2048) skip`, so a record that
  runs from one sector's payload into the next spills its remainder into the
  304-byte tail and those bytes never reach RAM — while the log still says
  "loaded". `savemsg.py` splits every run at payload boundaries and replays
  Ketchup's rule as an assert; the first build lost 142 of 442 bytes this way.
  Check any executable patch with the replay: mirrored bytes must equal written.

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

**The screen IS visible in the collection with its patch flags on** (verified
2026-09-03 with `DisableRAM`/`DisableCDROM` `true`): the collection substitutes
its own button UI in its wrapper menus, but the game's own KEY CONFIG screen
renders normally, so this port is no longer invisible — it is the one screen
still fully Japanese in a build that is otherwise English. It also matters for a
future patch aimed at raw PSX disc images. Reference shots of both games,
unintercepted, are in `reference/keyconfig_*.{usa,int}.jpg`, and every label's
art from both discs is rendered side by side in `keyconfig-textures.png`.

The collection's button involvement elsewhere is real but separate: its Squirrel
`_update_option_button_setting` (`play_standalone_mgs.nut:844`) rewrites the
whole `GM_Configuration` word (`0xB4D9C`) every frame with its own button-type
bits — see the language-bit race under Unlocks.

**Label mapping, confirmed from the rendered art — the two `sykan` names are
swapped from what you would guess:**

| texture | Integral | USA | where it is drawn |
|---|---|---|---|
| `key_button` | ボタンタイプ | `button type` | top row selector, in a hexagon |
| `key_sykan` | シュカンモード | `first person view` | **bottom row selector**, in a hexagon |
| `key_syukan` | シュカンボタン | `first person view` | the △ button's label, top right |
| `key_buki` | ブキボタン | `weapon` | □ or ○, side depends on button type |
| `key_action` | アクションボタン | `action` | ○ or □, side depends on button type |
| `key_hohuku` | ホフクボタン | `crawl` | ✕, left |
| `key_normal` | NORMAL | `normal` | first-person mode value |
| `key_reverse` | REVERSE | `reverse` | first-person mode value |

`key_sykan` is the MODE row and `key_syukan` is the BUTTON label, despite the
names reading the other way round; both say `first person view` in USA, at
different sizes (112x13 in the hexagon, 88x10 as the button label), so swapping
them would look almost right and be wrong.

**Three things the shots settle beyond the label art:**

- **The labels change sides with the button type.** Type A draws `weapon` on the
  □ (left) and `action` on the ○ (right); type C swaps them. The same texture is
  therefore drawn at more than one position, so a port must place every quad for
  each type, not once.
- **`normal` / `reverse` are already Latin in Integral but in a bold all-caps
  face** (`NORMAL`, `REVERSE`), against USA's lowercase. Porting changes the
  style, which is a visible change with no text change — allowed under the scope
  rule, since it is USA's own art for the same words.
- **Integral has a bottom help line that USA has none of at all**, one per
  selected row: `ボタン設定 ： タイプA`, `主観モード時の操作 ： 通常操作`,
  `オプション画面に戻ります。` These are the same family as the option screen's
  Japanese help lines (the colon of record 7) and **stay Japanese** — Integral's
  own additions with no USA counterpart, exactly like 完了しました / 中です.

Eight `option` DAR textures need USA's art (all eight sizes below re-measured
from both discs 2026-09-03 and unchanged). All are 4bpp; sizes differ because
the Japanese and English labels differ, so this is the same job as the 20
briefing labels (swap the art, place it in VRAM, keep the quad equal to the
texture — see the briefing section):

| texture | Integral | USA | USA VRAM | USA CLUT | colours | reads |
|---------|----------|-----|----------|----------|---------|-------|
| `key_button`  | 88x12  | 88x13  | (128,492) | (1008,234) | 15 | ボタンタイプ → button type |
| `key_sykan`   | 88x12  | 112x13 | (80,480)  | (928,234)  | 16 | シュカンモード → first person view |
| `key_syukan`  | 60x7   | 88x10  | (208,480) | (960,234)  | 16 | シュカンボタン → first person view (the △ label) |
| `key_normal`  | 52x6   | 40x10  | (175,492) | (992,235)  | 11 | NORMAL → normal |
| `key_reverse` | 64x6   | 44x6   | (11,504)  | (768,236)  | 10 | REVERSE → reverse |
| `key_action`  | 64x7   | 32x8   | (175,502) | (976,235)  | 11 | アクションボタン → action |
| `key_buki`    | 44x7   | 44x7   | (0,504)   | (896,235)  | 12 | ブキボタン → weapon (same size, 287 px differ) |
| `key_hohuku`  | 52x7   | 28x8   | (120,256) | (1008,235) | 10 | ホフクボタン → crawl |

Everything else on that screen is already pixel-identical: `key_option`,
`key_symbol`, `key_a`, `key_b`, `key_c` byte-for-byte, and `key_back_l`,
`key_back_r`, `key_pad` identical once rendered (their indices differ, their
colours do not).

Note `key_normal` and `key_reverse` are already Latin in Integral, but in a
bolder all-caps face; porting them changes the style to USA's lowercase.

## Memory-card messages (`en_savemsg`)

`menu/datasave.c` in the executable keeps two 12-entry caption tables,
`saveCaptions_8009EB4C` and `loadCaptions_8009EB7C`, indexed by the low byte of
the save/load request code (`captions[(unsigned char)dword_800ABB58]`, codes
like `0x45000003`). The request codes are identical in both games — checked by
enumerating every `lui/ori` pair in both executables — so an index means the
same state in both, and the port is index for index. USA's tables live at
`0x800A12A4` / `0x800A12D4` (found from the strings they must contain, then
confirmed against the code that indexes them at `8004EBF0` / `8004EC2C`; a
first dump that guessed the table start was off by one and made the tables look
shifted).

| idx | Integral | USA | shipped |
|---|---|---|---|
| 1 | セーブが完了しました。 / ロードが完了しました。 | "" | Integral's (USA shows nothing here) |
| 2 | セーブできませんでした。 | Save failed. / Load failed. | USA |
| 3 | エラーが発生しました。 | Error occured while saving. / … loading. | USA |
| 4 | 空きブロックがたりません。 / セーブファイルがありません。 | No empty block. / No save file. | USA |
| 5 | メモリーカードが初期化されていません。 | Memory Card is not formated. | USA |
| 6 | セーブしました。 / ロードしました。 | Data saved. / Data loaded. | USA |
| 7 | フォーマットに失敗しました。 | Formating failed. | USA |
| 8 | メモリーカードがさされていません。 | Memory Card undetected. | USA |
| 9 | セーブ中です。 / ロード中です。 | "" | Integral's |
| 10 | メモリーカードをチェックしています。 | Now checking Memory Card. | USA |
| 11 | フォーマットしています。 | Now formating Memory Card. | USA |

**Which entries are live** (from `init_file_mode_helper_helper_80049EDC`):
index 9 is requested with `0x01000009` immediately before `saveFile()` /
`loadFile()` runs, so it is on screen *during* the write or read; index 1 is
requested with `0xC1000001` on the success path (`block_75`) right after the
operation returns — that is the live completion message. USA's entries at both
are blank: it shows no caption while saving and none after a success (its
confirmation is the separate "COMPLETE" label in the file-list UI, which
Integral also has in English). So after a save Integral flashes
セーブが完了しました。 where USA shows nothing — Integral's own extra text, kept
under the rule; blanking it to match USA would be a one-pointer change.
Index 6 (セーブしました。 / "Data saved." and the load twins) is **never
requested**: no `0x…06` code exists and the only other draw is a hard-coded
`captions[4]`. Those strings are dead in both games; ported for completeness,
never visible.

USA's spelling ("formated", "occured") is kept verbatim. Everything else in the
module is already English in Integral (SAVING..., LOAD DATA, LOADING..., NO
FILE, NO SPACE, COMPLETE, YES/NO, OVERWRITE OK?, FORMAT OK?, EZ/NM/HD/EX,
MEMORY CARD 1/2) or is Integral-only Japanese drawn alongside the English (the
上書きしますか？ / フォーマットしますか？ prompts) and stays.

Mechanism: the same as the item descriptions. The 17 Japanese strings are one
contiguous pool at `0x80011F18..0x800120CB` (435 bytes); the 13 English strings
plus the 4 kept Japanese ones (338 bytes) are repacked into it and both pointer
tables rewritten — nothing outside the pool and the tables changes, and the
tool asserts that. `savemsg.py` emits a PPF per disc addressed at the
executable's sectors (Ketchup mirrors executable writes into RAM, since the
Master Collection never re-reads the executable). Both discs' executables are
identical here. The caption is drawn into the codec message-board KCB
(`radio.c`, `font_set_kcb(kcb, -1, -1, 0, 6, 2, 0)`, 252 px buffer), the same
code in both games, so placement follows.

**Verified in game 2026-09-02:** LOAD DATA with no save present draws
`No save file.` on rows 211–219, x 126–195 in both games. The header above it
differs only because `DisableRAM` (achievements off) filters the Master
Collection's own rename of MEMORY CARD → STORAGE, so Integral shows the
original wording; USA's reference shot predates that setting. The in-game save
flow (Mei Ling) has not been shot yet.

Not yet built into a save title: Integral composes the save-slot name in
full-width Shift-JIS (`ＭＧＳ．［ＮＭ］ time area`, `datasave.c` ~2261) where USA
uses ASCII; the Master Collection's own storage UI shows those names, so this
is a separate question.

## Not ported at all: the VR disc (SLPM-86249)

Integral's third disc — VR training — is untouched. `mods/INTEGRAL/VR-DISK/` is
empty, so Ketchup applies nothing to it, and no tool here targets it. What is
known so far, for whoever starts it:

- USA's counterpart is `SLUS-00957` (VR Missions), inside `alldata.bin` at image
  base `0xD39B7000`; its STAGE.DIR has the same 106-stage layout as Integral's
  VR disc, so stage-by-stage comparison is possible.
- Its option/text chain is **not** at `+0x1B8` like the main game's `option`
  stage — the offsets in `optscan.py` do not apply unchanged.
- MGSM2Fix's Ketchup table lists it as title 99, version `VR-DISK` (disk 0, exe
  range `0x99800`); `EnglishText` and `UnlockBriefing` deliberately skip that
  version (no option language toggle to hold; no briefing menu).
- The VR disc has its own overlays and executable, so nothing from the main-game
  port (overlay patches, stage relocations, chain edits) carries over.

## Why `en_menu3` crashes (diagnosed 2026-09-03)

`menu2.py` ports the same five disc-swap messages ("Insert DISC 1.", "Press the
Start Button", "after inserting DISC 1.", "Now Checking...", "The correct DISC
was not inserted.") into three places. Two of them — the `demosel` and `change`
stages — shipped as `en_menu2` and work. The third, the `title` stage
(`menu2.py menu3`), crashes on entry with a run of `GCL:WRONG CODE <byte>` and
those bytes are **the English letters themselves** (`73 68 65 74 61 72 74` =
`s h e t a r t`, every second byte of "Press the Start Button"), i.e. the
interpreter is executing the replacement text as bytecode. It always follows
`> set map 32249` (0x7DF9, the `-m` string every stage-load carries).

The cause is *where* the title's copies live. In `demosel` and `change` the
strings are a standalone data chain that `GCL_GetString` reads. In `title` they
are **inline arguments inside the executable script body**: chunk offset 0x11B5
sits within the script body (0x10DE, length 850, ends 0x1430), in the `-v`
option of the title actor's `CMD 9906` at 0x1138. The interpreter walks that
region as a value list.

The conflict is the terminator. The renderer centres these strings, so trailing
spaces before the NUL shift the visible text left; `menu2.py` therefore writes
`English + NUL + spaces`, keeping the length byte untouched. In a data chain
that is harmless. Inside the script body, something resumes parsing at the
early NUL and lands mid-payload, where ASCII bytes are opcodes that each eat an
operand — the double-NUL trick fixes the odd/even case but not the fact that
execution resumes inside the text at all.

The fix is the method already proven on `preope`: instead of padding, shorten
the STRING value's length byte and shrink every enclosing container
(`gclparse.py`'s `containers_over` returns exactly the sized nodes — the
OPTION's `len`, the COMMAND's BE16 size, each enclosing ARG, and the script's
BE32 length). Then there is no padding and no early NUL, so nothing resumes
inside the text, and the centring is correct because the string really is
shorter. Not attempted yet.

## The collection shows only four of USA's six brightness lines (found 2026-09-03)

Comparing the collection against SwanStation (a much more accurate emulator)
running the same discs:

| | brightness paragraph |
|---|---|
| SwanStation, USA disc | **six** lines, ending "Press the ○ button to return to the option screen." |
| the collection, USA | **four** lines, ending "game." |
| SwanStation, Integral disc | four Japanese lines, a blank line, then the ○ line |

USA's `sc_text` texture is 232x70 and **contains all six lines** (decoded with
`pcx4.py`; the whole 70 rows are inked). The collection is therefore dropping
two lines of USA's own help text.

It is not a data or revision difference: the USA `option` stage extracted from
the collection's `alldata.bin` (base `0xF12F8000`, STAGE.DIR lba 132344, sector
27023, 81 sectors) is **byte-identical** to the same span of the real USA disc's
STAGE.DIR — all 165,888 bytes.

It is not caused by disabling achievements: the collection's USA shot showing
four lines is from 2026-08-31, and that session's log records
`bPatchesDisableRAM: false` and `bPatchesDisableCDROM: false`, i.e. every
collection patch active.

Position, measured with the text's own line pitch as the ruler so aspect ratio
and the collection's border art cancel out (anchor: the green line):

    SwanStation USA   first line 1.88 line-heights below the green line
    collection USA    first line 2.88 line-heights below the green line

So the collection draws the block **exactly one line lower** and 24 rows
shorter. That is the same +12-row offset already met when placing the ported
quad (`y0 = 2` in USA's code renders where `y0 = 14` puts it), and a symmetric
12-row inset top and bottom accounts for both numbers. What inside the
collection's renderer does it is not identified.

### It is four of the collection's own CD-ROM patches (settled 2026-09-03)

The test ran: with `DisableRAM`/`DisableCDROM` **true**, the collection's USA
draws **all six lines**, at 2.05 line-heights below the green line against
SwanStation's 2.01 — the same place. So the collection was truncating it, and
the truncation is four CD-ROM patches, found by mapping the log's
`filtering CD-ROM patch file disc1_<offset>_patch` names onto stage bytes:

    disc1_165A34CC  disc1_165A3BD8  disc1_165A4508  disc1_165A4E38
    -> USA option stage, tag 1 (DAR), all four inside the ONE 5852-byte
       `sc_text` entry, at payload offsets 0, 1500, 3548 and 5596

i.e. the collection replaces that whole texture, in 2048-byte pieces. Its
replacement keeps the 232x70 canvas and centres four lines in it, which is why
the block also sat 12 rows lower: 70 − 46 = 24, split evenly. The dropped
sentence is "Press the ○ button to return to the option screen." — the ○ name is
platform-specific, and the collection substitutes its own button UI everywhere
else too (it intercepts KEY CONFIG and rewrites the button bits of
`GM_Configuration` every frame).

**This corrected the port.** `SC_ROWS` is back to **70** and the quad back to
USA's own `Init_Res(work, "sc_text", po, -121, 2, 111, 72, 0, 0)`. The earlier
"measured, not copied" `y0 = 14` with a 46-row crop had been fitted to the
collection's replacement artwork, not to USA — so the adversarial review that
argued for copying USA's constant was right, and the screenshot that appeared to
refute it was of patched art. It also means the shipped build was **dropping a
line of text both originals have**, which the no-abridgement rule forbids.
Rebuilt and deployed 2026-09-03: DAR 121680 → 127508 (+5828), stage 75 → 78
sectors, still DUMMY3M 384 (brf at 128..266 untouched); revert PPFs in
`work/backup_sctext46_disc{1,2}.ppf`.

**Lesson.** The collection's patch set is part of the baseline. A constant fitted
to a collection screenshot is fitted to whatever the collection patched, and
changing the patch flags changes the target. Before deriving any constant from a
shot, check the session's `bPatchesDisable*` lines, and check whether the asset
appears in the log's filtered patch list.

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

USA's member block also has a second branch for four or five items; see "The
member submenu with four or five items" below — it is now replicated.

### The rule constants are USA's own

With each submenu's half-height `v` now USA's, the rule needs no compensation:
top `s0 - 4` (Integral drew `s0 - 2`), bottoms `v - 36`, `v - 16`, `v + 14` —
USA's immediates verbatim. The earlier `-43` / `-12` were corrections for the
different `v`; the lengths already matched (12.8 / 62.8 / 102.8 game px) and
only the tops move with the rows.

### `brf_800C6930` is not the selection highlight: it draws the tree connectors

It was patched as the highlight once (box `[y, y+5]`, bar `[y+5, y+6]`), on the
belief that USA's `above` was the label's. It is not. The function positions,
per **flag-gated, indented item** — (27,28) `br_s01`, (29,30) `br_s03`, (31,32)
`br_s05`, (33,34) `br_s10`, (35,36) `br_s13`, (37,38) `br_s15` — the two textured
`br_line2` quads of an **L-shaped connector**: a *drop* from the parent row down
to the item and a short *bar* into its label. Both games draw them only while
the item's flag is 1, which is why they were invisible until the unlock.

Geometry, from USA's `800C910C` (its fifth argument is `K`):

    bar   [y+3, y+4]        x 14..22   (Integral had [y+10, y+11], x 30..44)
    drop  [y-K, y+3]        x 13..17   (Integral had [y-4,  y+10], x 29..33; the
                                        texture's line sits one texel in: draws at 14 / 30)
    K = s4, except br_s03's site (s4+8) and br_s13's (14)
    s4 = 10 in the outline block, 7 if the member block takes its 17-row branch,
         and 6 in the detailed block (800C99AC)

Integral's function takes no `K`, so it now reads it from `t8` (seeded 10 in the
outline block, set to `t9-10` by the member block, 6 by the detailed block),
adds 8 when `a2 == 30` and uses 14 when `a2 == 36`. The x's live in
`GetResources` (twelve `br_line2` calls, six per quad type) and are patched to
USA's; the first attempt moved only the bars and changed nothing visible, since
the drop is what shows. The last pixel found was the detailed drops being one
row taller: USA's `s4 = 6` there, not the member's 7.

### The member submenu with four or five items: USA's second branch

USA's member block has two branches. Three items: advance 20 (`br_s02` 30),
start `-21 - (20n-5)/2`, connector `K` 10. Four or five (Meryl and/or the
support crew unlocked): advance **17** (`br_s02` 27 = `17|10`), start
`-21 - (17n-2)/2`, `K` 7. Integral's advances were fixed immediates, so the
block is rewritten (same 44 words, two spare): the advance lives in `t9`, the
K base in `t8`, and the start is `(t9*(n-1) + 15) / 2`, which is `20n-5` or
`17n-2` in one expression (`mult`/`mflo`, no branch). The four `br_s03..s06`
positioner calls take `addu a3, t9, zero`; `br_s02` takes `ori a3, t9, 10`.
`t9` itself is computed by a five-word helper — `slti v1,a0,4; sll; addu; jr
ra; addiu t9,v0,17` — parked in the frame function's dead tail at `800C69A0`,
because the block had no room for it. `t8`/`t9` survive the block: its only
calls are our positioner (a0,a1,v0,v1) and frame function (t0,t1,a1,a3,v0,v1).
Simulated for n = 3, 4, 5 against USA's formulas before building: identical.

### `br_s01` (time limit) has its own reveal animation

Like `br_s00`, its x is animated every frame (`x0 = xl`, `x1 = xl + w*step/6`),
so the `GetResources` `xl` patch alone left it at Integral's 46 and 84 wide.
Integral's `w` is 84, which divides by 6, so the compiler folded the chain to
`14*step` and hardcoded 46 twice; USA's 52 does not, so it multiplies by the ÷6
reciprocal that `a0` still holds from the `br_s00` block (loaded at `800C7648`,
untouched in between). Rebuilt in place as `52*step/6 + 29`: the block's four
y-normalising stores are dead (the positioner writes all four y's each frame),
and the signed-quotient fixup is unnecessary for a non-negative numerator.
Settled widths 0, 8, 17, 26, 34, 43, 52 — USA's.

**Verified in game 2026-09-02, unlocked state (all sixteen items), sixteen shot
pairs against the user's USA set:** outline (2), member (5) and detailed (9),
after the `K = 6` fix every pair differs in 18–43 screenshot pixels (of 2.3 M),
all at game x≈155, y≈162–167 — left of the rule, grey 41 vs 97, identical in
every pair since the very first comparison, so a background detail rather than
anything the menu draws; no game pixel of the menu differs. Before the `K = 6`
fix each detailed shot had exactly two extra pixels, the tops of two drops. The
selection glow itself never differed: it follows the label quad.

**Verified in game 2026-09-02** against the user's USA set, ten shot pairs
(outline; member with each of three rows highlighted; detailed with each of six):
label row bands, rule extents and highlight boxes identical, and a pixel diff of
the right-column region (game x 150-320, y 55-190, tolerance 60/255) is 0.00%
on every pair. The FILE column was already identical.

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

## Unlocks: what gates the title-screen extras, and how the briefing is forced

Needed because the briefing-menu port can only be checked in the unlocked
states (Meryl / support crew / `br_s10` / `br_s13` / `br_s15`) and the user's
save has none of them. Read from the decomp (`onoda/brf/b_select.c`,
`onoda/open/open.c`, `libgcl/variable.c`) and the stage scripts.

**Briefing items are GCL `$f:` flags.** `GetResources` (`brf_800C99C0`) reads
the menu's `-f` option — sixteen values — with `GCL_GetOption('f')` /
`GCL_NextStr` / `GCL_StrToInt`, and the brf stage script (tag `c?`, offset
0x374, byte-identical in Integral and USA) supplies them as sixteen variable
references `14 bb 00 4c/4d/4e`: `GCL_GetVarTypeCode` 4 = bool, offset 0x4C–0x4E
into `var_buf`, bit `bb` — i.e. bits 0x4C.1–7, 0x4D.0–7, 0x4E.0. An item is
counted and drawn only while its flag == 1. `var_buf` is `libgcl/variable.c`'s
static 1024-short GCL variable memory: zeroed by `GCL_InitVar` on boot (a stage
init with `-v`), set by the stage scripts as the story advances, saved and
restored with the game. So a fresh boot shows 1 / 3 / 6 items in both games,
and the earlier idea that the flags meant "watched" was wrong — after a movie
ends the overlay stores `field_80[idx] = 1` too (800C9240), which is the same
state.

    var_buf     Integral SLPM-86247/86248  0x800B3CC8    USA disc SLUS-00594/00776  0x800B6448
    linkvarbuf  Integral                   0x800B4D98    USA disc                   0x800B7518

**The Master Collection's USA executable is not the retail disc's.** Read live
through the sqdbg bridge, its `GCL_GetVar` says `addiu a3, a3, 0x6440`: var_buf
at `0x800B6440`, 8 bytes below the `us1.bin` value, and MC's `scene_name`
define is `0xB7500` where the disc layout predicts `0xB7508`. Writes at the
disc-derived address landed on var_buf+0x54 and the menu never saw them — while
the log still said "Unlocked", because the read-back was of the same wrong
bytes. So `UnlockBriefing` does not hardcode: `variable.c` declares `var_buf`,
`sv_linkvarbuf`, `sv_var_buf`, `stage_name`, `linkvarbuf` in that order, which
puts var_buf 0x10D0 below linkvarbuf and MC's `scene_name` define (it is
`stage_name`) 0x10 below it, so `var_buf = scene_name - 0x10C0`. Checked against
live RAM in both games: Integral `0xB4D88 - 0x10C0 = 0xB3CC8`, USA
`0xB7500 - 0x10C0 = 0xB6440`, both matching the running code's constants.

MGSM2Fix's `GetRamValue`/`SetRamValue` take **RAM offsets**, not KSEG0 addresses
(the memory defines log as `0xb4d9d`; Ketchup's `PSX_ImageBase` is `0x10000`).

**`[Game] UnlockBriefing = true`** (MGSM2Fix, `src/mgs1.cpp`) holds all sixteen
flags set while the scene name is `title` or `brf`, and never otherwise —
var_buf is the live game's flag memory once a stage runs. Relies on the brf
stage's init not carrying `-v` (which would zero var_buf on entry, ahead of any
per-frame poke); the title script's `-v` sites are on other commands. Confirmed in game on Integral (all sixteen items, 2026-09-02). Setting the flags also makes the flag-gated frame polys
(27–38, see the brf section) draw, which is what USA does in the same state.

**Everything else on the title screen comes from the memory-card scan**
(`open.c` ~7600–7800), which reads only the *names* of the saves on the card:

    name[12] == 'G'   a game save; `(name[17] - '@') & 7` is the clear rank ->
                      fB2C[0..3] -> demo_rank 0..6 (EXTREME needs demo_rank != 0)
                      and, non-zero, has_clear_data = 1 (title BSS 0x800D92D0)
    name[12] == 'C'   photo data  -> photo_flag
    name[12] == 'V'   VR data     -> vr_flag

`spe_rank = photo_flag + 2*(demo_rank != 0) + 4*has_clear_data` picks the
SPECIAL menu page, and `has_clear_data` also runs the title script's `-k`
proc (0x0A1E). Not forced here: `demo_rank`/`photo_flag`/`vr_flag` live in the
title actor's heap Work, and the Master Collection keeps its saves in
`userdata/<id>/2131630/remote/data_008_0000.bin`, not as a raw card image. If
those states are ever needed, the honest lever is a cleared save (rank 6) plus
photo and VR saves; the cheap one is a PPF on the `title` overlay forcing the
scan's results.

## Unlock everything (test aid): `unlock_title.py`

Both games gate their title-screen extras on the memory-card scan in the
`title` overlay (`open.c`, `title_open_800D1CB4`): a cleared game save gives
`demo_rank` 1–6 (EXTREME difficulty, DEMO THEATER) and `has_clear_data` (1P
MODE, Integral only), a photo save gives `photo_flag` (PHOTO ALBUM), a VR save
`vr_flag`; `spe_rank = photo + 2*(demo≠0) + 4*clear` selects the SPECIAL page.
`unlock_title.py` patches the *derivation* of those results in the overlay, so a
fresh save sees everything, and emits one PPF per disc addressed at the `title`
stage's sectors (not relocated): `INTEGRAL_disc{1,2}_unlock_title.ppf` and, for
the USA reference game, `mods/MGS1_US/{0,1}/MGS1_disc{1,2}_unlock_title.ppf`.
Named `_unlock_`, not `en_`: delete them to restore normal gating.

| site | Integral | USA |
|---|---|---|
| `if (photo == 1)` / `if (vr == 1)` guards on the work stores | `bne` → `nop` ×2 | same |
| "no clear save" branch (`demo_rank = 0`) | store 6 instead, jump past the rank chain | same |
| `if (has_clear_data == 1) spe_rank += 4` | store 1 into `has_clear_data` where it was read, drop the test | absent in USA (no 1P MODE, no `has_clear_data`) |

Result: Integral `spe_rank` 7 (page with PHOTO ALBUM, DEMO THEATER, 1P MODE),
USA `spe_rank` 3 (its maximum: PHOTO ALBUM, DEMO THEATER); EXTREME selectable
in both. Every patched word is asserted against retail first.

**USA title overlay addresses are label −8.** The USA `title` payload's code
sits 8 bytes later than a base-plus-offset label predicts — its header entry
(`800D5578` vs the labelled `NewOpen` at `800D5580`), its printf references and
every `j` target agree — while USA's `brf` overlay does not have this offset.
File offsets are label-based, so patches land; encoded jump targets must use
the true (label −8) address. This is also why the USA release build's
`demo_rank` chain read as nonsense on first sight ("default 4"): the labels
were off, not the code.

### 1P MODE (Integral only): its Japanese pages, and the language it starts in

Selecting 1P MODE on the SPECIAL page runs the title script's `-s` proc
(0x1137). That proc does not start the game: it opens Integral's VR-style text
window (`koba/vr/vrwindow.c`; actor 0xD44E with `-w 32 53 256 118`,
`-m 16 17 240 101`) on **twenty-one pages of Japanese**, five procs each
chaining to the next through the window's `-p` option — 0x28CC (3 pages),
0x19B7 (5), 0x19B8 (5), 0x19B9 (3), 0x19BA (5) — and the last one ends on proc
0x963D. The pages exist only as the Japanese `-b` strings: USA has no 1P MODE
and Integral has no English for them, so under the no-translation rule they stay
exactly as shipped. They are a kept Integral difference, not an unported one.
(`gclprocs.py` / `gcldump.py` in the scratchpad decode a stage script's procs;
the title's proc table sits at chunk offset 0xEC: BE32 length, then
`id:BE16 offset:BE16` entries ending in a zero word, bodies after it, script
body at 0x10DE.)

Proc 0x963D is the 1P game start and mirrors NEW GAME's proc 0x13EF: `start -v`
(GCL_InitVar: zeroes var_buf and linkvarbuf but restores GM_GameLevel and
GM_Configuration), then `$w:118000be` = GM_FirstPerson = 1, GM_GameLevel = 1
(NORMAL — the last page says so), GM_Disk = 1, the shared item/weapon init proc
0xC8CF, and after 24 frames proc 0xB7ED: `load d00a -m … -s 1`, the same stage
NEW GAME loads. The log agrees: `scene_name "title" -> "d00a"`.

**Language.** The 1P game ran in Japanese although English was selected. The
language is GM_CONFIG_ENGLISH (0x0100) in GM_Configuration (linkvarbuf[2],
0x800B4D9C; MGSM2Fix's `language_setting` define is that word's high byte,
0xB4D9D, mask 1; `radio.c`, `radiomes.c`, `jimctrl.c`, `movie.c`,
`font_draw_string` all test the bit at draw time). Everything that could clear
the bit was checked against the decomp and the binaries, and nothing on this
path does:

- the 1P procs never reference `$w:11800004`. Across every stage script on both
  discs (exact GCL encoding: type nibble via `(v<<1)>>25`, link flag
  `v & 0xF00000 == 0x800000`, offset `v & 0xFFFF`) the only writes to it are
  `abst`/`rank` toggling the tuxedo bit 0x20; `roll`, `s10a`, `s18a` only read
  it (English credits and text branches).
- the executable has no direct store to 0x800B4D9C. Stores through the
  `linkvarbuf` base are GCL_InitVar (restores it), GCL_SetVar (scripts, above),
  DrawReadError (VIBRATION_OFF) and five `title` sites — all `andi 0xF7FF`,
  the RADAR_OFF clears on the DEMO THEATER items.
- `datasave.c` rewrites the 0xE100 option bits only while loading a save; no
  save is loaded. GCL_RestoreVar (continue) and `load -r 0` hard restarts are
  not on the path either.

So the writer is outside the game: the Master Collection's own layer — and a
`setRamValue` trace added to MGSM2Fix (2026-09-03) names it. **The collection's
script `_update_option_button_setting` (`system/script/play_standalone_mgs.nut`,
line 844, called from `poll` every frame) writes the entire 16-bit
GM_Configuration word at 0xB4D9C about sixty times a second**, with values such
as 0x100 (English, button type A) and 0x110 (the same plus the game's
"options changed" bit 0x10 once the option screen has been visited). It is how
the collection imposes its own button-type setting on the game — and the reason
the KEY CONFIG screen is "intercepted" by the collection. It is a
read-modify-write of the live word — confirmed by the read trace: the same
function does `getRamValue(16, 0xB4D9C)` at line 837 and `setRamValue` at line
844, every frame — so any game-side write to GM_Configuration
that lands between the collection's read and its write is lost, and the
language bit is one of those. The run in which 1P MODE played in Japanese
happened without these diagnostics; the next run, with them, kept English
throughout (2,700 writes traced, none changing the word), so the loss is
intermittent and was not reproduced. The collection's earlier access hook on
GCL_SetVar (`ACC HOOK: L80021778 R5=100`) and the `MEDAL_MISSION_START` unlock
turned out to be unrelated achievement plumbing.

MGSM2Fix now: logs every change of the language byte with its scene; traces the
collection's writes to the word (all of them at first, then only the ones that
change it) and its first reads, each with the Squirrel call stack; and
**restores English whenever the bit is cleared in any scene but `option`** —
the option screen being the only place the player can change it, a change seen
there is followed instead. The intro pages are untouched by any of it.

The general fix is **`[Patches] PreserveConfiguration`** (default on, every MGS1
version): at the collection's `getRamValue` of the word MGSM2Fix notes what it
is about to read; at its `setRamValue` it re-reads the word as the game has it
by then and rewrites the collection's argument in place to carry only the bits
the collection actually changed (`(now & ~changed) | (value & changed)`), so
the button-type enforcement survives and every other setting the game wrote in
between survives too. It logs `Preserved GM_Configuration` when it had to
intervene. The word's address is `scene_name + 0x14` (linkvarbuf is 0x10 above
variable.c's `stage_name`, GM_Configuration is linkvarbuf[2]); a version where
that did not hold would never see a collection write at that address and would
be left alone. The EnglishText guard stays as a second layer for the language
bit. This fix is not Integral-specific and is tracked for a separate upstream
pull request in `UPSTREAM.md`.

Also visible in that log: `Set the sixteen briefing flags (… write 3, scene
"title")` immediately after the 1P `start -v`. UnlockBriefing re-sets the flags
GCL_InitVar has just zeroed while the scene is still `title`, so a game started
from the title (NEW GAME or 1P MODE) begins with all sixteen briefing flags set
in its var_buf. That is the option doing its job, but it is state a stock game
would not carry into a new save; keep UnlockBriefing off when saves matter.

## Achievements

Per upstream (nuggs), the `DisableRAM` + `DisableCDROM` combination in
`MGSM2Fix.ini` suppresses achievements. There is no dedicated option.

**In effect since 2026-09-02** (to progress the save for the briefing unlocks
without earning achievements). Both flags filter the Master Collection's own
Squirrel patch tables (`SQNative_setRamValue` / `SQNative_entryCdRomPatch` in
`src/sqhook.cpp`). Verified from `MGSM2Fix.log`: the session filtered 348
CD-ROM offsets, 848 CD-ROM files and 88 RAM patches, against a pre-flag
baseline of 48 / 30 / 0 (the blacklist paths log the same message).

**Ketchup is unaffected.** All 5,542 `[Ketchup] CD-ROM write` lines in that
session have no `filtering` line immediately before them — the pre-hook runs
synchronously inside the call and Ketchup logs right after, so a dropped write
would always show one — and the executable-side RAM patches applied (3,068
bytes, 54 blocks). Likely because the filter resolves its data argument as an
`SQBinary` instance while Ketchup passes a plain array, but that is inferred,
not traced. The English text should be checked visually after any MGSM2Fix
update, since a change to that hook would silently drop every PPF.

**Side effect on comparisons:** `DisableRAM` also filters the collection's
cosmetic RAM patches — the memory-card screens revert from STORAGE 1 / 2 to
MEMORY CARD 1 / 2 — so a shot taken with the flags on differs from one taken
before in those strings. Not a port difference.

### The collection's RAM patches collide with `en_savemsg` (found 2026-09-03)

Read the filtered list out of the log
(`filtering RAM patch offset 0x… with size 0x…`) and six of the collection's
patches land **inside the caption pool `en_savemsg` repacks**
(`0x80011F18..0x800120CB`):

| patch address | size | retail string there | caption slots |
|---|---|---|---|
| `0x80011F34` | 14 | メモリーカードにエラー… | save 10, load 10 |
| `0x80011F6C` | 14 | メモリーカードが初期化… | save 8, load 8 |
| `0x80011F90` | 14 | フォーマットに失敗… | save 7, load 7 |
| `0x80011FC4` | 14 | メモリーカードをチェック… | save 5, load 5 |
| `0x80011FC8` | 14 | (into the same string) | — |
| `0x80012020` | 14 | セーブしました。 | save 2 |

Those are fixed addresses. `en_savemsg` **repacks** the pool, so after the port
those addresses sit in the middle of different strings — `0x80011F34` now holds
`failed.\0Error `, `0x80011FC4` holds `…\0Now chec`. With achievements enabled
(`DisableRAM = false`, the collection's default) the collection would write its
own 14 bytes over those offsets and corrupt the ported English mid-string. The
port has only ever been tested with `DisableRAM = true`, which is why this has
not been seen.

Fix when it matters: make `savemsg.py` **pin** those six strings at their retail
addresses (place them first, at the same offsets) so the collection's writes
land on the strings they were written for, or accept that `en_savemsg` requires
`DisableRAM = true`. Note the collection's replacements are its own wording
(the STORAGE rename family), not USA's, so pinning means the ported English is
overwritten by the collection's text on those six slots — the honest options are
pin-and-lose-six or require the flag. Not yet decided.

The collection also patches, outside the pool: the memory-card UI strings
(`MEMORY CARD 1/2`, `SELECT MEMORY CARD`, `PRESS * TO SELECT MEMORY CARD`,
`PRESS SELECT TO EXIT`) and two overlapping ~2.8 KB blocks of game-encoded text
at `0x8001101C` (+2895) and `0x8001108C` (+2838) covering the same region —
almost certainly one per language. All of that is the memory-card module's
`.rodata`; none of it is the brightness screen.

The deployed ini is a symlink into Vortex's mod folder
(`%APPDATA%\Vortex\metalgearsolidmc\mods\MGSM2Fix-*\MGSM2Fix.ini`); edit the
target, not the link (`sed -i` on the link replaces it with a plain file).
Pre-change copy: `scratchpad/MGSM2Fix.ini.before_achievements`. To restore
achievements, set both back to `false`.
