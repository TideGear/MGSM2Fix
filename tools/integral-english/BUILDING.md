# Rebuilding and packaging the current collection patch

`rebuild.py` builds all nine enabled patch families for both main discs in a
fresh directory (the ninth, `en_abst`, since 2026-09-05). It never installs patches or changes game files. This is the
collection variant; raw-disc packaging and the disabled `en_menu3` remain open.
M2Package packages the ASI separately and is not the Integral asset packager.

## Inputs

- A Windows installation of the Master Collection MGS1, including Integral DLC:
  `windata/dlc/dlc_japan.bin` and `windata/alldata.bin`.
- Four original retail executables in one directory: `int1.exe`, `int2.exe`,
  `us1.exe`, `us2.exe`. The collection's ISO executable extents are zero-filled;
  extracting them does **not** supply usable retail code. No game data is
  distributed in this repository.
- The local MGS decomp Git repository containing commit `7964de7`, and a PSYQ
  SDK tree accepted by that revision's `build/build.py --psyq_path` (the local
  tree contains `psyq_4.3`, `psyq_4.4`, `psyq_4.5` and `aspsx`).
- Python with `tarfile.extractall(filter='data')` support, Git, Pillow and the
  Python `ninja` package. The report records Python/package versions and hashes
  every SDK file outside `.git`; reproduce those inputs for matching output.
- Tracked scripts, `decomp-overlay-changes.patch` and `brf_quads_all.json`.
  Their hashes are recorded in the build report.

The builder rejects unsupported executable hashes:

| Files | Bytes | SHA-256 |
|---|---:|---|
| `int1.exe`, `int2.exe` | 641024 each | `4b8252b65953a02021486406cfcdca1c7670d1d1a8f3cf6e750ef6e360dc3a2f` |
| `us1.exe`, `us2.exe` | 651264 each | `615e136083336957ed0b9b3805145bf5bbb35f7a16c2f160dba8f17bb71cc640` |

Stage files are extracted from the collection and hashed in the report with
their container, image base, ISO path, LBA and size. Main-disc image bases are
Integral `0`, `0x2AE54800`; USA `0xF12F8000`, `0x11B3E5800`.

## Command

From this directory in PowerShell (substitute your input paths):

```powershell
py rebuild.py --output D:/mgsbuild/repro4 --game D:/Steam/SteamApps/common/MGS1 --decomp D:/mgsbuild/d --psyq D:/mgsbuild/psyq --executables D:/mgsbuild/integral-english-work/work --compare-deployed
```

The output directory must not exist and must have a short path without spaces.
`--compare-deployed` requires the existing 18 named PPFs under the game's
`mods/INTEGRAL/INTEGRAL/{0,1}`. Omit it for an independent build without that
reference set. Existing PPFs are read only as comparison references.

The builder exports the pinned decomp revision into the output directory,
applies the tracked patch, generates the build graph, and compiles only the
requested `option.bin`, `preope.bin` and `abst.bin` targets and their dependencies. The
original decomp checkout is not modified. It then runs the asset builders,
stages the two discs, validates PPF framing/sector boundaries and checks
conflicting writes across each complete patch set.

Comparison is by effective changed bytes against the original image, so PPF
description text and record grouping may differ without changing game data.
A failed comparison retains the report and does not create a ZIP.

## Outputs

- `Integral-English-collection.zip`: 18 PPFs in installation paths, README,
  `build-report.json` and `SHA256SUMS.txt`.
- `package/`: the same unpacked files for review.
- `work/`, `decomp/`, `build.log`: extracted inputs, intermediate assets and
  compiler/build evidence, retained for diagnosis.

The ZIP uses fixed metadata/order. Its report records the environment, so a
different SDK, Python version or source checkout may change the ZIP even if
the resulting patch effects match. Inspect `reference_effect_equal` for every
output when comparing against the known deployed set. The package README
lists installation, removal, ASI requirements and incomplete features.

## Recovered builders and obsolete experiments

The clean run on 2026-09-04 used Python 3.12.3, Pillow 11.0.0 and ninja 1.13.0.
All 16 patches matched the deployed set's effective changed bytes. Fourteen
also matched byte-for-byte; the two `en_menu2` files differ only in PPF encoding.
ZIP integrity and all 18 manifest entries were independently checked.
The local artifact is `D:/mgsbuild/repro4/Integral-English-collection.zip`, SHA-256
`b052a7105221130f024e0e7e4b1ca5701b66af761333dbbbd6a78b8ef0240366`.
Its full source/SDK/input/output ledger is in `build-report.json` beside the ZIP
and inside it. This is static equivalence evidence, not a new gameplay test.

`items.py` recovers the scratchpad's actual item generator (`mkpatch.py`).
`menu2.py` reconstructs current `en_menu` and `en_menu2` behavior, excluding the
broken historical menu3 mode. `optlabel2.py` rebuilds owned option captions
directly from retail and preserves the colon and all other unowned records.
`preope_usa.py` now builds both recaps directly; `preope_both.py` is an obsolete
experiment, not a prerequisite. Old `optbright.py`/font-text PPF output is not
an input. Briefing construction uses the USA donor; its 16 row and 53 quad
argument tuples were checked against the former European donor and match.

**Clean run 2026-09-05 (nine families).** After the MISSION LOG port, the same
command rebuilt all 18 PPFs in `D:/mgsbuild/repro5`; every one matched the
deployed set's effective changed bytes (16 byte-identical, the two `en_menu2`
differing only in record grouping as before). The exported decomp compiled
`abst.bin` byte-identical to the live checkout's (SHA-256
`a491c1d27a256cb7295da12f543620ef955c33ef3e72fa719c9c9d531283c966`, 48,087
bytes). ZIP SHA-256
`02346ac790a218429220b65f2c8bc930ea07f01cf07eab1f4e090d6f931a42f0`, 21 manifest
entries. `abst_build.py` also reads the mods folder to refuse any overlap with
the other PPFs' bytes, so a clean run wants the game installed even though it
never writes to it.

The collection option builder deliberately uses four brightness lines. Changing
that constant to six alone does not finish the raw-disc release: disc-change
text, runtime behavior and raw-image packaging still require work.
