# Changes worth a separate upstream pull request

The `integral-english-text` branch carries two kinds of work: the MGS Integral
English port (everything under `tools/integral-english/`, its PPFs and its
notes) and fixes to MGSM2Fix itself that help any Master Collection MGS1 player,
port or no port. This file tracks the second kind so it can be offered upstream
on its own. Add an entry whenever a commit touching `src/`, `MGSM2Fix.ini` or
`README.md` has a benefit beyond the port; leave port-only changes out.

| commit | change | who benefits | status |
|---|---|---|---|
| `5921ec9` | Ketchup: defer the RAM mirror of executable writes so PPF patches to the executable actually take effect | every Ketchup user (all titles) | in use daily since 2026-08 |
| `640f359`, `eccecb9` | `[Game] EnglishText`: hold Integral's language setting to English until the title screen has settled, so a new game starts in English instead of Integral's Japanese default | any Integral player, no port needed | in use since 2026-08-28 |
| `a57859e`, `d386a09` | `[Game] UnlockBriefing`: show all sixteen BRIEFING items on the title screen (Integral and USA); `var_buf` derived from the `scene_name` define, not hardcoded (the collection's USA executable differs from retail) | Integral and USA players who want the briefing menu complete | in use; note it seeds a new game's `var_buf` with the flags |
| `6fb21a5`, `4528f91` | `M2Game::SQOnRamWrite` / `SQOnRamRead` hooks with Squirrel call-stack logging (`SQHook::CallStack`); EnglishText guard that restores English when cleared outside the option screen; language-byte change log | tooling for any title; the guard is Integral only | verified: the trace named the collection's per-frame rewrite on its first run |
| `a5209ce` | `[Patches] PreserveConfiguration`: the collection's `_update_option_button_setting` rewrites all of `GM_Configuration` every frame from a copy read a moment earlier, so any setting the game wrote in between (language, caption, sound, vibration, radar, first-person reverse, tuxedo bit) can be lost. Re-read the word at the write and carry only the bits the collection changed. Address `scene_name + 0x14`, every MGS1 version | every MGS1 player in the collection | tested 2026-09-03: option toggles then 1P MODE ran clean (address resolved, hooks live, no intervention needed that run, no regressions); the race it guards against is intermittent, so a "Preserved GM_Configuration" line is the proof still to be caught |

Not for upstream: `tools/integral-english/*`, the PPF outputs under the mods
folder, and README sections that describe the port itself.
