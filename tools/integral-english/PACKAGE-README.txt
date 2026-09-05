Integral English text - Master Collection development build

Copy the mods folder into your MGS1 game folder. The two numbered folders are
Integral discs 1 and 2. Replace older copies of the same nine patch families;
remove duplicate/experimental PPFs, including the disabled en_menu3 and unlock
patches. Ketchup loads every PPF in each folder.

This package requires the MGSM2Fix integral-english-text branch with the
deferred executable RAM mirror fix and EnglishText enabled. It does not include
MGSM2Fix itself. Keep DisableRAM and DisableCDROM false for achievements.

This is the collection variant: four brightness-help lines and interception
of KEY CONFIG by the collection's Control Settings. It is not the raw-PSX
variant. Do not apply this package to an original PlayStation disc.

Known unfinished work: the title screen's disc-swap copy (en_menu3) and the VR
disc. Disc 2's patches pass static verification but still need a normal-gameplay
disc transition test. The Mission Log (en_abst) and the item-text fixes of
2026-09-05 were verified on screen the same day. Some Japanese is retained because USA provides no English
counterpart; no new translation has been made. Existing USA spelling is kept.

Uninstall: remove the nine INTEGRAL_discN_en_*.ppf files from each folder.
SHA256SUMS.txt and build-report.json identify the packaged build and validation.
