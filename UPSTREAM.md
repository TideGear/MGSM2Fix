# Changes worth a separate upstream pull request

The `integral-english-text` branch contains the Integral English port and
MGSM2Fix changes that also help players without the port. This ledger tracks
the latter. Commit IDs identify implementations; test status is evidence from
the recorded sessions, not a claim that every supported title was tested.

| Commits | Change and scope | Verification / remaining work |
|---|---|---|
| `5921ec9` | Ketchup defers executable writes to the RAM mirror. General mechanism for Ketchup titles. | In use since August 2026; not a test of every title. |
| `640f359`, `eccecb9` | `[Game] EnglishText` holds Integral's initial language through title setup. | In use since 2026-08-28. |
| `a57859e`, `d386a09` | `[Game] UnlockBriefing` reveals all 16 briefing entries in Integral and USA; addresses derive from `scene_name`. | In use. It also seeds a new game's `var_buf` with those flags. |
| `6fb21a5`, `4528f91` | Squirrel RAM read/write hooks and call-stack logging; Integral language guard follows option-screen choices. | Trace identified the collection's rewrite. Japanese/English choices and title round-trip tested 2026-09-03. |
| `a5209ce` | `[Patches] PreserveConfiguration` carries only the bits changed by the collection into the current configuration word. All MGS1 versions. | Option toggles and 1P MODE passed 2026-09-03. A logged intervention in the intermittent race is still needed. |
| `6308afb`, `4757fab`, `10661d3` | `[Patches] BrightnessText`: `fixed` uses four lines at the original position, `original` restores six, `collection` leaves collection behavior. **USA/title 981 only.** | Both changed modes verified 2026-09-03 with achievements active. `fixed` matched the Integral port pixel-for-pixel. Disc 2 and the range filter's independent contribution remain unobserved. Integral uses its own PPF, independent of this setting. |
| `81de8c0`, `8d7a2e7` | `SQHook::SetPatchWatch` logs collection writes to selected CD-ROM ranges, including inline patches, before filtering. | Caught the 24-byte KEY CONFIG doorbell patch. Upstream the general mechanism separately from the two Integral option-stage ranges. |
| `9bcca8f` | `Ketchup::Audit` reports whether RAM still contains the bytes Ketchup wrote. Read-only diagnostic. | Used in the save-message investigation. It does not repair foreign writes. |
| `5fa2cf5` | `[Game] GiveItems` grants specified items once per gameplay stage where their count is zero. | Build verified; a meaningful grant into an empty inventory remains to be tested. Granted items persist in subsequent saves. |
| `3f04e4a`, `d988e1d` | `[Game] StageSelect` accepts `select1` through `select4` directly; `true` retains the developer top menu. | `select3` reached `s11a` on disc 1. Direct `s14e` hung with missing story state. This proves menu selection, not disc-2 loading or safe entry into every stage. |

Ketchup's existing repair loop checks only the first byte of each write run.
A foreign write inside a run can therefore survive. Checking every byte could
fight a recurring writer and cause flicker/back-off; measure recurrence before
changing that behavior. `Audit` supplies evidence without starting that fight.

Port scripts, PPFs and port-specific README sections remain outside these
upstream changes. Current Integral build and audit status live in
[BUILDING.md](tools/integral-english/BUILDING.md) and
[COVERAGE.md](tools/integral-english/COVERAGE.md).
