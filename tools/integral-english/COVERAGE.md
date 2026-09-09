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


## The file-level blind spot, and what it hid (2026-09-09)

**Every sweep in this project until 2026-09-09 read exactly one file: `STAGE.DIR`**
(plus the four executables). Nothing had ever looked inside the other seven
files on a disc. The figures above - "153 Japanese strings a disc" and the rest -
are therefore true *of the stage archives* and were presented as though they were
true of the disc. They are not.

The prompt was a question from the user about an Integral-exclusive Japanese
developer-commentary codec channel. There is one, it is enormous, and no tool
here could see it.

### Every file on a disc, and whether anything had read it

Integral disc 1 against USA disc 1, whole-file scans (not samples):

| file | Integral d1 | delta vs USA | Japanese found | swept before today |
|---|---:|---:|---|---|
| `/MGS/DEMO.DAT` | 258,744,320 | +141,312 | ~1.8 KB, real text | no |
| `/MGS/VOX.DAT` | 196,173,824 | +159,744 | ~1.0 KB, real text | no |
| `/MGS/STAGE.DIR` | 75,132,928 | +3,239,936 | 153 strings deployed | **yes - the only one** |
| `/MGS/ZMOVIE.STR` | 47,517,696 | +10,240 | none | no (FMV stream) |
| `/DUMMY3M.DAT` | 27,648,001 | 0 | none | as relocation scratch only |
| `/MGS/RADIO.DAT` | 11,198,464 | **+9,421,613** | **megabytes** | **no** |
| `/MGS/BRF.DAT` | 5,724,160 | −73,728 | none | no - now verified clean |
| `/MGS/FACE.DAT` | 3,508,224 | 0 | none | no - byte-identical stats |
| `SLPM_862.47` | 641,024 | — | 5 strings | yes |

`BRF.DAT` and `FACE.DAT` are the reassuring rows: 380,941 bytes of English text
in Integral's `BRF.DAT` against USA's 382,771, and `FACE.DAT` identical on both
counts, so the briefing data and the codec portraits carry nothing Japanese.
That was assumed before and is measured now.

### `RADIO.DAT`: the codec, and the commentary

Codec dialogue is not in `STAGE.DIR` at all. `menu/radiomes.c` loads it from
`RADIO.DAT` by sector, with a fragment size packed into the radio code, so no
GCL sweep could ever have reached it.

**Integral's `RADIO.DAT` is 6.3x the size of USA's** - 11,198,464 bytes against
1,776,851 - and it splits cleanly in two:

| region | bytes | content |
|---|---:|---|
| `0x0000000`–`0x042C54C` | 4,375,884 | the story codec, **English and Japanese together** |
| `0x042C54C`–`0x0AAC050` | **6,814,468** | **Japanese only - no English dialogue line anywhere in 6.5 MB** |

The English half is USA's script, complete and essentially unchanged: 35,273
dialogue lines / 1,145,926 bytes in Integral against USA's 35,193 / 1,143,269.
**So Integral's codec is already in English** - it is the runtime language
setting that chooses, which is exactly what `[Game] EnglishText` exists to hold
(README, "Unlocks"; the collection's language race). Nothing there needs porting.

The Japanese-only half is the developer commentary. It was read by rendering it
with the game's own font (`rendertext.py`), because none of it is Shift-JIS:

* 「ニンジャにつづきスネークも　装衣えを用意すること」
* 「、デモはゲーム中とは別モデルでやる予定だったので」 - the cutscenes were
  planned to use a different model from the in-game one
* 「さらにこのインテグラル　では」 - *furthermore, in this Integral…*
* 「られたメモリをどうやりくりするか」 - juggling the memory they were given;
  this exact 32-byte run occurs **328 times**, so conversations share boilerplate

95.1% of that region's 2 KB blocks are distinct, so it is real content and not a
repeated pattern. `d0 03`, a Japanese text control code, appears **64,087** times
in Integral's file against **4** in USA's.

### The two small pockets

Both are Integral-only and both are real text, rendered to confirm it:

* **`DEMO.DAT`**, ~1.8 KB across 258 MB, 0 in USA's: 「そしてテロリストの」 -
  story narration.
* **`VOX.DAT`**, ~1.0 KB across 196 MB, 0 in USA's: 「エンジンやプロペラのノイズ」
  - sound-design commentary, sitting beside the audio it describes.

### What this does and does not mean for the port

It is **not** a porting gap. The commentary, the Japanese codec track and both
small pockets are Integral-exclusive: USA never shipped any of it, so there is no
English to copy and the standing rule (port English where English exists, never
invent) leaves every byte of it alone. The port's scope - menus, screens and the
executable's own strings - is unchanged.

What it changes is what this document may claim. The honest statement is:

> Of the text this port covers, nothing with a USA counterpart is still
> Japanese. Of the text on the disc, several megabytes are Japanese, almost all
> of it Integral-exclusive commentary that has no English source and would be
> **translation** rather than porting.

That second sentence had never been written down, and the first had been
standing in for it.

## What Japanese is still there, and why (measured 2026-09-08)

Every figure above is about what the port *covers*. This is the complement: what
a player still meets on the deployed discs - **in the stage archives.** It does
not cover `RADIO.DAT`, `DEMO.DAT` or `VOX.DAT`; the section above this one is
where those are counted, and `RADIO.DAT` alone holds more Japanese than every
figure in this section put together. `py jpremain.py` produces it, and it
is the only tool here that reads **deployed** bytes rather than retail - retail
sectors with every deployed PPF overlaid, and the STAGE.DIR entry followed for
the four families that relocate their stage into DUMMY3M (`en_abst`, `en_brf`,
`en_option`, `en_preope`). Reading the retail LBA would return the unpatched
stage and quietly overstate what is left.

**Totals, stage scripts:**

| | plain English | mixed | **Japanese** |
|---|---:|---:|---:|
| disc 1 | 3,282 | 4 | **153** |
| disc 2 | 3,282 | 4 | **153** |
| VR disc | 10,809 | 183 | **38** |
| all three | 24,373 | 191 | **344** |

`mixed` means letters and glyph codes together, and it is a bucket rather than a
verdict because both cases occur: `<9A0E>Tokyo Game Show, Spring '98<9A0F>` is
English in Integral's own typographic quotes (most of the VR disc's 183), while
`<9009>...<900B>NORMAL<9...>` is Japanese with an English word inside it.

### Disc 1 and disc 2 (identical), 153 each

| owner | stage | n | what it is | why it stays |
|---|---|---:|---|---|
| `chara 53C7` | `abst` | 31 | Integral's **Japanese** location list in `demo.gcx` | Integral-only; its English list is the one the port now gives USA's spellings |
| `chara D44E` | `rank` | 30 | the ranking screen's commentary | Integral-only feature; no USA counterpart (§5.9) |
| `chara D3C0` | `rank` | 16 | more of the same | as above |
| `chara 04F2` | `rank` | 2 | as above | as above |
| `chara CF79` | `title` | 22 | title-stage text, including the disc-swap block | `en_menu3` ports the swap strings but is **raw-disc only** - the collection patches those same bytes (§5.3) |
| `chara D44E` | `title` | 21 | the **1P MODE** pages | Integral-only; 21 Japanese pages before the mode starts |
| `chara B757` | `roll` | 12 | the staff roll | credits, Integral's own |
| `cmd 4AD9` | 12 gameplay stages | 12 | location titles, one per stage | **Japanese on the USA disc too** - USA never translated them |
| `cmd EC9D` | `ending`, `endingr`, `s12a` | 4 | debug/ending strings | Japanese on the USA disc too |
| `chara 566F` | `abst` | 2 | the caption under READ MISSION LOG? | kept by rule - USA draws nothing there; `KEEP_PROMPT_CAPTION` (§5.9, still open) |
| `chara 81C7` | `camera` | 1 | a PHOTO ALBUM prompt | USA leaves the slot empty |

Nothing in that table has a USA English counterpart that the port is refusing to
use. The two categories that could ever change are the `title` rows, which need
the raw-disc variant, and the `abst` caption, which is an open question.

### VR disc, 38

| owner | stage | n | what it is |
|---|---|---:|---|
| `chara 976C` | `option` | 22 | Integral-only option rows; USA's seven help lines are ported, the rest have no counterpart |
| `chara D44E` | `vrsave`, `vrtitle` | 9 | debug windows; USA carries the identical Japanese |
| `chara 5667` | `vrtitle` | 4 | the PocketStation help line, its prompt and はい/いいえ - USA's fifth EXTRA item is STAFF CREDIT, a different feature (§6) |
| `chara 81C7` | `camera` | 1 | the same PHOTOGRAPHING prompt as the main discs |

### The executables

Measured the same way, on the deployed executable:

* **item and weapon descriptions: 0 Japanese.** 26 item and 11 weapon strings,
  all English. The frozen Ration/Ketchup pair reads `Frozen.|Melt it before|you
  use.` - USA has its own text for those, so they were ported after all.
* **the MP5 SD description: 1 Japanese**, at file `0x2304`, immediately past
  `ARENA_B`'s exclusive end so the repack never touches it. Integral-only weapon
  on VERY EASY only; USA has neither (README, "Descriptions that change with the
  game state").
* **the memory-card message pool: 4 of 17 Japanese** - the four progress lines
  USA draws nothing for (now saving, save complete, now loading, load complete).
  The other 13 are English.

So per main disc the true total is **153 + 5 = 158**, and the VR disc's own
executable pools hold the same shape of leftovers (`vr_en_savemsg`'s two
untranslated indices, the MP5, the mine-detector difficulty line).

### Not covered by any of this

Texture lettering - Japanese drawn as art rather than stored as text - is
outside every tool here. The VR camera's EXORCISE textures are the known case
and are deferred; nothing else has been inventoried.

## The list itself: `jplist.py` (2026-09-09)

The two sections above describe what is left and where; neither was a *list*.
`py jplist.py` writes one - every untranslated Japanese string on all three
discs, one per line, to `work/japanese-inventory.tsv`:

    disc  source                      offset      bytes glyphs kana_kanji  text
    disc1 STAGE.DIR/abst/chara 566F   0x0            48     24         10  #{<9090><90CC>...
    disc1 RADIO.DAT                   0x90287F      152     76         70  <8113><812E>...

**190,180 strings, 3,318,254 kana/kanji glyph slots**, in a 32 MB file. It is
regenerated rather than committed - the repository keeps the counts, the method
and the tool.

| disc | source | strings | kana/kanji |
|---|---|---:|---:|
| disc 1 | `RADIO.DAT` | 94,246 | 1,652,457 |
| disc 1 | `DEMO.DAT` | 576 | 4,612 |
| disc 1 | `VOX.DAT` | 338 | 2,674 |
| disc 1 | `STAGE.DIR` | 98 | 764 |
| disc 2 | `RADIO.DAT` | 94,246 | 1,652,457 |
| disc 2 | `DEMO.DAT` | 318 | 2,538 |
| disc 2 | `VOX.DAT` | 229 | 1,798 |
| disc 2 | `STAGE.DIR` | 98 | 764 |
| VR | `STAGE.DIR` | 31 | 190 |
| | **total** | **190,180** | **3,318,254** |

`BRF.DAT` and `FACE.DAT` appear nowhere, and that is a result rather than an
omission - see below.

### What makes it a list of *Japanese* and not of bytes

Three tests, each of which was forced by a wrong answer earlier in this project:

1. **A run needs kana or kanji, not just high bytes.** `CORE` is the `0x81`,
   `0x82` and `0x96` banks; `0x80`, `0x90`, `0x9A`, `0xC1`, `0xC2` and `0xD0`
   are allowed *inside* a run without counting toward its length, because Latin
   letters, punctuation, button glyphs and text control codes all appear inside
   Japanese strings. That is what keeps the MP5 SD description (Latin name,
   Japanese body) in the list and pure-Latin `Tank Hanger` out of it.
2. **Repeated glyphs are not prose.** `BRF.DAT` matched 56 runs, every one a
   single code repeated - `<8283><8283><8283>…`. A run needs four distinct
   glyphs and no glyph taking more than half of it.
3. **Anything the USA disc also has is dropped.** This is the test that does the
   real work: it removed all 56 of `BRF.DAT`'s runs and all of `FACE.DAT`'s,
   because they are image data present on both releases. It would equally remove
   text USA left Japanese - a different category from Integral-exclusive
   content, and one the stage-archive sections above track separately.

### Where it disagrees with `jpremain.py`, and which to believe

`jplist.py` lists 98 stage-archive strings a disc where `jpremain.py` reports
153. The difference is `0x9Axx`: it holds real glyphs, but it is also where
Integral keeps its typographic quotes, so counting it would classify
`<9A0E>Tokyo Game Show, Spring '98<9A0F>` as Japanese. `jplist.py` therefore
excludes it and loses strings built only from that bank, such as the `cmd 4AD9`
location titles.

**For the stage archives, `jpremain.py` is the authority** - it works on complete
parsed records and weighs glyphs against Latin letters, which is the better test
where there is no binary to guard against. `jplist.py` earns its place on the
raw files, which nothing else reads at all.

### What the list is for

Not porting. Every string in it is Integral-exclusive, so there is no USA English
to copy and the standing rule leaves all of it alone. The list exists because
"how much untranslated Japanese is on this disc, and where exactly" had no answer
here until now, and because anyone who ever wants that commentary in English
needs a starting point - which is a translation project, not this one.

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
