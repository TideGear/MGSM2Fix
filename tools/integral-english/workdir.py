"""Where the port's working data lives, resolved once for every tool.

    from workdir import WORK          # .../work  - the directory itself
    WORK + '/int1_stage.dir'          # the extracted STAGE.DIRs, exes, PPF backups

Resolution, first match wins:

  1. INTEGRAL_ENGLISH_WORK          environment variable naming the ROOT that
                                    holds work/ (not work/ itself)
  2. D:/mgsbuild/integral-english-work   the durable home since 2026-09-03
  3. the current directory          the old convention, kept so `cd <root>`
                                    still works

Until 2026-09-03 every tool opened 'work/...' relative to wherever it was run
from, and the only copy of that data sat in a session scratchpad under Windows
Temp. The data moved; this module is what lets the tools follow it without each
one growing its own path logic.
"""
import os

_DEFAULT_ROOT = r'D:/mgsbuild/integral-english-work'

# --- which build is being made.
#
# Two constants differ between the collection patch and a raw PSX disc patch,
# and until 2026-09-07 both were edited by hand before a raw build:
#
#   SC_KEEP_LINES               optsctext.py   4 collection / 6 raw
#   OPTION_MC_CONTROL_SETTINGS  opt.c          1 collection / 0 raw
#
# plus `en_menu3`, which exists ONLY for the raw disc (the collection patches
# that block itself - README, "Why `en_menu3` is raw-disc only"). VARIANT is the
# one switch; `rebuild.py --variant raw` sets it for every tool it runs, and a
# tool run by hand picks it up from the environment the same way.
VARIANT = os.environ.get('INTEGRAL_ENGLISH_VARIANT', 'collection').strip().lower()
if VARIANT not in ('collection', 'raw'):
    raise SystemExit('INTEGRAL_ENGLISH_VARIANT must be "collection" or "raw", not %r' % VARIANT)
RAW = VARIANT == 'raw'


def pick(collection, raw):
    """the value for this build: pick(4, 6) is 4 normally, 6 under --variant raw"""
    return raw if RAW else collection


def _root():
    env = os.environ.get('INTEGRAL_ENGLISH_WORK')
    if env:
        return env
    if os.path.isdir(os.path.join(_DEFAULT_ROOT, 'work')):
        return _DEFAULT_ROOT
    return os.getcwd()


ROOT = _root()
WORK = os.path.join(ROOT, 'work').replace('\\', '/')
GAME = os.environ.get('INTEGRAL_ENGLISH_GAME', 'D:/Steam/SteamApps/common/MGS1')
DECOMP = os.environ.get('INTEGRAL_ENGLISH_DECOMP', 'D:/mgsbuild/d')

if __name__ == '__main__':
    print('VARIANT =', VARIANT)
    print('ROOT =', ROOT)
    print('WORK =', WORK, '(exists)' if os.path.isdir(WORK) else '(MISSING)')
