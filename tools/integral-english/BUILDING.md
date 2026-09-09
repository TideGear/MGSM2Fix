# Rebuilding and packaging the current collection patch

`rebuild.py` builds the whole port in a fresh directory - nine patch families
for both main discs, and since 2026-09-07 the VR disc's seven as well - and it
never installs patches or changes game files. M2Package packages the ASI
separately and is not the Integral asset packager.

**Two variants, one switch** (also 2026-09-07; before that both constants were
edited by hand):

    py rebuild.py --output <dir>                    # collection: what mods/ gets
    py rebuild.py --output <dir> --variant raw      # for a real PSX disc image

| | collection | raw |
|---|---|---|
| `SC_KEEP_LINES` (`optsctext.py`) | 4 - the collection drops USA's two ○-button lines | 6 - USA's own text |
| `OPTION_MC_CONTROL_SETTINGS` (`opt.c`) | 1 - reproduce the KEY CONFIG doorbell | 0 - nothing to intercept, and no RAM at 0x80200000 |
| `en_menu3` (the `title` disc-swap copy) | **excluded** - the collection patches that block itself and the two layouts kill the title stage | included |

The switch is `INTEGRAL_ENGLISH_VARIANT`, resolved in `workdir.py` next to
`WORK`/`GAME`/`DECOMP`, so a tool run by hand honours it too:
`INTEGRAL_ENGLISH_VARIANT=raw py optsctext.py`. `rebuild.py` sets it for every
tool it runs, edits the `opt.c` constant in its isolated decomp export before
compiling, records both values in the report, and names the ZIP for the variant.
`--compare-deployed` is refused with `--variant raw`, because what is deployed
is the collection build.

## Tests

`py selftest.py` runs 23 tests over the parts that need no game data — the PPF
emitter's two split boundaries (255 bytes and the 2048-byte payload edge), the
record chain, the PCX codec's run cap, the EDC/ECC algebra, the width model. It
takes a hundredth of a second and needs nothing installed, so there is no excuse
for skipping it before a build.

It is deliberately not a check against ground truth. `py cdecc.py` is that, for
the checksums, against the real discs; `rebuild.py --compare-deployed` is that
for the whole build. Each mutation of the three modules the suite covers was
confirmed to make it fail, so it is known to have teeth.

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
`--compare-deployed` requires the 25 deployed PPFs: the 18 under the game's
`mods/INTEGRAL/INTEGRAL/{0,1}` and the 7 under `mods/INTEGRAL/VR-DISK`. Omit it
for an independent build without that reference set. Existing PPFs are read only
as comparison references.

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

- `Integral-English-<variant>.zip`: the PPFs in installation paths (collection: 20 main + 7 VR; raw adds `en_menu3` × 2), README,
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

**Clean run 2026-09-05, later (item fixes).** After `items.py` and `savemsg.py`
changed to own every byte of their pools (README "Three item-text faults"), the
same command in `D:/mgsbuild/repro6` again matched all 18 deployed PPFs by
effect (16 byte-identical); `en_items` is now 26 records / 3518 bytes per disc and
`en_savemsg` 3 records / 618 bytes. ZIP SHA-256 `d8dba9d16b2325f60785ab443f8f7429babd6d7178d175dd6942cc0a6f97e9b5`, 21 manifest entries.

**Clean run 2026-09-05 13:06 (slide fix).** After the abst sprite-width fix
(decomp `26d27f1`, `abst.bin` 48,103 bytes, SHA-256 `f625fc8ece123648…`), `D:/mgsbuild/repro7`
again matched all 18 deployed PPFs by effect (16 byte-identical). ZIP SHA-256
`870a691a4782291c5e92d6a68f3035cb102ed132daf5ce478901a14dc8ec51ca`, 21 manifest entries. This was the deployed state until the VR disc was folded in (repro8, below).

**Clean run 2026-09-07 16:08 (repro8: the VR disc folded in, one switch for both
variants).** The same command in `D:/mgsbuild/repro8` built 25 PPFs, 18 main + 7
VR, with Integral's VR executable compiled from the decomp rather than copied,
and every one matched the deployed set's effective changed bytes. ZIP SHA-256
`a13eefc08fa93b61adcb7c0524d57e6d7e913e0f313262e961c293d13bd5faef`, 2,796,157
bytes, 27 manifest entries.

**Clean run 2026-09-08 (repro17: `en_pad2`, the tenth family).** The same
command in `D:/mgsbuild/repro17` built 27 PPFs, 20 main + 7 VR, and every one
matched the deployed set's effective changed bytes; the two new
`INTEGRAL_disc{1,2}_en_pad2.ppf` are byte-identical to what is deployed
(SHA-256 `ff45bcea…448a` and `4a7af1d1…6f99`, 273 bytes and 159 changed
bytes each). ZIP SHA-256 `3eb2e1058486fceb3f0aa866f3194bc7c07ed70987fc2eea439259d5e8e8a6fb`, 2,798,182
bytes, 30 manifest entries. This is the deployed state.

`--variant raw` flips the two constants and adds `en_menu3`. Since 2026-09-07 it
also does the two things a real disc needs, which the collection never did:

* **it recomputes error correction.** Changing a payload byte invalidates that
  sector's EDC and P/Q parity. `rawdisc.py` rebuilds the tail of every sector the
  set touches and ships them as one more PPF per disc, `INTEGRAL_disc{1,2}_zz_ecc.ppf`
  and `INTEGRAL_vr_zz_ecc.ppf` — 413, 413 and 2003 sectors. Before computing any
  tail it requires the sector, as we believe retail has it, to verify against its
  own **stored** parity, so it cannot invent one for a sector whose true content
  is unknown. The executables are zero-filled in the collection's images, so the
  retail file is substituted first; that they then reproduce the stored parity
  exactly (313/313, 313/313, 308/308) is what proves both the sums and the inputs.
* **it stamps a PPF3 block check** — 1024 bytes of the original image at 0x9320 —
  so a tool that honours it refuses a patch aimed at a different release.

Check a finished raw build end to end with `py rawdisc.py <output>/package`: it
applies the whole set in memory and reports whether every touched sector
verifies. Expect `all verify` on all three discs.

**Still not proven: the raw variant has never been applied to a real disc image
and booted.** The remaining question there is whether the collection's embedded
images equal a retail dump everywhere the patches address, and the strongest
evidence so far is the parity check above, which says they do in the executable
extents. `NextSteps.md` §5.4, §5.10 and §5.13.

## Clean runs, newest first

| run | date | what changed since the previous run | matched the deployed set | ZIP SHA-256 |
|---|---|---|---|---|
| `repro17` | 2026-09-08 | `en_pad2` added (`pad2.py`), ten families | 27 of 27 (20 main + 7 VR) | `3eb2e1058486fceb3f0aa866f3194bc7c07ed70987fc2eea439259d5e8e8a6fb` |
| `repro8` | 2026-09-07 16:08 | VR disc folded in, VR executable built from the decomp, `--variant` switch | 25 of 25 (18 main + 7 VR) | `a13eefc08fa93b61adcb7c0524d57e6d7e913e0f313262e961c293d13bd5faef` |
| `repro7` | 2026-09-05 13:06 | MISSION LOG slide fix (`abst.bin` 48,103 bytes) | 18 of 18 | `870a691a4782291c5e92d6a68f3035cb102ed132daf5ce478901a14dc8ec51ca` |
| `repro6` | 2026-09-05 | item-text fixes; `en_items` and `en_savemsg` own every byte of their pools | 18 of 18 | `d8dba9d16b2325f60785ab443f8f7429babd6d7178d175dd6942cc0a6f97e9b5` |
| `repro5` | 2026-09-05 | MISSION LOG (`en_abst`), nine families | 18 of 18 | `02346ac790a218429220b65f2c8bc930ea07f01cf07eab1f4e090d6f931a42f0` |
| `repro4` | 2026-09-04 | first clean run, eight families | 16 of 16 | `b052a7105221130f024e0e7e4b1ca5701b66af761333dbbbd6a78b8ef0240366` |

"Matched" is by effective changed bytes against the original image
(`reference_effect_equal`), not by PPF file hash; the paragraphs above hold each
run's details.

## The VR disc (in `rebuild.py` since 2026-09-07)

`rebuild.py` builds the seven VR PPFs in the same isolated run as the main
discs and packages them under `mods/INTEGRAL/VR-DISK/`. The tools below are what
it runs, and they still work standalone for iterating on one patch.

Three things are particular to the VR half of a clean build:

- **Integral's VR executable is built, not copied.** The collection's copy is
  unusable, so `rebuild.py` runs the decomp's generator a second time for the
  `vr_exe` variant, ninjas `obj_vr/_mgsi.exe`, and checks it against
  SHA-256 `c370f8e4…` before the tools see it. USA's `SLUS-00957` is a supplied
  input, hashed like the four main executables.
- **`vr_movie` composes on the run's own output.** It builds on top of
  `vr_en_missions`, which already owns the `movie` stage, and normally reads the
  deployed folder to do it. `rebuild.py` sets `INTEGRAL_ENGLISH_VR_PPF_DIR` to
  its own work directory so an isolated build never depends on what is installed.
- **The VR set has one deliberate overlap.** `vr_en_movie` shares bytes with
  `vr_en_missions` by construction and must land last, which Ketchup's name
  order gives. The packaged-set overlap check allows exactly that pair and no
  other, on top of the main discs' own check.

**Order matters inside the VR half.** `vr_windows.py` ports the `movie` stage
but writes none of its records: it hands the finished stage to `vr_movie.py` as
`work/vr_movie_base.bin`, so that one patch owns that stage and the two no longer
overlap (README, "The composite trap"). `vr_movie.py` therefore has to run after
`vr_windows.py`, which is the order `VR_SCRIPTS` gives. Run by hand, the same
applies. `rebuild.py` now refuses **any** overlap between two VR patches.

The unlock aids (`vr_unlock.py`, `vr_unlock_movies.py`, `vr_unlock_extras.py`)
are **not** built or packaged: they are test aids, they must never ship, and
they are documented under "Unlock every VR mission", "Unlocking the EXTRA
movies" and "Unlocking the EXTRA menu's items".

### Inputs

- The same Master Collection installation. Integral's VR ISO is inside
  `windata/dlc/dlc_japan.bin` at image base `0x57592000`; USA's VR Missions ISO
  is inside `windata/alldata.bin` at `0xD39B7000`.
- Two VR executables in the work directory, because the collection's copies are
  zero-filled:
  - `work/vrint.exe` — Integral's, rebuilt byte-exact from the decomp with
    `py build/build.py --variant vr_exe`, SHA-256 `c370f8e4…`.
  - `work/vrus.exe` — USA's `SLUS-00957`, from a real disc image. It is a
    five-language build: Spanish, Italian, French, German and English pools
    behind tables-of-tables, English first, selected by GCL variable `0x11`
    (0 = English).
- Two stage directories extracted from the two VR ISOs, `work/vrint_stage.dir`
  and `work/vrus_stage.dir` (`/MGS/STAGE.DIR;1`). `vrlib.py` locates the ISOs,
  reads STAGE.DIR and computes the LBA of every named stage itself.

### Commands

A clean build needs none of these - `py rebuild.py --output <dir>` runs them all
in isolation. They are for iterating on one patch against the installed game:

```powershell
py vr_windows.py --build --deploy     # en_missions  (slow: 92 stages rebuilt)
py vr_exe.py --deploy                 # en_items and en_savemsg
py vr_option.py --deploy              # en_option (help lines + KEY CONFIG)
py vr_menus.py --deploy               # en_title
py vr_camera.py --deploy              # en_camsave
py vr_movie.py --deploy               # en_movie (MOVIE captions; needs the
                                      #   deployed en_missions to build on)
py ppfcheck.py --deployed             # always, before the game sees a PPF
```

Without `--deploy` each tool writes only to `work/`. `--deploy` copies into
`mods/INTEGRAL/VR-DISK/`.

Expected output on a clean run: 1808 of 1813 windows ported, 15 031 records and
3 370 955 bytes for `en_missions` with **no stage grown** (ten padded back to
their original sector count); 63 records for `en_items`; 36 records / 431 bytes
for `en_savemsg`; 546 records / 121 471 bytes for `en_option` with the DAR at
120 754 of 120 832 bytes; 7 records / 915 bytes for `en_title`; 4 records /
617 bytes for `en_camsave`; 69 records / 753 bytes for `en_movie`.

`vr_movie.py` is the one with an ordering constraint: it builds on the composite
(retail plus every VR PPF that writes the `movie` stage), so by hand a fresh
sequence has to deploy `en_missions` first, and inside `rebuild.py` it runs last
against `INTEGRAL_ENGLISH_VR_PPF_DIR`, that run's own work directory. It writes
two PPFs and `--deploy` installs the full one, moving the older E3-only file out
of `mods/` - the two overlap and only one may be present (README "The MOVIE
selection captions").

`py vr_unlock.py` builds the removable test aid that unlocks every mission
(README "Unlock every VR mission"). It is deliberately *not* deployed by
default, and must never be deployed with achievements enabled.
