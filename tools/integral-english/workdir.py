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
    print('ROOT =', ROOT)
    print('WORK =', WORK, '(exists)' if os.path.isdir(WORK) else '(MISSING)')
