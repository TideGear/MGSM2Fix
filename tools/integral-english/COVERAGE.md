# Text coverage evidence (2026-09-04, VR section added 2026-09-06)

The current patch is not a complete English port. The title's disc-swap copy
(`en_menu3`) remains open in [NextSteps.md](NextSteps.md); the Mission
Log and the disc-change abstract (both in `abst`) were ported on 2026-09-05
(`en_abst`, seen on screen the same day), and the VR disc on 2026-09-06
(six PPFs; see "The VR disc" below and the README section of the same name).
The expanded scan closes the old tool's disc-1-only coverage gap for stage
inventory; it does not establish that every visible string has been audited.

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

Each main disc has 82 shared stage names and 13 Integral-only names:
`d18ar`, `endingr`, `init_ve`, `s03ar`, `s03dr`, `s03er`, `s07br`, `s07cr`,
`s09ar`, `s18ar`, `s19ar`, `s19br`, `s20ar`.
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

Read from the VR binaries by `vrlib.py` and the five `vr_*.py` builders, not by
`audit_text.py`. Every figure is what the builders report on a clean run.

| where the text is | how it is stored | Integral | ported |
|---|---|---|---|
| in-mission windows | `chara 0xD44E` (`vrwindow`) commands in each stage's `scenerio.gcx` | 1813 windows in 94 stages | **1808 in 92 stages** |
| item / weapon / capture-mode pools | executable string arenas behind tables at `0x8009C11C`, `0x8009C304` and `0x80011F0C` | 3 pools | all, minus MP5 and frozen items (no USA text) |
| save and load messages | executable tables at `0x8009C884` / `0x8009C8B4` | 12 + 12 | 20; indices 1 and 9 stay Japanese (USA draws nothing) |
| option help lines | `chara 0x976C` option `-e` in the `option` stage | 31 records | 7 (1, 2, 3, 5, 6, 12, 26); the rest are Integral-only rows |
| KEY CONFIG | eight label textures in the option stage's DAR, plus quad geometry in the overlay | 8 labels | all 8, with USA's rectangles and `key_syukan` +11 |
| EXTRA menu help lines | `chara 0x5667` option `-t` in `vrtitle` | 11 records | 4 (records 2–5) |
| PHOTOGRAPHING memory-card messages | string table in the `camera` overlay at `+0x608` / `+0x638` / `+0x668` / `+0x708` | 4 groups | all but the two Japanese prompts and the two USA-empty slots |

Known to remain Japanese on the VR disc, each because USA has no counterpart:
the PocketStation help line, prompt and はい/いいえ (USA's fifth EXTRA item is
STAFF CREDIT, a different feature); save/load indices 1 and 9; two camera
prompts; `vrtitle`'s four and `vrsave`'s one debug window, where USA carries the
identical Japanese; MP5, the frozen items and the mine-detector line.

Not yet inventoried on the VR disc: texture lettering outside the eight KEY
CONFIG labels (the camera's EXORCISE textures are known and deferred), the
`movie` stage's `-t` titles (USA has two records where Integral has one), and
any string reached only through the five-language selection in USA's executable
other than the English pool the port reads.
