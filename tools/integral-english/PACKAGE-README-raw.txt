Integral English text - RAW PSX DISC build

This is the raw-disc variant. It patches original PlayStation disc images, not
the Master Collection. If you are playing the Master Collection, stop here and
use the collection build instead: this one will not work there, and the title
screen's disc-swap patch (en_menu3) actively breaks it, because the collection
patches those same bytes itself.

WHAT IT IS FOR

  Integral disc 1   SLPM-86247
  Integral disc 2   SLPM-86248
  Integral VR disc  SLPM-86249

Each folder in mods/ holds one disc's patches. The folder names are the
collection's and are kept only so the two builds can be compared file by file;
apply the PPFs to the matching disc image with any PPF3 tool.

APPLY THE WHOLE SET, PER DISC

Every PPF for a disc must be applied, and the *_zz_ecc.ppf one must be applied
last. It carries the recomputed EDC and ECC of every sector the other patches
touch, worked out from the finished state of the complete set. Apply only some
of them and the error-correction data will describe a disc you do not have.
Order among the others does not matter.

Each patch carries a PPF3 block check, so a tool that honours it will refuse an
image that is not the disc the patch was built against.

WHAT DIFFERS FROM THE COLLECTION BUILD

  - the brightness help text keeps all six of USA's lines, including
    "Press the O button to return to the option screen.", which is true on a
    real PlayStation and is why the collection drops it;
  - KEY CONFIG is Integral's own screen with USA's English labels, because
    there is no Control Settings panel here to intercept it;
  - en_menu3 is included: the title screen's disc-swap prompt in English.

VERIFIED, AND NOT

The text itself is the same port as the collection build, which has been read
on screen extensively - see NextSteps.md in the repository for exactly which
screens. What has NOT been done is running this variant on a real disc image:
it builds, it packages, and every sector it rewrites was checked against that
sector's own stored parity before the new parity was computed, but nobody has
applied it to a disc image and booted it. Treat it as untested in that specific
sense, and please report what you find.

Some Japanese is retained on purpose, wherever the USA release has no English
counterpart. No new translation has been made, and USA's spelling is kept.


CREDITS

The option screen, Previous Operations and the MISSION LOG contain code
compiled from the MGS1 decompilation by FoxdieTeam:

    https://github.com/FoxdieTeam/mgs_reversing   (commit 7964de7)

That work is theirs and this port would not exist without it. The mod loader
and the fix this port targets are MGSM2Fix by nuggslet:

    https://github.com/nuggslet/MGSM2Fix

Every English string is copied verbatim from Konami's USA release. Nothing has
been translated, and no game data is redistributed with these patches.

UNINSTALL

PPF3 patches here carry no undo data. Keep an unpatched copy of your disc
images before applying anything.
