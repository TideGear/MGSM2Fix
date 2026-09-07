# Next steps — MGS Integral English text port

Written 2026-09-04 (evening), updated the same night after the
reproducible-build pass (§9), through 2026-09-05 as the MISSION LOG port,
the item-text fixes and their on-screen checks landed (§10), on 2026-09-06
when the **VR disc** was ported (§11), and through 2026-09-07, the day the VR
disc was tested on screen and the three items that were still open all closed:
the MOVIE captions, `en_menu3` and the VR KEY CONFIG (§12). Written for whoever
picks this up cold: a later session of the same assistant, a different model, or
a person. It says where everything
is, what the user's rules are (verbatim), how far each piece is verified, what
remains and in what order, and which decisions are the user's to make. The
technical record — byte formats, mechanisms, every gotcha with its evidence —
is `README.md` beside this file; section names are quoted below so they can be
found. [`BUILDING.md`](BUILDING.md) is the reproducible build and packaging
procedure; [`COVERAGE.md`](COVERAGE.md) is the text-coverage inventory and its
limits. `UPSTREAM.md` at the repo root tracks the MGSM2Fix changes that deserve
their own upstream pull request.

Everything that used to live only in the assistant's private memory files
(`~/.claude/projects/.../memory/*.md`) was merged into these two documents on
2026-09-04. Those files may still exist, but **these repo documents are
authoritative**; if they disagree with a memory file, the memory file is stale.

---

## 1. Where everything is

| what | where | notes |
|---|---|---|
| MGSM2Fix repo | `C:\Users\Tideg\My Drive\Development\MGSM2Fix`, branch **`integral-english-text`** | based on MGSM2Fix **3.6.0**; upstream is now **3.7.2** — a rebase is needed before any upstream PR |
| remotes | `origin` = `https://github.com/TideGear/MGSM2Fix.git` (push here); `upstream` = nuggslet's MGSM2Fix — **never push to upstream** | |
| decompilation | `D:\mgsbuild\d`, branch `integral-english-text`, origin `FoxdieTeam/mgs_reversing` — **do not push there** | our source changes are captured as `tools/integral-english/decomp-overlay-changes.patch` (= `git diff 7964de7`); regenerate it after any decomp edit. Local decomp commits exist (e.g. `0534934` for the doorbell in `opt.c`) |
| working data | `D:\mgsbuild\integral-english-work\` — `work\` (extracted STAGE.DIRs, the four retail executables, built binaries, baselines), `unlocks_parked\` (the four unlock PPFs, not deployed), `keyconfig_test\`, `map_pristine.map` (the pristine exe's symbol map), ini/log/`opt.c` snapshots | every tool imports `WORK` from `workdir.py`: `INTEGRAL_ENGLISH_WORK` env var → `D:\mgsbuild\integral-english-work` → cwd. `workdir.py` also exports `GAME` (`INTEGRAL_ENGLISH_GAME`, default the Steam folder) and `DECOMP` (`INTEGRAL_ENGLISH_DECOMP`, default `D:\mgsbuild\d`); no tool hardcodes those paths any more. `py workdir.py` prints what it resolved |
| VR working data | `work\vrint_stage.dir`, `work\vrus_stage.dir` (the two VR STAGE.DIRs), `work\vrint.exe` (rebuilt from the decomp, `build.py --variant vr_exe`, SHA-256 `c370f8e4…`), `work\vrus.exe` (real `SLUS-00957`), `work\INTEGRAL_vr_*.ppf` | `vrlib.py` finds the two VR ISOs inside the containers itself (`0x57592000` and `0xD39B7000`) and computes stage LBAs from STAGE.DIR |
| retail executables | `work\int1.exe`, `int2.exe` (641,024 bytes each), `us1.exe`, `us2.exe` (651,264) — hashes in `BUILDING.md`; `rebuild.py` rejects any other | **the collection's ISO executable extents are zero-filled**, so extracting an exe from `alldata.bin`/`dlc_japan.bin` yields no code — the first clean-build attempt failed on exactly that. These four files are the only source of executable bytes |
| reproducible build | `py rebuild.py --output <fresh dir> [--variant raw] [--compare-deployed]` (see `BUILDING.md`) | never installs anything. Builds **everything**: nine families × two main discs plus the VR disc's seven. Last artefact `D:/mgsbuild/repro8/Integral-English-collection.zip`, SHA-256 `a13eefc0…faef` (2026-09-07), **all 25 PPFs equal to the deployed set's effective bytes**. `--variant raw` builds the raw-disc variant instead (§5.4) |
| game | `D:\Steam\SteamApps\common\MGS1` (Master Collection Vol. 1, Steam app **2131630**) | launch: `Start-Process steam://rungameid/2131630`; process name `METAL GEAR SOLID`; **kill by PID only, never `taskkill /IM`** |
| Ketchup mods | `D:\Steam\SteamApps\common\MGS1\mods\INTEGRAL\INTEGRAL\0` (disc 1) and `\1` (disc 2); the VR disc is `mods\INTEGRAL\VR-DISK\` and the USA VR disc `mods\VR-DISK_US\` | Ketchup loads every PPF in the folder, so each patch is its own file and can be removed individually. Its `RootPath` adds a version folder only when a title has more than one version and a disk folder only when a version has more than one disk, which is why the two VR folders have no numbered subdirectory |
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
4. **Amendment (2026-09-03):** "Where Integral's art/gui/hud/etc. is intentionally different, consider moving the English text to fix it, but ask me first." — Measure the relationship USA has between text and the art it relates to, reproduce that relationship against Integral's art, do not port the art — and **ask before doing it**, case by case. Worked examples: `key_syukan` on KEY CONFIG, and the VR MOVIE EXIT box (§5.4a), where the chrome moved rather than the text. **The default, in the user's words (2026-09-07): "Usually we skew toward the Integral visuals."** So every such move is an exception that has to be asked for and written down.
5. **In the collection:** "in MC i prefer the circle message suppressed and key config intercepted" — the four-line brightness text (no ○-button line) and the collection's own Control Settings panel for KEY CONFIG.
6. **The raw disc matters:** "\"They'd still matter for a raw PSX disc patch.\" that was the point of porting the text. I want the intercept still in mc." — Text the collection hides (KEY CONFIG labels, disc-swap prompts) is still ported for a future raw-PSX-disc patch, while the collection keeps its interception.
7. **Documentation:** "Make sure you're remembering to document and gotchas worth documenting" — and, 2026-09-04: nothing important may live only in a conversation or a memory file.
8. **Upstream tracking:** anything changed in MGSM2Fix that benefits players who do not use the port goes into `UPSTREAM.md` for a separate PR; port-only changes stay out.
9. **Be careful:** "I need you to be more careful. Stop guessing when the hard data is available to you." — see §3.

---

## 3. How to work here (distilled from the mistakes)

- **Measure before theorising.** The decompiled source, both games' data, the retail binaries, the font tables and a relaunchable game are all available. Before proposing why something breaks, ask what single check rules it in or out, and run it.
- **Bisect against a stock run first.** Establish the fault is in our change before reasoning about mechanisms. The option-screen freeze implicated both overlay growth and `f924[12]`; reverting both together confounded the size-only diagnosis. Keep the conservative size guard and retail's `f924[8]`. KEY CONFIG interception was found by bisection plus `SetPatchWatch`.
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
- **Never take executable bytes from the collection's disc images** — their exe extents are zero-filled. Use the four retail executables in `work\` (§1).
- **Builders stage into `WORK` and deploy only with an explicit `--deploy`**; `rebuild.py` never touches the game folder. Compare a rebuild to the deployed set by *effective changed bytes* (`--compare-deployed`), not by PPF file hash — record grouping and the description text can differ without changing game data.
- **A normal disc swap proves only the normal swap path.** The title / wrong-disc, demo-theater and abstract copies of the disc-swap text need their own evidence; do not infer "unreachable" for all four from one silent swap.
- Absolute dates in notes, not "yesterday". Kill by PID. No AI attribution in commits.

---

## 4. State on 2026-09-07: what ships, and how far each is verified

### PPF patches (all deployed for both discs unless noted)

| patch | what | verified |
|---|---|---|
| `en_items` | item and weapon descriptions, the frozen Ration/Ketchup pair, the HARD/EXTREME Mine Detector message (executable) | in game. Three faults found from the user's shots and fixed 2026-09-05 (card level digit offset, SOCOM suppressor rewrite, a retail-equal byte the collection's RAM patch owned — README "Three item-text faults"); **the fixes were seen on screen at 12:55** (SOCOM, ID Card `level 7 security`, Mine Detector) and the audit is silent. The PPF owns every byte of both arenas |
| `en_menu`, `en_menu2` | menu strings; `en_menu2` includes the `demosel` and `change` disc-swap copies | in game (menus); the disc-swap copies **never seen** (see §5.1) |
| `en_option` | option-screen strings; KEY CONFIG labels (8 textures); brightness paragraph as USA's `sc_text` texture, four lines in the collection build | in game, pixel-measured; SCREEN / KEY CONFIG (collection panel via the doorbell) / EXIT all confirmed 2026-09-04 |
| `en_preope` | Previous Operations, USA's exact pagination (MG1 13 pages, MG2 19) | in game, 29 lines pixel-exact |
| `en_brf` | briefing labels, quads, row arithmetic | in game, 26 shot pairs, 0.00% right-column diff |
| `en_savemsg` | memory-card captions in the executable | in game 2026-09-04: save + load; kept slots idx 1/9 Japanese by rule. Since 2026-09-05 the PPF owns every byte of the pool and tables, so the collection's six writes cannot survive at retail-equal bytes (the mechanism that broke the SOCOM line) |
| `en_camsave` | the PHOTO ALBUM's own captions (`camera` overlay) | **fully verified 2026-09-04**: all 23 English on screen / by slot comparison; the six USA-blank slots stay Japanese (`ロード中です`, `ロードが完了しました`, `変更内容を上書き保存しますか？` are those) |
| `en_abst` | the MISSION LOG: all 122 pages in USA's two-screen model (7 lines a screen, page counter, ◄ ► EXIT, USA's input and slide), plus the disc-change abstract's eight strings — the fourth disc-swap copy | **built 2026-09-05 and seen on screen the same day**: both pages of the Heliport and Comm Tower A logs, the controls and the slide (the one fault, stale-VRAM fragments during the slide, fixed at 13:05 and confirmed clean at 13:50). Statically, pages re-parse and equal USA's byte for byte and the PPF records rebuild the relocated 88-sector stage exactly on both discs. Stage in DUMMY3M slots 462..549. Not yet seen: a demo.gcx page (disc-2 saves) and a count-7 page |
| `en_menu3` | the `title` disc-swap copy — the fourth and last | **built and verified 2026-09-07, RAW DISC ONLY, not deployed.** The collection patches the same block (`disc1_1822B55D_patch`, at the address of our record 0), and the two layouts do not mix: the title stage dies with a `GCL:WRONG CODE` run. Staged as `INTEGRAL_disc{1,2}_en_menu3_raw.ppf` for the raw variant; `menu3.py --deploy` refuses. §5.3 |
| unlock PPFs | title-screen extras | **parked**, `unlocks_parked\`, not deployed |

### VR-DISC patches (deployed 2026-09-06 in `mods\INTEGRAL\VR-DISK\`)

Ported from USA's VR Missions (`SLUS-00957`). README "The VR disc (SLPM-86249)"
is the technical record; `vrlib.py` is the shared library. **Four have been seen
on screen** — the option screen, both unlock aids and the E3 movie caption; the
two-line MOVIE captions were deployed 2026-09-07 and are the next thing to look
at; the rest are statically verified only, and §5.5 lists what is still unseen.

| patch | what | verified |
|---|---|---|
| `vr_en_missions` | 1808 of 1813 in-mission windows across 92 stages: titles, briefings, results, hints | statically: every stage re-parses, no stage grew (ten padded back to their sector count), 15 031 records / 3 370 955 bytes, fonts merged and every remaining glyph code proved to exist in the new font |
| `vr_en_items` | the VR executable's item, weapon and capture-mode pools | statically; the PPF owns every byte of all three arenas, as the main game's does since the SOCOM fault |
| `vr_en_savemsg` | the VR executable's 12 save and 12 load messages | statically; indices 1 and 9 stay Japanese (USA draws nothing) |
| `vr_en_option` | the option screen's 7 help lines and the whole KEY CONFIG screen | **the option screen is verified on screen 2026-09-06** after three faults, all found by bisecting the PPF: the DAR's entry sizes were not 4-aligned and crashed the stage at `load option`; record 3 doubled the vibration-test sentence; and Integral's colon/values were lit beside the English while the lines sat off-centre. Fixed by padding every DAR payload to 4 (paid for with `pcx4`'s real 63-byte run cap), blanking record 3 as the main game does, unlighting the colon/values via the state switch, and giving each ported entry USA's `{num 1, x 160, y 196}`. All five rows now read as one centred English line, measured within 0.3 game px of centre. **KEY CONFIG verified on screen 2026-09-07** with `DisableRAM`/`DisableCDROM` on: Integral's own screen draws, all eight labels English through all three button types, and `key_syukan`'s +11 clears the curve. One fault found and fixed the same day — the selection highlight on the `first person view` row was 24 px short (88 against USA's 112) because it is drawn by hardcoded `glow(work, x, y, w, h, ...)` calls rather than an `Init_Res` quad, so the transplant never touched it; measured 113 px against USA's 114 after the fix |
| `vr_en_title` | the EXTRA menu's four help lines | statically; record 6 (PocketStation) deliberately kept — USA's `See the staff credits.` is a different feature |
| `vr_en_camsave` | the PHOTOGRAPHING mode's memory-card messages | statically; 429 of the pool's 492 bytes used. Never seen on screen |
| `vr_en_movie` | the MOVIE selection captions | **all three ported 2026-09-07**, the two TGS ones as USA's two lines. The line count was never data: USA calls the actor's own `highlight(work, i)` twice — for `clip*2` and `clip*2+1` — where Integral calls it once, so the port retargets that one `jal` at a 16-word stub in the overlay's own sector padding. **Verified on screen 2026-09-07**, all three clips: both TGS captions on two rows with correct attribution and real typographic quotes, E3 on one. Line 1's ink then overlapped the EXIT box by 2 rows, because Integral's caption face is taller than USA's; the box moved up 4 px to USA's own y with the user's approval (§5.4a, §6), and **that part is not yet seen on screen** |
| `vr_unlock_movies` | the EXTRA movies unlocked (test aid) | **verified in game 2026-09-06: all three thumbnails appear.** One instruction in the `movie` overlay: its own `count / 3` score gate, separate from the mission one. Writes no progress; delete the PPF to relock |
| `vr_unlock` | the **mission menu** unlocked (test aid) | **verified in game 2026-09-06: every mission unlocked.** Emulation predicted 46 → 361 of 373 items on Integral (45 → 357 on USA) and its three words were verified in place against the deployed PPF. It does **not** open the EXTRA movies — that is a separate retail gate, `???` in USA's VR disc too. Safe to leave in and safe to save with (it writes no progress); delete the PPF to relock |

`ppfcheck.py --deployed` is clean over all 29 deployed files. The nine VR PPFs
are disjoint but for **one deliberate overlap**: `vr_en_movie` shares 686 of
its 753 bytes with `vr_en_missions`, which already owns the `movie` stage, so it
is built on top of it and must land last — Ketchup applies a folder in name
order and `...missions` sorts before `...movie` (README "The composite
trap"). For the same reason the superseded `vr_en_movie_e3` must **not** sit in
the folder beside it: it sorts last of the two and would overwrite part of the
full build. `vr_movie.py --deploy` moves it to `work/` with a `.was-deployed`
suffix. `vr_sweep.py` rebuilds every stage as the
game will see it and finds **222 game-encoded records against 10 809 English**
(USA's own disc: 940 against 10 344); 181 of the 222 are English with
local-font glyphs, and the rest are exactly the list the README calls
"Deferred, with reasons". Nothing with a USA English counterpart is still
Japanese.

**Reproducibility:** every one of the nine shipping families is rebuilt from
retail inputs in an isolated directory by `rebuild.py` — stage files extracted
from the collection, the four retail executables as hashed inputs, the decomp
exported at `7964de7` plus `decomp-overlay-changes.patch`, three overlays
recompiled (byte-identical to the shipped ones) — and all 18 PPFs match the
deployed set's effective changed bytes. **Since 2026-09-07 the VR disc's seven
are in the same run** (its executable built from the decomp, not copied), so the
last clean run, `repro8`, reproduces **25 of 25** against what is deployed. So the deployed patches are
no longer artefacts of a lost scratchpad: they can be regenerated. `BUILDING.md`
has the inputs, hashes, command, outputs and the ZIP's hash. This is static
equivalence, not a new gameplay test.

### MGSM2Fix features on this branch (see `UPSTREAM.md` for the upstream view)

| feature | ini | state |
|---|---|---|
| Ketchup RAM-mirror deferral | — | in use daily |
| `[Game] EnglishText` (+hold, +guard restoring English outside scene `option`) | `EnglishText = true` | tested, follow-the-player path tested |
| `[Patches] PreserveConfiguration` | `= true` | three clean runs; the race it guards has not been caught in the act |
| `[Game] UnlockBriefing` | `= false` | tested; seeds new-game `var_buf` |
| `[Patches] BrightnessText` (tri-state `fixed` / `original` / `collection`) | `= fixed` | USA only; fixed and original verified on disc 1. Integral's paragraph is built into its PPF independently of this setting |
| Ketchup built-in disc patches + `SetPatchRangeBlacklist` | — | shipping (the USA four-line brightness fix) |
| `SQHook::SetPatchWatch` (logs collection patches landing in a region) | — | in use; watches on `option`, `abst`, `change`, `demosel`, `title` and `camera` spans on both main discs, and since 2026-09-06 on the VR disc's `option`, `camera`, `vrtitle`, `movie` and `vrsave` spans (ASI rebuilt and deployed 2026-09-06 00:25) |
| `Ketchup::Audit` (every byte of every RAM run, read-only, every ~5 s) | — | in use; it caught two of the three item faults on 2026-09-05. Since both exe PPFs own whole regions it now sees every byte of both pools |
| `[Game] GiveItems` (test aid) | `GiveItems =` (empty) | built; **never exercised** — the developer menu grants everything anyway |
| `[Game] StageSelect` = `true` / menu name / stage name | `StageSelect = false` | works; see README "The disc-swap text" for what it can and cannot reach |

### Deployed ini right now (play defaults)

`DisableRAM = false`, `DisableCDROM = false` (achievements live), `StageSelect = false`, `GiveItems =`, `EnglishText = true`, `BrightnessText = fixed`, `PreserveConfiguration = true`, `UnlockBriefing = false`. The user has real saves: **Heliport** and **Comm Twr A** (both disc 1, the latter made with a full developer-menu inventory and a photo).

---

## 5. What remains — in the order I would do it

**State of play, end of 2026-09-07.** Three items in this section are now DONE
and kept only for their reasoning: 5.3 (`en_menu3`, raw-disc only), 5.4a (the
MOVIE captions) and 5.5's KEY CONFIG. **Nothing with a USA counterpart is known
to be Japanese any more, on any of the three discs.** What is left is of four
kinds:

| kind | items |
|---|---|
| **needs you at the controller**, nothing to build | 5.1, 5.2, and 5.5's list 1 |
| **real engineering** | 5.4 the raw-disc build switch, 5.5's item 6 (`rebuild.py` does not build the VR patches), 5.6 the upstream sync |
| **your call** | §6, and 5.9 |
| **loose ends** | 5.7 untested runtime features, 5.8 the text census, 5.5's item 5 |

### 5.1 Still to be seen (needs the user; nothing to build)
Everything built so far has been seen on screen except: a mission-log page from
demo.gcx (a disc-2 save) and a count-7 page (USA's `1/2` with an empty second
screen — reproduced on purpose, §5.9); the other weapon descriptions besides the
SOCOM; and the disc-swap screens, which only 5.2 can reach. If anything looks
wrong, bisect first: move the family's two PPFs out of the mods folders and
confirm the retail text comes back. No debug shortcut exists for any of it —
the collection's launcher waits for a game to be chosen before anything loads
(a `StageSelect = abst` smoke test idled there on 2026-09-05 00:39).

### 5.2 The disc-2 run (needs the user at the controller; nothing to build)
Load the **Comm Twr A** save (no debug) and play through the actual story disc
break. Watch whether the game's own swap flow draws (`Now Checking...` /
`Insert DISC 2.`) or the collection swaps silently; then read the log for
`Disk ID is 1`. This validates disc 2 and the normal swap path. It does **not**
establish reachability of all four copies: title/wrong-disc, demo-theater and
abstract paths require separate evidence. Unseen text still matters for the
raw-disc release. **The developer menu cannot do this** — disc 2 is set only by
`change.c`'s CD check (README "The disc-swap text: four copies"). Once on disc
2, glance at SCREEN / KEY CONFIG (byte-identical to disc 1) and load a disc-2
save to see a mission-log page from demo.gcx and a count-7 page.

Read the log afterwards for `Disk ID is 1`, any `WATCH` line on disc 2's
spans, and any audit line. The collection patches all four disc-swap text
copies with named files that begin two bytes before `en_menu2`'s `change` and
`demosel` records (README "Where the collection's own disc patches land"); the
watches proved on 2026-09-05 that those patches register on Windows but carry
no inline data, so only the swap screens themselves show whose bytes win. If
the game's own prompt draws in English, ours won; if it draws something else,
note exactly what.

### 5.3 `en_menu3` (the `title` copy) — DONE 2026-09-07, raw-disc only
Built, verified, and deliberately **not deployed**. `menu3.py` writes
`INTEGRAL_disc{1,2}_en_menu3_raw.ppf` into `work/` for the raw-disc variant
(§5.4); `--deploy` refuses and prints why.

**Why it cannot go in the collection.** The collection patches that exact block
itself: `disc1_1822B55D_patch` lands at image `0x1822B55D`, the address of
record 0's `07` header, from `099/patch/disc1_1822B55D_patch_PS5.bin` — a named
file, so the watch reports "0 bytes" and its contents stay invisible. It is not
filtered in normal play. Two patches writing the same five strings with
different layouts desynchronise the script walk: the title stage dies on entry
with a run of `GCL:WRONG CODE` reading out of `Press the Start Button`, the same
seventeen bytes on 2026-08-28, 08-29 and again on 09-07, and the log ends
mid-run. **The user's call, 2026-09-07: ship raw-only.** The alternative — an
ini flag blacklisting their patch so ours owns the block, the `BrightnessText`
mechanism — was declined as an ASI change buying a screen the collection cannot
reach.

**The old diagnosis in this section was wrong, and is corrected in the README.**
It said the interpreter resumes at the early NUL and prescribed shrinking four
container sizes. `GCL_GetNextValue` advances a STRING by its length byte, never
by `strlen`; and the artefact that sat in `mods/_disabled/` changed payload bytes
only, re-parsing cleanly with 25 records at retail's offsets. The prescription
was written on 09-03 from the 08-28/29 logs and attached to a build it had never
been tested against. The shape that crashed on 09-07 is the **length-preserving**
one, which leaves retail's layout completely intact — so the record shape was
never the fault.

What the builder does, for whoever picks this up: it rewrites the five records
inside the `-v` option of the title actor's `CMD 9906` (chara `0xCF79`,
CHARA_OPEN, `onoda/open/open.c` — the same generic numbered-text module as
`abst.c` and the VR captions), re-stamps the SCRIPT/ARG/COMMAND sizes that
`containers_over` reports over each edit, and leaves the `-v` option's own u8
alone because it is an overflowed truncation nothing reads (`v` is the last of
the command's eighteen options and `open.c` asks for exactly those eighteen) —
the same call `abst_build.py` makes for the mission log's `-i`. Record count and
order are preserved because `open.c` reads a fixed 24 and indexes each line's
position and colour by n. No text is modified: USA's sentences go in verbatim,
and only the record slot shrinks.

**Still unproven, and cheap when someone wants it:** boot once with
`DisableCDROM = true`, which filters the collection's patches, and the deployed
build should then load a clean title. That would turn "the collision is the
cause" from a strong inference into a measurement. It costs achievements for one
session, which is why it was not run.

### 5.4 The raw-disc variant — DONE 2026-09-07
One switch now builds both, where two constants used to be edited by hand:

    py rebuild.py --output <dir>                 # collection, what mods/ gets
    py rebuild.py --output <dir> --variant raw   # for a real PSX disc image

| | collection | raw |
|---|---|---|
| `SC_KEEP_LINES` (`optsctext.py`) | 4 | 6, USA's own text |
| `OPTION_MC_CONTROL_SETTINGS` (`opt.c`) | 1, the KEY CONFIG doorbell | 0, nothing to intercept |
| `en_menu3` | excluded | included (§5.3) |

It is `INTEGRAL_ENGLISH_VARIANT`, resolved in `workdir.py` beside
`WORK`/`GAME`/`DECOMP`, so a hand-run tool honours it too. `rebuild.py` sets it
for every tool, rewrites the `opt.c` constant in its own isolated decomp export
before compiling, records both values in the report, names the ZIP for the
variant, and refuses `--compare-deployed` with `--variant raw` (what is deployed
is the collection build). `BUILDING.md` has the table and the commands.

**One bug the first raw build found, and it is the kind only packaging finds.**
`en_menu3` rewrites the whole title block and shifts every record in it, while
`en_menu` writes `RADAR OFF` at retail's offset 130 bytes in - two patches on the
same bytes with different layouts. `rebuild.py`'s packaged-set overlap check
caught it on the first run, at `0x1822b5df`. The fix moves ownership: under
`--variant raw`, `menu2.py` skips that record and `menu3.py` ports it (index 4,
the one entry in its table with no change/demosel twin). Worth remembering as
the general shape - **a builder that shifts records has to own every patch that
writes into the region it moves**, and the only thing that notices is a check
over the assembled set.

**What is NOT proven: the raw variant has never run on a real PSX image.** It
builds and packages; nobody has applied it to a real disc and booted it. That is
the remaining raw-disc work, and it is where `en_menu3`, the six-line brightness
paragraph and Integral's own KEY CONFIG would finally be visible.

### 5.4a The VR movie captions — DONE and VERIFIED ON SCREEN 2026-09-07
All three MOVIE selection captions are ported and deployed as
`INTEGRAL_vr_en_movie.ppf`, and the user's three shots at 01:03 confirm every
one of them:

| clip | on screen |
|---|---|
| TGS ROLL A | `Exhibition clip “A” for` / `the Tokyo Game Show, Spring '98.` on two rows |
| TGS ROLL B | the same with `B` |
| E3 | `Video clip from E3 (6/97)`, one line |

Right text, right clip, two rows where USA has two, and the typographic quotes
render as quotes — so the local-font remap is right as well.

**What the fix is.** The captions are drawn by the engine's generic
numbered-text module — the same one `abst.c` implements in the decomp — which
draws *every* slot that is lit, so the line count is only ever "how many slots
get lit". That is the single place the two discs differ, in the clip-selection
code: USA calls the actor's own `highlight(work, i)` twice, for `clip*2` and
`clip*2+1`, where Integral calls it once with `clip`. USA's sequence is 14 words
and Integral's block has 11, so the port leaves the block alone, retargets its
one `jal` (one word) at a 16-word stub appended to the overlay, and the stub
calls retail's `highlight` twice. Plus USA's six records and USA's position
table, which places the pairs on rows 196/208.

The stub sits at overlay `+1DFB8` (RAM `0x800DF158`) in padding the stage
already carries — the payload is 122,808 bytes inside 60 sectors of 122,880 — so
**no payload moves, the stage keeps its 123 sectors and its LBA, and nothing is
relocated**. The RAM is overlay space by construction: USA's own `movie` overlay
runs 9,576 bytes past Integral's end at the same load base, and Integral's
`init` reaches `0x800EA1EC`. Six lines is what the module is dimensioned for
(its slot array ends exactly where `Act`'s tpage prims sit, at 24 slots; the
builder's cap is 24). The longest line measures **201 px against the 240 px wrap
limit** with Integral VR's own `font.res`, so nothing wraps — that check is a
build-time assertion, because a wrap here lands on the CLUT row and writes past
the buffer.

#### The EXIT box moved up — approved 2026-09-07, and an exception worth naming
Measured off the three shots (9 display px per game px, x offset 480):

| element | game y |
|---|---|
| EXIT box, top border | 190–191 |
| EXIT text | 193–199 |
| EXIT box, **bottom border** | **201–202** |
| caption line 1 | **201–213** — overlapped the border by 2 rows |
| caption line 2 | 215–225 — clear |
| E3's single line | 203–213 — cleared the border by 1 px |

A two-line caption at USA's rows collided with Integral's EXIT box by two pixel
rows. USA avoids it twice over, and the user confirmed both halves: its caption
face is **shorter**, and its **EXIT box sits higher**.

The font stays Integral's — a face is its own art, not text (README "The white
caption font differs between the two VR discs"), and line 1's ink is 12 rows
because it is topped by the two 12x12 script-local quote glyphs where the same
font draws the option screen's `Sound setting.` in 8. So the room comes from the
box, which is **chrome that positions text** under rule 3.

**The decision, in the user's words: "Make sure to document this decision.
Usually we skew toward the Integral visuals."** This is therefore a named
exception to that default, approved on 2026-09-07 after being asked: the box
moves because the English cannot otherwise sit where USA puts it. Nothing else
about the box changes — Integral's art, colour and size all stay.

**Where the position lives, and how much it moved.** Every widget in the stage is
built by `Init_Res(slot, 0, GV_StrCode(name), y)`, centring the texture from its
own header and offsetting it by y from screen centre 120. Listing all 28 calls in
both overlays gives y values **identical between the discs except one**:

    sp_exit    Integral y +70 (screen 190)      USA y +66 (screen 186)

and the measured retail top border is exactly 190, which confirms the model. One
immediate carries it — scanning every `addiu`/`ori`/`slti` in either overlay
finds precisely one instruction holding 70 (Integral) or 66 (USA) — so the port
writes `addiu a3, zero, 66` at overlay `+F128`, USA's own value.

**The highlight moves with it**, which the user asked to be sure of. The widget
is a single object at `work+0xF0`, and both things that light it anchor on that
object rather than on a coordinate of their own: `+10198` attaches the `cur_l`
cursor as `f(work+0xF0, strcode, 1, 1)`, and `+F38C` sets its lit state as
`f(work+0xF0, 0xFF, 1)`. Both call sites — and all ten references to
`work+0xF0` — are byte-identical between the discs. So USA's entire widget, box,
label and selection highlight, sits at 186 because of that one immediate;
nothing else could position the highlight, or USA's own would be wrong.

Deployed 2026-09-07. Expected on the next look: the box 4 px higher, its
highlight with it, and 3 rows of clearance under it instead of a 2-row overlap.
**Not yet seen on screen** — that and the EXIT highlight when selected are the
only things left to confirm here.

**If the whole thing ever has to come out**, the fallback is a file move, not a
rebuild: put `work\INTEGRAL_vr_en_movie_e3.ppf.was-deployed` back in
`mods\INTEGRAL\VR-DISK\` as `INTEGRAL_vr_en_movie_e3.ppf` and delete
`INTEGRAL_vr_en_movie.ppf` (never both — they overlap and `_e3` sorts last).
That returns to the 2026-09-06 state: the E3 caption in English at Integral's own
row, both TGS captions Japanese, and no code change in the overlay at all.

**Two earlier attempts failed, and both are recorded in the README** ("Three
corrections"): the record count alone (six records with one highlight gives one
line per clip and misattributes captions) and USA's position table alone (the
rows moved exactly as predicted and still one line each). The address that made
both look like dead ends was `Act`'s `lw` from `0x800A9580`, read as
`captions[clip]`; the decomp's `abst_sprt` indexes the same table with
**`GV_Clock`** — it is the per-frame ordering table, and the draw is handed an
OT, not a string. Lesson worth carrying: **when a disassembled function indexes
a global, find the same pattern in the decomp before naming the global.**

### 5.5 The VR disc: what has been seen, and the edges left
Ported 2026-09-06, deployed, and **first run on screen 2026-09-06/07**. Seen and
correct: the option screen's seven help lines, centred, after the three faults
§4 records; the mission menu with every mission unlocked; a clip's description
window in English when a TGS video opens; and EXTRA -> MOVIE with all three
thumbnails and, since 2026-09-07, all three captions in English — the two TGS
ones on two rows (§5.4a, which also records the one cosmetic item left there:
line 1 touches the EXIT box, because USA moves its EXIT up and Integral's face
is taller). What is left, in rough order:

1. **On screen 2026-09-07: mission windows.** Two shots, both correct English -
   `ADVANCED MODE / SOCOM LEVEL 01`, "Eliminate all enemy soldiers and head for
   the goal! / Enemies 2", and `1 MIN. BATTLE VS. TARGET / SOCOM`, "Use Socom to
   destroy targets! / Conditions to clear: 15 targets". That is the title and
   the briefing of the `vr_en_missions` family, the largest one, read in play.

   **Still unseen**: a mission RESULT window, the EXTRA menu's four help lines
   (`vrtitle`), an item and a weapon description, a save and a load message, and
   the PHOTOGRAPHING mode's card messages (the ALBUM path). If something is
   wrong, bisect the same way as the main game: move that one PPF out of
   `mods\INTEGRAL\VR-DISK\` and confirm the Japanese comes back.

   **On reaching the item and weapon descriptions:** there is no "give all" for
   VR and there does not need to be. Every mission fixes its own loadout, so the
   pools are covered by playing the mission that carries each one - the mission
   aid makes them all selectable and that is as far as unlocking can take you.
   Four entries are Japanese **on purpose** and are not faults: Integral's MP5 SD
   (no USA counterpart), the frozen Ration/Ketchup pair (no USA counterpart, and
   unreachable in VR), and the mine-detector HARD/EXTREME line (VR has no
   difficulty level).
2. **KEY CONFIG — DONE 2026-09-07.** Seen with `DisableRAM = true` and
   `DisableCDROM = true`: Integral's own screen, all eight labels English in
   all three button types, `key_syukan`'s +11 shift clearing the connector
   curve. The user spotted the one fault — the row's selection highlight was
   24 px short, because it is drawn by hardcoded `glow()` arguments rather than
   an `Init_Res` quad and the transplant only knew about quads. Fixed, redeployed
   and re-measured within a px of USA (README, "The VR KEY CONFIG on screen").
   The help line under the controller stays Japanese by rule: USA leaves records
   17..25 empty. **The flags are only for looking at it** — the user's rule
   stands that in the collection they prefer the interception, and the
   transplant is for the raw disc.
3. **Three unlock aids may stay for testing and must come out after.**
   `vr_unlock.py` (Integral's missions), `vr_unlock_movies.py` (the EXTRA clips)
   and - for the donor disc - `VRUS_unlock_missions.ppf`, which `vr_unlock.py`
   also builds. None writes progress, so saving with them in place is safe; the
   standing rule is achievements **off** first, unlock, test, delete the unlock
   PPFs, achievements back on.

   **The USA one sat unbuilt-into-place for a day**: it was written 2026-09-06
   and never copied to `mods\VR-DISK_US\`, so USA's missions were still locked
   when the user went to compare against them on 2026-09-07. Deployed then.
   Ketchup's base path for that title really is `mods\VR-DISK_US` with no
   version or disk subdirectory - confirmed in the log, `[Ketchup] base path is
   mods\VR-DISK_US`. There is no USA equivalent of `vr_unlock_movies` yet; USA's
   own EXTRA clips gate the same way and would need their own offsets.
4. **The number substitutions** in §6 need the user's word.
5. **Deferred edges**, each a small piece of work: the camera's EXORCISE
   textures, and whether anything in the mission windows overflows a line at
   240 px the way the main game's could. (The two TGS MOVIE captions were the
   third item here and are done — §5.4a.)
6. **`rebuild.py` builds the VR patches — DONE 2026-09-07.** All seven come out
   of the same isolated run as the main discs and are packaged under
   `mods/INTEGRAL/VR-DISK/`. Three things were needed: extracting the two VR
   stage dirs, **building** Integral's VR executable from the decomp rather than
   copying it (the generator runs a second time for the `vr_exe` variant, then
   ninja makes `obj_vr/_mgsi.exe`, checked against SHA-256 `c370f8e4…`), and
   giving `vr_movie` an `INTEGRAL_ENGLISH_VR_PPF_DIR` so it composes on the run's
   own output instead of the deployed folder. The VR set's one deliberate
   overlap (`vr_en_movie` over `vr_en_missions`) is allowed by name and any other
   is an error. The two unlock aids are deliberately not built: they are test
   aids and must never ship. Verified on `repro8`: **25 PPFs, 18 main + 7 VR, all
   25 equal to the deployed set's effective bytes.**

### 5.6 Sync with upstream, and the pull request — one job, done once
**Measured 2026-09-07, and the decision was to defer it deliberately.** A
fast-forward is impossible: that needs a branch with no commits of its own, and
this one has 133.

| | |
|---|---|
| merge base | `8fb944d` (v3.6 + 5 commits) |
| upstream commits we lack | **10**, through `48fe165` "Complete Wamsoft port" (2026-09-07) |
| our commits they lack | **133** |
| our `src/` footprint | 854 lines across **9 files** |

**Every file the port touches has moved upstream**, so any route has to follow
renames:

| ours | upstream | similarity | our lines |
|---|---|---|---|
| `src/mgs1.cpp` | `src/games/mgs1.cpp` | **54%** | +242 |
| `src/mgs1.h` | `src/games/mgs1.h` | 98% | +234 |
| `src/ketchup.{cpp,h}` | `src/m2fix/…` | 100% | +152 / +39 |
| `src/m2config.{cpp,h}` | `src/m2fix/…` | 100% | +62 / +20 |
| `src/m2game.h` | `src/m2fix/m2game.h` | 98% | +11 |
| `src/sqhook.{cpp,h}` | `src/modules/…` | 96 / 97% | +79 / +15 |

Eight of the nine are near-pure moves that git's rename detection will carry;
the work concentrates in `mgs1.cpp`, the one file upstream rewrote and the one
holding most of our lines.

**Why it is deferred rather than done: those ten commits give MGS1 Integral
nothing.** They are Vol. 2 support, MGS1in4 fixes, the Wamsoft port, PATRIOTS
text and the restructure. Upstream's own diff to `mgs1.cpp` is **0 insertions,
130 deletions** - code moved out, no MGS1 behaviour changed - and nothing in
them touches `MGS1_Ketchup`, Integral, the brightness text, the Ketchup
deferral or the patch watches. Against that, merging costs a conflict
resolution in our most-changed file plus a rebuild and a re-test of everything
runtime the ASI carries (`EnglishText`, `BrightnessText`,
`PreserveConfiguration`, the deferral, six patch watches).

**So it is one job, and the right moment is the pull request**, because the PR
needs our changes in upstream's new layout anyway - doing it now would mean
doing it twice. When it happens:

- try `git merge upstream/master` on a throwaway branch first and read the true
  conflict set before touching `integral-english-text`;
- `UPSTREAM.md` lists what goes up; its two omissions are right (789f4a2 is
  superseded by the BrightnessText tri-state, fbb170c is the port-only abst
  watch comment);
- separate two things when submitting: `SetPatchWatch` goes upstream as a
  mechanism *without* the Integral `option`/`abst` ranges `mgs1.h` registers,
  and `BrightnessText` covers title 981 (USA) only;
- re-test the runtime list above afterwards - the port's behaviour in the
  collection depends on all of it.

### 5.7 Still untested, low effort when the moment comes
- **The patch watch is blind while `DisableCDROM = true`**: the early return
  in `sqhook.cpp` precedes the watch loop. Answered 2026-09-05 12:57 with the
  flags live: the `_PS5`-suffixed `abst` patch does register on Windows (and is
  orphaned by the `en_abst` relocation); named-file patches carry no inline
  data, so their content stays unknown to the watch.
- `PreserveConfiguration` catching a real stale write (intermittent race).
- `GiveItems` in a stage where the inventory is actually empty (a real save,
  not the developer menu).
- `Ketchup::Audit` did report two `differs from what was written` lines on
  2026-09-05 — both were the game's own code editing ported strings, fixed in
  `items.py`. Both pools are now owned byte for byte; a future audit line means
  the collection wrote *after* Ketchup's pass, which has not been seen.

### 5.8 Finish the text census (`COVERAGE.md`)
`audit_text.py` inventories GCL string candidates and address references
across all three Integral images and USA's, but it is a framing heuristic.
Of disc 1's 1,414 flagged Integral candidates, 1,025 were the mission log (now
ported), 111 are preope's retained unread recap bytes, 51 `rank`'s Integral-only
sentences, 45 the 1P MODE pages, 20 the option screen's Japanese help lines;
about 160 remain across gameplay stages and need verification against their
callers, the font bank (`0x80xx` is Latin, `0x9001` a space) and a reachable
screen — USA itself shows 307 flagged, so a flag is not a Japanese string.
Texture lettering and runtime language branches are outside both tools.

### 5.9 Optional, ask first
- The caption under READ MISSION LOG? (作戦記録を参照しますか？): kept because
  USA draws nothing there; `KEEP_PROMPT_CAPTION = False` in `abst_build.py`
  gives USA's empty record. Also the `1/2` counter and empty second screen on
  count-7 pages — USA's own behaviour, reproduced.
- Location-name spellings in `abst` (`Tank Hanger` / `Medi rm` / `Cmnder rm`
  vs USA `Hangar` / `Medi room` / `Cmnder room`): Integral's own English, not
  Japanese — outside the rule as written, so ask.
- `rank`: 36 Integral-only Japanese sentences with no USA counterpart → stays
  Japanese unless a USA source turns up. Nothing to do without one.

---

## 6. Decisions that are the user's — ask, do not assume

- The caption under READ MISSION LOG? (kept Japanese by rule; one constant
  blanks it) and USA's `1/2` on single-screen pages (reproduced) — §5.9.
- Anything under the 2026-09-03 amendment: moving English text to fit
  Integral's own art.
- The `en_savemsg` collision approach, if one is ever observed.
- Achievements on or off for a given test session (`DisableRAM` /
  `DisableCDROM`); they are **on** now. Turning them off keeps SPECIAL / PHOTO
  ALBUM reachable without earning it and has never affected the PPFs.
- Anything that touches Integral's own English (5.9), the `abst` location
  spellings first.
- **The VR disc's three number substitutions.** Where Integral and USA state
  different values, USA's sentence was taken with **Integral's** numbers put
  into it, so the text matches the disc it runs on: SNEAKING MODE / NO WEAPON
  LEVEL 10 25 not 35; SNEAKING MODE / SOCOM LEVEL 03 40 not 43; WEAPON MODE /
  GRENADE LEVEL 02 5 not 4. Flip `SUBSTITUTE_NUMBERS_OFF = True` in
  `vr_windows.py` to take USA's numbers verbatim instead.
- **The VR KEY CONFIG's `key_syukan` +11 shift**, carried over from the main
  game's 2026-09-03 approval rather than asked again.
- **The VR MOVIE EXIT box, moved up 4 px — ASKED AND APPROVED 2026-09-07.** With
  USA's two-line caption the first line's ink overlapped Integral's EXIT box by
  two pixel rows; USA makes the room with a shorter caption face *and* a higher
  box. The face stays Integral's (its own art), so the box moved instead, to
  USA's own `sp_exit` y of +66 (screen 186 against 190) — one immediate at
  overlay `+F128`, and the selection highlight follows because it anchors on the
  same object. Approved against the user's stated default, **"usually we skew
  toward the Integral visuals"**, which makes this a named exception rather than
  a precedent: §5.4a has the measurements and the reasoning.
- **VR EXTRA menu record 6.** Integral's fifth item is PocketStation where
  USA's is STAFF CREDIT, so `See the staff credits.` was **not** used. If the
  user would rather see English there, it needs new text, which the rule
  forbids without authorisation.

---

## 7. Tools (all in this directory; `py <tool>`; they find `work\` themselves)

| tool | purpose |
|---|---|
| `workdir.py` | resolves the working directory **and the build variant** (`py workdir.py` prints both); `VARIANT`/`RAW`/`pick(collection, raw)` come from `INTEGRAL_ENGLISH_VARIANT` |
| `ppfcheck.py [--deployed]` | validates PPFs exactly as Ketchup reads them — run before deploying anything |
| `optsctext.py` | builds `en_option` (sc_text texture, KEY CONFIG art, chain, relocation to DUMMY3M slot 384, doorbell stub check) |
| `verify_integral_option.py`, `verify_usa_brightness.py` | read the deployed PPFs / built-in patch back and check them |
| `shotcmp_brightness.py A.jpg [B.jpg]` | measures brightness-screen shots |
| `preope_usa.py` | Previous Operations directly from retail, USA pagination; stages PPFs unless `--deploy` is supplied |
| `brf_build.py`, `brf_widen.py` | briefing labels and quads |
| `savemsg.py`, `camsave.py` | the two memory-card caption ports |
| `abst_build.py [--deploy]` | the MISSION LOG port: rewrites both GCX scripts in the `abst` stage with USA's pages, swaps the bottom-bar art, packs the stage with `obj/abst.bin`, relocates to DUMMY3M slot 462, verifies, stages/deploys the PPFs |
| `abstscan.py [page N]` | mission-log scoping data, both games (retail data; the port's own checks are in `abst_build.py`) |
| `jpsweep.py` | historical disc-1 pointer-slot candidate scan; not a completeness proof |
| `gclparse.py`, `gcldec.py` | GCL container parsing / record walking — `containers_over` for resizing |
| `optscan.py` | option-stage inspection |
| `optlabel2.py` | current option captions from retail, including the restored colon; replaces the unsafe recovered experiment |
| `items.py`, `menu2.py` | recovered item/menu builders; the `title` copy lives in `menu3.py` instead |
| `menu3.py [--collection]` | the `title` stage's disc-swap copy, **raw disc only** — rewrites the five records inside `CMD 9906`'s `-v` option, re-stamps the SCRIPT/ARG/COMMAND sizes and leaves the overflowed `-v` u8; `--deploy` refuses, `--collection` rebuilds the shape that crashes so the fault can be reproduced (§5.3) |
| `audit_text.py` | main-disc and VR candidate inventory, save-title encoding; see `COVERAGE.md` |
| `rebuild.py [--variant raw]` | the isolated build of **everything**: nine main families for both discs and the VR disc's seven, checks, manifest and ZIP. Builds Integral's VR executable from the decomp rather than copying it, and points `vr_movie` at its own output. `--variant raw` swaps the two constants and adds `en_menu3`; `--compare-deployed` checks every PPF's effective bytes against `mods/`. See `BUILDING.md` |
| `portio.py` | shared read-only disc access and deterministic PPF/stage serialisation (`stage`, `pack_stage`, `records`, `encode_records`, `changed_runs`, `ppf`, `relocation`) — the module the recovered builders and `rebuild.py` are built on |
| `iso.py` | raw-sector disc reader (`Disc(path, base)`; mode-2 24-byte headers), used to read the images inside `alldata.bin` / `dlc_japan.bin` |
| `kcplace.py`, `kcquads.py`, `kcrects.py` | KEY CONFIG port helpers: VRAM/CLUT allocation for USA's eight labels, quad extraction from an option overlay, the per-button-type label rectangles |
| `quadscan.py`, `rowargs.py` | briefing helpers `brf_widen.py` imports: quad-call arguments and a linear register simulation for the row arithmetic |
| `measure.py`, `align.py`, `rows.py` | screenshot measurement for the briefing menu (label ink, rows against the divider, right-column bands) |
| `optbright.py` | **historical** — the font-text brightness build the `sc_text` texture superseded; its wrap-width notes are still the reference for other option entries, its output is no longer an input to anything |
| `ppfgen.py`, `reloc_ppf.py` | **legacy** PPF emitter and manual DUMMY3M relocation; `rebuild.py` and the builders use `portio.ppf` / `portio.relocation` instead. Still runnable; `reloc_ppf.py` needs disc images in `discs/` |
| `preope_both.py` | **obsolete** experiment (both recaps re-wrapped, 12/19 pages); `preope_usa.py` supersedes it and needs nothing from it — a candidate for removal |
| `unlock_title.py` | builds the (parked) main-game unlock PPFs |
| `vrlib.py` | **the VR disc's shared library**: both VR ISOs and stage dirs, the GCL parser/emitter used for VR scripts (`parse_arg`/`emit_arg`, options, expressions, the language variable), `Gcx` script/proc/font container, in-place stage repacking with sector padding, PPF records with gap merging, deploy |
| `vr_windows.py [--build] [--deploy]` | the mission-window port: pools USA's windows by title, matches by content, merges the script-local fonts, substitutes Integral's numbers, rebuilds 92 stages in place |
| `vr_exe.py [--deploy]` | the VR executable's item/weapon/capture pools and its save and load messages |
| `vr_option.py [--deploy]` | the VR option stage: help-line chain, the KEY CONFIG label transplant (per-type function, 21 call sites, `key_syukan` +11) and the re-encoded texture archive |
| `vr_menus.py [--deploy]` | the VR EXTRA menu's help lines |
| `vr_camera.py [--deploy]` | the VR camera overlay's memory-card messages |
| `vr_movie.py [--deploy]` | the MOVIE selection captions. Builds **two** PPFs into `work\`: `..._movie.ppf` (all six USA records, USA's position table and the two-line stub — **the port**, deployed) and `..._movie_e3.ppf` (the E3 caption alone, retail structure and no code change — the fallback). `--deploy` installs the first and moves the second out of `mods\`, since they overlap and only one may be present. Built on the composite, since `vr_en_missions` already owns the stage |
| `vr_kcgeom.py` | VR KEY CONFIG geometry read from an overlay: `Init_Res` quads and the per-button-type rectangles (imported by `vr_option.py`) |
| `vr_unlock.py [--deploy]` | the removable VR **mission** unlock test aid — three words, never deploy with achievements live |
| `vr_unlock_movies.py [--deploy]` | the removable VR **movie** unlock test aid — one instruction in the `movie` overlay's own `count / 3` score gate, which `vr_unlock` does not touch. Writes no progress; delete the PPF to relock |
| `vr_sweep.py [--samples]` | rebuilds every VR stage from the deployed PPFs and reports what is still game-encoded, beside USA's own tally — the VR equivalent of `jpsweep.py`, and the only tool here that inverts `portio.image_offset`'s 2352-byte sector geometry |
| `bridge.py` | the Squirrel-debugger client for live RAM reads/pokes (README "Toolchain and environment"); writes `sqcmd/`, `sqout/`, `bridge.log` beside itself (git-ignored) |
| `gcldump.py`, `gclprocs.py` | dump a stage script's command tree / every proc with decoded values (used to read the title script's 1P MODE path) |
| `pcx4.py` | encode/decode the 4-plane RLE PCX the texture loader expects (how `sc_text` and the KEY CONFIG art were read and written) |

Rescued from the session scratchpad on 2026-09-04, where they existed nowhere
durable: `bridge.py`, `gcldump.py`, `gclprocs.py` (now in this directory) and
`map_pristine.map`, the pristine executable's symbol map (now at
`D:\mgsbuild\integral-english-work\`). `items.py`, `menu2.py` and `optlabel2.py`
were likewise recovered and rewritten with explicit inputs and no implicit
deployment. Nothing the build needs lives in a scratchpad any more; the scripts
that only shaped documentation are disposable.

---

## 8. Where the details live (README section names)

Gotchas → "Gotchas" (freeze/crash triage, overlays, font limits, GCL chain,
textures, disassembly, screenshots, PPFs, toolchain) · "The three limits" ·
"Things that do not work" · "Wrap width" · KEY CONFIG → "The KEY CONFIG screen",
"The collection's KEY CONFIG interception, and how the port broke it", "How the
KEY CONFIG port was built" · PPF → "PPF3's description field is 50 bytes" ·
captions → "Memory-card messages (`en_savemsg`)", "The PHOTO ALBUM's own
memory-card messages (`en_camsave`)" · sweep → "Sweep: is any UI text still
Japanese?" · mission log → "The MISSION LOG port", "The disc-swap text: four
copies", "Why `en_menu3` is raw-disc only" (and its two sub-sections: the
diagnosis it replaces, and "The general trap: the collection may already own the
bytes you are porting") · scope → "Scope", "What stays
Japanese, and why" · brightness → "The collection shows only four of USA's six
brightness lines", "Option → SCREEN", "The sc_text texture port" · briefing →
"Briefing menu (`brf` stage)" · unlocks → "Unlocks", "Give items", "Unlock
everything", "Unlock every VR mission", "Unlocking the EXTRA movies",
"Achievements" · VR → "The VR disc (SLPM-86249)", "The MOVIE selection
captions", "The white caption font differs between the two VR discs",
"Sweep: is any VR text still Japanese?" · tests → "Not tested" (struck-through items are
done, with dates) · decomp → "Audit against the decomp".

## 9. The 2026-09-04 late pass: what changed and what it settled

Commits `d988e1d` … `5b8d280`. In one evening the project went from "the
deployed PPFs work but some were built by scripts that no longer exist" to a
build anyone can reproduce and check:

- **`rebuild.py` + `BUILDING.md`**: isolated, retail-input build of all eight
  families for both discs; PPF framing and sector-boundary validation; a
  cross-set overlap check; a ZIP with `SHA256SUMS.txt` and `build-report.json`
  (environment, SDK file hashes, every input and output). The clean run matched
  the deployed set (see §4). It never installs.
- **Recovered builders** (`items.py`, `menu2.py`, `optlabel2.py`) with explicit
  inputs; `optsctext.py` builds its caption chain from retail via
  `optlabel2.py`, so the pinned font-text PPF and the "builder consumes its own
  output" hazard are gone; `preope_usa.py` builds both recaps from retail with
  an explicit `--deploy`; `brf_*` read the real USA stage and the row/quad
  constants were re-verified against it (all 16 row and 53 quad tuples match).
- **`audit_text.py` + `COVERAGE.md`**: three-disc candidate inventory with its
  limits stated; the save-slot title is full-width in USA too, so it is
  branding/encoding, not a port target; one more retained camera caption noted.
- **Stale guidance corrected**: `f924` stays `[8]` (growing it *causes* the
  EXIT freeze); `MG2_RECAP_OFFSET` is 22042 for the 13-page build; a silent
  normal disc swap does not prove the other three disc-text copies unreachable;
  `UPSTREAM.md` has real hashes and current status; `BrightnessText` is
  `[Patches]` and USA-only.
- Verified independently afterwards: the ZIP hash, all 16 `reference_effect_equal`
  flags, the decomp patch equal to the live decomp diff, deployed mods untouched
  (`ppfcheck --deployed` clean on all 18 files).

None of this closed the gameplay items, the disc-text family, the raw-disc
variant, VR or the census. It made them buildable and checkable when they are
done — which the Mission Log then was (§10).

## 10. The 2026-09-05 pass: the MISSION LOG, then three item faults

The user's go-ahead came with the USA screenshots ("the English one takes 2
screens") and "I want everything ported over perfectly when I return. Don't
forget to use the decomp files for reference where it helps." In order:

- **Night — the port.** `abst_build.py` rewrites the two GCX scripts
  (scenerio.gcx and demo.gcx — the cache section's tag sizes are offsets, and
  the 42 `d`-PROCID pages are demo.gcx's) with USA's counts and line records
  verbatim, keeps Integral's record 0 (the caption) and both fonts, and
  re-stamps every container; the disc-change abstract gets USA's eight strings
  (+13,804 bytes). `abst.c` grown to USA's model (128×20 KCBs in two VRAM
  columns, the 15-entry line table, the counter, the cursor frame, the slide,
  USA's input model), read from USA's overlay instruction by instruction, with
  one guard against colouring KCBs a count-7 page never allocates. USA's three
  bottom-bar textures in the footprint of Integral's two; every other texture
  and palette stays Integral's. 88 sectors, DUMMY3M 462..549, both discs.
  `rebuild.py` builds nine families and three overlays. An unattended smoke
  test was tried and cannot work: the collection's launcher waits for a game.
- **Night — three item faults**, found from the user's first shots after the
  deployment and pinned down by Ketchup's audit lines (README "Three item-text
  faults"): the card level digit offset (code, 46 → 45), the SOCOM suppressor
  rewrite into the Mine Detector text (code, six stores NOPed), and a
  retail-equal byte the collection's RAM patch owned (both exe PPFs now write
  every byte of their regions; `Applied … RAM patches` reads 3,755).
- **Night — the collection's disc-patch map** (README "Where the collection's
  own disc patches land"): it patches all four disc-swap text copies with named
  files two bytes before `en_menu2`'s `change`/`demosel` records; watches added
  for `change`, `demosel`, `title`, `camera` on both discs. The ASI build hung
  overnight (six idle `cl.exe`, stopped by PID); rebuilt and deployed 12:49.
- **Morning — on screen.** The user's shots: both mission-log pages of two
  logs right; the item fixes right; the page slide showed coloured fragments
  (stale VRAM in texels 504..511 of each line — the KCB buffer is 504 px wide
  and USA's second sprite 256 — fixed by drawing 248 px, decomp `26d27f1`,
  deployed 13:05, **confirmed clean 13:50**). The watches showed the
  collection's `camera` and `title` offset patches are its STORAGE rename
  strings and that its named disc-swap patches register with no inline data.
- **Clean run `repro7`** (13:06) reproduces all 18 deployed PPFs after every
  fix; `ppfcheck --deployed` clean on 20 files.
- Doc corrections found on the way and folded in: the `_disabled` path, the
  PatchWatch-blind-under-DisableCDROM note, the upstream re-port sizing, eight
  stale README passages (verify_shipped.py, scratchpad tools, the optbright
  build paragraph, `discs/`, the pinned chain input, the What ships row, the
  mission-log cross-reference, the ini snapshot path), and the "items proven
  intact" conclusion, which held only for bytes a record named.

---

## 11. The 2026-09-06 pass: the VR disc

The whole of §5.5 as it used to read ("not started") is done. What the pass
established, beyond the patches themselves:

- **The VR disc is its own game.** Its own executable, overlays and containers;
  the only thing the main-game port supplied was the file formats and the
  discipline (own every byte of a pool; never relocate a stage; run
  `ppfcheck.py`). Every address in the README's VR section was read from the VR
  binaries, not assumed from disc 1.
- **USA's VR executable ships five languages.** English is first in the
  tables-of-tables and GCL variable `0x11` selects; the port reads the English
  pool and `vrlib.language_of()` recognises the same variable in scripts.
- **Windows are matched by content, not position.** The user's warning that the
  shots were not taken in the same order was right about the data too: the two
  discs do not lay their stages out alike. Titles reduced to uppercase
  alphanumerics key a pool; same-stage matches win, then pool-unique matches,
  then position for the few windows with no ASCII title.
- **Script-local fonts had to be merged, not chosen.** Codes ≥ `0x9A00` index a
  font inside each script. Integral's holds the Japanese glyphs, USA's the
  typographic quotes; keeping either alone produces mojibake, so USA's glyphs
  are appended and the ported strings' codes rewritten.
- **Nothing grew.** Ten stages shrank by a sector and were padded back, so no
  stage moved and no collection patch was orphaned.
- **Progress on the VR disc lives in VRAM.** The clear bitmap is a 12×16
  rectangle at (160, 224) that every mission stage's overlay knows; the save
  file is built from it. That is why `vr_unlock.py` can unlock everything
  without ever writing progress, and why deleting it restores the real state.
- **The KEY CONFIG textures did not fit** until every texture in the option
  stage's archive was re-encoded losslessly, which is why `pcx4.py` gained an
  8-bit codec.
- **The disc image has raw 2352-byte sectors.** A PPF offset is
  `(lba + off // 2048) * 2352 + 24 + off % 2048`. The first version of
  `vr_sweep.py` divided by 2048 instead, applied every record at a nonsense
  offset, and made a finished port look unported — for about twenty minutes it
  looked like a serious gap. Anything that reads a deployed PPF back must use
  `portio.image_offset`'s geometry. The port itself was always correct; only
  the checker was wrong.

Left where it was: the collection still intercepts VR's KEY CONFIG, so seeing
Integral's own needs `DisableRAM` and `DisableCDROM`. The ASI was rebuilt with
five VR patch watches and deployed at 00:25.

## 12. The 2026-09-07 pass: the VR disc on screen, and the last three items

A long day. The VR port's first play test fixed three faults; then the three
items that had been open longest all closed - the two-line MOVIE captions,
`en_menu3`, and the VR KEY CONFIG behind the collection's interception. Two
earlier conclusions recorded here were corrected in the process, and one
recorded diagnosis turned out to describe an artefact it had never been tested
against.

- **The option screen crashed the stage, and the cause is a general invariant.**
  `load option` died with `r3000: illegal instruction`. A DAR entry header is
  `{u16 id, s16 ext, u32 size}` written immediately after the previous payload,
  so an **odd payload size misaligns the next header's `u32`**. Our rebuilt
  archive had 39 odd sizes and 41 of 51 entry starts misaligned; all four retail
  DARs checked (Integral and USA, main and VR) have zero. Padding every payload
  to 4 fixed it. It cost run length: `pcx4._rle` had capped runs at 62 when
  `PCX_RLE_CODE(0xC0) + run` allows **63**, so `maxrun` became a parameter (it
  still defaults to 62, and the main game's `en_option` rebuilds byte-identical).
- **Then the option rows overlapped.** Record 3 held the vibration-test sentence
  that Integral draws at the row-label position, so the sentence appeared twice
  — blanked, the same decision the main game took on 2026-09-02. Integral's
  colon and values were still lit beside the English — unlit through the
  per-state colour switch, which sets every entry it skips to colour 0. And the
  lines sat off-centre — each ported entry got USA's `{num 1, x 160, y 196}`,
  measured afterwards within 0.3 game px of centre.
- **The EXTRA movies were gated separately from the missions.** `vr_unlock`
  patches `selectvr`; the clips are gated in the `movie` overlay's own
  `count / 3` score against 45 and 75, which is why they stayed `???` with the
  mission aid in place — and why USA's unpatched VR disc showed `???` too.
  `vr_unlock_movies.py` replaces one instruction. All three thumbnails appear.
- **The EXIT box moved 4 px up, and that was the user's call.** With USA's
  two-line caption the first line's ink overlapped Integral's EXIT box by two
  pixel rows. USA makes the room with a shorter caption face *and* a higher box;
  the face is Integral's own art and stays, so the box moved to USA's own
  `sp_exit` y — one immediate, and the selection highlight follows because it
  anchors on the same widget object. Asked and approved, and recorded as an
  exception to the user's stated default, "usually we skew toward the Integral
  visuals" (§5.4a, §6, and the README's amendment table).
- **The MOVIE captions took three attempts, and the third is deployed.** USA
  draws each TGS caption as two lines where Integral draws one per clip. Adding
  USA's records gave `record = clip` (clip A a fragment, the other two clips
  someone else's line); writing USA's caption **position table** moved the rows
  exactly as predicted and *still* gave one line each, which was read as "so it
  is all code". Both were half-right. The actor is the engine's generic
  numbered-text module — the same one `abst.c` implements — and it draws *every*
  slot that is lit, so the line count is only ever how many slots get lit. That
  is the one place the discs differ: USA calls the actor's own
  `highlight(work, i)` **twice**, for `clip*2` and `clip*2+1`, where Integral
  calls it once. The port retargets that single `jal` at a 16-word stub in the
  overlay's own sector padding, and keeps USA's records and position table. All
  three captions are now English and deployed; the two-line form has not been
  seen on screen yet. §5.4a and README "The MOVIE selection captions".

- **`en_menu3` is done, and the answer was "not here".** The last Japanese text
  in the main game with a USA counterpart now has a builder (`menu3.py`) and two
  verified PPFs - and they ship for a raw PSX disc only. The collection patches
  that same block itself, at the exact address of our first record, and the two
  layouts do not mix: the title stage dies on entry. Both the August crash and a
  fresh one on 09-07 are the same seventeen bytes. The recorded diagnosis
  (container sizes) turned out to describe nothing that was wrong with the file,
  and the shape that crashed is the one that leaves retail's layout untouched.
  The user chose raw-only over blacklisting the collection's patch. §5.3.

- **The VR KEY CONFIG was seen for the first time, and the highlight box was
  wrong.** With `DisableRAM`/`DisableCDROM` on, Integral's own screen draws with
  all eight labels English in all three button types and `key_syukan`'s +11
  clearing the curve. The user spotted what the measurements had not: the
  selection highlight on the `first person view` row stopped 24 px short, which
  is exactly USA's 112-wide art against Integral's 88. It is drawn by hardcoded
  `glow(work, x, y, w, h, ...)` calls, not by an `Init_Res` quad, so the geometry
  transplant never saw it - four immediates fixed it, re-measured at 113 px
  against USA's 114. §5.5, and README "The VR KEY CONFIG on screen".
- **Upstream was measured and deliberately not merged.** A fast-forward is
  impossible (133 commits of our own), every file the port touches has moved,
  and the ten upstream commits change no MGS1 behaviour at all - their `mgs1.cpp`
  diff is 0 insertions and 130 deletions. Deferred to the pull request, which
  needs the same work anyway. §5.6.

Three process notes worth keeping:

- **Ship what can be seen, not just what is safe.** The E3-only caption build
  was deployed first because it was provably safe under any mapping — but it is
  the clip behind `???`, so the user's next look showed Japanese captions and
  nothing else. Visibility should be checked before safety.
- **"The code is identical, so it must be data" is worth one experiment.** Every
  function in the caption *actor* was diffed against USA's and found logically
  identical, which made a data explanation feel forced rather than chosen. The
  position table was data, the write demonstrably landed, and the behaviour did
  not change. Reasoning of that shape earns a test, not a build. The error the
  failed test then invited was the mirror image — "so it is all code, in the
  functions I already read" — when the answer was seven words away in a function
  nobody had opened: the *input handler*, not the actor.
- **When a disassembled function indexes a global, find the same pattern in the
  decomp before naming the global.** `Act`'s tail loads from a table with a
  global at `0x800A9580` and that was written down as `captions[clip]`, which
  made `record = clip` look structural in the drawing code and sent two sessions
  hunting for a line count there. The decomp's `abst_sprt` indexes the same way
  with **`GV_Clock`** — frame parity — and the table is the per-frame ordering
  table. One misnamed global cost two builds and two play tests. The general
  lever: the decomp does not have to contain the *function* to name what it
  touches, and here it contained the whole module under another name.
