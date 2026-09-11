# Next steps — MGS Integral English text port

Written 2026-09-04 (evening), updated the same night after the
reproducible-build pass (§9), through 2026-09-05 as the MISSION LOG port,
the item-text fixes and their on-screen checks landed (§10), on 2026-09-06
when the **VR disc** was ported (§11), and through 2026-09-07, the day the VR
disc was tested on screen and the three items that were still open all closed:
the MOVIE captions, `en_menu3` and the VR KEY CONFIG (§12), and through
2026-09-09, when the untranslated Japanese was dumped and the glyph
identification was set up as the one open task (§17), and on 2026-09-10,
when the raw disc booted for the first time and the briefing turned out to
be broken on it (§24 - `ROW_H`; **fixed late the same day**: an R3000
load-delay hazard, one `nop`, and a scanner so it cannot recur), and when that task was
finished - all 1,200 bank-1 glyphs named, 100% of the
Japanese readable as text, and the fragment map §17 rested on found to be
wrong for 93% of strings and rebuilt (§18), and then the export itself
finished: the byte scanner retired for a walk of the game's own records, a
bank-1 index bug found that had been naming every `0x97xx` glyph one position
too far along, and 25 more characters identified - the last of them, 蒼, named
from outside the disc because it occurs exactly once on it - leaving the export
complete with **zero** unresolved glyph codes (§19), and finally the VR disc
added - it had been dropped by a loop over two disc indices, so 97% of the
export looked like all of it - and the last game data taken back out of the
repository, the glyph table now shipping digests of the font bitmaps rather
than the bitmaps (§20), and a regression guard put on the fragment map after two
plausible-looking metrics were measured and thrown away (§21) - and on
2026-09-08, when the housekeeping was cleared, the sweep's one uncovered
finding became the `en_pad2` family, the three sweeps §5 had filed under "to
investigate" were all run, and the four `abst` location names were decided
(§5.11, §5.9, §5.14, §15), and finally later on 2026-09-10, when the Redump
dumps of all three discs were measured against the collection's embedded
copies - identical outside the hollowed-out executables, which those dumps also
supply at the exact hash the builder demands - and `mkimage.py` closed the gap
between a raw build and an actual patched disc image, from either source
(§22) - and late that night and into 2026-09-11, when the briefing's
connector left ends were found to have been Integral's under USA's boxes and
were moved (§26), and the collection's faint connector lines were traced to
M2's renderer sampling the wrong texel of a one-pixel quad and fixed at the
source in MGSM2Fix as `[Patches] ThinTexturedQuads`, then confirmed with every
briefing unlocked, twenty pairs at 0.00% against USA (§26). Written for whoever
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
| working data | `D:\mgsbuild\integral-english-work\` — `work\` (extracted STAGE.DIRs, the four retail executables, built binaries, baselines), `unlocks_parked\` (the four unlock PPFs, not deployed), `keyconfig_test\`, `map_pristine.map` (the pristine exe's symbol map), ini/log/`opt.c` snapshots | every tool imports `WORK` from `workdir.py`: `INTEGRAL_ENGLISH_WORK` env var → `D:\mgsbuild\integral-english-work` → cwd. `workdir.py` also exports `GAME` (`INTEGRAL_ENGLISH_GAME`, default the Steam folder) and `DECOMP` (`INTEGRAL_ENGLISH_DECOMP`, default `D:\mgsbuild\d`); the builders and `rebuild.py` take every path from it; a few standalone helpers still carry their own — `ppfcheck.py`'s `MODS`, `audit_text.py`'s argparse defaults, and the repo path that `jpsweep.py`, `kcplace.py`, `kcquads.py` and `kcrects.py` insert into `sys.path`. `py workdir.py` prints what it resolved |
| VR working data | `work\vrint_stage.dir`, `work\vrus_stage.dir` (the two VR STAGE.DIRs), `work\vrint.exe` (rebuilt from the decomp, `build.py --variant vr_exe`, SHA-256 `c370f8e4…`), `work\vrus.exe` (real `SLUS-00957`), `work\INTEGRAL_vr_*.ppf` | `vrlib.py` finds the two VR ISOs inside the containers itself (`0x57592000` and `0xD39B7000`) and computes stage LBAs from STAGE.DIR |
| retail executables | `work\int1.exe`, `int2.exe` (641,024 bytes each), `us1.exe`, `us2.exe` (651,264) — hashes in `BUILDING.md`; `rebuild.py` rejects any other | **the collection's ISO executable extents are zero-filled**, so extracting an exe from `alldata.bin`/`dlc_japan.bin` yields no code — the first clean-build attempt failed on exactly that. These four files are the only source of executable bytes |
| reproducible build | `py rebuild.py --output <fresh dir> [--variant raw] [--compare-deployed]` (see `BUILDING.md`) | never installs anything. Builds **everything**: ten families × two main discs plus the VR disc's seven. Last artefact `D:/mgsbuild/repro20/Integral-English-collection.zip`, SHA-256 `9dff4849…bce3` (2026-09-08), **all 27 PPFs equal to the deployed set's effective bytes**. `--variant raw` builds the raw-disc variant instead (§5.4) |
| game | `D:\Steam\SteamApps\common\MGS1` (Master Collection Vol. 1, Steam app **2131630**) | launch: `Start-Process steam://rungameid/2131630`; process name `METAL GEAR SOLID`; **kill by PID only, never `taskkill /IM`** |
| Ketchup mods | `D:\Steam\SteamApps\common\MGS1\mods\INTEGRAL\INTEGRAL\0` (disc 1) and `\1` (disc 2); the VR disc is `mods\INTEGRAL\VR-DISK\` and the USA VR disc `mods\VR-DISK_US\` | Ketchup loads every PPF in the folder, so each patch is its own file and can be removed individually. Its `RootPath` adds a version folder only when a title has more than one version and a disk folder only when a version has more than one disk, which is why the two VR folders have no numbered subdirectory |
| deployed ini | `D:\Steam\SteamApps\common\MGS1\MGSM2Fix.ini` is a **Vortex symlink**; edit the target: `%APPDATA%\Vortex\metalgearsolidmc\mods\MGSM2Fix-5-3-6-0-1774482213\MGSM2Fix.ini` | edit with Python or via `realpath`; `sed -i` on the link would replace the link with a file. The repo's `MGSM2Fix.ini` is the committed default, not what the game reads |
| deployed ASI | same Vortex folder, `MGSM2Fix64.asi` | |
| build | `"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\MSBuild\Current\Bin\MSBuild.exe" MGSM2Fix.sln /p:Configuration=Release /p:Platform=x64` → `x64\Release\MGSM2Fix.asi` → copy to the Vortex folder as `MGSM2Fix64.asi`; compare hashes | **Run it from PowerShell**: Git Bash rewrites `/p:` into paths (MSB1008). Since the 2026-09-10 rebase the Zydis prebuild needs the toolset passed through (`build_zydis.cmd` second argument, done 2026-09-11). The post-build step calls `python M2Install.py`, which is not on this PATH (`py` is), so MSBuild reports exit 1 with error 9009 **after** the ASI is linked - the `.asi` is good; deploy by hand. If MSBuild times out it can leave `cl.exe` processes behind — stop them by PID |
| log | `D:\Steam\SteamApps\common\MGS1\MGSM2Fix.log` (rotates to `.prev`) | **Corrected 2026-09-07.** The boot-time `Error parsing ini file ... at these lines: 12` was recorded here as a harmless inipp quirk on the `[Internal Resolution]` header at line 12. It was neither. inipp prints the offending line's **content**, not its number, and the content really was a bare `12` — the deployed ini's `[Update Notifications]` section header had been overwritten by it at some point. It was not harmless: with the header gone, `CheckForUpdates = true` fell into `[Game]` and the fix read `bShouldCheckForUpdates: false`. Header restored; the file now has all ten sections and no unparseable line. **If that message comes back, read the line it quotes as text and go find it.** |
| screenshots | `C:\Program Files (x86)\Steam\userdata\7924217\760\remote\2131630\screenshots` | 3840×2160; 9 display px per game px, x offset 480 |
| USA source data | `work\usa1_stage.dir` / `usa2_stage.dir` (real USA discs, extracted from `windata\alldata.bin`); `work\us1_stage.dir` is **European** despite its name — do not source text from it | README "Toolchain and environment" and the source-discs note |
| credit and provenance | [`CREDITS.md`](CREDITS.md) | whose work this is built on, what of it is in this repository, and the one thing that is **not settled**: the decomp states no licence |
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
4b. **Amendment (2026-09-07): Integral's own ENGLISH may be replaced by USA's,
   when asked.** The no-translation rule and the scope rule were both written
   for Japanese text: port English where English exists, keep what Integral did
   differently. Neither says what to do when **Integral already has English and
   it differs from USA's**. The first case forced the question and the user
   settled it, of the item side-column abbreviation: *"this is a case where we
   are replacing existing english in integral instead of japanese, so it's an
   exception to our rule."*

   **Applied twice so far, and each time it was asked first.** `SCARF` ->
   `HANDKER` (2026-09-07, §5.9) and the four `abst` location names (2026-09-08,
   §5.9). The amendment is a licence to ask, not a default: where Integral's own
   English merely reads differently and nobody has asked, it stays.

   So it is an exception, not a new default: an Integral string that is already
   English is left alone unless it is asked for, case by case, exactly like the
   art amendment above. Done so far: **one**, `SCARF` -> `HANDKER` (§5.9).
   Still outstanding under the same heading and NOT done: the `abst` location
   spellings (four of them — §5.9).

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
| `en_items` | item and weapon descriptions, the frozen Ration/Ketchup pair, the HARD/EXTREME Mine Detector message (executable) | **Fully verified against USA on screen 2026-09-07**: all 24 items and all 10 weapons photographed in both games and compared side by side, text, line breaks and glyphs - `<<`/`>>`, the O/X/[] button glyphs, apostrophes, the `<Limitless>` single angle quotes. **34 of 34 identical.** The only difference anywhere in those shots was the side column's short name for item 22, `SCARF` against `HANDKER` - a different table the port did not touch. **Asked and changed the same evening** (§5.9, and §2 amendment 4b: the port's first replacement of Integral's own English); redeployed 22:56 and **seen on screen at 23:03**. The two conditional descriptions were photographed the same evening too (§5.1a), so every form of every item and weapon description in this family has now been read on screen. Earlier: in game. Three faults found from the user's shots and fixed 2026-09-05 (card level digit offset, SOCOM suppressor rewrite, a retail-equal byte the collection's RAM patch owned — README "Three item-text faults"); **the fixes were seen on screen at 12:55** (SOCOM, ID Card `level 7 security`, Mine Detector) and the audit is silent. The PPF owns every byte of both arenas |
| `en_menu`, `en_menu2` | menu strings; `en_menu2` includes the `demosel` and `change` disc-swap copies | in game (menus); the disc-swap copies **never seen** (see §5.1) |
| `en_option` | option-screen strings; KEY CONFIG labels (8 textures); brightness paragraph as USA's `sc_text` texture, four lines in the collection build | in game, pixel-measured; SCREEN / KEY CONFIG (collection panel via the doorbell) / EXIT all confirmed 2026-09-04 |
| `en_preope` | Previous Operations, USA's exact pagination (MG1 13 pages, MG2 19) | in game, 29 lines pixel-exact |
| `en_brf` | briefing labels, quads, row arithmetic | in game, 26 shot pairs, 0.00% right-column diff |
| `en_savemsg` | memory-card captions in the executable | in game 2026-09-04: save + load; kept slots idx 1/9 Japanese by rule. Since 2026-09-05 the PPF owns every byte of the pool and tables, so the collection's six writes cannot survive at retail-equal bytes (the mechanism that broke the SOCOM line) |
| `en_camsave` | the PHOTO ALBUM's own captions (`camera` overlay) | **fully verified 2026-09-04**: all 23 English on screen / by slot comparison; the six USA-blank slots stay Japanese (`ロード中です`, `ロードが完了しました`, `変更内容を上書き保存しますか？` are those) |
| `en_abst` | the MISSION LOG: all 122 pages in USA's two-screen model (7 lines a screen, page counter, ◄ ► EXIT, USA's input and slide), plus the disc-change abstract's eight strings — the fourth disc-swap copy | **built 2026-09-05 and seen on screen the same day**: both pages of the Heliport and Comm Tower A logs, the controls and the slide (the one fault, stale-VRAM fragments during the slide, fixed at 13:05 and confirmed clean at 13:50). Statically, pages re-parse and equal USA's byte for byte and the PPF records rebuild the relocated 88-sector stage exactly on both discs. Stage in DUMMY3M slots 462..549. **Since 2026-09-08 it also carries USA's four location-name spellings** (`USA_LOCATION_NAMES`, §5.9): +12 bytes, still 88 sectors, and the verifier re-parses the 31-record list and asserts it equals USA's record for record. Not yet seen: a demo.gcx page (disc-2 saves), a count-7 page, and the four location names |
| `en_menu3` | the `title` disc-swap copy — the fourth and last | **built and verified 2026-09-07, RAW DISC ONLY, not deployed.** The collection patches the same block (`disc1_1822B55D_patch`, at the address of our record 0), and the two layouts do not mix: the title stage dies with a `GCL:WRONG CODE` run. Staged as `INTEGRAL_disc{1,2}_en_menu3_raw.ppf` for the raw variant; `menu3.py --deploy` refuses. §5.3 |
| `en_pad2` | the controller-port subtitle `second.c` draws in the Psycho Mantis room, at all three of its call sites per disc | **built and deployed 2026-09-08**, 159 bytes a disc. Statically verified by effect: the archive keeps its length, both stages re-walk to the same command structure, every changed byte is inside the three slots, and each slot re-parses at length 55 with USA's English at the front. Disjoint from all nine other PPFs on each disc. **Never seen on screen** — it needs the Mantis room *and* a controller in port 2. §5.11 |
| unlock PPFs | title-screen extras | **parked**, `unlocks_parked\`, not deployed |

### VR-DISC patches (deployed 2026-09-06 in `mods\INTEGRAL\VR-DISK\`)

Ported from USA's VR Missions (`SLUS-00957`). README "The VR disc (SLPM-86249)"
is the technical record; `vrlib.py` is the shared library. **Seen on screen by
the end of 2026-09-07:** the option screen, KEY CONFIG (with the two flags on),
the mission menu with every mission unlocked, all three MOVIE captions, the
EXTRA menu with every item, mission title and briefing windows, and an item and
a weapon description. **Still unseen:** a mission RESULT window, three of the
EXTRA help lines, a save and a load message, the PHOTOGRAPHING card messages,
and the EXIT box after its move — §5.5's list 1 and §5.4a.

| patch | what | verified |
|---|---|---|
| `vr_en_missions` | 1808 of 1813 in-mission windows across 92 stages: titles, briefings, results, hints | statically: every stage re-parses, no stage grew (ten padded back to their sector count), 15 031 records / 3 370 955 bytes, fonts merged and every remaining glyph code proved to exist in the new font |
| `vr_en_items` | the VR executable's item, weapon and capture-mode pools | statically; the PPF owns every byte of all three arenas, as the main game's does since the SOCOM fault |
| `vr_en_savemsg` | the VR executable's 12 save and 12 load messages | statically; indices 1 and 9 stay Japanese (USA draws nothing) |
| `vr_en_option` | the option screen's 7 help lines and the whole KEY CONFIG screen | **the option screen is verified on screen 2026-09-06** after three faults, all found by bisecting the PPF: the DAR's entry sizes were not 4-aligned and crashed the stage at `load option`; record 3 doubled the vibration-test sentence; and Integral's colon/values were lit beside the English while the lines sat off-centre. Fixed by padding every DAR payload to 4 (paid for with `pcx4`'s real 63-byte run cap), blanking record 3 as the main game does, unlighting the colon/values via the state switch, and giving each ported entry USA's `{num 1, x 160, y 196}`. All five rows now read as one centred English line, measured within 0.3 game px of centre. **KEY CONFIG verified on screen 2026-09-07** with `DisableRAM`/`DisableCDROM` on: Integral's own screen draws, all eight labels English through all three button types, and `key_syukan`'s +11 clears the curve. One fault found and fixed the same day — the selection highlight on the `first person view` row was 24 px short (88 against USA's 112) because it is drawn by hardcoded `glow(work, x, y, w, h, ...)` calls rather than an `Init_Res` quad, so the transplant never touched it; measured 113 px against USA's 114 after the fix |
| `vr_en_title` | the EXTRA menu's four help lines | statically; record 6 (PocketStation) deliberately kept — USA's `See the staff credits.` is a different feature |
| `vr_en_memcard` | the memory-card captions of the `vrsave` and `selectvr` overlays (SAVE / LOAD / REPLAY DATA screens): 12 save + 12 load each, USA's English index for index, 1/9 and the prompts kept | **built and deployed 2026-09-11 11:29**, 7 records, both pools 390/492 bytes; verified by reading every slot back. Found from the CLEAR DATA screen - whose own copy, in `vrtitle`, is Japanese in USA too and stays. Not yet seen on screen: its captions are the error and edge states (Save failed, No save file, No empty block...), which the 22 shots of 11:11 did not reach |
| `vr_en_camsave` | the PHOTOGRAPHING mode's memory-card messages | statically; 429 of the pool's 492 bytes used. Never seen on screen |
| `vr_en_movie` | the MOVIE selection captions | **all three ported 2026-09-07**, the two TGS ones as USA's two lines. The line count was never data: USA calls the actor's own `highlight(work, i)` twice — for `clip*2` and `clip*2+1` — where Integral calls it once, so the port retargets that one `jal` at a 16-word stub in the overlay's own sector padding. **Verified on screen 2026-09-07**, all three clips: both TGS captions on two rows with correct attribution and real typographic quotes, E3 on one. Line 1's ink then overlapped the EXIT box by 2 rows, because Integral's caption face is taller than USA's; the box moved up 4 px to USA's own y with the user's approval (§5.4a, §6), and **that part is not yet seen on screen** |
| `vr_unlock_movies` | the EXTRA movies unlocked (test aid) | **verified in game 2026-09-06: all three thumbnails appear.** One instruction in the `movie` overlay: its own `count / 3` score gate, separate from the mission one. Writes no progress; delete the PPF to relock |
| `vr_unlock` | the **mission menu** unlocked (test aid) | **verified in game 2026-09-06: every mission unlocked.** Emulation predicted 46 → 361 of 373 items on Integral (45 → 357 on USA) and its three words were verified in place against the deployed PPF. It does **not** open the EXTRA movies — that is a separate retail gate, `???` in USA's VR disc too. Saving with it in place is safe (it writes no progress) and deleting the PPF relocks; the standing rule still holds — achievements off (`DisableRAM`/`DisableCDROM` true) while any unlock aid is deployed |

`ppfcheck.py --deployed` is clean over all **27** deployed files (20 main, the
ten families × two discs, and the VR disc's seven), and **every one of them is
disjoint from every other** as of 2026-09-08.

That last part is new, and it is what §5.10 item 1 bought. Until then
`vr_en_movie` shared 686 of its 753 bytes with `vr_en_missions` and worked only
because Ketchup applies a folder in name order and `...missions` sorts before
`...movie` — a dependency nothing enforced and nothing would have reported. The
two now own one stage each and share **0 bytes**; the split was proved equal in
effect before it was kept, and `rebuild.py` refuses *any* VR overlap. The
deployed pair was still the old one until 2026-09-08, when the VR seven were
redeployed from `repro17` together. The superseded `vr_en_movie_e3` still must
**not** sit in the folder — it writes the same stage — and `vr_movie.py
--deploy` moves it to `work/` with a `.was-deployed` suffix. `vr_sweep.py` rebuilds every stage as the
game will see it and finds **222 game-encoded records against 10 809 English**
(USA's own disc: 940 against 10 344); 181 of the 222 are English with
local-font glyphs, and the rest are exactly the list the README calls
"Deferred, with reasons". Nothing with a USA English counterpart is still
Japanese.

**Reproducibility:** every one of the ten shipping families is rebuilt from
retail inputs in an isolated directory by `rebuild.py` — stage files extracted
from the collection, the four retail executables as hashed inputs, the decomp
exported at `7964de7` plus `decomp-overlay-changes.patch`, three overlays
recompiled (byte-identical to the shipped ones) — and all 20 PPFs match the
deployed set's effective changed bytes. **Since 2026-09-07 the VR disc's seven
are in the same run** (its executable built from the decomp, not copied), so the
last clean run, `repro20` (2026-09-08), reproduces **27 of 27** against what is deployed. So the deployed patches are
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
| `[Patches] ThinTexturedQuads` (2026-09-11) | `= true` | a mid-hook on M2's GP0 polygon dispatch: a textured polygon one pixel tall (or wide) takes the texel of its leading edge, which is what the PlayStation GPU draws; the collection sampled another and drew MGS1's briefing connector lines faint. All PSX titles; seen on screen 00:07 and in twenty unlocked-briefing pairs 00:13-00:17 (§26). Deployed as `MGSM2Fix64.asi` SHA-256 `9ea87429…` |
| Ketchup built-in disc patches + `SetPatchRangeBlacklist` | — | shipping (the USA four-line brightness fix) |
| `SQHook::SetPatchWatch` (logs collection patches landing in a region) | — | in use; watches on `option`, `abst`, `change`, `demosel`, `title` and `camera` spans on both main discs, and since 2026-09-06 on the VR disc's `option`, `camera`, `vrtitle`, `movie` and `vrsave` spans (ASI rebuilt and deployed 2026-09-06 00:25) |
| `Ketchup::Audit` (every byte of every RAM run, read-only, every ~5 s) | — | in use; it caught two of the three item faults on 2026-09-05. Since both exe PPFs own whole regions it now sees every byte of both pools |
| `[Game] GiveItems` (test aid) | `GiveItems =` (empty) | built; **never exercised** — the developer menu grants everything anyway |
| `[Game] StageSelect` = `true` / menu name / stage name | `StageSelect = false` | works; see README "The disc-swap text" for what it can and cannot reach |

### Deployed ini right now, and the play defaults

**Live at 2026-09-11 00:11 — a TEST SESSION is open**: `UnlockBriefing = true`, `DisableRAM = true`, `DisableCDROM = true` (achievements off), to look at the six flag-gated briefing items and their L-connector bars on the collection with `ThinTexturedQuads`. **11:09: the three VR unlock aids** (`INTEGRAL_vr_unlock_{missions,movies,extras}.ppf`) **are deployed to `mods\INTEGRAL\VR-DISK\`** for §5.5's remaining VR checks; delete them when the session ends, before achievements go back on. `[Patches] ThinTexturedQuads = true` is also in the live ini now. Put the three back to the play defaults below when the session is over. Note `DisableCDROM` also drops the collection's KEY CONFIG interception, so Integral's own KEY CONFIG shows meanwhile - expected.

**Before that, live at 2026-09-08 22:20 — back at the play defaults, and the test session was over.** `DisableRAM = false`, `DisableCDROM = false` (achievements live), `GiveItems` and `GiveWeapons` both empty, and **no `_unlock_` PPF anywhere under `mods\`** — all four aids (`INTEGRAL_vr_unlock_{missions,movies,extras}.ppf` and `VRUS_unlock_missions.ppf`) were deleted. Remember the ini the game reads is the **Vortex symlink target**, `%APPDATA%\Vortex\...\MGSM2Fix.ini`; write that, not the link. **27 PPFs are deployed and `ppfcheck.py --deployed` is clean over all of them**: 20 main (the ten families × two discs) and the VR disc's seven. The VR seven were redeployed from `repro17` the same evening, which is what finally put the **disjoint** `vr_en_missions` / `vr_en_movie` pair on disk — the deployed pair had still been the old overlapping build, 686 bytes shared and every one of them conflicting, working only because Ketchup applies a folder in name order. They now share **0 bytes**, and the whole VR set was proved equal in effect to what it replaced before it went on (`vr_set_effect_equal`, no differences).

**Play defaults:** `DisableRAM = false`, `DisableCDROM = false` (achievements live), `StageSelect = false`, `GiveItems =`, `EnglishText = true`, `BrightnessText = fixed`, `PreserveConfiguration = true`, `UnlockBriefing = false`, and no `_unlock_` PPF anywhere under `mods\`. The user has real saves: **Heliport** and **Comm Twr A** (both disc 1, the latter made with a full developer-menu inventory and a photo).

---

## 5. What remains — in the order I would do it

**Correction, 2026-09-07 evening.** This section used to say that nothing with
a USA counterpart was still Japanese on any disc. That was believed on the
strength of `vr_sweep.py` for the VR disc and a candidate inventory for the main
discs — and a candidate inventory cannot establish it. `mainsweep.py`, written
this evening to do for discs 1 and 2 what `vr_sweep` does for the VR disc, found
**one**: §5.11, **built and deployed 2026-09-08**. Everything else it flags is
inside a stage a patch family already owns, or is Japanese on the USA disc
too. Its own universe turned out to have a hole as well — it compares only
the 82 stage names both discs share, so the same string in the
Integral-only `s07br` was invisible to it. That is recorded in
`COVERAGE.md` now.

**State of play, end of 2026-09-08.** Most of this section is now DONE and kept
only for its reasoning: 5.1a (the six conditional descriptions, all seen), 5.3
(`en_menu3`, raw-disc only), 5.4 (the raw-disc build switch), 5.4a (the MOVIE
captions), 5.5's items 2 and 6, 5.10 (the whole patch-side review), and — all on
2026-09-08 — 5.8 (the census closed, 0 unaccounted), 5.11 (`en_pad2`), 5.14
(swept; a fourth `abst` spelling found), and both of 5.9's decided cases,
`SCARF` -> `HANDKER` and the four `abst` location names.

**Nothing with a USA counterpart is known to be Japanese any more, on any of the
three discs**, and every Japanese GCL string on the main discs is accounted for
by name (5.8). What is left is of five kinds — and none of it is text to port:

| kind | items |
|---|---|
| ~~**housekeeping**~~ | **DONE 2026-09-08 22:20.** The four `_unlock_` PPFs deleted, `GiveItems`/`GiveWeapons` emptied, `DisableRAM`/`DisableCDROM` back to `false`, the disjoint VR pair finally deployed, and the branch committed. §4's "Live at" paragraph is the current state |
| **needs you at the controller**, nothing to build | 5.1, 5.2, 5.5's list 1, the moved EXIT box of 5.4a, the `en_pad2` subtitle (5.11, needs a pad in port 2) and the four `abst` location names (5.9, free with the 5.2 run) |
| ~~**real engineering**~~ | **The briefing: FIXED 2026-09-10 late** - `ROW_H` was an R3000 **load-delay hazard**, `subu` reading `a1` in the slot right after `lbu a1`; one `nop` in place, no stub, and `hazards.py` now scans every rewritten block on every build (§24, top). Build `repro32raw`, images in `D:\mgsbuild\patched`. **Seen on screen 22:38, matching the MC set** for every reachable state; the six flag-gated items and their connectors still want a save with them earned on the raw disc. Still real work: **submit the pull request** (5.6), and look at the other two raw-only screens |
| **needs a fresh pair of eyes** | the briefing's six flag-gated indented items and their L-connectors on the **raw disc** (a save with them earned, or a raw-disc unlock aid that does not exist yet). On the collection they were seen 2026-09-11 00:13-00:17 with `ThinTexturedQuads`, twenty pairs, 0.00% against USA (§26) |
| ~~**the one open task**~~ | **DONE 2026-09-10.** The count was never 1,813 - that figure came from a broken fragment map. 1,214 bank-1 shapes are named, the byte scanner is retired for a walk of the game's own records, and the export is complete, on all three discs: 68,242 lines, 3,923,944 kana/kanji, zero unresolved codes. §18 and §19 |
| **to investigate** | ~~5.14~~ swept and ~~5.8~~ closed on 2026-09-08 — but see §16: on 2026-09-09 both turned out to have been sweeping **one file**. `RADIO.DAT` holds 6.5 MB of Integral-exclusive Japanese developer commentary no tool here could see. That is translation, not porting, so the port's scope is unchanged; what needs redoing is any claim of completeness. Also left: what the 13 Integral-only `*r` stages **are**; and per-family verifiers where they are missing (5.14 step 3) |
| **held open on purpose** | §6's **three** remaining **[open 2026-09-07]** items: the READ MISSION LOG? caption and USA's `1/2` counter, the VR number substitutions, and VR EXTRA record 6. The fourth, the `abst` location names, was decided on 2026-09-08 (use USA's). Raised, considered beside the `SCARF` case, and held on purpose — see the note at the head of §6 |
| **loose ends** | 5.7's remaining untested runtime features, 5.5's items 4 and 5, and the `us1.exe` parity mismatch in 5.13 |

### 5.1 Still to be seen (needs the user; nothing to build)
Everything built so far has been seen on screen except: a mission-log page from
demo.gcx (a disc-2 save) and a count-7 page (USA's `1/2` with an empty second
screen — reproduced on purpose, §5.9); the other weapon descriptions besides the
SOCOM; the disc-swap screens, which only 5.2 can reach; the controller-port
subtitle of §5.11, which needs the Mantis room and a pad in port 2; and the four
`abst` location names now reading USA's (§5.9), which show in the MISSION LOG's
own location column and so come free with the 5.2 run. If anything looks
wrong, bisect first: move the family's two PPFs out of the mods folders and
confirm the retail text comes back. No debug shortcut exists for any of it —
the collection's launcher waits for a game to be chosen before anything loads
(a `StageSelect = abst` smoke test idled there on 2026-09-05 00:39).

### 5.1a The six conditional descriptions — ALL SEEN ON SCREEN 2026-09-07
Found 2026-09-07 by reading the two functions that decide which description is
printed (README, "Descriptions that change with the game state"). An item's text
is not always the string its table points at, and six slots change with the game
state. Four were already covered by the 34-pair comparison against USA; the two
conditional ones had never been drawn, and `GiveItems` made both reachable
whatever the difficulty. **Both were photographed the same evening and both are
right:**

- **The Mine Detector on HARD** (seen 23:08) draws USA's three lines,
  `《Mine Detector》` / `Cannot be used in` / `HARD or EXTREME mode.` That is also
  the first on-screen proof that this string's **relocation** works - it is 59
  bytes against Integral's 53, so `items.py` moves it and repoints the
  `lui`/`addiu` pair that reaches it.
- **The MP5 SD on VERY EASY** (seen 23:07, 999/999 rounds). On that difficulty
  Integral **replaces the FA-MAS with the MP5 SD** - it is a different weapon,
  not a relabelled one, and it reuses `WP_Famas` as its id, which is why the
  code reads as if it were about the FA-MAS. Three places do it: `check_type`
  (`game/item.c`) returns 0 for that id so the **FA-MAS pickup never spawns**;
  `menu/weapon.c` names the slot from an inline `"MP 5 SD"` literal; and the
  description pointer becomes the MP5's. **Its text is Japanese and correct, not
  a fault** - Integral-only, and USA has neither the weapon nor the difficulty:
  `《MP 5 SD》 サブマシンガン。□ボタンを押すと発砲。押しつづけると、フルオート連射。サプレッサー装備。`

### 5.2 The disc-2 run (needs the user at the controller; nothing to build)
Play through the actual story disc break from a late disc-1 save (no debug).
Where exactly the break falls in the story has not been checked here; do not
take a route from this file. Watch whether the game's own swap flow draws (`Now Checking...` /
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

**BOOTED 2026-09-10.** The user ran the patched disc 1 and it worked. That is
the first time anything in this project has been proved to run outside the
Master Collection, and it closes the item this paragraph carried from
2026-09-07. What it establishes is that the image is *valid* - it loads, the
executable runs, the game plays - not that every ported screen is right on it;
the raw-only three (`en_menu3`, the six-line brightness paragraph, Integral's
own KEY CONFIG) still want eyes on them, and they are now reachable for the
first time.

The image tested was built before the language default existed, so it started
in Japanese - correct behaviour for a retail disc, and the reason §23 was
written. Rebuilt with `--english-default yes` the same day.

**Three things used to stand in front of that boot, and all three are now
closed** (§22). Two were closed in code by §5.10 the same evening this
paragraph was written, and the text above them went stale: `rebuild.py
--variant raw` gives every PPF a **block check** (`place()`, from
`blockcheck_of`) and emits a per-disc **`zz_ecc` PPF** carrying the recomputed
EDC/ECC of every touched sector (`raw_tails()`, `rawdisc.py`). The third — show
the collection's embedded images equal a retail dump — was measured on
2026-09-10 against the Redump set and holds byte for byte outside the
executables. **Do not re-plan work that the code already does; read
`rebuild.py` before believing a paragraph in this file.**

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
ones on two rows (§5.4a; the overlap those shots showed between line 1 and the
EXIT box was fixed the same day by moving the box to USA's y, deployed and not
yet seen). What is left, in rough order:

1. **On screen 2026-09-07: mission windows.** Two shots, both correct English -
   `ADVANCED MODE / SOCOM LEVEL 01`, "Eliminate all enemy soldiers and head for
   the goal! / Enemies 2", and `1 MIN. BATTLE VS. TARGET / SOCOM`, "Use Socom to
   destroy targets! / Conditions to clear: 15 targets". That is the title and
   the briefing of the `vr_en_missions` family, the largest one, read in play.

   **Also on screen 2026-09-07**: an item description (`《Diazepam》 Anti-anxiety
   drug. Temporarily stops involuntary trembling.`) and a weapon description
   (`《PSG1》 Sniper rifle. Aim with directional buttons, press □ to fire.`, the
   button glyph rendering correctly) - and the same PSG1 window shot on USA's
   own disc reads **identically**, which is the port matching its donor word for
   word rather than merely looking plausible.

   **Still unseen**: a mission RESULT window, three of the EXTRA menu's four
   help lines (EXIT's was seen; see the aid below), a save and a load message,
   and the PHOTOGRAPHING mode's card messages (the ALBUM path). If something is
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
3. **Four unlock aids may stay for testing and must come out after.**
   `vr_unlock.py` (Integral's missions), `vr_unlock_movies.py` (the EXTRA
   clips), `vr_unlock_extras.py` (the EXTRA MENU's items) and - for the donor
   disc - `VRUS_unlock_missions.ppf`, which `vr_unlock.py` also builds.

   **There are three separate gates on this disc and each needed its own aid**,
   which is the lesson: the mission menu is gated in `selectvr`, the clips in
   `movie`, and the menu items in `vrtitle`. The last was found 2026-09-07 when
   the user reported only MOVIE, ALBUM and EXIT on the menu, leaving three of
   `vr_en_title`'s four ported help lines unreachable. The EXTRA menu builds a
   visibility bitmask at `work+0x1e` from progress flags at `+0x1a1c`, one item
   per test, each test also bumping the item count - so the aid forces the three
   **tests** (`andi v0, v0, 3` / `0x10` / `0x40` -> `addiu v0, zero, 1`) rather
   than the mask, because a mask forced from outside would leave the count and
   the layout disagreeing. With it, PocketStation appears too, and its help line
   is Japanese **on purpose** (Integral's fifth item is PocketStation where USA's
   is STAFF CREDIT, §6). None writes progress, so saving with them in place is safe; the
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
**REBASED 2026-09-10: the branch now sits on `upstream/master` (`97172f5`).**
The rest of this section is the 2026-09-07 estimate, kept because most of it
still describes the pull request, and because **its cost estimate was wrong in
a way worth recording** - see "What it actually cost" at the end. A
fast-forward was never possible: that needs a branch with no commits of its
own, and this one had 133 then and 161 now.

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

**What it actually cost, measured 2026-09-10.** The estimate above said a
merge would cost "a conflict resolution in our most-changed file". It did not.
Following this section's own advice - try it on a throwaway branch first -
both routes were run, and both produced **one** conflict, in
`build_zydis.cmd`, where upstream moved the submodule to `src/extern/zydis`
and our commit had quoted the old path. Everything else applied by itself:

| | |
|---|---|
| upstream commits taken | 11, through `97172f5` |
| our commits replayed | 161 |
| conflicts | **1**, at commit 1 of 161 |
| `src/mgs1.cpp`, the feared file | auto-merged |

Git's rename detection carried all nine files into upstream's new layout
(`src/games/`, `src/m2fix/`, `src/modules/`) unaided. The rebased tree and the
merged tree came out with **the same tree hash**, `356d3798` - that is the
check worth copying: if a rebase and a merge of the same work disagree, one of
them lost something.

Verified after: all fourteen feature markers appear the same number of times
as before (`bGameEnglishText`, `SetPatchWatch`, `Ketchup_DiskPatch`,
`BrightnessText`, ...), and `selftest.py` still passes 35/35.
`backup-before-rebase` points at the pre-rebase tip, `b6513f8`.

**One piece of fallout, and it is not git's fault.** Upstream moved six
*submodules* into `src/extern/`, and a submodule's working tree does not move
with a checkout. `git submodule sync --recursive && git submodule update
--init --recursive` populates the new paths; the old
`src/{imgui,inipp,json,safetyhook,spdlog,zydis}` checkouts are left behind as
untracked duplicates - 53 MB, including a built `Zydis.lib` that
`build_zydis.cmd` regenerates at the new path on the next build. **Deleted
2026-09-11 00:25** after they surfaced as six "new" items in GitHub Desktop;
the live submodules under `src/extern/` were verified present first.

**The lesson for the estimate.** Nothing about the 2026-09-07 reasoning was
careless: it read the rename percentages and the line counts and concluded the
work was concentrated in `mgs1.cpp`. What it never did was spend two minutes
running the merge on a throwaway branch - which this very section recommended.
A deferral justified by an unmeasured cost is a guess, and this one was wrong
by about a day of imagined work.

### 5.7 Still untested, low effort when the moment comes
- **The patch watch is blind while `DisableCDROM = true`**: the early return
  in `sqhook.cpp` precedes the watch loop. Answered 2026-09-05 12:57 with the
  flags live: the `_PS5`-suffixed `abst` patch does register on Windows (and is
  orphaned by the `en_abst` relocation); named-file patches carry no inline
  data, so their content stays unknown to the watch.
- `PreserveConfiguration` catching a real stale write (intermittent race).
- ~~`GiveItems` in a stage where the inventory is actually empty~~ **Exercised
  for the first time 2026-09-07, and it did not work. Fixed the same evening.**

  Run on MGS1 **USA** (title 981, disc 1, stage `s01a`) with all 24 ids, it
  logged twenty-four lines and granted nothing: `count 65535 -> 65535`, over and
  over, while the inventory stayed empty. **An item Snake does not have is
  stored as -1, not 0.** `game/g_define.h` says so in one line - `IT_None = -1`
  - and `game/item.c` tests `GM_Items[IT_Ketchup] == -1`. The feature looked for
  a count of zero, which is a state an absent item is never in, so the guard
  that was meant to protect a real inventory silently protected everything.

  Two things it got wrong beyond the sentinel, both now corrected in
  `src/mgs1.cpp`. It also wrote `GM_ItemsMax[id]` wherever that read 0, which
  helps nothing: for the three consumables the max the game actually consults is
  `GM_Items[id + 11]` (`item.c` `add_item`), and for everything else `add_item`
  simply assigns. That write is gone. And an owned-but-**disabled** item is a
  third state - `disable_equipment()` ORs `IT_TYPE_DISABLED` (0x8000) into the
  entry - so `0x8001` is now deliberately left alone rather than being read as
  "absent" and quietly re-enabled.

  The log line says which happened: `granted (65535 -> 1)` or `already held,
  left alone`. **Confirmed working on screen 2026-09-07**: all 24 items in the
  inventory on MGS1 USA disc 1.

- **`[Game] GiveWeapons`, added 2026-09-07** once the items worked and the
  weapons visibly had not. Weapons are a different shape: two arrays, ammo in
  `GM_Weapons` (`linkvarbuf[17..26]`) and capacity in `GM_WeaponsMax`
  (`[27..36]`), ten of each, in MGS1's own `WP_` order - which is **not** the
  menu's: 0 SOCOM, 1 FA-MAS, 2 Grenade, 3 Nikita, 4 Stinger, 5 Claymore, 6 C4,
  7 Stun Grenade, 8 Chaff Grenade, 9 PSG1.

  Ownership is the same convention the items turned out to use, and the menu
  states it outright - `GM_Weapons[i] >= 0` (`menu/weapon.c`), so -1 is "not
  carried". **What goes in the magazine is taken from the game, not invented.**
  Its own `add_weapon` lifts a negative entry to 0 and fills toward
  `GM_WeaponsMax`, so a granted weapon gets the full magazine the game already
  records for it, and an empty one where no capacity is recorded. Nothing writes
  `GM_WeaponsMax`: there is no capacity table anywhere in the decompiled source
  to write a truthful one from, and making up ammo counts is the kind of
  invention this project does not do. If a weapon arrives empty, that is the
  game having no number for it, and the log says so.

  Both keys work on **Integral** as well as USA - the code is in the shared
  `MGS1` handler, keyed on the `scene_name` memory define every version has,
  with no title check. Set both back to empty for normal play.

  **The lesson is the general one this project keeps relearning:** the feature
  was written, built, reviewed and documented as working for five weeks without
  ever being pointed at an empty inventory. "Built" is not "exercised", and a
  guard that never fires looks exactly like a guard that never needs to.
- `Ketchup::Audit` did report two `differs from what was written` lines on
  2026-09-05 — both were the game's own code editing ported strings, fixed in
  `items.py`. Both pools are now owned byte for byte; a future audit line means
  the collection wrote *after* Ketchup's pass, which has not been seen.

### 5.8 Finish the text census — CLOSED FOR GCL STRINGS 2026-09-08
`mainsweep.py --census` accounts for **every** Japanese GCL string rather than
classifying flagged candidates, and the buckets are asserted to sum to the
total so a residue cannot hide in the framing. Both discs, identical: of
**1,360** Japanese strings, 1,260 are inside a stage a patch family owns, 17 are
Japanese on the USA disc too, 83 have no owner on the USA disc at all
(Integral-only content), and **0 are unaccounted**. It exits non-zero if that
last bucket is ever not 0, so it is a regression guard and not just a report.
The Integral-only stages are folded in through `base_stage`, so this covers
every stage on the disc and not only the shared names.

That supersedes the paragraph below, which is kept because it says what the
older tool measures and why its residue was never a defect list. Texture
lettering, executable UI beyond the save-title probes, and runtime language
branches remain outside both tools.

**The older framing:**
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
**Held open on purpose, 2026-09-07.** Both remaining items here were put to the
user the same evening the `SCARF` case below was decided, and both were kept
open rather than swept along with it. They are decisions still owed, not
oversights; §6 carries the same marker.

- **[open 2026-09-07]** The caption under READ MISSION LOG? (作戦記録を参照しますか？): kept because
  USA draws nothing there; `KEEP_PROMPT_CAPTION = False` in `abst_build.py`
  gives USA's empty record. Also the `1/2` counter and empty second screen on
  count-7 pages — USA's own behaviour, reproduced.
- **The `abst` location names: USA's, ASKED AND DONE 2026-09-08.** The second
  application of amendment 4b, and the first one that needed a container to
  grow. `mainsweep.py --diff-english` enumerated the table: 30 English names in
  each game, aligned 1:1, and **four** differ - the three the documents listed
  plus `Cmnd rm`, which was in none of them.

  | Integral | USA |
  |---|---|
  | `Tank Hanger` | `Tank Hangar` |
  | `Medi rm` | `Medi room` |
  | `Cmnder rm` | `Cmnder room` |
  | `Cmnd rm` | `Cmnd room` |

  *What it is.* One `0x9906` command in `scenerio.gcx`'s script body -
  `mainsweep.py` calls it `chara 53C7` after the actor its first STRID spawns -
  carrying 31 records directly in its value list with **no option list at all**,
  which is why `page_of` returns None for it and `rebuild_body` used to skip it.
  The names are **two-byte font codes**, not ASCII (`0x80xx` Latin, `0x9001` a
  space), which is why no ASCII search of the PPFs had ever turned them up. Both
  games use the same encoding, so USA's bytes drop straight in.

  *How it was done.* `USA_LOCATION_NAMES` in `abst_build.py`, beside
  `KEEP_PROMPT_CAPTION`. USA's **whole command** is taken rather than its four
  records, and that is the point: the block carries **two** derived length fields
  - the COMMAND's BE16 size and a **u8 at `start+5`** that `option_starts` uses
  to reach the option list - and both are 12 bytes larger on USA's disc. Patching
  the records and forgetting the u8 would leave a block whose size says one thing
  and whose offset byte says another. Taking the block whole keeps them in step
  by construction. `abst_build.py` already recomputes every enclosing container
  (command size, proc body ARG length, proc table offsets, proclen, script
  length) and relocates the stage, so nothing else was needed.

  *Cost.* One name is length-neutral (`e` -> `a`), three grow by 4 bytes each -
  two extra glyphs at 2 bytes a glyph - so **+12 bytes**, measured both ways:
  the rebuilt chunk is 104,600 bytes with the constant off and 104,612 with it
  on. The stage is still **88 sectors** and still lands in DUMMY3M slots
  462..549, so no budget moved.

  *Verified.* The builder's own verifier now re-parses the location list out of
  the rebuilt script and asserts it equals its source record for record, and that
  the constant is honoured exactly once - `verified: the 31-record location list
  equals USA's exactly; 4 record(s) differ from retail Integral`. Both directions
  were run: with the constant off it reports Integral's own list and 0 differing.
  Deployed to both discs 2026-09-08; `ppfcheck.py --deployed` clean over 27
  files. **Not yet seen on screen.**

  *The Japanese location list is untouched.* `demo.gcx` carries Integral's own,
  31 records USA has no counterpart for, and it is not offered to the
  substitution at all.
- **The item short-name table: `SCARF` -> `HANDKER`, ASKED AND DONE 2026-09-07.**
  **This is the port's first replacement of Integral's own English** rather than
  of its Japanese, and therefore the first case under amendment 4b in §2.

  *What it is.* The abbreviations in the inventory's side column are a different
  string set from the descriptions: NUL-terminated names on an 8-byte stride in
  the executable, items 23 down to 0, **already Latin on both discs**, which is
  why the port had never touched them. Dumping both tables and comparing entry
  by entry, exactly one differs - item 22, `SCARF` on Integral against
  `HANDKER` on USA. Every other item and weapon abbreviation was already
  identical.

  *Why it was worth changing.* Integral's own Japanese description for that item
  reads 《ハンカチ》 - *hankachi*, a handkerchief - and its own description says
  so. Its short label was the only thing calling it a scarf, so the change makes
  Integral agree with itself as well as with USA. Read with `rendertext.py`.

  *What went in, and what could not.* `HANDKER`, which is USA's own string - not
  "Handkerchief". The slot is 8 bytes, so seven characters is the ceiling, and
  any other abbreviation would be invented text rather than ported text. USA's
  is exactly seven, so it lands in the existing slot and **nothing moves**:
  the patch grew by exactly 8 bytes per disc and changed nothing else, which the
  deployed-set comparison confirms byte for byte.

  *Where it lives.* `items.py`, `IN_SHORTNAME = 0x09BCC0` against USA's
  `0x09E448`, added to the regions `en_items` owns outright so Ketchup writes
  and audits all 8 bytes. Both discs, deployed 2026-09-07 22:56. **Not yet seen
  on screen.**

  **Seen on screen 2026-09-07 23:03**: the side column reads `HANDKER`, beside
  the description it already agreed with.

  Two facts about that block worth keeping. **Cold Medicine and Diazepam are not
  in it** - both names are 8 characters, one too many for a slot that must also
  hold a terminator, so both games keep those two elsewhere. And the `MP 5 SD`
  string sitting near the table is **not a table entry** - a first pass with a
  fixed 8-byte stride suggested Integral's table was one longer than USA's, and
  that was wrong: it is a string literal in `menu/weapon.c` that names the FA-MAS
  slot on VERY EASY, emitted into rodata beside the table. Walk this region as
  NUL-terminated strings and compare by content, never by index.
- `rank`: 36 Integral-only Japanese sentences with no USA counterpart → stays
  Japanese unless a USA source turns up. Nothing to do without one.

### 5.10 The patch-side pass — DONE 2026-09-07 (evening)
Seven robustness and completeness gaps were identified in the morning review and
all seven were closed the same evening. None of them changes what a player sees;
what they change is what can go wrong unnoticed.

**1. The two VR patches that wrote the same stage now have one owner each.**
`vr_en_movie` used to share 686 of its 753 bytes with `vr_en_missions` and work
only because Ketchup applies a folder in file-name order — a dependency nothing
enforced and nothing would report. `vr_windows.py` now ports the `movie` stage
as before but writes none of its records, handing the finished stage to
`vr_movie.py` as `work/vr_movie_base.bin` (`vr_windows.HANDOVER`); `vr_movie`
emits against **retail** and owns the stage outright. The two share **0 bytes**,
the deployed-folder dependency (`INTEGRAL_ENGLISH_VR_PPF_DIR`) is gone, and
`rebuild.py` now refuses *any* VR overlap instead of allowing that one pair.

**Verified by effect, which is what made it safe to do at all:** applying the new
pair gives the disc byte for byte what the old pair gave. Of 136 positions where
the two sets differ as *files*, every one is a byte equal to retail either way —
the old set wrote them redundantly inside merged runs. **Positions where the disc
would actually differ: 0.** Both files must be replaced together when this is
deployed; neither works with the other's old copy.

**2. Width checking, and what it turned out the invariant is.** `widths.py`
derives a `vrwindow`'s real budget from the decomp rather than guessing it —
`align4(w) - 16`, to VRAM words, to whole 12-px cells, less the 12 px
`font_draw_string` reserves — so a 256-wide window gives 228 px. Then the
measurement said not to assert it: **retail Integral has 107 lines over that
budget and USA has 19**, so it is not an invariant, it is an estimate. What IS
enforced is exact and cheap: `substitute_numbers` may never make a line render
wider than the USA line it came from (the only width known to be safe, because
USA shipped it), plus the 255-px ceiling that `kcb->max_width` imposes on
anything, over every record the port writes. Both hold today and every VR patch
rebuilds byte-identical, so these are regression guards, not fixes.

`vr_exe.py` deliberately has **no** width check, and the reason is recorded in
it: its pools hold multi-line descriptions, the English ones break on `0x807C`,
and retail Integral's own Japanese entries in the same arena measure 540 px
unsplit — so they break on something not yet established. Asserting there would
fail on bytes the game ships and works with.

**3. The raw disc now carries correct error correction.** A PPF that changes a
payload byte invalidates that sector's EDC and P/Q parity; the collection's
emulator does not care and a real console may. `cdecc.py` implements both sums
and `rawdisc.py` recomputes the tail of every sector a raw patch set touches —
413 sectors per main disc, 2003 on the VR disc. Each PPF also gains a PPF3 block
check so a tool can refuse the wrong image. `py rawdisc.py <package>` applies a
finished set in memory and confirms every touched sector verifies; it does.

**The pass rests on one invariant, checked per sector: before anything is
applied, the sector as we believe retail has it must verify against its own
stored parity.** That is a 280-byte sum over 2048 bytes, so it cannot pass by
accident, and it is what makes the executables safe — their ISO extents are
zero-filled in the collection's images, so the retail file is put back first.

**4. The collection's named-file patches are no longer a mystery.** See §5.12.

**5, 6, 7. Ketchup, the sweep and the tests.** `Ketchup::ApplyBlock` now warns
when part of a record lands in a sector's 304-byte tail and is not mirrored,
instead of logging success — the silent loss that once cost `en_savemsg` 142 of
442 bytes. `ReportOverlaps` warns when two PPFs in a folder write the same byte
with **different** values, naming both files. `ApplyPPF3` validates the whole
record chain before applying any of it, so a malformed file is refused rather
than walked to a count that never reaches zero — the 306 MB log. The block check
is still skipped and now says so: the fix has no way to read the disc image
back, so it cannot be verified here. `mainsweep.py` is §5.11. `selftest.py` runs
23 tests over the pure pieces in a hundredth of a second, and each one was
checked by mutation to confirm it fails when the thing it guards is broken.

### 5.11 The one thing the main-disc sweep found — BUILT AND DEPLOYED 2026-09-08
`mainsweep.py` pairs every GCL string on both discs by the command that owns it,
so "Integral has Japanese here and USA has English" becomes a comparison rather
than a guess. Run over discs 1 and 2 it reports twelve owners; nine are inside
stages a patch family already owns, two are Japanese in identical numbers on the
USA disc as well (`cmd 4AD9`, the location titles; `chara 9302`, `rank`). One
was neither, and it is now the `en_pad2` family — `pad2.py`, two PPFs, 159 bytes
each, deployed 2026-09-08 22:02.

**What the text is.** Stage `s07b` is the Psycho Mantis room (`stage/s07b.c`
registers `CHARA_PSYCHOMANTIS`). The owner is `CHARA_2D0A_2ND` → `NewSecond` in
`game/second.c`, 45 lines long, and it settles by itself what draws the string:
the actor takes **one** string per spawn, writes it as a subtitle with
`MENU_JimakuWrite(work->message, 20000)` when `GV_PadData[1].status` first goes
true, and clears it when pad 1 comes back. So it is the line shown when the
controller moves to **port 2** for the Mantis fight, telling the player to put
it back. Integral's reads コントローラ端子1のコントローラを|使用してください。
(`rendertext.py`; three of its codes fall outside the located font bank, so read
the PNG, not the codes). USA's is `PLUG CONTROLLER INTO | CONTROLLER PORT 1.`

**This entry used to describe it wrongly, in two ways.** It said "two records"
of one owner, record 0 English on USA and record 1 Japanese, and that USA
"translated the first of the pair". Both are wrong, and reading `second.c` is
what shows it: one string per spawn means there is no record 0/record 1 to
index. What the script has is **two separate spawns, in two branches**:

| | Integral | USA |
|---|---|---|
| site A | string at script `body+0x88C`, path `elif 1903 → if 2043` | same offset, **byte-identical Japanese** |
| site B | string at script `body+0xC3A`, path `elif 2845 → if 2985` | `body+0xC0E`, **English** |

So USA translated the **later** site by offset, not the first, and left the
other — its own inconsistency, because both branches hand the same message to
the same actor.

**And there is a third site the sweep cannot see.** `s07br` carries the same
string at `body+0xC3A`. That stage is one of the 13 **Integral-only** names, and
`mainsweep.py` walks only the 82 names the two discs share, which puts every
Integral-only stage outside its universe. This is a second blind spot beside the
one §5.14 records, and it is now written down in `COVERAGE.md` as a limit of the
tool rather than left to be rediscovered. `s07br`'s overlay source is
byte-identical to `s07b`'s (`diff` is empty), so it is the same code over
different stage data; **what that stage is for has not been established.**

Five sites in total: three per disc, two discs, and both discs hold both stages
at the same LBA with identical bytes, so the two PPFs are the same writes at the
same offsets.

**The decision, and it was the user's.** Porting only USA's one site is what
"placed where USA places it" says literally, and it would leave a player who
trips the other branch — or who is in `s07br` at all — reading Japanese. Asked
and answered 2026-09-08: **port every site.** The text is USA's own verbatim
either way; the rule exists to forbid invention, not to reproduce an oversight.

**Why nothing had to move.** A GCL STRING is length-prefixed and
`GCL_GetNextValue` advances by that length byte, never by `strlen` (the
correction §5.3 records). USA's 42 bytes fit inside Integral's 55-byte slot, so
the length byte stays at 55 and the walk steps over the same bytes it always
did. The English and its terminator go in at the front, the dead tail is spaces,
and the record's own final NUL is left alone — `menu2.py`'s convention.
`MENU_JimakuWrite` only stores the pointer and `font_print_string` reads to the
NUL (`menu/jimaku.c`), so the tail is never looked at. No container to
re-stamp, no sector to grow, no relocation, no DUMMY3M slot.

**One trap worth keeping.** The padding must go *after* the terminator, never
before it. `font_print_string` measures what it draws and jimaku centres on that
width (`field_4_x = (FRAME_WIDTH - max_width) / 2`), so trailing spaces ahead of
the NUL would silently pull the line off centre. `selftest.py` guards it, and
that guard was confirmed by mutation along with three others.

**How far it is verified.** Statically, and by effect rather than by inspection:
applying the build to the archive leaves its length unchanged, re-walks both
stages to the same 1279 and 906 commands with identical structure (so nothing
desynced), leaves all 159 changed bytes inside the three slots, and each slot
re-parses at length 55 with the English at the front. The English itself is read
out of `usa1_stage.dir` at build time rather than retyped. The two PPFs are
disjoint from all nine deployed PPFs on each disc, `ppfcheck.py --deployed` is
clean over all 31 files, and the family is registered in `rebuild.py`: the clean
run `repro17` rebuilt both PPFs **byte-identical** to the deployed ones, 27 of 27
across the set.

**Not yet seen on screen** — and it needs more than a save: the subtitle only
fires when pad 2 becomes active, so it wants the Mantis room *and* a second
controller in port 2 (or the emulator's port-2 assignment). `StageSelect = s07b`
can load the stage, but §5.7 records a direct `s14e` entry hanging without story
state, so expect to reach it in play. Which branch the game actually takes, and
whether site A is reachable at all, is worth noting when it is seen.

### 5.12 What the collection's own disc patches contain — ANSWERED 2026-09-07
Three documents said this could not be known. It can.

The collection's patch table has two kinds of entry. An *offset* patch carries
its bytes inline, so `SQHook::SetPatchWatch` logs them. A *named file* patch
carries only a name and the game reads the bytes from its own archive later, so
the watch reports "0 bytes" and the content stayed invisible — including the
five that land on the port's own text. `m2archive.py` reads them.

**How.** `windata/alldata.bin` is a flat blob and `alldata.psb.m` beside it is
its index: an MDF (`mdf\0`, a u32 size, then a zlib stream XOR-obfuscated with a
64-byte keystream from `MD5("25G/xpvTbsb+6" + the file's own lowercased name)`
seeded through MT19937 — the literal is in the game exe at 0x75ECE0). Inflated,
it is a PSB v3 whose `file_info` maps 4,926 paths to `[offset, size]`.
`099/patch/` holds 176 entries, each an MDF wrapping a *stored* deflate block,
so the payload is plain bytes behind one layer of obfuscation and its adler32
checks — which is what makes an extraction certain rather than plausible.

**What they say.** Not translation: they **blank the line telling the player to
open the disc tray** and reword the prompt. On the `title` block (`0x1822B55D`,
592 bytes, 30 differing from retail) record 1 becomes twelve spaces and record 2
is reworded; the `abst` block (`0x132F2716`, 240 bytes, 83 differing) blanks
records 1 and 3; `change` (`0x18345E07`, 174 bytes, 48) blanks record 2. One,
`disc1_18412A95_patch_PS5` on `demosel`, differs from retail in **0 of its 19
bytes** — it writes exactly what is already there. The platform suffixes
(`_NX`, `_PS`, `_PS5`, `_XBOX`, `_STEAM`) differ only in button-glyph codes.

**Three things this settles.**

* **`en_menu3`'s collision is confirmed with bytes.** Their patch overwrites 592
  bytes starting at the address of our record 0, in retail's own layout. Ours
  rewrites the same block with USA's English and different record boundaries.
  Whichever lands last decides, and if ours does not, the block is inconsistent
  — which is the `GCL:WRONG CODE` run seen three times. Raw-disc-only stands.
* **The `abst` patch our relocation orphans is harmless.** It blanked two
  Japanese strings that `en_abst` replaces with USA's English anyway.
* **The archive index confirms every image base this port found by scanning.**
  Integral discs 1/2/3 at 0, `0x2AE54800`, `0x57592000`; USA discs 1/2 at
  `0xF12F8000`, `0x11B3E5800`; USA VR at `0xD39B7000`. All six, exactly.

### 5.13 Two measurements worth keeping
**Integral's images are faithful retail dumps where it matters, and that is now
proved rather than assumed.** Put the separately supplied retail executable back
into its zero-filled ISO extent and recompute the parity the collection left
behind: `int1.exe` reproduces all **313** stored sector tails, `int2.exe` all
313, and `vrint.exe` — which is *built from the decomp*, not copied — all **308**.
A 280-byte sum over 2048 bytes, matched 934 times. So the decomp's output is the
disc's own bytes where its source is unchanged, and the raw-disc variant's
assumption about these images holds.

**`us1.exe` is not the executable the collection's USA image was built with.**
The same check reproduces only **8 of 318** tails there. The file is a genuine
`SLUS` build by its own strings and the image's `SYSTEM.CNF` boots
`slus_005.94`, so the likeliest explanation is a different pressing — but it is
not established, and it is one more reason the port takes USA text from
`usa1_stage.dir` (real USA discs) rather than from this image. It does not touch
the Integral patches, which is why it is recorded rather than chased.

### 5.14 Where else does Integral's own English differ from USA's? — SWEPT 2026-09-08
Raised by the user 2026-09-07, immediately after the `SCARF` case: *"if there are
other instances of existing English in Integral that differ from USA."*

**Three are known now. Two were found by accident; the third was found by the
sweep this section asked for.** `SCARF` against USA's
`HANDKER` turned up because it happened to sit in the corner of a screenshot
taken for another purpose; the `abst` location spellings (`Tank Hanger`,
`Medi rm`, `Cmnder rm`) turned up while porting the mission log — and there is a
fourth, `Cmnd rm`, that only the sweep found. Neither of the first two was
found by looking. There is no reason to think two is the total.

**Why nothing here would have caught them.** Every sweep this project owns hunts
*Japanese*: `mainsweep.py` and `vr_sweep.py` pair a record with USA's and ask
whether Integral's is Japanese where USA's is English; `jpsweep.py` scans for
Japanese-looking pointer slots; `audit_text.py` inventories game-encoded string
candidates. A string that is already English on both discs and merely **says
something different** passes all four without a murmur. That is the blind spot,
and it is exactly the shape of both known cases.

**A method that would work, sketched.** The obstacle is pairing: the two builds
lay their data out differently, so a positional diff is meaningless. But both
known cases sit in a *sequence* whose neighbours match - `SCARF` is between
`SUPPR.` and `ROPE` on both discs - which is what a diff is for.

1. ~~**Executables.**~~ **DONE 2026-09-07, and the answer is one.** Extract the
   ordered NUL-terminated Latin strings from `int1.exe` and `us1.exe` and run a
   sequence diff over the two lists: equal runs align themselves, and a
   **replace** hunk of one string against one, with matching context either
   side, is exactly the `SCARF`/`HANDKER` shape.

   Filtering to text-like strings - printable, mostly letters - and running it
   at minimum lengths of 5, 4 and 3 characters gives the **same single result
   every time**: `SCARF` against `HANDKER` at 0x09BCC0, the one already changed.
   Nothing else in the executable differs. (Both discs' executables are
   byte-identical, so disc 2 is covered by the same pass.)

   The other hunks are all accounted for and none is portable text: the region
   and product strings (`...for Japan area` / `BISLPM-86247` against
   `...for North America area` / `BASLUS-00594`), a scatter of `.c` source
   filenames USA's build kept, USA's memory-card message pool - which shows as
   an insert only because Integral's counterparts are Japanese and so never
   enter a Latin extraction - and a few short runs of MIPS code that read as
   ASCII.
2. **Stage archives — DONE 2026-09-08.** `mainsweep.py --diff-english` sequence-
   diffs the two discs' ordered English strings per stage, so equal runs align
   themselves and a `replace` hunk is the shape being hunted. Disc 1 gives **15
   replace hunks over 82 stages, 8 holding player-readable text**, and after
   triage the residue is exactly one family: the `abst` location names
   (`chara 53C7`), where **four** pairs differ, not the three every document
   listed. The fourth is **`Cmnd rm` against USA's `Cmnd room`** — nobody had
   noticed it, and it sits in the same table as the other three. Disc 2 is
   identical. All four are live on the deployed disc: `abst_build.py` rewrites
   only the `0x9906` pages and the disc-change block, so the location list is
   copied through as Integral wrote it.

   The other seven readable hunks are all explained, and the explanation is the
   noise profile to expect: voice-clip and stage asset ids (`sound`, `selectd`,
   `chara 4EFC` — `vc319010` and the like), and hunks where one side's
   counterpart is *Japanese* and therefore never entered an English list at all
   (`abst`'s 907 recap lines, `option`'s help lines, `title`'s disc-swap block,
   and USA disc 1's `vr01`..`vr10` mission names, which Integral's disc has no
   equivalent of).

3. **The VR disc — asked, and it needs a different input.** Two things had to be
   learned. USA's VR disc carries **five languages**, so the diff must take only
   the English arm of a language branch (`lang in (None, ENGLISH)`, the test
   `vr_windows.py` already uses); without that the alignment collapses — 548
   hunks against 267 with it, and no one-against-one hunk either way. Then a
   per-owner fuzzy match (Integral's English strings absent from USA's at the
   same owner, with their nearest USA counterpart) turned up **`FAMAS` against
   USA's `FA-MAS`** across the mission titles — and it is a **non-finding**: the
   deployed `vr_en_missions.ppf` holds **142 `FA-MAS` and zero `FAMAS`**, because
   the port takes USA's window text verbatim, so those windows already read
   USA's spelling.

   **That is the lesson, and it is the opposite of the Japanese question's.**
   `mainsweep.py` reads *retail* on purpose, so a gap cannot hide behind a patch
   that is already deployed. The English-against-English question must be asked
   of the **deployed** bytes instead, because there the port's own replacements
   are precisely what has to be subtracted — otherwise the sweep rediscovers the
   port's own work and calls it a finding. Only `vr_sweep.py` has the plumbing to
   reconstruct a deployed stage (`deployed()`); `mainsweep --diff-english` does
   not, which is safe today only because the one family it finds sits in records
   no patch rewrites.

   **Half of that is fixed as of 2026-09-08, the cheap half.**
   `--diff-english` now checks each finding's stage against `PORTED` and prints
   `!! <stage> is owned by <family> and these are RETAIL bytes` beside it, with
   a closing summary naming every flagged stage. It cannot tell you what the
   patch writes - it turns a silent trap into a printed one, which is what was
   actually dangerous. Three stages flag today: `abst`, `option`, `title`. The
   `abst` four are flagged and *were* real, and are now ported, so from here the
   flag is what stops someone porting them twice.

   **And the expensive half should NOT be built.** The first plan here was a
   deployed-stage reconstruction like `vr_sweep.deployed()`, extended to follow
   `en_abst`'s and `en_brf`'s relocation into DUMMY3M. That was the wrong
   answer, and the reason is worth keeping: it re-derives by the hardest
   available route something the project already has. **The builders construct
   the ported stage in memory.** Reconstructing it from PPF records means
   parsing the patch, applying it, following a relocated directory entry and
   re-parsing the result - and needing an extension every time another family
   starts relocating.

   **The right division of authority, and it is mostly already in place:**

   | bytes | authority | mechanism |
   |---|---|---|
   | a family owns them | that family's builder | a verifier over its own built output |
   | nobody owns them | the sweep, reading retail | retail *is* deployed there, so it is already right |
   | the boundary between | the `!!` flag | "a patch owns this, go read its builder" |

   So the cheap fix is not a stopgap; it is the correct thing at the boundary.
   `abst_build.py` now verifies its location list against USA record for record,
   and `vr_windows.py` has always checked every window against USA's. **What is
   actually left is per-family verifiers where they are missing** - small, local,
   testable, and they fail at build time instead of waiting for a sweep to be
   run. Note also that the Japanese sweep and `--census` must keep reading
   **retail**, so the input is a per-question choice and never a global switch.

4. **Not textures.** Lettering drawn as art is out of scope for a text sweep and
   stays that way.

**Expect noise, and know its shape before starting.** Integral-only features
(VERY EASY, the MP5 SD, PocketStation, `rank`'s commentary), product branding and
the save-title suffix, and version or build strings will all differ legitimately.
The useful output is the small residue: the same UI element, worded differently.

**What to do with a result is already settled** - §2 amendment 4b. Each find is
the user's call, one at a time, and the answer may well be "leave it": Integral's
own English is not wrong, it is just not USA's.

---

## 6. Decisions that are the user's — ask, do not assume

**Four of these were put to the user on 2026-09-07 and deliberately left open;
one of the four - the `abst` location names - was then decided on 2026-09-08,
so THREE remain.** The three are marked **[open 2026-09-07]** below. Being held
is a decision in itself, not an
oversight: they were raised, considered alongside the `SCARF` case that was
decided the same evening, and held. Do not re-raise them as though they were
newly noticed, and do not read the passage of time as consent - each still needs
an explicit answer before anything changes.

- **[open 2026-09-07]** The caption under READ MISSION LOG? (kept Japanese by
  rule; one constant blanks it) and USA's `1/2` on single-screen pages
  (reproduced) — §5.9.
- Anything under the 2026-09-03 amendment: moving English text to fit
  Integral's own art.
- The `en_savemsg` collision approach, if one is ever observed.
- Achievements on or off for a given test session (`DisableRAM` /
  `DisableCDROM`); they are **on** now. Turning them off keeps SPECIAL / PHOTO
  ALBUM reachable without earning it and has never affected the PPFs.
- **The `abst` location names — ASKED AND ANSWERED 2026-09-08: use USA's.**
  Four of them, not the three this file used to list; §5.9 has the table, the
  mechanism and the measurements. The **second** application of amendment 4b,
  after `SCARF` -> `HANDKER`, and the first that made a container grow (+12
  bytes, absorbed by `abst_build.py`'s existing re-stamping). Built, verified
  both ways and deployed the same day; not yet seen on screen.
- **[open 2026-09-07] The VR disc's three number substitutions.** Where Integral and USA state
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
- **The item short-name `SCARF` -> `HANDKER` — ASKED AND APPROVED 2026-09-07,
  and it set a precedent.** Integral's side-column abbreviation for item 22 was
  already English and disagreed both with USA's and with Integral's own Japanese
  description (《ハンカチ》, a handkerchief). The user's instruction created
  amendment 4b in §2: replacing Integral's **existing English** is an exception
  to the rule, allowed when asked, case by case. It is not a new default - the
  `abst` location spellings are the same shape and remain undone and unasked.
- **[open 2026-09-07] VR EXTRA menu record 6.** Integral's fifth item is PocketStation where
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
| `brf_build.py`, `brf_widen.py` | briefing labels and quads; the build asserts zero load-delay hazards against retail |
| `overlaydiff.py [--vr] [--all] [--stage NAME] [--debug]` | **per-stage English-vs-Integral overlay comparison**: which printable strings USA's copy of each stage overlay has that Integral's lacks, net of what the deployed PPFs already write, with debug/symbol strings and the four other languages filtered. The question the 2026-09-11 memory-card finding showed nobody had asked; a byte inventory that judges per string cannot ask it. Also worth running over the executables (the same three lines of Python, in §26) |
| `hazards.py <built> <base-hex> [--retail <retail>]` | **R3000 load-delay scanner** for hand-written MIPS: a load followed at once by a read of the loaded register, a non-load write in that slot, a branch in a branch's delay slot, mfhi/mflo too close to a mult. With `--retail`, only word pairs the port changed are judged. The Master Collection's emulator does not model the delay, so no screenshot taken there can catch this class of bug - this is the check. `selftest.py` proves it catches the 2026-09-10 briefing bug at its own address |
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
| `mkimage.py` | **writes a patched disc image** from a raw build — the step that turns PPFs into something a burner or emulator can open. `--redump <disc.bin>` or `--collection --game ... --exe int1.exe` (the collection hollows the executable out, so it refuses without one). Checks four things before writing: every PPF's block check against the image, no record past the end, every touched sector's parity **before** patching, and again **after**. §22 |
| `rawdisc.py [package]` | the EDC/ECC pass `rebuild.py --variant raw` runs, and `verify_set` — apply a finished set in memory and check every touched sector against the parity the set wrote |
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
| `vr_unlock_extras.py [--deploy]` | the removable VR **EXTRA menu** unlock test aid — three `andi` tests in the `vrtitle` overlay's visibility-mask construction, so PHOTOGRAPHING / ALBUM / PocketStation always appear. Writes no progress; delete the PPF to relock |
| `vr_unlock_movies.py [--deploy]` | the removable VR **movie** unlock test aid — one instruction in the `movie` overlay's own `count / 3` score gate, which `vr_unlock` does not touch. Writes no progress; delete the PPF to relock |
| `vr_sweep.py [--samples]` | rebuilds every VR stage from the deployed PPFs and reports what is still game-encoded, beside USA's own tally — the VR equivalent of `jpsweep.py`, and the only tool here that inverts `portio.image_offset`'s 2352-byte sector geometry |
| `bridge.py` | the Squirrel-debugger client for live RAM reads/pokes (README "Toolchain and environment"); writes `sqcmd/`, `sqout/`, `bridge.log` beside itself (git-ignored) |
| `gcldump.py`, `gclprocs.py` | dump a stage script's command tree / every proc with decoded values (used to read the title script's 1P MODE path) |
| `pcx4.py` | encode/decode the 4-plane RLE PCX the texture loader expects (how `sc_text` and the KEY CONFIG art were read and written) |
| `selftest.py` | **44 tests over the pieces that need no game data** — the PPF emitter's two split boundaries, the record chain, the PCX codec, the EDC/ECC algebra, the width model, the language default, the load-delay scanner. `py selftest.py`, a tenth of a second. Ground truth lives elsewhere: `cdecc.py` against the real discs, `rebuild.py --compare-deployed` against the deployed set |
| `cdecc.py` | EDC and P/Q parity for raw Mode 2 Form 1 sectors. `py cdecc.py` is the check that proves both the sums and the retail executables: it rebuilds each zero-filled executable extent from the supplied retail file and matches the parity the collection left behind (313/313, 313/313, 308/308) |
| `rawdisc.py` | the raw-disc EDC/ECC pass. As a library `rebuild.py --variant raw` uses it to emit each disc's `*_zz_ecc.ppf`; as a command, `py rawdisc.py <package>` applies a finished raw set in memory and confirms every touched sector verifies |
| `widths.py` | how wide a ported line renders and how wide it may be: the `vrwindow` budget derived step by step from the decomp, the 255-px `max_width` ceiling, and the pool line separator. Read its docstring before adding a width assert — the per-window budget is **not** an invariant, retail exceeds it |
| `mainsweep.py` | the main discs' answer to `vr_sweep.py`: pairs every GCL string with the USA disc's by owning command, so "Integral Japanese where USA has English" is measured. `py mainsweep.py [--disc 2] [--samples]`. Its one uncovered finding is §5.11, ported 2026-09-08. Three modes were added the same day: `--integral-only` pairs each of the 13 Integral-only stages with the USA stage it is a variant of (the shared-name universe's hole — 1 string, already ported); `--diff-english` sequence-diffs the two discs' English for wording differences (§5.14 step 2 — found the fourth `abst` spelling); `--census` accounts for every Japanese GCL string and **exits non-zero unless the unaccounted bucket is 0** (§5.8) |
| `radiomap.py` | **where every `RADIO.DAT` fragment starts and where its bank-1 font sits.** Parses each candidate sector's record list (self-checking) and checks the result against the 192 fragment extents the game's own radio codes declare. Prints DISTINCT bitmaps the text lookups produce (1,200) and their blank-twelfth-row rate (100%), which is a far better measure than the share of strings attributed that the broken predecessor reported - but both are aggregates and blind to a single fragment's base slipping, so pair it with `radiotext.py --check` (§21). `py radiomap.py` |
| `radiotext.py` | **every subtitle, by walking the records the game walks** (`menu_gcl_exec_block_800478B4` and the TALK/IF/SWITCH/RANDSWITCH payloads). Replaces the byte scanner for `RADIO.DAT`, which was dropping 15% of the commentary. Also carries **the regression guard on the fragment map**: `--check` requires every fragment's bank-1 text to also appear in another fragment (worst real score 96.0%, a base slipped one glyph scores 0.0%), and `--selftest` slips bases on purpose and requires `--check` to catch them - which the first two versions of the check did not. §21 records both metrics that failed. `py radiotext.py [--check] [--selftest] [--dump out.txt]` |
| `glyphsheets.py` | renders the unidentified bank-1 glyphs to `work/glyphs-to-identify.pdf` and matching PNGs, ordered by frequency, **with a `.txt` of real decoded sentences beside each page** - that companion file is the more important half, because at 12x12 線/緑 and 間/問 are the same picture and a sentence is not. Leaves the 78 already-known shapes in unmarked, with the answers in `work/glyph-answers.tsv`, so a pass can be scored. `py glyphsheets.py` |
| `glyphfill.py` | merges a transcription into the TSV and **scores it**: against those 78 known answers, and against the invariant that bank 1 never reuses a bank-0 character. Every warning it raised in the 2026-09-10 pass was a real error. `py glyphfill.py [--score]` |
| `glyphreview.py` | prints the **full** decoded lines a glyph appears in - `--verify` does one sentence for every shape, which is the read-through that caught 黙/弄 swapped and 完 for 璧. `py glyphreview.py --verify` |
| `glyphocr.py` | identifies the game's 12x12 glyphs by matching them against a system Japanese font. **47% top-1 / 59% top-3**, measured against the 238 hand-transcribed `0x90` kanji — a shortlist tool, not an oracle; its errors are 鏡/鎌 and 線/緑, which at 12x12 are the same picture. `py glyphocr.py --validate` |
| `dumpjp.py` | **the dump**: every in-scope Japanese line, as readable text (`<disc>_<source>.txt`), as a locating index (`index.tsv`) and drawn from the game's own glyph bitmaps (`.pdf`). 68,242 lines, 3,923,944 kana/kanji, zero unresolved codes. `--scope unported` (default) keeps only Japanese USA has no counterpart for. `RADIO.DAT` comes from `radiotext.py`, not the inventory. Discs are keyed by name - `disc1`, `disc2`, `vr` - because the VR disc has a stage archive but no `RADIO.DAT`, and a loop over indices used to skip it entirely (§20). `py dumpjp.py [--discs 1,2,vr]` |
| `jptext.py` | **makes the list readable**: font codes -> Japanese (kana by arithmetic, the `0x90`/`0x91` kanji banks by transcription, bank 1 through `bank1-glyphs.tsv`'s 1,214 shapes). Bank 1 needs the block's own font blob to turn a code into a bitmap, so `jptext.py` **run on its own still reports 87.2%** - it is reading the inventory with no blobs. Hand it one (`dumpjp`, `radiotext`) and it resolves everything: the export has zero unresolved codes. Writes `work/japanese-readable.tsv`; `--hex` decodes one run, `--sample N` prints the longest. Bank 1 is a per-block table carried by the block (proven: `abst`'s blob glyph 0/1 are 記/録), so what is left is glyph recognition, not reverse engineering |
| `jplist.py` | **the list** - but see the warning in §19: its scanner **ends a run at any code it does not recognise**, so it holds only 85% of the commentary's glyphs and `RADIO.DAT` should be read through `radiotext.py` instead. Every untranslated Japanese string on all three discs, one per line, to `work/japanese-inventory.tsv` — 190,180 strings / 3,318,254 kana-kanji glyphs, 32 MB, regenerated not committed. Drops any run the USA disc also has, which is what empties `BRF.DAT` and `FACE.DAT`. `py jplist.py [--min N] [--render N]` |
| `discaudit.py` | **every file on every disc**: size, the Integral-vs-USA delta and a crude text probe. Written 2026-09-09 because every other sweep here reads only `STAGE.DIR`; the delta is the diagnostic (`RADIO.DAT` is +9.4 MB on Integral, and that is the developer commentary). `py discaudit.py` |
| `jpremain.py` | **what Japanese is still on the three DEPLOYED discs** — the only tool here that reads deployed bytes (retail + every deployed PPF, following the relocated STAGE.DIR entry for `abst`/`brf`/`option`/`preope`). 153 Japanese strings a disc, 38 on the VR disc, all itemised with reasons in `COVERAGE.md`. `py jpremain.py` |
| `pad2.py` | `en_pad2`: USA's controller-port subtitle into all three of the sites `second.c` is spawned at, on both discs. Length-preserving — the English goes in at the front of Integral's longer slot and the length byte never changes. `py pad2.py` |
| `rendertext.py` | **reads the game's own Japanese, by drawing it.** The scripts store font indices, not Shift-JIS, so no table turns a Japanese string into characters - `game_text` can only print `<822F><8253>...`. This looks the glyphs up the way `font.c` does and renders them to a PNG: `py rendertext.py --item 22`, `--weapon N`, `--hex ...`, `--exe us1.exe`. Two things in it were settled by rendering a word whose reading was known, not by reasoning - the bit order, and a one-glyph bank offset - because either mistake produces plausible-looking Japanese that is simply the wrong Japanese |
| `m2archive.py` | reads the collection's own archive: `--roms` the disc images and bases, `--list 099/patch` what it patches, `--patches` every Integral disc-1 CD-ROM patch decoded against retail, `--extract` one member. This is what answered §5.12 |

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
"Unlocking the EXTRA menu's items",
"Achievements" · VR → "The VR disc (SLPM-86249)", "The MOVIE selection
captions", "The white caption font differs between the two VR discs",
"Sweep: is any VR text still Japanese?" · tests → "Not tested" (struck-through items are
done, with dates) · decomp → "Audit against the decomp" ·
text found late → "The controller-port subtitle (`en_pad2`, 2026-09-08)",
"The `abst` location names (Integral's own English -> USA's, 2026-09-08)" ·
what Japanese is left → `COVERAGE.md`, "What Japanese is still there, and why"
(`jpremain.py`) · asked from outside → "Psycho Mantis's memory-card table, and
the RAM-patch question" ·
the collection's own patches → "Where the collection's own disc patches land",
"What the collection's named-file patches say" (what they contain, read
2026-09-07) · raw disc → "Raw-disc error correction, and what it proved on the
way" · widths → "Line widths: what is an invariant here and what only looks like
one" · credit and licence → `CREDITS.md`.

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
  three captions are English, deployed, and were seen on screen the same day
  (the user's shots at 01:03: both TGS captions on two rows, E3 on one); the
  EXIT box's 4 px move that followed is the part not yet seen. §5.4a and README
  "The MOVIE selection captions".

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

## 13. The 2026-09-07 evening pass: the seven-item review, closed

A review of the port asked what could be improved in the patches themselves
rather than in the text, listed seven things, and then did all seven. Details
are in §5.10 to §5.13; what the day is worth remembering for is smaller than
that list.

- **A budget you derived is still a guess until you check it against retail.**
  The `vrwindow` width budget was read out of the decomp one call at a time and
  is, as far as anyone can tell, correct — and retail Integral has 107 lines
  over it. Asserting it would have failed on the game's own shipped data. The
  invariant that survived is the one with a witness: never render wider than the
  USA line this came from, because USA drew it.
- **The thing three documents called unknowable took one afternoon.** "A named
  patch's bytes are only visible through `SetPatchWatch`, and named-file patches
  carry no inline data" was true and complete about the *watch*, and it quietly
  became a belief about the *bytes*. They were in a file on disk the whole time.
  When a document says something cannot be known, check whether it means cannot
  be known or merely was not tried by the route in front of you.
- **A checksum makes a good oracle for questions that are not about checksums.**
  Recomputing sector parity was meant to make raw-disc patches correct. It also
  proved the retail executables are the disc's, proved the decomp's build is
  byte-faithful, found the collection's zero-filling in a second measurement,
  and showed that its USA image was not pressed with the executable this port
  uses. None of that was the reason for writing it.
- **Test the tests.** All 23 passed on their first run, which is not evidence.
  Mutating three modules one at a time and confirming each mutation is caught is
  evidence — and it immediately turned up a real trap: a same-length edit
  restored within the same second leaves Python running the **cached bytecode**,
  so a test can appear to fail against source that is already correct. Clear
  `__pycache__` before believing a result like that.

## 14. The 2026-09-07 late pass: the item text read against USA, end to end

The evening's seven-item review (§13) was the port looking at itself. What
followed was the opposite - the game being read on screen against its donor,
which turned up two faults in the fix, one gap in the port, and two corrections
to things this file had asserted.

- **`[Game] GiveItems` had never worked, and nobody knew** because nobody had
  pointed it at an empty inventory in five weeks. An item Snake does not have
  is stored as **-1**, not 0, so its "only where the count is zero" guard could
  never fire; it logged twenty-four grants and made none. Fixed, along with two
  neighbouring faults, and `[Game] GiveWeapons` added beside it once items alone
  turned out not to be the ask. §5.7.
- **All 24 items and all 10 weapons were then photographed in both games and
  compared** - text, line breaks, and glyphs including `《》`, the button glyphs
  and the apostrophes. **34 of 34 identical.** The one difference in any of the
  shots was in a table the port had never touched: the side column's
  abbreviation, `SCARF` against USA's `HANDKER`.
- **That produced a new rule.** Replacing Integral's *own English* is a case
  neither standing rule covered; the user's answer is amendment 4b in §2, and
  `SCARF` -> `HANDKER` is its first and so far only application. Four other
  questions of the same family were deliberately left open.
- **A description is not always the string its table points at.** Reading the
  only two functions that print one turned up six slots that change with the
  game state - and one of them, the MP5 SD that replaces the FA-MAS on VERY
  EASY, is Japanese, reachable, and correct. Both conditional forms were then
  seen on screen for the first time. §5.1a.

Three process notes, and the first two are the same note twice:

- **"Built" is not "exercised."** `GiveItems` was written, compiled, reviewed and
  documented as working, and its guard had never once been in a state where it
  could fire. A guard that never fires looks exactly like a guard that is never
  needed.
- **A stride is not a structure.** Walking the short-name region on a fixed
  8-byte stride said Integral's table had an extra entry, `MP 5 SD`. It does
  not: the table ends earlier, and that string is a literal the compiler put
  nearby. Walking the same region as NUL-terminated strings gave the right
  answer immediately. The first version of that claim reached this file before
  the second version corrected it.
- **The bytes could not be read without drawing them.** None of the Japanese
  here is Shift-JIS - it is font indices, so `game_text` can only ever print
  `<822F><8253>`. `rendertext.py` draws a string with the game's own font, and
  two of its own details (bit order, and a one-glyph bank offset) were settled
  by rendering a word whose reading was already known. Both mistakes produce
  plausible-looking Japanese that is simply the wrong Japanese, which is the
  only reason the check was worth making.

## 15. The 2026-09-08 pass: the sweep's last finding, and what the sweep could not see

`en_pad2` was built, verified, deployed and registered in one short pass (§5.11
has the record). It is the smallest family in the port — 159 bytes a disc, three
slots, no container touched — and the interesting part is not the patch.

- **Reading the caller settled in five minutes what the notes had guessed at
  for a day.** `game/second.c` is 45 lines. It takes one string per spawn and
  draws it with `MENU_JimakuWrite` when pad 2 goes live. That single fact showed
  the "two records, record 0 and record 1" this file described could not exist:
  what `s07b` has is two *spawns*, in two script branches, and USA translated
  the later one. The general form of this is already in §13 — when a document
  describes data, check whether anyone has read the code that consumes it.
- **A sweep's universe is part of its result.** `mainsweep.py` reports "one
  finding" and that is true of the 82 stage names both discs share, which is
  what it compares. The same string sits in `s07br`, one of the 13
  Integral-only names, where nothing was ever going to look for it. Neither the
  tool nor the three documents quoting it said so. A tool that pairs two things
  can only see their intersection, and that boundary belongs in the write-up
  beside the count.
- **The user's decision is the one worth recording.** USA is inconsistent here:
  the same message reaches the same actor down two branches and only one was
  translated. "Verbatim USA text, placed where USA places it" read literally
  means shipping that inconsistency. Asked, and the answer was to port all five
  sites — the rule forbids inventing text, not fixing a donor's oversight with
  the donor's own words. Worth remembering the next time the rule and the
  outcome point in different directions: ask, and say which way each points.
- **The trap in a length-preserving edit is where the padding goes.** After the
  terminator it is dead bytes; before it, it is drawn — and jimaku centres on
  the width it measures, so the line would drift off centre with nothing in the
  bytes to suggest why. `selftest.py` guards it, and the guard was proved by
  mutation, as §13 requires: four mutations, four failures.

### The same day: the three sweeps that were owed, and one input that is wrong

The housekeeping was done first (the four unlock aids deleted, the flags back to
`false`, the disjoint VR pair finally deployed, the branch committed), and then
the three items §5 filed under "to investigate" were all run. Two closed
cleanly; the third found something and then taught the method a lesson.

- **The Integral-only stages (`--integral-only`).** All 13 pair onto the USA
  stage they are a variant of, and across all 13 on both discs there is
  **exactly one** Japanese string whose base-stage owner has English:
  the `s07br` copy `en_pad2` had just ported. So the hole in the sweep's
  universe was worth closing and was empty. That is the good outcome, and it is
  only knowable by looking.
- **The census (`--census`).** All **1,360** Japanese GCL strings on each disc
  now fall in one of three explained buckets with **0 unaccounted**, and the
  buckets are asserted to sum to the total, so the tool cannot report a clean
  result by dropping a string. It exits non-zero if the last bucket is ever not
  0. This replaces "about 160 remain and need verification" with a number:
  none.
- **English against English (`--diff-english`), and the fourth spelling.** The
  sweep §5.14 asked for found the `abst` location table has **four** differences
  from USA's, where three documents listed three. `Cmnd rm` against USA's
  `Cmnd room` had never been written down. The residue really is that small: 15
  replace hunks over 82 stages, 8 with readable text, and after triage one
  family.
- **And the input is wrong for that question.** Run against the VR disc, a
  per-owner fuzzy match reported `FAMAS` against USA's `FA-MAS` in the mission
  titles - which the port had already fixed, because it takes USA's window text
  verbatim: the deployed PPF holds 142 `FA-MAS` and no `FAMAS`. `mainsweep.py`
  reads **retail** on purpose, so a Japanese gap cannot hide behind a deployed
  patch. For English-against-English that discipline is exactly backwards: the
  port's own replacements are what must be subtracted, so the question belongs
  on the **deployed** bytes. It is safe today only because the one family it
  finds sits in records no patch rewrites - which is a fact that was checked,
  not a property of the tool. **The rule: match the input to the question, and
  say which one the tool reads.**

USA's VR disc also carries five languages, so any diff there must take only the
English arm of a language branch (`lang in (None, ENGLISH)`); without it the
alignment collapses and the output is 548 hunks of nothing.

### And then the location names were decided

The four `abst` spellings the sweep turned up were put to the user the same
evening and the answer was **use USA's**. That makes two applications of
amendment 4b in two days, and this one had teeth the `SCARF` case did not: the
text grows, so a container had to move.

- **The block carries two derived lengths, not one.** A COMMAND's BE16 size is
  the obvious one; the u8 at `start+5` that `option_starts` reads to reach the
  option list is the one that would have been missed - `0xAD` against USA's
  `0xB9`, exactly the 12 bytes of growth. Patching the four records and
  re-stamping only the BE16 would have produced a block that disagreed with
  itself. Taking USA's **whole command** keeps both in step by construction, and
  is also the most literal reading of the rule.
- **The names are font codes, not ASCII.** `0x80xx` Latin, `0x9001` space. An
  ASCII search of the PPFs for `Tank Hangar` finds nothing, which briefly looked
  like evidence the port already owned them. `rendertext.py` exists for exactly
  this reason and the same trap is recorded in §14.
- **The constant was run both ways.** Off: 104,600-byte chunk, list equals
  Integral's own, 0 records differing. On: 104,612, equals USA's, 4 differing.
  A measurement of the cost rather than a claim about it - and the 12-byte delta
  is the arithmetic checking itself.
- **The verifier catches the offset byte without testing it.** `location_block`
  finds the command through `option_starts`, which reads that u8 and requires the
  empty option list it points at, so a wrong value fails to find the block at all
  instead of passing quietly. The best checks are the ones a wrong answer cannot
  route around.

And the input question the user pushed back on - whether the English-against-
English sweep needed a deployed-bytes reconstruction - resolved the other way
once it was thought through. The builders already construct the ported stage;
reconstructing it from PPF records would re-derive that by the hardest route and
need extending for every relocation. The authority for owned bytes is the
family's own verifier, the sweep's authority stops at the boundary, and the `!!`
flag marks where. §5.14 step 3 carries the table.

## 16. The 2026-09-09 pass: the file nobody had opened

A question from outside the project - is there an Integral-exclusive Japanese
developer-commentary codec channel? - turned out to have an answer no tool here
could reach. There is, it is **6.5 MB**, and the reason it was invisible is
structural rather than careless.

- **Every sweep read one file.** `mainsweep.py`, `vr_sweep.py`, `jpsweep.py`,
  `audit_text.py` and the day-old `jpremain.py` all walk `STAGE.DIR` and the
  executables. A disc has nine files. Codec dialogue lives in `RADIO.DAT`,
  loaded by sector out of `menu/radiomes.c`, so no GCL walker could ever have
  seen a word of it - and four documents said the port was complete without
  naming the file their claim was about. `discaudit.py` now audits all nine.
- **The diagnostic was a size delta, not a sweep.** Integral's `RADIO.DAT` is
  6.3x USA's. That single number is what located the commentary; the same
  measure clears `BRF.DAT` (381 KB of English on both) and `FACE.DAT`
  (identical), which had been assumed rather than checked.
- **A correct ratio described the wrong thing.** 964 KB of Japanese against
  1,146 KB of English is 42%, exactly what a faithful translation of the same
  script gives - so the totals said "paired subtitle track, nothing extra".
  Mapping *where* each language sat, window by window, is what exposed a 6.5 MB
  block containing no English at all. Aggregate ratios can be right and still
  answer a different question.
- **The port's scope did not change.** USA never shipped the commentary, so
  there is no English to copy and the standing rule leaves it alone. What
  changed is what the documents may claim: "nothing with a USA counterpart is
  still Japanese" is true of the text this port covers, and was being read as
  true of the disc. `COVERAGE.md` now states both sentences.
- **The general lesson, and it is the same one as §13's.** When a claim of
  completeness is made, say what it ranges over. Every sweep here answered its
  question correctly inside a universe none of them named - shared stage names
  for `mainsweep`, one archive for all of them - and each time the gap was found
  by someone asking about a thing outside it rather than by the tools.

## 17. The 2026-09-09 pass: the untranslated Japanese, dumped — and what to do next

### DONE - see §18

The glyph identification is finished: **all 1,200 shapes are named and 100.00%
of the Japanese decodes**. Two things this section said are wrong and are
corrected in §18, because they matter more than the fact that the job is done:

* **"1,813 glyph shapes"** was an artefact. The real count is **1,200**; the
  extra 613 came from a fragment map that was wrong for 93% of strings.
* **"Two rules give 100.000% (94,246 of 94,246 strings)"** measured that every
  string got *an* answer, which the rule guarantees. It was not a check. The
  check is how many distinct 12x12 bitmaps the text lookups produce: 91,834
  then, 1,200 now. `radiomap.py` prints it.

The image budget this section warns about also turned out to be the wrong
worry. The whole pass cost eleven images, because the glyphs were read against
decoded sentences (`glyphsheets.py` writes them beside each page) rather than
by squinting harder at 144 pixels.

### The scope, which is the user's decision and narrows this a lot

**Only Japanese that MGS1 USA has no counterpart for.** Asked and answered
2026-09-09. `RADIO.DAT` holds two halves: a story-codec region where the
Japanese is a *subtitle track* for conversations USA ships in English, and a
commentary region with no English anywhere in it. The first is covered by USA
and out of scope; only the second needs anything.

| | rows (disc 1) | kana/kanji | |
|---|---:|---:|---|
| story codec `0x0`-`0x042C54C` | 16,869 | 282,280 | out of scope |
| **commentary `0x042C54C`-`0x0AAC050`** | **77,361** | **1,369,719** | in scope |

`jplist.py` already applied that test to `DEMO.DAT`, `VOX.DAT`, `BRF.DAT` and
`FACE.DAT` by subtracting anything that also appears in USA's copy of the same
file - which is what empties the last two entirely. `RADIO.DAT` slipped through
it, because USA's codec text is plain ASCII and there were no font-code runs to
subtract against. `dumpjp.py --scope unported` is where the region split lives.

### What was produced

`py dumpjp.py` writes **156,379 lines over 5,589 pages**, every line rendered
from the game's own glyph bitmaps, so the images are exact by construction:

    work/jpdump/disc1_RADIO_DAT.pdf   77,361 lines  2,763 pages   the commentary
    work/jpdump/disc1_DEMO_DAT.pdf       576 lines     21 pages
    work/jpdump/disc1_VOX_DAT.pdf        338 lines     13 pages
    work/jpdump/disc1_STAGE_DIR.pdf       98 lines      4 pages
    work/jpdump/disc2_*.pdf                            (RADIO is a duplicate)
    work/jpdump/index.tsv            156,379 rows

`index.tsv` locates every line: disc, source, fragment base, byte offset, page
and row, the text decode so far, and the raw codes.

Verified without eyes, because the image budget was gone by then: 4,000 sampled
lines render with none blank or sparse, and every glyph cell of a line matches
the font byte for byte.

### Bank 1's table, and reading the parser instead of guessing

`0x9A01 + i` indexes a `.gcx` script's own font blob; `RADIO.DAT` carries one
per fragment, and `menu/radiomes.c`'s
`menu_radio_codec_task_proc_80047AA0()` gives the address outright:

    radioDatIter   = fragment + 8
    fontAddrOffset = BE16(radioDatIter + 1) + 1
    font_set_font_addr(1, radioDatIter + fontAddrOffset)

so `base = fragment + 9 + BE16(fragment + 9)`. Fragment 0 yields `0x1B1`, the
value proved independently by finding the single place in 11 MB where 本 is
immediately followed by 出 - they sit at adjacent indices in that conversation.

**Fragments are sector-aligned but MULTI-sector** (`size = (radioCode /
0x1000000) * 2048`), which is the fact that made attribution hard: a
mid-fragment sector can produce a sane-looking base by accident, and a string's
true fragment can be tens of KB behind it. Two rules give **100.000%** (94,246
of 94,246 strings, 77,361 of 77,361 in the commentary): a candidate must contain
a string in its text region `[frag+8, base)`, and a string belongs to the
nearest candidate behind it that covers it, searching **128 KB** back.

Five attempts preceded that and are worth knowing so they are not repeated:
first-plausible-run-after-the-text (99.4%), coordinate ascent on
repeated-sentence agreement (61.5%), greedy non-overlapping fit (49.9%), a
sequential fragment walk (78.1%), the same walk with a stricter accept test
(16.3%). The lesson is the ordinary one: the first method was the best and was
abandoned over a 0.6% residue instead of being repaired, and reading the
parser - which took one grep - beat all five.

### Dead ends, measured, so nobody spends a day on them

Template matching cannot identify these glyphs. Two references were tried
against the 238 hand-transcribed kanji, which is a real labelled test set from
the same font:

| reference | top-1 |
|---|---:|
| MS Gothic / Meiryo, 96px rasterised then area-averaged to 12x12, ZNCC + ink gate | 47% |
| **Shinonome 12-dot** (MIT, native JIS X 0208 at exactly 12 dots, 6,879 glyphs) | **0% exact, 5.9% fuzzy** |

Shinonome was the right idea - a native 12-dot bitmap font is the
apples-to-apples comparison - and it failed because **Konami drew their own
12x12 design**. There is no font to look these up in. An OCR engine is also the
wrong shape: `manga-ocr` and Tesseract recognise text *lines* at real
resolution, and the input here is 144 pixels, where the glyph *is* a specific
bitmap design rather than a picture of a character.

## 18. The 2026-09-10 pass: the commentary is readable, and the map it rested on was wrong

**All 1,200 bank-1 glyph shapes are identified: 100.00% of the glyph codes in
`japanese-inventory.tsv` now decode to text.** Read that qualifier - it is
load-bearing, and "Where the number stops" below says exactly what it excludes.
The developer commentary §16 found is no longer a stack of pictures; it is
156,379 lines of readable Japanese in `work/jpdump/disc1_RADIO_DAT.txt` (plain
text, conversations separated by a blank line) and `work/jpdump/index.tsv`
(one row per line, with offsets and raw codes). The channel says what it is in
its own words:

> この周波数では「メタルギアソリッド」制作スタッフによる制作過程での裏話などをお伝えします。
> なお、この周波数のみ字幕言語設定が英語の場合でも日本語で表示されます。

That second sentence is the game telling you §16's conclusion directly: this
frequency stays Japanese even with the language set to English. There is no
English to port and the standing no-translation rule leaves it alone.

### The thing to learn from this pass

§17 set up the glyph work on a fragment map that was **wrong for 93% of
strings**, and said so in the language of certainty: "Two rules give 100.000%
(94,246 of 94,246 strings)". That number counted strings that got *an* answer.
It could not have counted anything else — the rule always terminates.

One cheap measure exposes it. Bank-1 codes index a font, so resolving them
yields 12x12 bitmaps; **count the distinct ones.** A Japanese font has a couple
of thousand. The old map produced **91,834**, and only 9.8% of them had the
blank twelfth row that every real glyph in this font has. The current map
produces **1,200**, all of them with it.

So: when a walk over data reports a percentage, ask what the percentage would
look like if the walk were wrong. If the answer is "the same", it is not a
check. `radiomap.py` prints the distinct-bitmap count for exactly this reason —
that is the number to look at, not the share of strings attributed.

### What the map is now (`radiomap.py`)

Two things fixed it, both from reading the game rather than the bytes.

* **Parse the script.** A `RADIO.DAT` fragment's script is not GCL; it is a
  record list of its own (`menu_gcl_exec_block_800478B4`, `menu/radiomes.c`):
  `FF <code> <BE16 size> <payload>`, next record at `+size+2`, a 0 byte ends it,
  and the font blob sits at `script + totalSize + 1`. Walking those records is
  self-checking — a sector that is not a fragment desynchronises within a record
  or two. 597 of 5,468 sectors survive, and the first ends at exactly `0x1B1`,
  the value §17 had proved independently.
* **Get an answer key.** Fragments are named by "radio codes", unpacked by
  `sub_80047D70`: `startSector = code & 0xFFFF`, Japanese `(code >> 24)` sectors
  there, English `((code >> 16) & 0xFF)` sectors immediately after. The codes are
  arguments to the GCL `radio` command (id `0x24E1`, `GV_StrCode("radio")`,
  `game/script.c`) in the stage scripts; 192 are recoverable. **All 192 Japanese
  starts and all 192 English starts are among the 597 the parse found, and no
  declared extent is overrun.** That is what makes the parse trustworthy instead
  of merely plausible.

A nested `IF`/`SWITCH` body has the same header as a fragment, so one that lands
8 bytes after a sector boundary parses like one. Dropping every candidate inside
another candidate's script region removes all 28 such cases the radio codes prove
false and none of the 384 they prove true, leaving **553 fragments**: 26 of
94,246 strings unattributed, zero glyph over-runs.

Note the layout this exposes: **Integral's `RADIO.DAT` stores each conversation
twice, Japanese then English, adjacent**, and one runtime flag picks the half.

### How the 1,200 were named, and how good it is

Not by looking harder at 144 pixels. `glyphsheets.py` now writes, beside each
page of glyphs, a `.txt` of **real lines from the game with the glyph marked and
everything already readable spelled out**. At 12x12 線/緑, 鏡/鎌 and 間/問 are
the same picture; in a sentence they are not. The bitmap says which characters
are possible and the sentence says which one it is. Every case where the two
disagreed, the sentence was right: 望 was 量 (大量に分泌), 屈 was 肩 (肩もみ),
惜 was 情 (情報), 問 was 聞 (直接聞くさ), 昔 was 替 (すり替えた).

Then `glyphreview.py --verify` prints **one full decoded sentence per glyph, all
1,200**, and they get read. That is what catches the rest: 黙 and 弄 had been
swapped ("なぜ今まで黙っていた" / "…のように弄ばれつづけた"), and two more fell
to comparing a bitmap against its near-twin — 完 was 璧 (identical to 壁 in its
top three rows, with 玉 below where 壁 has 土) and 朴 was 林.

**Measured, not asserted:** 78 shapes had already been identified from the stage
archives, and `glyphsheets.py` puts them on the sheets unmarked with the answers
in `work/glyph-answers.tsv`. **78 of 78 correct.** Two of those 78 were scored
wrong at first and turned out to be errors in the *key* (below), which is the
only reason to trust the other 76.

The whole pass cost **11 images**: eight sheet pages, two magnified sheets for
the name kanji that no sentence can check, and one single glyph.

### Five characters in the existing tables were wrong

The complete decode makes bank-0 mistakes visible, because a wrong bank-0
character now sits in an otherwise readable sentence.

| where | was | is | the sentence that settles it |
|---|---|---|---|
| `GLYPH_90[0x9078]` | 句 | **匂** | 硝煙の匂いがなつかしいぜ |
| `GLYPH_90[0x90A5]` | 端 | **奪** | 力を奪う事ができる / メリルに服を奪われて |
| `GLYPH_90[0x90D0]` | 継 | **繊** | 筋繊維を刺激してみたの / 大胆にして繊細 |
| `BANK1[('roll',0x9A05)]` | 五 | **六** | レイブンは六人もの人間を運んだ (against 四人運び) / 第六感 |
| `BANK1[('rank',0x9A0D)]` | 液 | **清** | ウイルス兵器だ。必ず血清がある |

All five are fixed in `jptext.py`. The 五/六 one is worth dwelling on: it was
"proved" by 二万五千 in the staff roll, and the roll gives no way to tell 五 from
六 at 12 pixels. `RADIO.DAT` does, twice.

### An invariant worth keeping

**Bank 0 and bank 1 never share a bitmap, and — once those five are corrected —
never share a character either.** All 1,200 bank-1 shapes were compared against
every glyph in `font.res`: not one matches. So a character bank 0 already has
(the 255 kanji of `GLYPH_90`, the kana, the punctuation) cannot be the answer to
a bank-1 glyph, and `glyphfill.py` warns when an assignment breaks that. Every
warning it raised in this pass was a real error — three in `GLYPH_90`, none in
the new work.

### Every conversation already has an English slot (asked 2026-09-10)

Asked whether the process could be reversed - English written where the
Japanese is. The engine already has the mechanism, and the commentary already
has the space. `sub_80047D70` picks a fragment half by the language flag:

    startSector = code & 0xFFFF
    Japanese    = (code >> 24) sectors there
    English     = ((code >> 16) & 0xFF) sectors immediately after

Measured on disc 1, over the fragments the radio codes name:

| | Japanese half | English half |
|---|---|---|
| story codec | 28.7% glyph codes | **1.6% glyph codes, 73.9% ASCII** - `"Be careful, Snake. That air lock is set..."` |
| commentary | 35.6% glyph codes | **35.6% glyph codes** - a copy of the Japanese |

So the story codec's English half is plain ASCII, and **the commentary's
English half is a duplicate of the Japanese** - which is exactly what the
channel says about itself: 「なお、この周波数のみ字幕言語設定が英語の場合でも日本語で表示されます。」
None of the 192 recovered codes declares an empty English extent.

Writing ASCII into the English half therefore shows in English mode and leaves
the Japanese untouched in Japanese mode - no relocation, no new allocation.
The budget is comfortable: ASCII is one byte per character against two for
glyph codes, and the English half needs no font blob (1.49 MB of the
commentary's 6.81 MB is font).

What would still have to be built: a writer that keeps the record's BE16 size,
the script's BE16 total and the fragment's declared sector count in agreement,
and that respects the 240px line width (README, "font render limits"). Then
the usual on-screen check.

**None of this is authorised.** Filling those slots means writing English that
Konami never shipped, which is translation - rule 1, verbatim: *"I'm not
authorizing you to translate (yet) anything only in english with no port should
be left in Japanese."* The mechanism is recorded here so the answer exists; the
decision is the user's.

### Where the number stops, measured the day it was claimed

The 100% is over `japanese-inventory.tsv`, and **the inventory is not the
file**. `jplist`'s scanner walks for runs of glyph codes and **ends a run at
any code it does not recognise**, so text after such a code starts a new row
and the code itself is dropped. Two ranges it does not recognise carry real
text:

* **`0x91xx`** - bank 0's second kanji page. `GLYPH_90` covers `0x90xx` and
  only four characters of `0x91xx` were ever identified, so the scanner treats
  the rest as "not Japanese".
* **`0x97xx`** - bank 1 above index 255. The README says bank-1 codes "never
  leave `0x9601`-`0x96FF`"; that is wrong. The commentary's font blobs hold up
  to **441** glyphs and the codes run straight on into `0x97xx`.

The symptom is visible in the dump: 「無限バンダナは制作チーム内では昆」 - the
布 of 昆布 is `0x9106`, the run stops on it, and the next row begins after it.

Measured over the commentary region, counting only codes that resolve to a
glyph passing the blank-twelfth-row test:

| | glyph instances |
|---|---:|
| captured by the inventory (all decode) | 1,729,477 |
| **skipped by the inventory** | **301,473** (14.8%) |
|  of those, decodable with today's tables | 287,601 (95.4%) |
|  needing new identifications | 13,872 (0.68% of the commentary) |

So the shape table holds up well on the text it never saw - 640 of the 653
distinct bank-1 shapes in the skipped bytes are already named. What is missing
is small and specific: **13 bank-1 shapes** and **23 bank-0 codes**, the
commonest being `0x9101` (2,538 uses), `0x8F65` (2,198), `0x9110` (1,754) and
`0x910C` (1,712).

**The next job, in order:** extract text from the parsed `TALK` records instead
of scanning bytes - `radiomap.walk_block` already gives the records, and
recursing into `IF`/`SWITCH` bodies is the missing piece - then name those 36
characters. That takes the commentary from 85.2% of its glyphs to all of them.

And note what this is an instance of. §16 said: *when a claim of completeness
is made, say what it ranges over.* The claim above ranged over the inventory
and was written as if it ranged over the disc, one section after that lesson
was recorded. The habit does not install itself.

### What is left

* **One glyph, two uses.** `('title', 0x9A27)` in 「⟪9A27⟫のラブソング」, a
  demo-theater label in the stage archive. Its bitmap is mostly mid-tone rather
  than stroke-and-background, so it may not be a kanji at all; it was
  unidentified before this pass too. 2 uses out of 4.2 million.
* ~~**The VR disc's stage text is not in the dump.**~~ **Fixed §20.**
  `dumpjp` looped over disc indices 0 and 1, so the VR archive's 31 `vr`
  rows were skipped entirely. The three discs are keyed by name now and the
  export is 68,242 lines. It was *not* small: it was a whole disc, and the
  note above talked itself out of checking.
* **`dumpjp.stage_blobs` assumes one font blob per stage.** `roll` and `abst`
  have two. It takes the first, which is right for everything checked so far.
* **Nothing here changes the port's scope.** USA never shipped the commentary,
  so there is no English to copy. What changed is that the Japanese can now be
  read, by anyone, as text.

## 19. The 2026-09-10 pass: the export finished, and the scanner retired

**The unportable Japanese is exported in full.** 68,242 lines, 3,923,944
kana/kanji, **zero** unresolved glyph codes. (The figures here were 
68,211 / 3,923,661 until §20 added the VR disc.)

    work/jpdump/disc1_RADIO_DAT.txt   the developer commentary, plain text
    work/jpdump/disc<n>_<source>.txt  DEMO.DAT, VOX.DAT, STAGE.DIR likewise
    work/jpdump/index.tsv             one row per line, with offsets and codes
    work/jpdump/*.pdf                 the same lines drawn from the game's font

### What was still wrong when §18 was written

§18 said 100% and meant "100% of `japanese-inventory.tsv`". Chasing that
qualifier turned up two real defects, and the second one had been quietly
corrupting text since the beginning.

**1. The inventory is not the file.** `jplist`'s scanner ends a run at any code
it does not recognise, dropping the code and starting a new row after it. It
did not recognise `0x91xx` (bank 0's second kanji page) or `0x97xx` (bank 1
above index 255), and both carry real text - so the inventory held **85.2%** of
the commentary's glyph instances. The fix is not a better scanner:
`radiotext.py` walks the records the game walks (`menu_gcl_exec_block_800478B4`
and the `TALK`/`IF`/`SWITCH`/`RANDSWITCH` payloads), which is where the text
provably is. It finds **33,277 subtitles and 2,257,918 glyph instances** in the
commentary against the inventory's 1,729,477, reaches all **125** commentary
fragments where the inventory reached 124, and has more text than the inventory
in **every single fragment** - it never trades one gap for another.

**2. The bank-1 index was off by one from `0x97xx` on.** Every tool here used
`code - 0x9601`. The game uses `zen_index` (`font/font.c`, via
`rendertext.zen_index`), which is `((code - 0x956B) - code/256) | 0x1000` - the
index drops one per 256-page, because each page's `00` entry is not a glyph. So
`code - 0x9601` is exactly right inside `0x96xx` and one too high from `0x97xx`
onward, naming every glyph one position too far along.

The inventory only ever contained `0x96xx` codes, so **the error was invisible
until the record walk started reading `0x97xx`** - 58,704 codes in the
commentary, every one of them a wrong kanji. It showed up as one sentence
rendering differently in different fragments:
「プログラムの記述が楽になる効果」 in one, 「述□が楽になる効果」 in another. `radiomap.bank1_index`
is now the single copy of that rule and every tool calls it.

The lesson is the cheap one again: the two renderings could not both be right,
and that was visible in the output long before it was explained. Read the
output.

### The 24 characters that were hiding behind the scanner

The text the inventory dropped needed 11 more bank-0 codes and 13 more bank-1
shapes. Every one is settled by a sentence, not by a second look at 144 pixels:

| | | |
|---|---|---|
| `0x9101` 気 無邪気 | `0x9102` 絶 気絶している | `0x9103` 安 安田有希子 |
| `0x9104` 属 付属機関 | `0x9106` 布 昆布 | `0x9107` 完 完成した |
| `0x910C` 自 建物自体 | `0x910D` 拳 中国拳法 | `0x910E` 銃 銃口 / 銃身 / 銃弾 |
| `0x9110` 初 業界初 / 当初 | `0x900D` 『 pairs with `0x900E` 』 | 貢 + 献 作品総体に対し貢献する |
| 師 ドット絵師 | 泣 怒ったり泣いたり | 委 想像力に委ねた |
| 梯 梯子昇降 | 即 即座に当たる | 伴 それに伴うカメラ |
| 痢 下痢モーション | 又 又、後半の | 涙 （涙） |
| ＊ and ＄ - ○＃％＆＊＄! , a censored expletive | | |

`bank1-glyphs.tsv` now holds **1,213** shapes and `GLYPH_91` fourteen codes.

### What is left, exactly

* **Nothing.** The last glyph, `('title', 0x9A27)`, is **蒼** - see below.
  1,214 bank-1 shapes, zero unresolved codes in the whole export.
* **Two `IF` records fail to parse**, both in the story-codec region, which is
  out of scope (USA ships that dialogue in English). The commentary walk is
  clean.
* **The story codec is not exported.** By design - §17's scope decision - but
  note the record walk only reaches 43 of its 425 fragments, so anyone who
  wants it should expect to work on the walk first.

### The last glyph: 蒼, and why the disc could not name it

`('title', 0x9A27)` resisted every method here, and the reason is instructive:
**there was nothing on the disc to check it against.** The bitmap occurs
exactly once per disc - index 38, the last glyph of the `title` blob - and
appears in no other stage on disc 1, disc 2 or the VR disc, and in none of
`RADIO.DAT`'s 1.4 MB of font blobs. Its one string, 「⟪9A27⟫のラブソング」,
sits orphaned among the memory-card prompts. Context is what settled the other
1,213; here there was none to have.

It came from outside: TCRF's *Metal Gear Solid (PlayStation)* page documents
the Japanese DEMO THEATER, whose four rolls are titled 蒼のラブソング,
蒼色の青春, 紅のラブソング and 紅色の青春. Integral replaced all four with
メリル / オタコン / （赤忍者）メリル / （赤忍者）オタコン - and the disc agrees
exactly: searching both main archives for the byte sequence のラブソング finds
**one** hit each, the leftover ROLL A title. The other three went with their
strings, which is why 蒼's glyph survives with no companion characters.

The bitmap decomposes as 艹 over 倉 (`g647`), which is 蒼. Note the honest
weight of that last check on its own: at 12x12 a shifted 倉 agrees with it on
85% of pixels and an unshifted one on 84.7%, so the pixel test decides nothing.
What decides it is the external source naming the exact string plus the disc
holding exactly that string, once, orphaned.

*A method note.* This is the one character out of 1,214 that no amount of
reading the disc could settle, and the lesson is not that the method failed -
it is that a cross-reference is the whole method, and when a glyph has exactly
one use anywhere, there is nothing to cross-reference. Recognising that early
is worth more than another pass over the pixels.

### What is now believed with what evidence

| claim | how it is checked |
|---|---|
| the fragment map is right | all 192 JP + 192 EN radio-code starts parse; no declared extent overrun; 1,200 distinct bitmaps from the inventory's codes, 100% with the blank twelfth row. **Those are aggregates and cannot see one fragment slip** - `radiotext.py --check` is the per-fragment guard, and `--selftest` proves it catches a slip (§21) |
| the text extraction is complete | more text than the inventory in *every* commentary fragment, all 125 reached, 0 unresolved codes |
| the glyph table is right | 78/78 on the labelled holdout; every one of 1,200 read back against a full sentence; the 13 new ones each settled by a sentence |
| the bank-1 index is right | it is `zen_index`, from the game; and the sentence that used to render two ways now renders one way everywhere |

## 20. The VR disc, and no game data in the repository

Two small things, both from the same question: is what is committed actually
what it says it is?

### The export was missing a disc

`disc1_RADIO_DAT.txt` is 97% of the export, which is close enough to all of it
to stop looking - and stopping there would have been wrong. `dumpjp.main`
looped `for disc_ix in (0, 1)`, so the **VR disc was never dumped at all**: 31
lines of it, sitting in `japanese-inventory.tsv` the whole time under a `vr`
key nothing consumed. §19 noted the VR disc had no `RADIO.DAT` and moved on
without noticing that it does have a stage archive.

The fix is that the three discs are now three names, not two indices:
`STAGE_DIR = {disc1, disc2, vr}` maps each to its archive, `collect(disc)`
takes the same key the inventory rows carry, and the `RADIO.DAT` half is
skipped for `vr`, which genuinely has none. Output files are named by that key
too, so the third is `vr_STAGE_DIR.txt` rather than a `disc3_` that would be
wrong. The export is 68,242 lines now; it was 68,211.

*Worth naming the shape of this one.* Every check in §18 and §19 was a check
on **content** - do the glyphs resolve, does the text match the records, does
one sentence render the same way twice - and all of them passed on a set that
was silently missing a member. A completeness check has to enumerate the
inputs, not audit the outputs. The inventory had a `vr` row all along; nothing
compared the set of discs in it against the set the dumper walked.

### No game data in the repository

`CREDITS.md` says "No game data is in this repository." That had stopped being
true, in three places, and all three were added by this work:

| what | why it counted | what now |
|---|---|---|
| `reference/keyconfig_*.jpg`, 6 files, 1.46 MB | photographs of both games running | deleted; `README.md` says how to reproduce them, and the label mapping they settled stays |
| `keyconfig-textures.png`, 37 KB | eight of the game's own textures, rendered side by side | deleted, same |
| `bank1-glyphs.tsv`, 104 KB | its `shape_hex` column was 1,214 raw 12x12 font bitmaps - the Japanese font itself, in hex | `shape_id`: a 64-bit digest of each bitmap (`jptext.shape_key`) |

The digest is the interesting one, because it costs almost nothing. Lookup
hashes the bitmap the game hands it and reads the table, so every decode works
exactly as before - the round-trip is byte-identical and the 78-answer holdout
still scores 78/78. What it can no longer do is *render* a glyph from the
committed copy, which was a real debugging aid (it is how the 完/璧 and
朴/林 misreads were caught). That capability stays available where the data
legitimately is: `work/glyphs-to-identify.tsv` keeps `shape_hex`, and
`glyphreview.py` reads that one. `jptext.load_shape_table` accepts either
spelling, so the two are interchangeable for lookup.

`glyphfill.py --publish` is the step that strips the bitmaps out. It exists so
the next transcription pass cannot put them back by accident, and it refuses to
write if two shapes ever hash alike. `.gitignore` blocks images under
`tools/integral-english/`.

**What is deliberately kept:** short quotations of game text in the
documentation - the sentence a glyph was read against, the subtitle that
exposed the `0x97xx` index bug. Those are the evidence; a finding nobody can
check is not a finding. They come to a few thousand characters against the 3.9
million the export holds, and the export is written to `work/`, outside the
repository, where it stays.

### "Is that all of it?" - the two other ways the inventory under-reports

Asking whether `disc1_RADIO_DAT.txt` was the whole export turned up the VR
disc above. Chasing the same question through the remaining containers turned
up two more limits, neither of which costs the export anything, and both worth
knowing before anyone trusts `japanese-inventory.tsv` for something new.

**`BRF.DAT` and `FACE.DAT` are scanned and correctly produce nothing.** They
are image data. 56 runs in `BRF.DAT` match the font-code range by coincidence
and `looks_like_prose` rejects every one.

**`--min 6` drops short strings in raw files.** `jplist.runs_in` keeps a run
only if `core_count(run) >= minimum`, and `core_count` counts kana and kanji
only - the long-vowel mark, `。`, `、` and full-width symbols are excluded,
because those are exactly what makes binary noise look like prose. The
threshold is not optional: in a raw file any two bytes in `0x8140`-`0x9AFF`
decode as a font code, so without it the scan drowns. But it is blunt, and
short genuine strings fall under it. `セーブ中です。` is seven characters on
screen and **five** by `core_count` (`セ ブ 中 で す` - the `ー` and the `。` do not
count), so a min-6 scan does not see it.

This is a *second*, independent way the inventory under-reports, on top of the
scanner bug in §19 that ended runs at unrecognised codes. Another reason the
export stopped sourcing `RADIO.DAT` from it.

**Where that led, and why it does not change the export.** Rescanning the
executables at `--min 3` finds four strings that a min-6 scan misses -
セーブが / セーブ中です。 / ロードが / ロード中です。 at `0x2718`, `0x27BB`,
`0x27FF`, `0x285B`. They are **not on the retail discs**: those offsets are
zero in retail bytes on both discs. They appear only in the *deployed*
executable, and the patch that owns `0x2600`-`0x2A00` is our own
`INTEGRAL_disc<n>_en_savemsg.ppf` (531 EXE bytes). So the export, which reads
retail bytes, is not missing them.

**What it does raise is a port question, and it is open.** `en_savemsg`
relocates the save-message table into that free space, and Japanese strings
are sitting in the relocated copy. Either those slots have no USA counterpart,
in which case leaving them Japanese is correct under rule 1, or they were
missed. Deciding it means reading the relocated table against USA's, not
guessing from these four - and the `en_savemsg` area already has an
UNDETERMINED note against it (README, the MC RAM-patch collision). Filed here
so it is not lost; it is not part of the export and does not block it.

## 21. A regression guard on the fragment map, and two metrics that failed

`radiomap.py` prints two aggregates - distinct bitmaps produced and their
blank-twelfth-row rate - and they catch a map that is grossly wrong. They
caught the one that was (§18): 91,834 distinct bitmaps at a 9.8% blank rate.

**They cannot catch one fragment's base going bad.** A base wrong by a whole
number of glyphs still slices on glyph boundaries, so every bitmap it reads is
a real glyph with a real blank twelfth row. Valid bitmaps, wrong characters,
both aggregates unmoved against 125 fragments, and the output is fluent-looking
nonsense. Nothing committed would have said a word.

`py radiotext.py --check` closes that, and `--selftest` proves it does.

### Two metrics that looked right and were worthless

Recording these because both are the obvious thing to reach for, and the
second one cost real time.

**"What share of this fragment's bank-1 codes hit a *named* shape?"** This is
the check I proposed, and it does not work now the table is complete. Every
shape in every blob is named, so slipping a base one glyph just reads a
*different named shape*: the score moves from 100.00% to **99.89%**. It was
diagnostic during the identification pass, when the table was half empty. It
is saturated now, and a saturated metric is worse than none because it reads
like a pass.

**"What share of its characters are in the corpus top 100?"** Real text
over-samples common characters heavily, so a permuted mapping should flatten.
It does flatten - but there is no margin. **Bank 1 holds the rare kanji**;
bank 0 has the common ones. So bank-1 frequency is inherently flat and
fragment-specific. Legitimate fragments run down to **34.1%** and a slipped
base sits at about **35%**. Chasing the four lowest-scoring fragments to see
whether they were broken found them decoding as clean, ordinary commentary.

The general lesson: before trusting a metric, **slip a base on purpose and see
what it reads.** Both of these looked convincing until they were made to fail.

### What works: cross-fragment agreement

The commentary is duplicated across fragments, and every copy carries its own
font blob with its own codes - so the same sentence is encoded differently in
each and must still decode identically. That is the invariant that exposed the
`0x97xx` index bug in §19, and it does not care how rare a fragment's
vocabulary is.

**Only lines that contain a bank-1 code are scored**, because those are the
only lines a wrong base can change. This matters more than it sounds:
fragment `0x03F6800` has 23 lines and **two** that use bank 1, so scoring all
of its text dilutes a slip to 8.7% and it walks through any sane floor. On
bank-1 lines alone the same fragment is correctly reported as *too thin to
check* rather than passed.

Measured on both discs:

| | |
|---|---|
| fragments checked | 126 |
| no bank-1 line - nothing a base can break | 40 |
| too thin (<4 bank-1 lines) | 5 |
| worst legitimate agreement | **96.0%** |
| median | 100.0% |
| one base slipped by a single glyph | **0.0%** |

The default floor of 50% sits in the middle of that gap. A slip large enough
also makes the record walk itself throw, which `check` reports rather than
raising.

### The selftest, and why it is not optional

    py radiotext.py --selftest

It slips three fragments' bases by +1, -1 and +8 glyphs and requires `--check`
to name each one. **The first two versions of the check passed their baseline
and failed this**, which is the only reason they were caught: a guard nobody
has watched fail is not a guard.

Its victims are drawn from exactly the set `--check` claims to cover, so it
cannot pass by testing something the check never promised. Fragments with no
bank-1 line are reported separately rather than counted as passes - one of
them holds nothing but four copies of a leftover English developer warning,
and counting it would inflate the number that means something.

**What this does not check** is whether a shape is named *correctly* - that is
the 78-answer holdout in `glyphfill.py --score`. This checks the base.

## 22. The 2026-09-10 pass: the Redump images, and patched discs that build

The question was whether the Redump dumps of Integral work with these patches,
and whether a patched image can be built from **either** them or the
collection's embedded copies. Both answers are yes, and both were measured
rather than argued.

### The two sources are the same disc

Streaming all three Redump `.bin` files against the same discs inside
`windata/dlc/dlc_japan.bin`, sector by sector:

| | disc 1 | disc 2 | VR |
|---|---|---|---|
| Redump size | 719,667,312 | 745,788,624 | 481,969,488 |
| collection's copy | identical length | identical length | identical length |
| sectors that differ | 312 | 312 | 307 |
| where | `SLPM_862.47` | `SLPM_862.48` | `SLPM_862.49` |
| anywhere else | **none** | **none** | **none** |

1.9 GB across three discs, and the **only** bytes that differ are the
executable extents the collection zero-fills — exactly what `rawdisc.py` says
and nothing more. (312 of 313 sectors, not 313: one sector of the executable is
genuinely all zeros, so the hollow copy happens to equal it.) The 1024 bytes at
`0x9320` that a PPF3 block check carries are identical on all three.

**So the Redump set closes the last of §5.4's three prerequisites** — the one
that could not be closed from inside, because it is a question about a file
this project does not ship.

### It also supplies the executables the build asks for

`BUILDING.md` requires `int1.exe` and `int2.exe` as separately supplied inputs,
because extracting them from the collection yields zeros. Extracted from the
Redump images instead, both hash to
`4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f` — **the
exact hash the builder demands**. The VR disc's `SLPM_862.49` hashes to
`c370f8e41ec8fb78238bfe2ddbfc25a6d37ec8f0972c86ebfde075ecd4ee8dca`, which is
the hash `rebuild.py` already checks its **decomp-built** VR executable
against. So the decomp reproduces that executable byte for byte, and a real
retail dump says so independently. With the Redump set present the build has
no unsourced input left.

### `mkimage.py`

Everything else here emits PPFs and stops, because the collection applies them
itself. `mkimage.py` is the missing step. It takes a raw build's PPF folder and
writes a patched `MODE2/2352` image plus its `.cue`, from either source, and it
checks four things before it writes anything:

1. every PPF's block check equals the image's own bytes at `0x9320`;
2. no record reaches past the end of the image;
3. every touched sector verifies against **its own stored parity before
   patching** — a 280-byte sum over 2048 bytes, which is what actually proves
   the dump is the pressing the patches were computed against;
4. every touched sector verifies **again after patching**, against the parity
   the set's own `zz_ecc` PPF wrote.

Check 4 is why the set is all-or-nothing: a tail is computed from the final
payload of the whole set, so dropping one family leaves right data behind wrong
parity. `--allow-partial` skips it for bisecting and says so in the output.

**From the collection it requires `--exe` and refuses without it.** That is the
one asymmetry between the sources and it is not a formality: an image built
from the collection's copy without the retail executable put back is 641,024
bytes of zeros where the game's code belongs. Neither the collection nor this
repository can supply those bytes.

### Built, on the current patch set

`repro21raw` (32 PPFs — 12 per main disc, 8 VR, `en_pad2` included) applied to
all three Redump dumps:

| disc | PPFs | touched sectors | patch bytes | parity before | after |
|---|---:|---:|---:|---|---|
| 1 | 12 | 417 | 907,240 | all pass | all pass |
| 2 | 12 | 417 | 907,240 | all pass | all pass |
| VR | 8 | 2,003 | 4,058,372 | all pass | all pass |

Content-checked on disc 1 rather than trusting the counts: the executable now
holds `Cannot be used in`, `Anti-anxiety`, `Sniper rifle` and `HANDKER` (and no
longer `SCARF`), and `preope`, `brf`, `option` and `abst` point into DUMMY3M at
slots 0, 128, 384 and 462 — the documented four.

**And the two sources produce the same disc.** Building disc 1 from the Redump
dump and from the collection's copy with `int1.exe` supplied gives two files
with the same SHA-256,
`a51415b91c03465274795b5b010049918c1b630820823514947f491616ea85e1`
on `repro21raw` (and the same agreement on the older `repro14raw` set, at a
different hash). Which source you start from does not matter; only whether the
executable is accounted for. Getting there needed one length rule: the
container pads to a 2048-byte boundary between images, which is not a sector
boundary, so flooring the span to whole 2352-byte sectors is what reproduces
the Redump length exactly on all three discs.

### What testing the failure paths found

Both were found by running them, not by reading the code, which is the only
reason they are not still there:

- **A failed post-patch check used to leave the bad image on disk** - 719 MB
  that fails its own parity, under the name the good one would have had. Both
  parity checks now run in memory over the touched sectors alone (about a
  megabyte on a main disc, 4.7 MB on VR) and **nothing is written until both
  pass**; any failure mid-write unlinks the partial file.
- **A collection build pointed at a disc image is the realistic mistake**, and
  it is caught: its PPFs carry no block check (warned) and no `zz_ecc`, so all
  415 touched sectors fail the after-check and the run stops with the reason.
- **The block check discriminates all three discs** - disc 1, disc 2 and VR
  have different bytes at `0x9320`. Handing disc 2's image the disc-1 folder
  stops on the first PPF, before anything is read past the header.

### What this does and does not establish

It does **not** boot a disc. Every check here is static — parity, framing,
block checks, string content — and the raw variant's first run on real
hardware or a strict emulator is still the open item in §5.4. What it removes
is everything that stood *in front of* that test: there is now a command that
produces the image to test.

    py mkimage.py --redump "<disc 1>.bin" --ppfs <pkg>/mods/INTEGRAL/INTEGRAL/0 \
        --output "MGS Integral English (Disc 1).bin" --cue

### The method note, and it is §16's again

Two of §5.4's three blockers had been closed in code on the same evening the
paragraph naming them was written, and it sat there for three days reading like
open work. The section listing what remains is not evidence; `rebuild.py` is.
Before planning work off a paragraph in this file, read the code it describes.

## 23. The 2026-09-10 pass: the language default, offered rather than assumed

A raw disc has no ASI, so the one runtime behaviour a player would miss is
`[Game] EnglishText`. `mkimage.py` now asks whether to bake it in, and applies
it or not according to the answer.

### What the bit is, and what it is not

`GM_CONFIG_ENGLISH` (0x0100) in `GM_Configuration` (`linkvarbuf[2]`). Grepping
the decomp gives **exactly four** places that act on it:

| | |
|---|---|
| `radiomes.c:526` | picks the **English half** of a codec fragment - §18's mechanism |
| `radio.c:1320` | `NO RESPONSE` over its Japanese twin |
| `movie.c:54`, `jimctrl.c:390` | pick the movie / cutscene subtitle stream |

`opt.c` sets it and reflects it into the option row; `datasave.c` restores it
from the memory card. **Nothing else reads it.** The README used to list
`font_draw_string` as a fifth reader and that was wrong (`cfbc635`) - the
correction is load-bearing, because if font drawing tested the bit then the
menus this port wrote in place would depend on it. They do not: **every string
this port wrote is English whether the bit is set or clear.** What the bit
gates is *Integral's own* English.

So the honest description of the default is: English menus, Japanese story,
until the player visits Integral's OPTION screen - where the setting is
Integral's own and saves to the memory card.

### Where it is set, and why the patch fits in 72 bytes

`GCL_StartDaemon` runs once, from `Main()`, and its second call is
`GCL_InitVar` - which reads `GM_Configuration`, zeroes all of `linkvarbuf`,
and writes the value back. A store in **that call's delay slot** therefore
lands before `GCL_InitVar`'s body and is carried through it by the game's own
code. Once per boot, before anything reads it, and the option screen and
memory card still override it afterwards.

Three instructions have to be found room for in an 18-instruction function,
and they are paid for exactly:

| word | paid by |
|---|---|
| `sh $v1, off($v0)` | the `nop` in `jal GCL_InitVar`'s delay slot |
| `addiu $sp, $sp, 0x18` | the `nop` after `lw $ra` (a load-delay slot) |
| the third | turning the last call into a **tail call** - `GCL_ChangeSenerioCode` is a leaf ending in `jr $ra`, so jumping to it with `$ra` restored returns straight to `Main()` and the `jr $ra` word is freed |

18 instructions in, 18 out, same 72 bytes, same five calls in the same order.
Nothing relocates.

### There is no free space in that executable, and that was checked

The first plan was a stub in a zero run. Every zero run in the image turns out
to be live: the 4,203-byte one at `0x800AA095` holds `Hcount`, the 1,771-byte
tail holds `GM_StageName` - they are `.sdata`/`.sbss` inside the loaded image,
not padding. `__bss_obj` is at `0x800ABBB0`. And `GCL_ResetSystem`, the one
`/* do nothing */` function next door, is **called** from `0x8002AA68` - a scan
for every `jal`/`j`/pointer to it found one, against a control scan that found
two for `GCL_InitVar`. Fitting in place was not elegance; it was the only
option, and finding that out cost less than assuming it.

### Nothing is hardcoded

`langdefault.py` matches `GCL_StartDaemon` by its exact 18-word shape and
requires **exactly one** match; reads `linkvarbuf` out of `GCL_InitVar`'s own
`lui`/`addiu` pair, confirmed by the two `lh` at +2 and +4 that the C names
`GM_GameLevel` and `GM_Configuration`; and checks the tail-call target really
is a leaf before jumping to it. That is why it works unchanged on the VR
executable, where the function is at `0x8001FE10` and `linkvarbuf` is 0x23A0
lower - both derived, neither typed in:

    int1.exe   GCL_StartDaemon at 0x8001FCDC, GM_Configuration at 0x800B4D9C
    int2.exe   GCL_StartDaemon at 0x8001FCDC, GM_Configuration at 0x800B4D9C
    vrint.exe  GCL_StartDaemon at 0x8001FE10, GM_Configuration at 0x800B29FC

(`int1.exe` and `int2.exe` are byte-identical, so the two main discs take the
same patch at the same offset.)

### How it asks

`--english-default ask` is the default. On a terminal it explains what the bit
does - including that it does *not* affect this port's text - and takes y/n.
**Off a terminal it refuses** rather than choosing: a build script has to pass
`yes` or `no` explicitly. Declining is byte-exact: disc 1 built with
`--english-default no` reproduces `a51415b9…`, the same image as before this
feature existed.

### The one thing that needed care

The set's `zz_ecc` PPF computes each tail from the final payload of the whole
set - so adding 72 bytes to a sector invalidates the tail the set wrote for
it. `mkimage.py` recomputes the tail for the sectors the language patch
touches, and **only** those; everywhere else the set's own tail still governs,
and the post-patch parity check over every touched sector is what says so.
Measured: disc 1 goes from 417 touched sectors to 418, disc 2 the same, VR
2,003 to 2,004, and all of them verify.

### Tested

Seven tests in `selftest.py` (35 total now), over a synthetic executable so
they need no game data: same length, all five calls preserved in order, the
store lands on `GM_Configuration`, it follows `linkvarbuf` rather than
assuming it, the store is in the delay slot, and it refuses an unrecognised
function, a non-leaf tail-call target and two matches. Each was confirmed to
fail when the module is mutated - changing the bit value or turning the tail
call back into a `jal` both break it.

And the patch was read back out of a finished image: the disassembly of
`SLPM_862.47` inside `MGS Integral English (Disc 1).bin` shows
`addiu $v1, $zero, 0x100` / `sh $v1, 0x4d9c($v0)` / `j 0x8001fcb0` with
`--english-default yes`, and the retail `jr $ra` without it.

**Still not booted.** Same caveat as §22: this is static verification.

## 24. The 2026-09-10 pass: the raw disc booted, and the briefing is broken

The raw variant ran for the first time (§5.4). Everything checked so far is
right except the **briefing**, whose right column renders as vertical stripes
of sampled VRAM. This section is written while the fault is still open,
because the eliminations are worth more than the conclusion will be.

### FIXED, late 2026-09-10: one `nop`. Read this before the rest of §24

The fault was never the arithmetic. It was the **R3000 load delay**: the
instruction after a load still sees the register's *old* value, and the
port's eleven words read `a1` in the very slot after `lbu a1, 13(v0)`:

    lbu  a0, 29(v0)      v2
    lbu  a1, 13(v0)      v0
    subu v1, a0, a1      <- a1 is still the caller's poly index (9..24)

So `height` came out as `v2 - idx` - a hundred rows and more - and every
label was stretched down the column: vertical stripes of sampled VRAM.
Retail's eleven words never touch a register in the slot after loading it
(the compiler schedules for this), and neither does any other block the port
rewrote in this overlay. `hazards.py` now proves that on every build.

Every observation below falls out of it, with nothing left over:

| observation | why |
|---|---|
| the same bytes render cleanly on the Master Collection | its emulator does not model the load delay, so the arithmetic ran as written - the 26 shot pairs could never have shown it |
| SwanStation and hardware break | both model the delay |
| `height` alone: smears | `subu a0, a0, a1` right after `lbu a1`: height = v2 - idx |
| `above` alone: rows shifted | `andi a1, a1, 7` right after `lbu a1`: above = idx & 7, 0..7 by row |
| the POLY_FT4 code-byte guard made a diagonal fan | `lbu` then `andi` on the code byte - one more hazard |
| the stub running retail's own words: clean | retail's words have no hazard |
| the stub's restored X normalisation did not help | `lh a1, 8(v0)` then `sh a1, 0x18(v0)`: x2 took the row's top y |

The premise this section built on - that the routine "also draws rows that
are not textured labels" - is **false**. `b_select.c` decompiles
`brf_800C69B4`, and the register simulation over `brf_800C6E88` (its only
caller) lists sixteen call sites, every one with a poly index 9..24: the
sixteen `br_sNN` labels, all textured, all with valid UVs. The reverse
engineering §24 asked for was done and found nothing to fix.

The fix is in place, eleven words, no stub and no stage growth: `lbu a0`,
`lbu a1`, **`nop`**, then the same arithmetic and the four stores. The
overlay is retail's 127,702 bytes again. `brf_widen.py` `ROW_H_NEW` carries
the words and the explanation; `brf_build.py` asserts zero load-delay
hazards against retail before it writes the stage; `hazards.py` is the
scanner and `selftest.py` proves it catches exactly this pattern at exactly
this address. Scanned the same way the same evening: `en_items`,
`en_savemsg`, `vr_en_items`, `vr_en_savemsg`, the language default on both
executables, the VR MOVIE stub and the VR option call sites - **no other
hazard anywhere in the port**. (The scanner reports four "branch-slot" hits
inside the relocated string pools at `0x80011E00`-`0x80012200`; those are
text bytes, not code.)

**SEEN ON SCREEN 22:38 the same night.** Seven SwanStation shots of the
`repro32raw` disc 1 image (outline, member and detailed submenus, with
`infiltration method`, `person in charge of the operation` and `hostages`
highlighted, and EXIT) read against the 2026-09-02 MC set: label art at true
size, single- and two-line highlight boxes, the 16/26 and 20 row advances,
rules and horizontal connectors all match. The save on that disc has none of
the six flag-gated indented items earned (the user confirmed it), so the
L-connectors and the member block's 17-row branch (`FRAME_NEW`, `MEMBER_NEW`,
`DETAIL_NEW`) are still unseen on an accurate renderer; `hazards.py` clears
them and MC drew them right, but seeing them on the raw disc needs a save with
those briefings earned - `UnlockBriefing` is an ASI feature and does not
exist there.

**The lesson is new for this project.** The Master Collection is not only a
different renderer; it is a **lenient CPU**. Anything written by hand in
MIPS and verified only there can be wrong in exactly this way, which is why
the scan was run on every family and not only `brf`. And §16's rule applies
to the theory in the rest of this section: six formula guesses were made
against a routine whose arithmetic was right all along, and the one
sentence that would have ended it - "what does the instruction after the
load see?" - was never asked.

*The rest of §24 is the record of the bisect as it stood before the cause was
found. The eliminations were sound; the conclusions drawn from them ("both
halves are wrong", "reverse engineer the callers") were not.*

### What is established

| | |
|---|---|
| unpatched Integral and USA, SwanStation | **clean** |
| patched, `en_brf` removed (parity regenerated) | **clean**, Japanese |
| patched, `en_brf` present | **broken** |
| the same `en_brf` on the Master Collection | **clean** |
| `en_brf`, raw build vs collection build | **byte-identical**, 276,482 bytes, 0 differing offsets |

So `en_brf` is the fault; it is not raw-specific; and the collection build
carries the same bug and always has. The emulator is not at fault - the
settings are the accurate end of the scale (`GPU_Renderer = Software`,
`ResolutionScale 1`, no PGXP, no filtering, no widescreen hack) and retail
discs render correctly under them.

### The verification that could not have caught it

§4 records `en_brf` as verified by "26 shot pairs, 0.00% right-column diff".
That compared **Integral-on-MC against USA-on-MC**. Both sides were drawn by
the same emulator, so anything MC does differently from a PlayStation cancels
out of the difference exactly and is invisible to the method. The check
establishes that the port reproduces USA's layout *as MC executes it*; it
cannot distinguish that from reproducing it as hardware executes it.

That figure was quoted twice on 2026-09-10 as though it settled the question.
It does not, and the general form is worth keeping: **a differential test
against a reference rendered by the same suspect component proves only
agreement, never correctness.** §16's lesson again - say what the claim
ranges over.

### Three hypotheses tested and rejected

1. **The language default (§23).** Rejected: the briefing overlay reads
   `GM_Configuration` zero times, and an image built without the language
   patch is equally broken.
2. **`ufits` is wrong for 8bpp** (a page is 128 texels wide at 8bpp, not 256,
   and the guard uses a flat 255). Real bug in principle, not this one:
   every one of the 20 widened labels is 4bpp and every one fits, the
   tightest at 248 of 256.
3. **Move the relocated labels to VRAM rows 256..511**, which the whole stage
   leaves empty. **Strictly worse**: the relocated labels themselves render
   as garbage while the three that stay in place are fine. This code path
   cannot address the lower half of VRAM - the tpage field selects one
   256-row half and the briefing assumes the top one. `vfits` permits
   `py >= 256` and that permission is wrong here. Reverted; the comment in
   `brf_widen.py` now says so.

### What the current placement does, and what it does not explain

`busy()` models the `nd` payload's 51 textures and nothing else. USA's labels
are wider than Integral's - `br_s00` goes 13 units to 25 - so 17 of 20 cannot
stay put, and the search relocates them to **x 896..958, y 1..156**, a band
Integral's stage uses only at y 226-228 (CLUTs, which are avoided).

But the relocated labels *draw correctly* there. It is the right column that
does not. So this is not simply "the labels landed on something": their bytes
are intact and correctly addressed. Something the port changed is making the
**column** sample wrongly.

A scan for the runtime uploads that `brf_800CAC7C()` performs found nothing
in the stage - it pages content in from `BRF.DAT` by sector, so the data is
outside every payload this toolchain parses.

### RESOLVED TO ONE ROUTINE - read this part first

The bisect finished. **`ROW_H` is the fault**: 11 instructions at `0x800C69C8`,
inside `set_row_box(work, i, y, advance)` at `0x800C69B4`. Everything else in
`en_brf` - the texture swap, the VRAM placement, the quad widths, the xl
moves, the five block rewrites - is innocent.

| build (all disc 1, SwanStation software renderer) | briefing |
|---|---|
| retail, unpatched | clean |
| `en_brf` removed entirely | clean, Japanese |
| textures + VRAM placement only | clean English, badly squashed |
| + quad/xl/rule/anim/start-y/connectors (`INTEGRAL_BRF_NO_COUNTS=1`) | **clean English, correct sizes, row spacing wrong** |
| + counts, - the five block rewrites | striped |
| `ROW_H` alone | striped |
| full set | striped |

**`TEST - Disc 1 no counts.bin` is a good disc.** Correct English everywhere;
the only visible flaw is that `next-generation / special force unit` sits
cramped, because `ROW_H` - the thing that fixes row spacing - is off in it.
That build is `D:/mgsbuild/repro25nocounts`.

### What ROW_H does, and why both halves of it are wrong

Retail's eleven words set the row's box to `[y, y+13]` and normalise the
quad's X corners (left pair take x0, right pair take x3). The port replaced
them with:

    height = v2 - v0        (bytes at poly+0x1D and poly+0x0D)
    above  = v0 & 7
    box    = [y - above, y - above + height]

and, needing six words for that arithmetic in an eleven-word hole, **deleted
the four X-normalisation stores**.

Tested on screen, each term alone, through the stub described below:

| box | on screen |
|---|---|
| `[y, y+13]` - retail, via the stub | **clean** |
| `[y - above, +13]` - only the shift | bad: rows shifted and overlapping |
| `[y, y + (v2-v0)]` - only the height | **really bad**: smears |
| both | bad |

Two different failures with one root cause: **the routine asks the polygon
for per-label information the polygon does not reliably carry.**

* `above` reads `v0 & 7`, but only the sixteen `br_s*` labels ever had their
  VRAM row chosen to encode anything (`row_ok`). Every other row this routine
  draws - and it draws plain decoration too - gets a meaningless 0-7 shift.
  A 7px shift cannot smear, which is why this failure is layout, not garbage.
* `height` reads `v2 - v0`, which is the texture height only when the poly is
  a textured label. On anything else it is two arbitrary bytes.

Guarding on the GPU code byte (`poly+7 & 4`, set for POLY_FT4) so only
textured quads take the UV path was tried and **did not fix it** - it changed
the failure from vertical smears to a diagonal fan.

### The delivery mechanism works, and is proven

There is no room at `0x800C69C8` and no free space inside the overlay - not
one 32-byte zero run in 127,702 bytes. There is room **after** it: every stage
overlay loads at `0x800C3208`, and the game itself loads `init_ve`
(169,568 bytes) there against brf's 127,702, so ~41 KB past brf's end is
scratch. So `ROW_H` becomes `j <stub>` + `nop`, and the stub is appended to the
overlay, ending `jr $ra` / `addu $v0,$a2,$a3` (the original return value).

**This was verified with a control**: a stub containing retail's exact eleven
instructions rendered exactly like retail. The jump, the appended memory, the
return - all sound. `brf_build.py` grows the overlay, `nsect` is recomputed
from the payload sizes, and the stage goes from 138 to 139 sectors, which
DUMMY3M slot 128 absorbs (next stage at 384).

So whatever the right formula turns out to be, there is unlimited room to
write it. That constraint is gone.

### What to do next, and why it is not another formula

The information the routine needs - this row's height and shift - is
per-label, and the **caller** knows which label it is drawing. The port
smuggled it through the texture's VRAM position only because it had no spare
instructions. That constraint no longer applies.

The next step is reverse engineering rather than iteration: disassemble every
`jal 0x800C69B4` site in `brf_800C62B0` and `brf_800C6E88`, work out what each
one draws and what poly index it uses, and pass the height in properly. A
static table indexed by poly slot will **not** work - the same slot draws
different labels on different pages.

Six formula guesses were tried on screen before this was accepted. Do not try
a seventh.

### The diagnostic switches, all in `brf_build.py`

    INTEGRAL_BRF_NO_CODE=1        textures + placement only, no geometry
    INTEGRAL_BRF_NO_REWRITES=1    skip the five block rewrites
    INTEGRAL_BRF_NO_COUNTS=1      skip all six count/index groups
    INTEGRAL_BRF_SKIP=a,b,c       skip named groups: rowh s00 s00x
                                  unshare memadv advances

(`INTEGRAL_BRF_ROWH_MODE` and `INTEGRAL_BRF_ROWH_PASSTHROUGH` went with the
stub when the cause was found; the row box is eleven words in place again.)

They are diagnostics, not features. `INTEGRAL_BRF_NO_CODE` also relaxes the
quad==texture assertion, because with the geometry discarded they legitimately
disagree.

### Four groups were never tested alone (moot since the fix)

`INTEGRAL_BRF_NO_COUNTS` turns off six groups. Only `rowh` was isolated and
shown guilty. **`s00`, `s00x`, `unshare`, `memadv` and `advances` may be
perfectly fine** - they were switched off as collateral and never individually
retested. Before shipping anything with `rowh` disabled, turn those four back
on and check, or the disc is missing layout work it did not need to lose.

*With the cause found (top of §24) nothing is disabled: `hazards.py` finds no
hazard in any of them, and `repro32raw` ships them all. The one check still
owed is the full set on screen.*

### A measurement that lied, worth keeping

Scoring the screenshots programmatically - lit pixels and tall runs in the
right column - reported the `above` build as **cleaner than the control**. It
was not; the user's eyes said bad. Corrupted rows overlapping each other light
*fewer* pixels than correct text does, so the metric was anti-correlated with
correctness in exactly the case it was built to judge. §21 already records two
metrics that failed this way. Three now.

### The old plan, kept for its reasoning

`en_brf` does two separable things, and only one of them was tuned by eye:

| half | how it was derived |
|---|---|
| texture swap + VRAM placement | fit constraints - `ufits`, `vfits`, `row_ok`, `busy` |
| quad immediates + row arithmetic (`FRAME`, `MEMBER`, `S01`, `DETAIL`, `ROW_H`, xl, connectors) | **matched against Master Collection screenshots** |

`INTEGRAL_BRF_NO_CODE=1` builds the first half alone: every assert still
runs, the geometry changes are discarded, and the labels draw stretched to
Integral's original quads. Clean-but-stretched implicates the tuned half;
still-broken implicates the placement.

The suspicion is the tuned half, and it came from the user: the geometry was
reverse-engineered to make Integral's output *look like* USA's on MC, so a
polygon whose UVs are wrong in a way MC tolerates would have been accepted as
correct. `FRAME_NEW` rewrites "frame polys 27-38" - and a polygon with wrong
UVs samples VRAM as vertical stripes, which is the symptom.

### Two things this does not change

The collection build is not at risk of regressing: M2 shipped a final patch
months ago and will not change the renderer underneath it. And the fix, when
it comes, belongs in `en_brf` and not in MGSM2Fix - the two builds share this
patch byte for byte, and fixing it in the ASI would repair one environment,
leave every other one broken, and split a file that is currently identical.

## 25. The 2026-09-10 working state, for whoever opens this next

Written at the end of the session that booted the raw disc, and updated late
the same night when the briefing was fixed. **Read the top of §24 first** - the
cause and the fix are there. This is only where things are.

### Discs and images

| what | where |
|---|---|
| Redump dumps (zipped, MODE2/2352) | `C:\Users\Tideg\Desktop\MGS1 Integral` |
| extracted | `D:\mgsbuild\redump` |
| built images | `D:\mgsbuild\patched` |
| RetroArch screenshots | `C:\Users\Tideg\My Drive\RetroArch\Screenshots` |

The three images in `patched\` (`MGS Integral English (Disc 1/2/3)`) were
rebuilt at 23:24 from **`repro33raw`** (`repro32raw`'s briefing fix plus the
connector left ends of §26; the 22:31 images were removed first) - and disc 3
again at 11:37 on 2026-09-11 from **`repro34raw`**, which adds
`vr_en_memcard` (9 VR PPFs, 2,009 sectors verified); all three passed `mkimage.py`'s before-and-after
parity over every touched sector (418 / 418 / 2,004), and the fixed eleven
words were read back out of both main-disc images, once each, at the
relocated `brf` stage, with the old sequence absent. `TEST - Disc 1 no
counts.bin` beside them is the 17:05 diagnostic build (`repro25nocounts`) and
can go. **The briefing on disc 1 was looked at 22:38**: seven shots, every
reachable state matching the MC set (§24, top). Unseen: the flag-gated
indented items, which that disc's save has not earned.

### The builds that matter

| directory | what it is |
|---|---|
| **`repro33raw`** / **`repro33`** | `repro32raw` plus the connectors' left ends (§26). The raw one is what the images in `patched\` are built from; the collection one's two `en_brf` PPFs are **deployed** in `mods\` since 23:24 (the pair they replaced is `workrf_deployed_before_connector_disc{1,2}.ppf`) |
| `repro32raw` | the `ROW_H` fix alone: the load-delay `nop`, in place, every group on; 32 PPFs, ZIP `a2ebded6…` |
| `repro21raw` | the full raw set before any of this; what the first (broken) images came from |
| `repro25nocounts` | the bisect's clean build - `INTEGRAL_BRF_NO_COUNTS=1`, briefing clean, row spacing wrong; superseded |
| `repro29control` | the stub running retail's own row-box code; proved the append-and-jump mechanism, which is no longer used |
| `repro30`, `repro31above`, `repro31height` | the three failed fix attempts - each carried the hazard (§24, top) |
| `repro20` | the last **collection** build (not raw). The collection build shares `en_brf` byte for byte, so it carries the same bug until it is rebuilt and redeployed; MC hides it, but the fix should go there too |

Every `mkimage.py` run used `--english-default yes`.

### The emulator, and why its settings matter

SwanStation in RetroArch, and the settings are the accurate end of the scale -
`GPU_Renderer = Software`, `ResolutionScale 1`, `TextureFilter Nearest`, no
PGXP, no TrueColor, no dithering, no widescreen hack, texture replacements
off. Core options live at
`C:\Users\Tideg\My Drive\RetroArch\Core Config\retroarch-core-options.cfg`,
not in the RetroArch folder. **Retail Integral and retail USA both render the
briefing correctly under these settings**, which is what proves the port is at
fault rather than the emulator.

### What the Master Collection has to do with it

Nothing, in the end. MC renders the same bytes cleanly, so the bug hid there
for as long as the family has existed - but MC is not inaccurate, it just left
different garbage in the primitive buffer. M2 shipped a final patch months ago
and will not change, so the collection build is not at risk of regressing; the
reason to fix `ROW_H` is that it is wrong, and that the raw disc shows it.

The fix belongs in `en_brf`, **not** in MGSM2Fix. The two builds share that
patch byte for byte (276,482 bytes, zero differing offsets), and repairing it
in the ASI would fix one environment, leave every other one broken, and split
a file that is currently identical.

### Where the session's own mistakes are recorded

§24 has them, and they are worth reading before repeating them: six formula
guesses, a fix tested in a full build where other disabled groups could mask
it, a mechanism trusted because its *bytes* disassembled correctly rather than
because it had been shown to *execute*, and a screenshot metric that scored a
broken build cleaner than the control. The two results that actually moved
this forward both came from controls - removing `en_brf` entirely, and running
retail's own code through the new stub.

One more, from the user rather than the assistant, and it is the reason the
bug was found at all: the 26-shot-pair verification that signed `en_brf` off
compared Integral-on-MC against USA-on-MC. Both sides were drawn by the same
renderer, so its behaviour cancels out of the difference. That check proves
agreement, never correctness.

## 26. The 2026-09-10 late pass: the connectors' left ends, and the collection's dim line

Two things the user saw once the briefing rendered on an accurate emulator.

### The horizontal connectors started in the wrong place - a port bug, fixed

The line from the selected FILE button to the submenu's rule begins at a
hardcoded x per submenu. Integral: -46 / -24 / -46; USA: -39 / -32 / -27. The
port kept Integral's, on the recorded belief that they "anchor to the FILE
column" - but the FILE column's boxes are USA's now, so the outline and
detailed lines ran 7 px into their box and the member line stopped 8 px short
of its. Retail USA on SwanStation starts the line exactly at the box edge; so
did retail Integral against its own, wider box. The 26 shot pairs that signed
`en_brf` off compared game x 150-320 and never looked at x 114-136.

All six writers (layout and reveal animation, three submenus) now take USA's
value; the detailed one needed its own register because its layout store
shared `s7` with the outline's. `hazards.py` clean. README, "The connectors'
left ends". Built as `repro33raw` / `repro33` (see §25 for what was written
where). **Seen on the collection 23:26** in all three submenus: the line now
begins at the box edge, and the member gap is gone. **Seen on SwanStation
from the `repro33raw` disc 1 image at 23:45** as well: both targets confirmed.

### The dim connector on the Master Collection is the collection's, not ours

On MC the same connector draws faint (USA and Integral alike, patched or not);
on SwanStation and hardware it is full brightness. Its texture `br_line1` is
4x2 with a bright row (grey 135) over a dark one (grey 23) and the quad is one
pixel tall with V spanning both rows, so the renderer's texture-coordinate
rounding picks the row: hardware takes the bright one, M2's renderer the dark
one (measured: MC's line sits +25 over the background, the dark texel's
value). Not dithering - that cannot move a texel from 135 to 23 - and not the
USA `BrightnessText` patch, which never touches this stage. **Not the
upscaler either**: the user's 23:25 shots were taken at Resolution
"Original", Smoothing off, Pixel Perfect, Screen Filter off, and the line is
just as dim, so it is M2's base renderer. MGSM2Fix's own renderer options
(internal-resolution override, widescreen) are off in the live ini. README, "The
horizontal connector is dim on the collection". Fixable in MC by pinning the
three connectors' UVs to the bright texel (code, needs room; a USA stub would
ride the built-in disc-patch mechanism) - offered, not done: it is cosmetic,
MC-only, and outside the port's scope until the user says otherwise.

**Is it only the briefing?** Surveyed 23:42: every `*line*` texture on disc 1
drawn as a stretched quad. The two-row line texture is a house style - the
option screen's `line` (4x2, 135 over 23) and the title's `sp_line` use it
as **2-px** quads, which show bright row plus shadow on every renderer;
`b_line1`, `cam_line1..3` and `sub_sline` have uniform rows and cannot
disagree. The briefing is the only place that squeezes a two-row texture
into a **1-px** quad (`br_line1` connectors, `br_line2` bars), so within the
main disc it is one menu's misuse of a shared asset.

**The user's objection, and it is right:** pinning UVs in the disc bytes is a
band-aid that would only ever run in the collection, because the raw disc is
already correct - and anything that runs only in the collection can live in
MGSM2Fix, which already hooks M2's emulated GPU (smoothing, internal
resolution). The fix at the source is an ASI rule on the GPU's primitive
path: a textured quad one pixel tall whose V spans more than one texel gets
its V collapsed to the first row, which is what hardware draws. One rule,
both titles, no disc patch, upstream-worthy. Cost unknown: it needs the point
in M2's GPU code where primitives are consumed, which MGSM2Fix has not
mapped. Next step if wanted: a scoping pass to find that hook point before
writing anything.

**Done, 2026-09-10 late: `[Patches] ThinTexturedQuads` in MGSM2Fix.** The
scoping pass took the emulator apart from the log's `gpu` system-module
record: constructor `0x140102B30` (registers `dev/gpu`, `gpu:vram`), the GPU
struct's FIFO at `+0x2C` and depth at `+0x6C` (both in the header already),
the FIFO push at `0x1401064D0` whose tail dispatches on the command byte -
polygons via an eight-entry word-count table `[4,7,5,9,6,9,8,12]` at
`0x1407689E8`, indexed by the textured/quad/gouraud bits - to the polygon
handler `0x140103EE0`, which has exactly one caller: `mov rcx, rbx; call` at
`0x140106AF9`, with `rdx` still pointing at the FIFO words. That is the hook.
`PSX::GPU_PolygonCommand` (psx.cpp) rewrites the words in place before M2
reads them: textured polygon, Y extent exactly 1, top-edge vertices agreeing
on V -> every vertex takes that V; the same for U with X extent 1; nothing
else touched, so two-pixel lines keep their shadow row. Signature
`48 C1 E8 02 4C 8D 15 ?? ?? ?? ?? 83 E0 07 42 0F B6 84 10 ?? ?? ?? ?? 44 3B
C0 7C 0F 48 8B CB E8` +0x1C, one hit in the MGS1 executable. Default on;
`iEmulatorLevel >= 2` logs each snap. UPSTREAM.md has the entry. The
scanning scripts are in the session scratchpad only (`gpu_scan1..5.py`);
the method is what matters: log address -> module record -> constructor ->
displacement scan over `.pdata` function ranges -> single caller.

**Deployed 2026-09-11 00:02** as `MGSM2Fix64.asi` (SHA-256 `9ea87429…`), the
previous ASI kept beside it as `MGSM2Fix64.asi.bak-before-thinquads`. **Seen
on screen 00:07**: the log has `[PSX] GPU_PolygonCommand hook succeeded`, the
outline connector on the collection measures +205 over the background (it was
+0 the night before, and +25 on the detailed one), it starts at the box edge,
and nothing else in the shot changed. The collection's briefing now matches
SwanStation's.

**00:13-00:17, every briefing unlocked (`UnlockBriefing`, achievements off),
twenty Integral shots against twenty-one USA shots on the collection.** They
pair one-to-one in order (one spare USA shot is a repeated state) and the
submenu column differs **0.00%** in every pair at a 40/255 threshold; the
FILE column's 0.1% is JPEG noise on the box borders. Seen for the first time
with the fix: all six flag-gated items - `time limit`, `support crew`,
`Meryl`, `genetic strengthening`, `the reason for unanimous approval`,
`Liquid Snake` - each with a complete L-connector, drop **and** foot, where
the 09-02 shots had the drop alone; the member submenu on its five-item
17-row branch; the detailed submenu with nine items. So `ThinTexturedQuads`
covers the bars too, as predicted. Caveat, the §24 one: both sides of these
pairs are the collection with the same ASI, so they prove Integral equals
USA there, not hardware; hardware truth for the connectors is the
SwanStation measurement, and the flag-gated items are still unseen on
SwanStation because the raw disc has no unlock aid.

### 11:11, the VR disc with the three unlock aids: 22 shots, and a family nobody had seen

Seen and right: all four EXTRA help lines (`View the movie.`, `Take a
picture.`, `See the album.`, `Return to the title screen.`; PocketStation's
Japanese is the open §6 item), the RESULT window in every highlight state
with its 1ST/2ND/3RD and RECORD, `SAVE REPLAY DATA` with `NEW FILE [NEED 1
BLOCK]`, LOAD DATA and SAVE DATA with `LOADING...` / `SAVING...` /
`COMPLETE`, the by-rule Japanese at indices 1 and 9, and the `OVERWRITE OK?`
caption that is Integral-only. That closes §5.5's list except the moved
MOVIE EXIT box, which was not in the set.

**And one thing wrong: CLEAR DATA's `NO FILE` caption is Japanese.** Chasing
it found that the memory-card module is compiled into three VR overlays as
well as the executable, each with its own caption tables, and only the
executable's had been ported. `vr_en_memcard` (new, `vr_memcard.py`) ports
`vrsave` and `selectvr`, where USA's copies are English; `vrtitle` - the
CLEAR DATA screen itself - is Japanese in USA's own table and stays. README,
"The memory-card modules". Built, deployed to `mods\INTEGRAL\VR-DISK\`
(31 files clean), in `repro34raw` (33 PPFs, 24 main + 9 VR) and the disc 3
image rewritten from it at 11:37.

**How it was missed, and what else could be.** Asked directly, so answered
directly. The sweeps read GCL records; overlay pools are not records. The
byte inventory saw the strings but judged each *string*, and this one also
lives in `vrtitle` where USA has the same Japanese, so all three copies
inherited that verdict. The general form of the hole is "text USA has in
*this stage* that Integral's copy lacks", and `overlaydiff.py` now asks
exactly that, per stage, both discs, net of deployed PPFs. Its full run on
2026-09-11: disc 1 clean (22 candidates, all debug strings); VR disc clean
apart from this family (881 candidates, all USA's debug symbol tables and
printf strings, plus the other four languages in the three memory-card
stages); both executables clean (a boot string, debug prints, and two item
names that ARE ported). One residue: USA `selectvr`'s `SAVE?` menu record
where Integral's is empty - probably an unused window, to be looked at, not
read. Other blind spots that remain by nature: texture lettering (art, not
text - the EXORCISE textures are the known case), English stored in font
codes rather than ASCII in an overlay (none known; GCL text is swept
separately), and the Master Collection's leniency as a CPU and a GPU, which
§24 and §26 record and which only an accurate emulator can catch.

## 27. The 2026-09-11 cross-check against the MGS1 Translation Toolkit

The user pointed at <https://github.com/DoktorDeSparkle/mgs1-translation-toolkit>
(a PySide6 front end) and its library
<https://github.com/drsparklegasm/mgs1-scripts>, asking whether it reveals
anything we did not know - with the rule that nothing is taken from it and
that a useful reference is credited. Both are GPL v3. Nothing was copied;
CREDITS.md has the entry.

**How much weight it carries.** Not much on its own, and the user said so:
its README states that most of the GUI is "vibe coded by Claude", and its
glyph table is OCR (credited to Green_goblin) with "~30 kanji yet to
identify, numerous others are wrong" in its own words. So a disagreement
with it is a prompt to look again, never a verdict. Every change below was
decided by re-reading our tile and re-reading our sentence, and would have
been made the same way had the prompt come from anywhere else.

**What it is.** Tooling for an *undub*: English subtitles into the Japanese
release's RADIO.DAT, DEMO.DAT, VOX.DAT and ZMOVIE.STR, with a font editor for
the 440-slot kana/kanji font and a `.tbl` encoder. Different scope from this
port, which never touches subtitles. Its README lists its own open issues:
Integral's RADIO.DAT does not recompile (sector-aligned calls, extra
graphics padding), "~30 kanji yet to identify, numerous others are wrong".

**What it revealed: all six of our disputed readings were wrong.** Their
`graphicsData` maps 6,877 codec-glyph bitmaps (Japanese disc 1) to
characters. Hashing their bitmaps with `jptext.shape_key` and looking them
up in `bank1-glyphs.tsv`: **all 1,214 of our shapes occur in their table,
1,208 agree, 6 differ.** The six were adjudicated by rendering the tile
beside 12-px reference glyphs of both candidates (three system fonts, ±1 px
alignment, best pixel agreement) and by re-reading the export's sentences:

| id | uses | was | now | pixels | why |
|---|---:|---|---|---|---|
| g518 | 80 | 京 | 涼 | 62.5 / 70.1 | three dots down the left edge, the water radical 氵, which 京 has no room for. The one context is a staff credit, `モーション 吉村京子`, and 吉村涼子 is as good a name, so the sentence cannot decide and the pixels do |
| g1030 | 8 | 綺 | 華 | 54.9 / 71.5 | horizontal bars the full width with one central vertical, the shape of 華; 綺 would have a thread radical 糸 down the left, and there is none. `確かに綺麗すぎです` ("too clean") and 確かに華麗すぎです ("too showy") both read as self-criticism, so sense does not rule it out |
| g1156 | 2 | 瀕 | 餓 | 59.0 / 66.0 | the left component is boxed like 食, not the three dots of 氵. The two uses are in text the export does not cover, so pixels alone decided |
| g210 | 624 | 綿 | 緻 | 51.0 / 54.6 | **right half only** - 綿 and 緻 share 糸, so a whole-tile score is mostly agreement about the half not in dispute. On the right half the tile is dense with diagonals, which is 攵 in 致; 帛 would leave a clean white box interior and there is none. 緻密な配慮 and 綿密な配慮 are equally real, so again the pixels decide |
| g1045 | 6 | 輌 | 輛 | 53.6 / 54.1 | **a tie on pixels, adopted for want of anything against it.** At 12x12 両 and 兩 differ only by an inner stroke and no reading is measurably better; 0.5 points is noise. Nothing supported 輌 either, and the two are one word, so nothing turns on it |
| g658 | 44 | 〝 | ” | 12.5 / 66.7 | **the clearest of the six, and the one called a "variant" without looking.** The tile's marks are thick at the top and step down to the left, which is ”; 〝 leans the other way. Decisive corroboration: the table holds **one** quote glyph and the text uses it at *both* ends - `彼の髪形は〝タコ〝`, `〝隠れる事〝` - and a 〝…〟 pair needs two. One symmetric mark used for open and close is ”, not 〝 |

**Do the sentences still make sense?** Asked twice, and checked both times.
吉村涼子 is a name where 吉村京子 was one. 華麗すぎ is a real word where 綺麗すぎ
was. 緻密な配慮が必要 means what 綿密な配慮が必要 meant. 輛 is the same word as
輌. `彼の髪形は"タコ"ということで` and `ゲームの基本ルールである"隠れる事"を` read
*better* than before, because 〝…〝 was never valid typography and "…" is.
餓 has no sentence to fit. Sense never objected to any of the six, which is
exactly the point: the sentence test cannot see a misread that lands on a
name, a near-synonym, a variant form or a quotation mark.

`bank1-glyphs.tsv` is corrected for all six (the table loads and
`selftest.py` passes). The export in `work/jpdump/` was written with the old
readings and is not regenerated - it is a reading aid outside the repository,
and the three characters occur in 90 of its 68,242 lines; `py radiotext.py
--dump` rewrites it whenever it is next wanted. §19's claim stands as
written - zero *unresolved* codes - but its 78/78 holdout and "read against a
full sentence" could not see these, because a name, a near-synonym, a variant
form and a quotation mark all pass a sentence test either way.

**The second lesson is about the first pass at this section, not the table.**
It first adopted three of the six and kept three, calling 綿/緻 "undecided"
and 輌/輛 and 〝/” "variants" - which sounds like judgment and was closer to
defending the existing entry. The user looked at the picture and said all
three of those were the toolkit's to win. Re-tested properly they were: the
whole-tile score for a compound character is dominated by the radical both
candidates share, so **the test has to exclude the shared component**, and on
the right half alone 緻 wins; and the "variant" 〝/” was never scored at all,
which is how a 12.5-versus-66.7 miss stayed in the table wearing the word
"variant". A disagreement is not settled by being renamed. Score the half
that differs, score every row, and keep the count honest: **six of six.**

**What it corroborates, from its docs, without changing anything here.**
The font block layout (12-byte header, 96-entry variable-width ASCII table,
12-px 2bpp glyphs, 36-byte kana/kanji tiles) matches what `widths.py` and
`jptext.py` model. The 0x80-prefixed style-flag bytes (`0x80 0x22`, `0x80
0x2D`) they note as USA/Integral-specific are the ones `game_text` strips,
as `font.c` does. Their codec subtitle limit is **260 px and 4 lines per
block**; this port's 240-px figure is the *menu* renderer's `u8 max_width`
path and a different limit, so neither corrects the other. Their DEMO.DAT
parser names chunk type `0x04` "a second language chunk" - the dual-language
mechanism behind Integral's (En,Ja) cutscenes, which §23's language bit
selects. Integral's RADIO.DAT calls are 0x800-aligned with graphics padding,
which is the fragment geometry `radiomap.py` walks.

**Nothing to take.** Their tables are their transcription work under GPL v3
and this port's are its own; the digests met in the middle and that is all.
