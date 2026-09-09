# Text coverage evidence (2026-09-04, VR section added 2026-09-06, updated 2026-09-08)

The current patch is not a complete English port. The title's disc-swap copy
(`en_menu3`) is ported but raw-disc only - the collection patches that block
itself, so it is not deployed here (README, "Why `en_menu3` is raw-disc only");
the Mission
Log and the disc-change abstract (both in `abst`) were ported on 2026-09-05
(`en_abst`, seen on screen the same day), and the VR disc on 2026-09-06
(seven PPFs since the MOVIE captions on 2026-09-07; see "The VR disc" below and the README section of the same name).
Two more things landed on 2026-09-08: `en_pad2`, the controller-port subtitle in
the Psycho Mantis room, which was the last main-disc string with a USA
counterpart and no family (all five of its call sites, across `s07b` and the
Integral-only `s07br`); and USA's four MISSION LOG location-name spellings,
inside `en_abst`. **Ten families now, 20 main-disc PPFs and 27 in all.**
The expanded scan closes the old tool's disc-1-only coverage gap for stage
inventory; it does not establish that every visible string has been audited.

**Since 2026-09-07 there is a stronger tool for the main discs: `mainsweep.py`.**
`audit_text.py` inventories *candidates* by framing and says so; it cannot tell
whether a candidate has an English counterpart, which is why about 160 of them
sat unclassified here. `mainsweep.py` does for discs 1 and 2 what `vr_sweep.py`
does for the VR disc: it pairs every GCL string with the USA disc's by the
command that owns it, so "Integral is Japanese here and USA has English" becomes
a comparison between two discs rather than a judgement about bytes. Run on
retail on both sides, deliberately, so a gap cannot hide behind a patch that is
already deployed.

**Result, both discs, identical:** twelve owners hold Japanese strings whose
owner has English on the USA disc. Nine are inside stages a patch family already
owns (`abst`, `preope`, `option`, `title`, `change`, `demosel`). Two are Japanese
on the USA disc in identical numbers, so there is nothing to port: `cmd 4AD9`,
the location titles, 12 Japanese and 58 English on **both** discs, and
`chara 9302` in `rank`, 1 and 30 on both. One was neither, and it is now the
`en_pad2` family, **built and deployed 2026-09-08**:

| | |
|---|---|
| stage | `s07b` on both discs, and `s07br` |
| owner | `chara 2D0A` — `CHARA_2D0A_2ND` → `NewSecond`, `game/second.c` |
| what it is | the subtitle drawn when the controller moves to port 2 for the Psycho Mantis fight: コントローラ端子1のコントローラを｜使用してください。 |
| Integral | 55 bytes of Japanese at **two** call sites in `s07b` and one in `s07br` |
| USA | English at the second `s07b` site, `PLUG CONTROLLER INTO \| CONTROLLER PORT 1.` (42 bytes); the first site is the identical Japanese |

**The table this replaces was wrong in two ways, and reading the caller is what
showed it.** `second.c` takes one string per spawn, so there is no record 0 and
record 1 to index: `s07b` holds two separate *spawns*, in two branches of its
script, and USA translated the **later** one. USA's English is shorter than the
slot, so the port is length-preserving — no container resized, no stage
relocated. All five sites are ported on the user's instruction, because both
branches hand the same message to the same actor and shipping USA's
inconsistency would leave Japanese on screen. `NextSteps.md` §5.11 has the
reasoning and the verification.

**A second limit of this sweep, found the same day.** `mainsweep.py` compares
the **82 stage names both discs share**, so every one of the 13 Integral-only
stages is outside its universe. The third copy of that string, in `s07br`, was
therefore invisible to it and was found only by looking for the same owner in
the Integral-only stages by hand. A count from this tool means "among shared
stages"; Integral-only stages need their own pass, and none has been done.

**A description is not always the string its table points at.** Six item and
weapon slots swap or rewrite their text with the game state, mapped 2026-09-07
from the only two functions that print one (README, "Descriptions that change
with the game state"). Five are ported or deliberately matched to USA. The
sixth has no counterpart and **stays Japanese**: on VERY EASY the FA-MAS slot
becomes the MP5 SD outright - label and description both - and USA has neither
that weapon nor that difficulty. The description is 103 bytes at RAM 0x80011B04;
the label is an inline literal in the menu code, not a table entry. Confirmed on
screen 2026-09-07. Note that neither sweep could have
found it - it is an executable string, so `mainsweep.py` does not see it, and
`audit_text.py` reads the executables only for the save-title probes.

**One more text set, found and partly ported 2026-09-07.** The inventory's
side-column abbreviations are a separate block of names in the executable,
already Latin on both discs, which is why no sweep or audit had flagged them.
Comparing Integral's against USA's entry by entry, one differed: item 22 was
`SCARF` where USA has `HANDKER`. That one was changed on the user's instruction
and is the port's first replacement of Integral's **own English** rather than of
its Japanese (README, "Amendment, 2026-09-07"). The rest of the block already
matched. Integral's weapon names carry one entry USA does not have at all,
`MP 5 SD`.

**The blind spot this file used to share with every sweep - now swept, on the
main discs.** All of them - `mainsweep.py`, `vr_sweep.py`, `jpsweep.py`,
`audit_text.py` - look for *Japanese*, so a string that is already English on
both discs and simply **says something different** passed all of them
unremarked. `mainsweep.py --diff-english` asks that question directly
(2026-09-08): 15 replace hunks over disc 1's 82 shared stages, 8 with
player-readable text, and one residue after triage - the `abst` location names,
where **four** pairs differ and not the three the documents listed. The new one
is `Cmnd rm` against USA's `Cmnd room`. Disc 2 is identical.

| Integral | USA |
|---|---|
| `Tank Hanger` | `Tank Hangar` |
| `Medi rm` | `Medi room` |
| `Cmnder rm` | `Cmnder room` |
| `Cmnd rm` | `Cmnd room` |

**All four now read USA's**, asked and answered 2026-09-08: `USA_LOCATION_NAMES`
in `abst_build.py` takes USA's whole command, +12 bytes, the stage still 88
sectors. That is the second application of amendment 4b after `SCARF` against
`HANDKER`, and the builder's verifier now re-parses the list and asserts it
equals its source record for record. Note that `mainsweep.py` reads **retail**,
so it still reports these four - it now prints `!!` beside any finding in a
stage a patch family owns, which is what stops them being ported twice.

**The VR disc has not been swept this way, and one input has to change first.**
USA's VR disc carries five languages, so the diff must take only the English arm
of a language branch. With that done, a per-owner fuzzy match reports `FAMAS`
against USA's `FA-MAS` in the mission titles - and that is a **non-finding**,
because the deployed `vr_en_missions.ppf` holds 142 `FA-MAS` and no `FAMAS`: the
port already writes USA's spelling. The English-against-English question must
therefore be asked of the **deployed** bytes, the opposite of the discipline the
Japanese question needs, or a sweep rediscovers the port's own work.

**So the claim this file can now make** is that on the main discs, every string
whose owning command has English on the USA release is either already ported or
Japanese on the USA disc too — the last exception, `s07b`, was ported on
2026-09-08. That is a measurement, and it is a measurement over the 82 stage
names the two discs share (see the limit noted above).
What it still does not cover is texture lettering, executable UI beyond the
probes below, and runtime language branches.

## Reproduce the inventory

```powershell
py audit_text.py --game D:/Steam/SteamApps/common/MGS1 --executables D:/mgsbuild/integral-english-work/work --output D:/mgsbuild/repro4/text-audit.json
```

This reads deployed PPFs, follows relocated stage entries, inventories GCL
STRING framing candidates and scans main-game overlay pointers and short
LUI/ADDIU or LUI/ORI address sequences. JSON retains stage/PPF/executable hashes,
offsets, raw bytes, decoded candidates, stage differences and extraction errors.
It writes only the requested report. Run it again after changing deployed PPFs.

| Image | Integral named stages | USA named stages | Stage extraction errors |
|---|---:|---:|---:|
| Main disc 1 | 95 | 96 | 0 |
| Main disc 2 | 95 | 96 | 0 |
| VR | 105 | 105 | 0 |

**The Integral-only stages are swept now too** (`mainsweep.py --integral-only`,
2026-09-08). Each of the 13 pairs onto the USA stage it is a variant of - the
base name without the trailing `r`, or `init` for `init_ve` - and across all 13,
on both discs, there is **exactly one** Japanese string whose base-stage owner
has English on the USA disc: the `s07br` copy of the controller-port line, which
`en_pad2` ports. So the hole this tool's shared-name universe left is measured
and closed rather than merely known.

Each main disc has 82 shared stage names and 13 Integral-only names:
`d18ar`, `endingr`, `init_ve`, `s03ar`, `s03dr`, `s03er`, `s07br`, `s07cr`,
`s09ar`, `s18ar`, `s19ar`, `s19br`, `s20ar`. **These are outside `mainsweep.py`'s
universe**, which is the two discs' shared names; `s07br` is the one so far known
to hold portable text, and `en_pad2` covers it. What the `*r` stages are for has
not been established - `s07br`'s overlay source is byte-identical to `s07b`'s.
Integral's VR ISO was located by its PVD and `SLPM_862.49` path at container
base `0x57592000`; USA VR is at `0xD39B7000`. The older 106-stage count included
one more than the 105 named entries actually enumerated; use 105 for inventory.

## What the scan can and cannot prove

- `jpsweep.py` compares pointer slots at equal offsets on disc 1. Equal offsets
  do not establish matching tables across differently compiled overlays. The
  camera pairing was independently verified; other pairings need evidence.
- GCL scanning is a framing heuristic, including data that overflows an
  OPTION's one-byte length. Opcode-like bytes inside operands can yield false
  positives. A candidate needs structural and caller verification before use.
- Address-reference scanning also yields code/data false positives. It does
  not model all register flow or discover every indirect reference.
- The font strips `0x6000` style flags. `0x80xx` can be Latin and `0x9001` a
  space; other glyphs depend on the font bank. `unresolved_glyphs` is therefore
  not a Japanese-language classification. USA also contains non-ASCII glyphs.
- VR overlay load bases are not established by this tool, so its VR reference
  scan is explicitly disabled. VR GCL candidates and stage inventory are read.
  The VR port established them separately — `0x800C11A0` for Integral and
  `0x800C4350` for USA, both `_bss_objend` — but `audit_text.py` has not been
  taught them, so its VR numbers below come from the port's own tools.
- Texture lettering, executable UI beyond the save-title probes, runtime
  language branches, collection-provided replacements and screen reachability
  still need targeted inspection. Zero extraction errors is not zero gaps.

The report is a reproducible investigation index. Completing the translation
census still requires verifying residual candidates against callers, fonts,
the USA path and reachable screens. No translations are inferred from it.

## Save-slot title encoding

The original USA executable also stores full-width Shift-JIS Latin. The old
suggestion that Integral's title should be replaced with an ASCII USA title
was incorrect for these inputs:

| Token | Integral executable offsets | USA executable offsets | Bytes |
|---|---|---|---|
| Full-width MGS prefix | `0x2AF4`, `0x31EC` | `0x3264`, `0x9E6D8` | `826c82668272` |
| Full-width Dock | `0x8F410` | `0x91B68` | `8263828f8283828b` |
| Full-width [NM] | `0x2AC0` | `0x2B44` | `816d826d826c816e` |

Integral appends `81e7` (the integral sign) to the MGS prefix. This is product
branding. `source/menu/datasave.c`'s `makeTitle` also constructs full-width time
digits; the caption tables are separate from the save-title formatting path.
No blanket ASCII conversion is warranted. These byte probes do not claim that
every possible location or runtime save title has been displayed and tested.

## Additional retained caption

The camera stage's first GCL STRING at script `+0x1B8` contains
`90639a019a029a038152910b9027810d902b902c8117813e8119810bc03f`
in Integral; USA's corresponding record is empty. This is separate from the
six retained `camsave` overlay slots and was missing from the earlier list.
It stays unchanged under the existing no-invented-translation rule.

The retained recap bytes and ranking/location glyphs must also be interpreted
through their callers. In particular, the rebuilt preope keeps unread retail
recap bytes while its MG2 renderer uses the appended English blob. Counting
encoded strings in the file overstates what remains visible in Japanese.

## The VR disc (inventoried and ported 2026-09-06)

Read from the VR binaries by `vrlib.py` and the six `vr_*.py` builders, not by
`audit_text.py`. Every figure is what the builders report on a clean run.

| where the text is | how it is stored | Integral | ported |
|---|---|---|---|
| in-mission windows | `chara 0xD44E` (`vrwindow`) commands in each stage's `scenerio.gcx` | 1813 windows in 94 stages | **1808 in 92 stages** |
| item / weapon / capture-mode pools | executable string arenas behind tables at `0x8009C11C`, `0x8009C304` and `0x80011F0C` | 3 pools | all, minus MP5 and frozen items (no USA text) |
| save and load messages | executable tables at `0x8009C884` / `0x8009C8B4` | 12 + 12 | 20; indices 1 and 9 stay Japanese (USA draws nothing) |
| option help lines | `chara 0x976C` option `-e` in the `option` stage | 31 records | 7 (1, 2, 3, 5, 6, 12, 26); the rest are Integral-only rows |
| KEY CONFIG | eight label textures in the option stage's DAR, plus quad geometry in the overlay | 8 labels | all 8, with USA's rectangles and `key_syukan` +11; **verified on screen 2026-09-07** in all three button types, and the row's selection highlight widened to match (README, "The VR KEY CONFIG on screen"). Its help line under the controller stays Japanese: USA leaves records 17..25 empty |
| EXTRA menu help lines | `chara 0x5667` option `-t` in `vrtitle` | 11 records | 4 (records 2–5) |
| PHOTOGRAPHING memory-card messages | string table in the `camera` overlay at `+0x608` / `+0x638` / `+0x668` / `+0x708` | 4 groups | all but the two Japanese prompts and the two USA-empty slots |
| MOVIE selection captions | `chara 0xFAA8` option `-t` in the `movie` stage | 3 captions (4 records) | **all 3** (6 records), the two TGS ones as USA's two lines |

Known to remain Japanese on the VR disc, each because USA has no counterpart:
the PocketStation help line, prompt and はい/いいえ (USA's fifth EXTRA item is
STAFF CREDIT, a different feature); save/load indices 1 and 9; two camera
prompts; `vrtitle`'s four and `vrsave`'s one debug window, where USA carries the
identical Japanese; MP5, the frozen items and the mine-detector line.

The last VR item that was **blocked rather than absent** is now ported: the two
TGS **MOVIE captions**. USA draws each as two lines where Integral drew one, and
the count is neither the record count nor the position table but two calls in the
clip-selection code, one of which Integral does not make; the port retargets that
call at a 16-word stub that lights both of a clip's lines, exactly as USA does
(README "The MOVIE selection captions"). Nothing on the VR disc with a USA
counterpart is still Japanese for a reason other than the list above.

Not yet inventoried on the VR disc: texture lettering outside the eight KEY
CONFIG labels (the camera's EXORCISE textures are known and deferred), and any
string reached only through the five-language selection in USA's executable
other than the English pool the port reads.
