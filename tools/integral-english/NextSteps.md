# Next steps — MGS Integral English text port

Written 2026-09-04 (evening) for whoever picks this up cold: a later session of
the same assistant, a different model, or a person. It says where everything
is, what the user's rules are (verbatim), how far each piece is verified, what
remains and in what order, and which decisions are the user's to make. The
technical record — byte formats, mechanisms, every gotcha with its evidence —
is `README.md` beside this file; section names are quoted below so they can be
found. `UPSTREAM.md` at the repo root tracks the MGSM2Fix changes that deserve
their own upstream pull request.

Everything that used to live only in the assistant's private memory files
(`~/.claude/projects/.../memory/*.md`) was merged into these two documents on
2026-09-04. Those files may still exist, but **`README.md` + `NextSteps.md`
are authoritative**; if they disagree with a memory file, the memory file is
stale.

---

## 1. Where everything is

| what | where | notes |
|---|---|---|
| MGSM2Fix repo | `C:\Users\Tideg\My Drive\Development\MGSM2Fix`, branch **`integral-english-text`** | based on MGSM2Fix **3.6.0**; upstream is now **3.7.2** — a rebase is needed before any upstream PR |
| remotes | `origin` = `https://github.com/TideGear/MGSM2Fix.git` (push here); `upstream` = nuggslet's MGSM2Fix — **never push to upstream** | |
| decompilation | `D:\mgsbuild\d`, branch `integral-english-text`, origin `FoxdieTeam/mgs_reversing` — **do not push there** | our source changes are captured as `tools/integral-english/decomp-overlay-changes.patch` (= `git diff 7964de7`); regenerate it after any decomp edit. Local decomp commits exist (e.g. `0534934` for the doorbell in `opt.c`) |
| working data | `D:\mgsbuild\integral-english-work\` — `work\` (extracted STAGE.DIRs, exes, built binaries, baselines), `unlocks_parked\` (the four unlock PPFs, not deployed), `keyconfig_test\`, ini/log/`opt.c` snapshots | every tool imports `WORK` from `workdir.py`: `INTEGRAL_ENGLISH_WORK` env var → `D:\mgsbuild\integral-english-work` → cwd. `py workdir.py` prints what it resolved |
| game | `D:\Steam\SteamApps\common\MGS1` (Master Collection Vol. 1, Steam app **2131630**) | launch: `Start-Process steam://rungameid/2131630`; process name `METAL GEAR SOLID`; **kill by PID only, never `taskkill /IM`** |
| Ketchup mods | `D:\Steam\SteamApps\common\MGS1\mods\INTEGRAL\INTEGRAL\0` (disc 1) and `\1` (disc 2) | Ketchup loads every PPF in the folder, so each patch is its own file and can be removed individually |
| deployed ini | `D:\Steam\SteamApps\common\MGS1\MGSM2Fix.ini` is a **Vortex symlink**; edit the target: `%APPDATA%\Vortex\metalgearsolidmc\mods\MGSM2Fix-5-3-6-0-1774482213\MGSM2Fix.ini` | edit with Python or via `realpath`; `sed -i` on the link would replace the link with a file. The repo's `MGSM2Fix.ini` is the committed default, not what the game reads |
| deployed ASI | same Vortex folder, `MGSM2Fix64.asi` | |
| build | `"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe" MGSM2Fix.sln /p:Configuration=Release /p:Platform=x64` → `x64\Release\MGSM2Fix.asi` → copy to the Vortex folder as `MGSM2Fix64.asi`; compare hashes | if MSBuild times out it can leave `cl.exe` processes behind — stop them by PID |
| log | `D:\Steam\SteamApps\common\MGS1\MGSM2Fix.log` (rotates to `.prev`) | it logs an ini parse error at **line 12** every boot — that is the `[Internal Resolution]` header, an old inipp quirk, harmless; every setting still parses |
| screenshots | `C:\Program Files (x86)\Steam\userdata\7924217\760\remote\2131630\screenshots` | 3840×2160; 9 display px per game px, x offset 480 |
| USA source data | `work\usa1_stage.dir` / `usa2_stage.dir` (real USA discs, extracted from `windata\alldata.bin`); `work\us1_stage.dir` is **European** despite its name — do not source text from it | README "Toolchain and environment" and the source-discs note |
| git identity | `git -c user.name=TideGear -c user.email=tidegear@gmail.com commit` | **no `Co-Authored-By: Claude` or any AI attribution in commit messages** |
| title ids | from `MGS1_Ketchup` in `src/mgs1.h`: **99** INTEGRAL, **980** MGS1_JP, **981** MGS1_US, 101/102 VR, 982–986 EU | attribute a collection patch to a title by its id, never by the order lines appear in a log |

---

## 2. The user's standing rules — verbatim

These were given during the work and govern everything. Quote them, do not
paraphrase them away.

1. **No translation.** "Btw I'm not authorizing you to translate (yet) anything only in english with no port should be left in Japanese." — Any string without an English counterpart in a released build stays Japanese exactly as it is: not blanked, not paraphrased, not abridged. When English is longer than Integral's slot, grow the slot; never shorten the text.
2. **Previous Operations:** "For Previous Operations, change the page count. Do not edit."
3. **Scope:** "the goal is verbatim text placed identically, but integral could have relevant adjustsments (since it was a later release) that are worth keeping I'm ok with keeping Integrals differences if they aren't text translation and appropriate positioning." — Fix text and the chrome that positions text (rules, connectors, highlight boxes, row spacing); leave Integral's colour, brightness, blend and background-art differences alone and note them in the README's Scope table.
4. **Amendment (2026-09-03):** "Where Integral's art/gui/hud/etc. is intentionally different, consider moving the English text to fix it, but ask me first." — Measure the relationship USA has between text and the art it relates to, reproduce that relationship against Integral's art, do not port the art — and **ask before doing it**, case by case. Worked example: `key_syukan` on KEY CONFIG.
5. **In the collection:** "in MC i prefer the circle message suppressed and key config intercepted" — the four-line brightness text (no ○-button line) and the collection's own Control Settings panel for KEY CONFIG.
6. **The raw disc matters:** "\"They'd still matter for a raw PSX disc patch.\" that was the point of porting the text. I want the intercept still in mc." — Text the collection hides (KEY CONFIG labels, disc-swap prompts) is still ported for a future raw-PSX-disc patch, while the collection keeps its interception.
7. **Documentation:** "Make sure you're remembering to document and gotchas worth documenting" — and, 2026-09-04: nothing important may live only in a conversation or a memory file.
8. **Upstream tracking:** anything changed in MGSM2Fix that benefits players who do not use the port goes into `UPSTREAM.md` for a separate PR; port-only changes stay out.
9. **Be careful:** "I need you to be more careful. Stop guessing when the hard data is available to you." — see §3.

---

## 3. How to work here (distilled from the mistakes)

- **Measure before theorising.** The decompiled source, both games' data, the retail binaries, the font tables and a relaunchable game are all available. Before proposing why something breaks, ask what single check rules it in or out, and run it.
- **Bisect against a stock run first.** Establish the fault is in our change before reasoning about mechanisms. The option-screen freeze was an overlay 32 bytes over retail; the KEY CONFIG interception was found by bisection plus `SetPatchWatch`, after three wrong theories.
- **Check the cheap invariant.** Sizes, counts, hashes against the known-good before logic.
- **Absence of observation is not a negative result.** Before saying "there is no X", establish you would have *seen* an X. Three wrong conclusions in one day came from this (README "The collection's KEY CONFIG interception").
- **Re-run every static check on the artefact you actually deploy** — a check on build N says nothing about build N+1.
- **Do not "fix" retail's quirks in an overlay.** `f924[8]` must stay `[8]`; growing it caused the very freeze it was meant to cure.
- **Read the README section for a stage before touching it.** Each stage has its own traps; the README records them with evidence.
- **Run `ppfcheck.py` before any PPF goes near the game.** A 60-byte description in the 50-byte field once crashed the game and produced a 306 MB log.
- **Keep a GCL chain's byte delta at exactly zero when you can** (pad the shortest record with trailing spaces); otherwise use `gclparse.containers_over` to resize every enclosing container. A −8,055-byte shift crashed the script with no exception.
- **Never let an executable PPF record cross a 2048-byte payload boundary** — Ketchup drops the spill silently while logging success.
- **The extracted `int1_stage.dir` is unpatched.** To see what the deployed game shows, apply the deployed PPF first (see the `en_camsave` verification, 2026-09-04) — reading the extraction alone shows Japanese everywhere and proves nothing.
- **Function pointers decode as "text".** `addiu sp,sp,-N` (`c0 ff bd 27`…) in a pointer table is code. Known in `camera` at overlay 0x6E0–0x6E8.
- Absolute dates in notes, not "yesterday". Kill by PID. No AI attribution in commits.

---

## 4. State on 2026-09-04: what ships, and how far each is verified

### PPF patches (all deployed for both discs unless noted)

| patch | what | verified |
|---|---|---|
| `en_items` | item descriptions (executable) | in game; proven intact against the collection's RAM patches |
| `en_menu`, `en_menu2` | menu strings; `en_menu2` includes the `demosel` and `change` disc-swap copies | in game (menus); the disc-swap copies **never seen** (see §5.1) |
| `en_option` | option-screen strings; KEY CONFIG labels (8 textures); brightness paragraph as USA's `sc_text` texture, four lines in the collection build | in game, pixel-measured; SCREEN / KEY CONFIG (collection panel via the doorbell) / EXIT all confirmed 2026-09-04 |
| `en_preope` | Previous Operations, USA's exact pagination (MG1 13 pages, MG2 19) | in game, 29 lines pixel-exact |
| `en_brf` | briefing labels, quads, row arithmetic | in game, 26 shot pairs, 0.00% right-column diff |
| `en_savemsg` | memory-card captions in the executable | in game 2026-09-04: save + load; kept slots idx 1/9 Japanese by rule; `Ketchup::Audit` saw no collision with the collection's RAM patches |
| `en_camsave` | the PHOTO ALBUM's own captions (`camera` overlay) | **fully verified 2026-09-04**: all 23 English on screen / by slot comparison; the six USA-blank slots stay Japanese (`ロード中です`, `ロードが完了しました`, `変更内容を上書き保存しますか？` are those) |
| `en_menu3` | the `title` disc-swap copy | **disabled** — crashes the title stage; diagnosed, not rebuilt (§5.4) |
| unlock PPFs | title-screen extras | **parked**, `unlocks_parked\`, not deployed |

### MGSM2Fix features on this branch (see `UPSTREAM.md` for the upstream view)

| feature | ini | state |
|---|---|---|
| Ketchup RAM-mirror deferral | — | in use daily |
| `[Game] EnglishText` (+hold, +guard restoring English outside scene `option`) | `EnglishText = true` | tested, follow-the-player path tested |
| `[Patches] PreserveConfiguration` | `= true` | three clean runs; the race it guards has not been caught in the act |
| `[Game] UnlockBriefing` | `= false` | tested; seeds new-game `var_buf` |
| `[Game] BrightnessText` (tri-state `fixed` / `original` / `collection`) | `= fixed` | both fixed and original verified in game, both titles |
| Ketchup built-in disc patches + `SetPatchRangeBlacklist` | — | shipping (the USA four-line brightness fix) |
| `SQHook::SetPatchWatch` (logs collection patches landing in a region) | — | in use; watches on `option` and `abst` spans, both discs |
| `Ketchup::Audit` (every byte of every RAM run, read-only, every ~5 s) | — | in use; first-byte blind spot of `Update()` documented as open |
| `[Game] GiveItems` (test aid) | `GiveItems =` (empty) | built; **never exercised** — the developer menu grants everything anyway |
| `[Game] StageSelect` = `true` / menu name / stage name | `StageSelect = false` | works; see README "The disc-swap text" for what it can and cannot reach |

### Deployed ini right now (play defaults)

`DisableRAM = false`, `DisableCDROM = false` (achievements live), `StageSelect = false`, `GiveItems =`, `EnglishText = true`, `BrightnessText = fixed`, `PreserveConfiguration = true`, `UnlockBriefing = false`. The user has real saves: **Heliport** and **Comm Twr A** (both disc 1, the latter made with a full developer-menu inventory and a photo).

---

## 5. What remains — in the order I would do it

### 5.1 The disc-2 run (needs the user at the controller; nothing to build)
Load the **Comm Twr A** save (no debug) and play across the break: Comm Tower
A → B → Hind D → Sniper Wolf → capture. Watch whether the game's own swap flow
draws (`Now Checking...` / `Insert DISC 2.` — Japanese in Integral, since the
visible copies may be the unported ones) or the collection swaps silently; then
read the log for `Disk ID is 1`. This one run answers: disc 2 in game, the
reachability of **all four** disc-swap text copies, and whether `en_menu3`
and the `ab_ch` copy are visible bugs or raw-disc completeness. **The
developer menu cannot do this** — disc 2 is set only by `change.c`'s CD check
(README "The disc-swap text: four copies"). Once on disc 2, glance at SCREEN /
KEY CONFIG (byte-identical to disc 1, so they should just work) and any
disc-2 mission-log page.

### 5.2 The MISSION LOG port (`abst` stage) — the largest remaining port
The user said "We're gonna have to port that over too" but has not said start;
it was scoped and deliberately left. README "TO DO: port the MISSION LOG" has
every number; `abstscan.py` prints them and `abstscan.py page N` dumps a page
from both games. In short: 122 text pages in each game; the text is the `i`
option's payload (`INT count` then `count+1` STRING records); **never touch the
`i` option's length byte** (overflowed u8, never read); USA draws 7 lines per
screen, two screens per page, in 128×20 KCBs with a VRAM column wrap, Integral
up to 11 on one screen (`abst.c`, `kcb[12]`, 128×21). Method = the `preope`
method (resize records + the COMMAND's BE16), grow `abst.c` to USA's model,
relocate into DUMMY3M from slot 462, composite the PPFs. Open before the first
edit: USA's two-screen paging code, pairing pages by the shared `l`/`r`/`e`
ids, the USA counterpart of the `READ MISSION LOG?` caption, and the
collection's `disc1_132F2716_patch_PS5.bin` inside the stage (watch registered,
nothing logged yet). A USA screenshot of the mission log would confirm the
layout in one look. Reference JP shot: `D:\mgsbuild\integral-english-work\`.

### 5.3 The disc-change abstract (`ab_ch.c`, in `abst`)
Small: eight strings inside the `e` option of one block (Integral chunk
`+0xB0A5`, USA `+0xC6D1`); USA's are shorter so the block shrinks; keep `e`'s
length byte consistent. Do it together with 5.2 (same stage, same relocation)
or with 5.4 (same text family). README "TO DO: the disc-change abstract".

### 5.4 Rebuild `en_menu3` (the `title` copy)
README "Why `en_menu3` crashes" and "How to test it": shorten the STRING length
bytes and shrink the enclosing containers per edited record (they span more than
one OPTION — SCRIPT size `@0x10DA` BE32, ARG `@0x10DF` BE16, COMMAND `0x9906`
`@0x1139` BE16, OPTION `v` `@0x11AF` u8), `gclparse` self-check, then the
trivial test: boot to the title. Whether it is worth doing depends on 5.1.

### 5.5 A build switch for the raw-disc variant
Two constants differ between the collection build and a raw PSX disc patch:
`SC_KEEP_LINES` (4 collection / 6 raw — `optsctext.py`) and
`OPTION_MC_CONTROL_SETTINGS` (1 / 0 — `opt.c`). Today they are edited by hand;
they should be one switch that builds both variants. README "The sc_text
texture port" and "The collection's KEY CONFIG interception".

### 5.6 The VR disc (SLPM-86249)
Not started. USA's `SLUS-00957` exists in `windata\alldata.bin` (base
`0xD39B7000`), so it is portable in principle. README "Not ported at all: the
VR disc".

### 5.7 Upstream pull request
Rebase the general-benefit commits onto MGSM2Fix **3.7.2** and offer them
separately; `UPSTREAM.md` lists them with test status. Port-only commits stay
on this branch.

### 5.8 Still untested, low effort when the moment comes
- `PreserveConfiguration` catching a real stale write (intermittent race).
- The `_PS5` patch inside `abst` — does a `_PS5`-suffixed collection patch
  apply on Windows at all? The watch will say the next time `abst` loads under a
  fresh patch application.
- `GiveItems` in a stage where the inventory is actually empty (a real save,
  not the developer menu).
- If `Ketchup::Audit` ever reports a `differs from what was written` line in
  the `en_savemsg` pool: decide between completing Ketchup's check (flicker
  risk) and adopting the collection's English rename strings. README "The
  collection's RAM patches collide with `en_savemsg`".

### 5.9 Optional, ask first
- Location-name spellings in `abst` (`Tank Hanger` / `Medi rm` / `Cmnder rm`
  vs USA `Hangar` / `Medi room` / `Cmnder room`): Integral's own English, not
  Japanese — outside the rule as written, so ask.
- `rank`: 36 Integral-only Japanese sentences with no USA counterpart → stays
  Japanese unless a USA source turns up. Nothing to do without one.

---

## 6. Decisions that are the user's — ask, do not assume

- Whether and when to start the mission-log port (5.2), and whether a USA
  screenshot can be produced first.
- Anything under the 2026-09-03 amendment: moving English text to fit
  Integral's own art.
- The `en_savemsg` collision approach, if one is ever observed.
- Achievements on or off for a given test session (`DisableRAM` /
  `DisableCDROM`); they are **on** now. Turning them off keeps SPECIAL / PHOTO
  ALBUM reachable without earning it and has never affected the PPFs.
- Anything that touches Integral's own English (5.9).

---

## 7. Tools (all in this directory; `py <tool>`; they find `work\` themselves)

| tool | purpose |
|---|---|
| `workdir.py` | resolves the working directory (`py workdir.py` prints it) |
| `ppfcheck.py [--deployed]` | validates PPFs exactly as Ketchup reads them — run before deploying anything |
| `optsctext.py` | builds `en_option` (sc_text texture, KEY CONFIG art, chain, relocation to DUMMY3M slot 384, doorbell stub check) |
| `verify_integral_option.py`, `verify_usa_brightness.py` | read the deployed PPFs / built-in patch back and check them |
| `shotcmp_brightness.py A.jpg [B.jpg]` | measures brightness-screen shots |
| `preope_usa.py`, `preope_both.py` | Previous Operations (USA pagination); `reloc_ppf.py` relocates a stage into DUMMY3M (still used for `brf`) |
| `brf_build.py`, `brf_widen.py` | briefing labels and quads |
| `savemsg.py`, `camsave.py` | the two memory-card caption ports |
| `abstscan.py [page N]` | mission-log scoping data, both games |
| `jpsweep.py` | census of remaining Japanese UI text (stricter second pass documented) |
| `gclparse.py`, `gcldec.py` | GCL container parsing / record walking — `containers_over` for resizing |
| `optscan.py`, `optbright.py`, `optlabel2.py` | option-stage inspection and earlier chain tools |
| `unlock_title.py` | builds the (parked) unlock PPFs |

The scripts that shaped tonight's documentation live only in the session
scratchpad and are disposable; everything they established is in the README.

---

## 8. Where the details live (README section names)

Gotchas → "Gotchas" (freeze/crash triage, overlays, font limits, GCL chain,
textures, disassembly, screenshots, PPFs, toolchain) · "The three limits" ·
"Things that do not work" · "Wrap width" · KEY CONFIG → "The KEY CONFIG screen",
"The collection's KEY CONFIG interception, and how the port broke it", "How the
KEY CONFIG port was built" · PPF → "PPF3's description field is 50 bytes" ·
captions → "Memory-card messages (`en_savemsg`)", "The PHOTO ALBUM's own
memory-card messages (`en_camsave`)" · sweep → "Sweep: is any UI text still
Japanese?" · TO DO → "TO DO: port the MISSION LOG", "TO DO: the disc-change
abstract", "The disc-swap text: four copies" · scope → "Scope", "What stays
Japanese, and why" · brightness → "The collection shows only four of USA's six
brightness lines", "Option → SCREEN", "The sc_text texture port" · briefing →
"Briefing menu (`brf` stage)" · unlocks → "Unlocks", "Give items", "Unlock
everything", "Achievements" · tests → "Not tested" (struck-through items are
done, with dates) · decomp → "Audit against the decomp".
