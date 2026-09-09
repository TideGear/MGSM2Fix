Integral English text - Master Collection build (collection variant)

Copy the mods folder into your MGS1 game folder. It holds three sets:
  mods/INTEGRAL/INTEGRAL/0   Integral disc 1 - ten INTEGRAL_disc1_en_*.ppf
  mods/INTEGRAL/INTEGRAL/1   Integral disc 2 - ten INTEGRAL_disc2_en_*.ppf
  mods/INTEGRAL/VR-DISK      Integral's VR disc (SLPM-86249) - seven INTEGRAL_vr_en_*.ppf
Replace older copies of the same files, and first remove any duplicate or
experimental PPF from those folders, including any en_menu3, *_movie_e3 or
*_unlock_* file. Every patch in this package writes its own bytes and no two of
them overlap, so file order does not matter - but install a disc's files as a
set, and if you are replacing an older package, replace
INTEGRAL_vr_en_missions.ppf and INTEGRAL_vr_en_movie.ppf together: in packages
before 2026-09-08 those two shared bytes and the pair is not interchangeable.

This package requires the MGSM2Fix integral-english-text branch (the deferred
executable RAM mirror and EnglishText) with EnglishText = true. It does not
include MGSM2Fix itself. Keep DisableRAM and DisableCDROM false for
achievements; the patches need neither.

This is the collection variant: four brightness-help lines, KEY CONFIG handed to
the collection's Control Settings panel, and no en_menu3 (the collection patches
the title screen's disc-swap block itself, and the two layouts do not mix). It is
not the raw-PSX variant. Do not apply this package to an original PlayStation
disc; that needs a build made with --variant raw.

Verification at packaging (NextSteps.md in the repository has the current list):
every main-disc family has been seen on screen on disc 1 except the game's own
disc-swap prompts, which only the story's disc change can reach; the controller-
port subtitle in the Psycho Mantis room, which needs a second controller in port
2; and the four MISSION LOG location names that now read USA's spelling
(Tank Hangar, Medi room, Cmnder room, Cmnd room). Disc 2 is
byte-identical wherever the patches touch it but has not been played across
that change. On the VR disc the option screen, KEY CONFIG, mission windows, item
and weapon descriptions and the MOVIE captions have been seen; a mission RESULT
window, the save and load messages and the PHOTOGRAPHING memory-card messages
have not. Some Japanese is retained on purpose because USA provides no English
counterpart; no new translation has been made, and USA's spelling is kept.


CREDITS

The option screen, Previous Operations and the MISSION LOG contain code
compiled from the MGS1 decompilation by FoxdieTeam:

    https://github.com/FoxdieTeam/mgs_reversing   (commit 7964de7)

That work is theirs and this port would not exist without it. The mod loader
and the fix this port targets are MGSM2Fix by nuggslet:

    https://github.com/nuggslet/MGSM2Fix

Every English string is copied verbatim from Konami's USA release. Nothing has
been translated, and no game data is redistributed with these patches.

Uninstall: remove the ten INTEGRAL_discN_en_*.ppf files from each numbered
folder and the seven INTEGRAL_vr_en_*.ppf files from VR-DISK.
SHA256SUMS.txt and build-report.json identify the packaged build and validation.
