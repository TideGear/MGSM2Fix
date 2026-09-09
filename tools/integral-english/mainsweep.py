"""Is any main-disc UI text still Japanese where the USA release has English?

The VR disc has had this since 2026-09-06 (`vr_sweep.py`) and it is what lets
that disc's coverage be stated as a measurement rather than a hope. Discs 1 and
2 had only `audit_text.py`, which inventories *candidates* by framing and
explicitly cannot say whether a candidate has an English counterpart - which is
why `COVERAGE.md` still lists about 160 unclassified strings. This closes that
gap the same way `vr_sweep` did.

THE METHOD, and why it is stronger than counting strings

Every string lives inside a GCL command, and a command is identified by what it
spawns - `chara 0x9906` is the generic numbered-text module, `chara 0xCF79` the
title actor, and so on. Tallying strings *by owner* on both discs at once turns
a pile of bytes into a comparison:

    owner X:  Integral 40 Japanese, 0 English | USA 0 Japanese, 41 English

is a porting target. Whereas

    owner Y:  Integral 12 Japanese, 0 English | USA 12 Japanese, 0 English

is text USA never translated either, and

    owner Z:  Integral 0 Japanese, 30 English | USA 0 Japanese, 30 English

is already done. No heuristic about what "looks Japanese" has to be trusted:
the two discs are read the same way and compared with each other.

WHAT IT READS

Retail bytes on both sides, from the stage archives the build already extracts
(`int1_stage.dir` / `int2_stage.dir`, and `usa1_stage.dir` / `usa2_stage.dir` -
the REAL USA discs, not `us1_stage.dir`, which the port established is not the
USA build). Retail rather than the deployed state on purpose: the point is to
enumerate everything USA has in English, and then subtract what the port
already covers, so a gap cannot hide behind a patch that is already there. The
stages the port owns are listed in PORTED below and reported separately.

    py mainsweep.py                  disc 1
    py mainsweep.py --disc 2
    py mainsweep.py --samples        show an example string per owner

A main-game stage differs from a VR one in a way that matters here: its cache
section can hold SEVERAL `.gcx` scripts and `scenerio.gcx` need not be last, so
this walks every one rather than using `vrlib.stage_gcx`, which asserts the VR
layout (that assertion is right for the VR disc and is what lets a rebuilt
script grow there).
"""
import argparse
import os as _os
import sys as _sys
from collections import defaultdict

_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import portio
from audit_text import game_text
from vrlib import Gcx, cache_files, chunk_index, parse_arg, walk_commands, be16
from workdir import WORK

CMD_CHARA = 0x9906

# Stages the port already owns, so a residual Japanese string in them is
# accounted for rather than a finding. Each is named after the patch family.
PORTED = {
    'option':  'en_option',
    'preope':  'en_preope',
    'brf':     'en_brf',
    'abst':    'en_abst',
    'camera':  'en_camsave',
    'menu':    'en_menu',
    'title':   'en_menu / en_menu3 (raw only)',
    'change':  'en_menu2',
    'demosel': 'en_menu2',
    # `s07br` is Integral-only, so it never enters this sweep's shared-name
    # universe at all; it is listed because `en_pad2` ports it too.
    's07b':    'en_pad2',
    's07br':   'en_pad2',
}


def scripts(stage_data):
    """every GCL script in a stage's cache section, not merely the last one"""
    tags, payloads, _ = portio.stage(stage_data)
    try:
        ci = chunk_index(tags)
        files = cache_files(tags)
    except (IndexError, KeyError):
        return
    for ext, _tid, start, _end in files:
        if ext != 'g':
            continue
        try:
            yield Gcx(payloads[ci], start)
        except Exception:
            continue                     # not a script we can walk; counted as skipped


def owner_of(body, cmd):
    if cmd.id == CMD_CHARA:
        args = cmd.args()
        if args and args[0].kind == 'STRID':
            return 'chara %04X' % be16(body, args[0].pos + 1)
    return 'cmd   %04X' % cmd.id


def strings(gcx):
    """(owner, raw bytes) for every non-empty STRING in the script and its procs"""
    for body in [gcx.script] + [b for _, b in gcx.procs]:
        try:
            block = parse_arg(body)
        except Exception:
            continue
        for cmd, _lang, _path in walk_commands(body, block):
            who = owner_of(body, cmd)
            for value in cmd.values:
                pool = ([value] if value.kind == 'STRING'
                        else [v for v in value.values if v.kind == 'STRING']
                        if value.kind == 'OPTION' else [])
                for sv in pool:
                    raw = body[sv.pos+2:sv.end]
                    if len(raw) > 1:
                        yield who, raw


def tally(stage_data, into, name):
    for gcx in scripts(stage_data):
        for who, raw in strings(gcx):
            text, japanese = game_text(raw[:-1])
            entry = into[who]
            if text is None:
                entry['odd'] += 1
            elif japanese:
                entry['jp'] += 1
                entry['stages'].add(name)
                entry.setdefault('sample', text)
            else:
                entry['en'] += 1


def blank():
    return defaultdict(lambda: {'jp': 0, 'en': 0, 'odd': 0, 'stages': set()})


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--disc', type=int, choices=(1, 2), default=1)
    parser.add_argument('--samples', action='store_true')
    args = parser.parse_args()

    isd = open('%s/int%d_stage.dir' % (WORK, args.disc), 'rb').read()
    usd = open('%s/usa%d_stage.dir' % (WORK, args.disc), 'rb').read()
    names = sorted(set(portio.entries(isd)) & set(portio.entries(usd)))
    print('disc %d: %d stage(s) present on both discs\n' % (args.disc, len(names)))

    I, U = blank(), blank()
    for name in names:
        tally(_stage_bytes(isd, name), I, name)
        tally(_stage_bytes(usd, name), U, name)

    targets, done, both_jp = [], [], []
    for who in sorted(set(I) | set(U)):
        i, u = I[who], U[who]
        # A target is any owner Integral still has Japanese in where USA has
        # English AT ALL. Requiring USA to be free of Japanese was too strict
        # and hid the mission log's own actor, which USA ships as 907 English
        # strings beside 2 Japanese ones.
        if i['jp'] and u['en']:
            targets.append((who, i, u))
        elif i['jp'] and u['jp']:
            both_jp.append((who, i, u))
        elif i['en']:
            done.append((who, i, u))

    print('%-12s %7s %7s | %7s %7s   stages' % ('owner', 'INT jp', 'INT en', 'USA jp', 'USA en'))
    print('-- USA has English where Integral is Japanese: PORTING TARGETS --')
    if not targets:
        print('   (none)')
    for who, i, u in sorted(targets, key=lambda t: -t[1]['jp']):
        covered = sorted({PORTED[s] for s in i['stages'] if s in PORTED})
        rest = sorted(s for s in i['stages'] if s not in PORTED)
        note = ('  [covered by %s]' % ', '.join(covered)) if covered and not rest else ''
        if not note:
            note = '  <-- NOT covered by any patch family'
        print('%-12s %7d %7d | %7d %7d   %s%s'
              % (who, i['jp'], i['en'], u['jp'], u['en'],
                 ', '.join(sorted(i['stages'])[:6]) + ('...' if len(i['stages']) > 6 else ''), note))
        if args.samples:
            print('             e.g. %s' % (i.get('sample') or '')[:72])

    print('\n-- Japanese on BOTH discs: nothing to port (USA never translated it) --')
    for who, i, u in sorted(both_jp, key=lambda t: -t[1]['jp'])[:12]:
        print('%-12s %7d %7d | %7d %7d   %s'
              % (who, i['jp'], i['en'], u['jp'], u['en'], ', '.join(sorted(i['stages'])[:5])))
    if len(both_jp) > 12:
        print('   ... and %d more owners' % (len(both_jp) - 12))

    ijp = sum(v['jp'] for v in I.values())
    ien = sum(v['en'] for v in I.values())
    ujp = sum(v['jp'] for v in U.values())
    uen = sum(v['en'] for v in U.values())
    print('\nIntegral: %d Japanese, %d English   USA: %d Japanese, %d English'
          % (ijp, ien, ujp, uen))
    unported = sum(i['jp'] for _, i, _ in targets
                   if any(s not in PORTED for s in i['stages']))
    print('Japanese strings whose owner has English on the USA disc, in stages the'
          ' port does NOT already own: %d' % unported)
    return 0


def _stage_bytes(sd, name):
    lba, _ = portio.entries(sd)[name]
    tags, payloads, offsets = portio.stage(sd, name)
    size = sum(len(v) for v in payloads.values())
    del tags, offsets, size
    # portio.stage() already resolved the stage; re-slice its raw extent so the
    # Gcx offsets inside the chunk stay meaningful.
    base = lba * 2048
    count = int.from_bytes(sd[base+2:base+4], 'little')
    return sd[base:base + count * 2048]


if __name__ == '__main__':
    _sys.exit(main())
