#!/usr/bin/env python
"""Port the VR MOVIE selection captions from USA's VR disc.

WHAT THE CAPTIONS ARE
---------------------
The one line under the thumbnail on EXTRA -> MOVIE. The *description* shown when
a clip opens is already English (it comes from `vr_en_missions`' window text);
this is the short caption beside the title, and it is still Japanese.

They live in `OPTION 't'` of the `movie` script's `CMD 9906` whose chara is
`0xFAA8` (the second id is `0x1D31`). Integral holds four records, USA six,
because **USA splits each TGS caption across two lines**:

    Integral                                  USA
    +125 36B  東京ゲームショウ'98春 出展映像A    +125 25B  Exhibition clip {"}A{"}for
                                              +140 33B  the Tokyo Game Show, Spring '98.
    +14B 36B  ...the same with B               +163 + +17E  likewise
    +171 23B  E3{(}97/6{)}...映像              +1A1 26B  Video clip from E3 (6/97)
    +18A  1B  (empty terminator)               +1BD  1B  (empty terminator)

Confirmed on screen 2026-09-06 from a USA VR shot beside an Integral one: USA
really does draw two lines, and its EXIT sits ~19 display px higher to make room.

WHY THE ARITHMETIC IS THE VERIFICATION
--------------------------------------
Replacing each Integral record with USA's counterpart(s) changes the record
bytes by +24, +24 and +3 = **+51**, and Integral's `t` is 105 bytes against
USA's 156 - exactly 105 + 51. So a correct edit makes Integral's `t` payload
**byte-identical to USA's**, which `verify()` asserts. Everything outside `t`
stays Integral's, and every enclosing container is re-stamped by
`Gcx.build()` the way `vr_option.port_chain` does it.

WHAT IS PROVEN, AND THE ONE THING THAT IS NOT
---------------------------------------------
The caption builder in the `movie` overlay was diffed against USA's
instruction-for-instruction (Integral +FE44, USA +FF44, the function ends at
+C0). It is **identical** but for one immediate - `addiu v1, zero, 832` against
USA's `768`, the font VRAM column, the same 832/704 pattern `abst` has - and its
read loop is `GetOption('t')` then `NextStr`/`GetString` until NULL, i.e. a
while-loop, **not a fixed count**, so extra records are read. Diffing a whole
0x1200-byte window at that alignment found 38 differences and every one is a
data-address displacement, no logic difference at all.

**Unresolved: how one clip's line(s) are selected.** With identical code,
Integral's four records give KCB lines [A][B][E3][] and USA's six give
[A1][A2][B1][B2][E3][], so something must map clip -> line(s) and it is not in
the code that was compared. The candidates are the caption command's other two
options, which DO differ:

    OPTION 'f'   Integral  VAR 11 00 04 80      USA  VAR 11 00 04 82
    OPTION 'm'   Integral  VAR 12 00 04 82      USA  VAR 12 00 04 81

Those are GCL variable *references*, and copying USA's ids would make Integral
read slots its own scripts never write, so they are deliberately left alone.

THEREFORE THIS SCRIPT ONLY STAGES ITS PPF; it never deploys.
If the selection is record-count driven the captions come out right; if it is
`clip -> line` arithmetic, clips B and E3 will show the wrong English line,
which is worse than leaving them Japanese (misattributed text, against the
port's rule). One launch decides it. Deploy by hand after checking all three
clips - the `vr_unlock` aid opens them - and if clip B is wrong, the answer is
the 'f'/'m' variables above, not this chain edit.

    py vr_movie.py            # stages work/INTEGRAL_vr_en_movie.ppf, never deploys
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from workdir import WORK, GAME
import struct, sys

import portio
from vrlib import (INT_STAGE, USA_STAGE, int_disc, stage_lba, stage_bytes, stage_gcx,
                   parse_arg, emit_arg, Gcx, inplace_records, write_ppf, be16, CMD_CHARA,
                   walk_commands)

PPF_NAME = 'INTEGRAL_vr_en_movie.ppf'
DESC = 'MGS Integral VR-DISC: English movie captions'
assert len(DESC) <= 50
CAPTION_CHARA = 0xFAA8
LETTER = 't'
# Integral record index -> the USA record indices that replace it
PAIRING = {0: (0, 1), 1: (2, 3), 2: (4,)}
EXPECT_DELTA = 51

# THE SAFE SUBSET, and why it is safe under ANY clip->line mapping.
# Integral's records are [A][B][E3][empty] and USA's E3 caption is a single
# record too, so swapping record 2's text leaves the record COUNT and ORDER
# exactly as retail: whatever maps a clip to record 2, record 2 is still the E3
# caption, now in USA's English. Nothing structural changes, so this needs no
# knowledge of the selection mechanism and cannot misattribute a caption.
# The two TGS captions are the ones that need one Integral record to become two
# USA lines, and those wait for the mapping to be settled in game.
SAFE_PAIRING = {2: (4,)}
SAFE_NAME = 'INTEGRAL_vr_en_movie_e3.ppf'


def captions(gcx):
    """(script bytes, parsed block, the OPTION 't' and its STRING records) of the
    CMD 9906 whose chara is CAPTION_CHARA. The command is NOT top level - it sits
    inside an enclosing command's `-e` option, wrapped in an ARG - so this walks
    the tree with vrlib.walk_commands rather than scanning `parse_arg`'s result."""
    body = gcx.script
    block = parse_arg(body)
    for c, _lang, _path in walk_commands(body, block):
        if c.kind == 'COMMAND' and c.id == CMD_CHARA:
            a = c.args()
            if a and a[0].kind == 'STRID' and be16(body, a[0].pos + 1) == CAPTION_CHARA:
                o = c.option(LETTER)
                assert o is not None, "the caption command has no -%s option" % LETTER
                return body, block, o, [v for v in o.values if v.kind == 'STRING']
    raise AssertionError('caption command (chara %04X) not found' % CAPTION_CHARA)


def composite(isd):
    """The `movie` stage as the game actually sees it: retail plus every DEPLOYED
    VR PPF's writes to it.

    `vr_en_missions` already rebuilds this stage - it is where the clips'
    English descriptions and the merged script-local font come from - so a
    caption PPF built from retail would overwrite all of that. Caught 2026-09-06
    by a byte-overlap check between the deployed PPFs: a retail-based build
    clashed with `vr_en_missions` over all 704 of its bytes. Same trap as
    `menu.ppf`'s chain records on the main game (README, "The sc_text texture
    port"): build from the composite, and the emitted records then carry only
    the caption delta.
    """
    base = bytearray(stage_bytes(isd, 'movie'))
    lba = stage_lba(int_disc(), isd, 'movie')
    lo, hi = lba * 2352, (lba + len(base) // 2048) * 2352
    applied = {}
    d = _os.path.join(GAME, 'mods/INTEGRAL/VR-DISK')
    for name in sorted(_os.listdir(d)):
        if not name.endswith('.ppf') or name == PPF_NAME or name == SAFE_NAME:
            continue
        n = 0
        for off, data in portio.read_ppf(_os.path.join(d, name)):
            if not (lo <= off < hi):
                continue
            sec, within = divmod(off - 24, 2352)
            fo = (sec - lba) * 2048 + within
            if fo < 0 or fo + len(data) > len(base):
                continue
            base[fo:fo + len(data)] = data
            n += len(data)
        if n:
            applied[name] = n
    print('composite base: %s' % (', '.join('%s %d bytes' % kv for kv in applied.items()) or 'retail only'))
    return bytes(base)


def build(pairing=PAIRING, expect_delta=EXPECT_DELTA, check_usa=True):
    isd, usd = open(INT_STAGE, 'rb').read(), open(USA_STAGE, 'rb').read()
    idata = composite(isd)
    itags, ipay, ici, ifiles, igcx = stage_gcx(idata)
    utags, upay, uci, ufiles, ugcx = stage_gcx(stage_bytes(usd, 'movie'))
    ibody, iblock, iopt, irecs = captions(igcx)
    ubody, ublock, uopt, urecs = captions(ugcx)
    assert len(irecs) == 4 and len(urecs) == 6, (len(irecs), len(urecs))
    print('caption option -%s: Integral %d records / %d bytes, USA %d records / %d bytes'
          % (LETTER, len(irecs), iopt.u8, len(urecs), uopt.u8))

    replace, delta = {}, 0
    for i, sources in sorted(pairing.items()):
        blob = b''
        for j in sources:
            rec = ubody[urecs[j].pos:urecs[j].end]
            assert rec[0] == 7 and rec[1] == len(rec) - 2, 'USA record %d is malformed' % j
            blob += rec
            txt = rec[2:-1]
            print('  record %d <- USA %d (%2d B) %r' % (i, j, len(txt),
                  ''.join(chr(b) if 32 <= b < 127 else '#' for b in txt)[:46]))
        old = ibody[irecs[i].pos:irecs[i].end]
        replace[id(irecs[i])] = blob
        delta += len(blob) - len(old)
    assert delta == expect_delta, 'record delta is %+d, expected %+d' % (delta, expect_delta)

    igcx.script = emit_arg(ibody, iblock, replace)
    new_gcx = igcx.build()
    payloads = dict(ipay)
    payloads[ici] = ipay[ici][:igcx.start] + new_gcx
    payloads[ici] += bytes(-len(payloads[ici]) % 4)
    stage = portio.pack_stage(itags, payloads)
    assert len(stage) == len(idata), 'stage changed size: %d -> %d' % (len(idata), len(stage))
    verify(stage, ibody, irecs, ubody, uopt, urecs, pairing, check_usa)
    return idata, stage


def verify(stage, ibody, irecs, ubody, uopt, urecs, pairing, check_usa):
    """Every ported record must equal USA's byte for byte, every record the
    pairing does not name must still equal Integral's, and the script must
    round-trip. For the full port the whole -t payload equals USA's."""
    tags2, pay2, ci, files, gcx = stage_gcx(stage)
    body, block, opt, recs = captions(gcx)
    want_n = len(irecs) + sum(len(v) - 1 for v in pairing.values())
    assert len(recs) == want_n, 'rebuilt option has %d records, want %d' % (len(recs), want_n)
    k = 0
    for i in range(len(irecs)):
        if i in pairing:
            for j in pairing[i]:
                assert body[recs[k].pos:recs[k].end] == ubody[urecs[j].pos:urecs[j].end], \
                    'record %d is not USA record %d' % (k, j)
                k += 1
        else:
            assert body[recs[k].pos:recs[k].end] == ibody[irecs[i].pos:irecs[i].end], \
                'record %d should still be Integral\'s' % k
            k += 1
    if check_usa:
        got, wanted = body[opt.pos:opt.end], ubody[uopt.pos:uopt.end]
        assert got == wanted, 'the -t option is not byte-identical to USA'
        print('verified: -t byte-identical to USA (%d bytes, %d records); script round-trips; '
              'stage stays %d bytes' % (len(wanted), len(recs), len(stage)))
    else:
        print('verified: %d record(s) taken from USA, the rest still Integral\'s; %d records total; '
              'script round-trips; stage stays %d bytes'
              % (sum(len(v) for v in pairing.values()), len(recs), len(stage)))
    assert emit_arg(body, block, {}) == body, 'the rebuilt script does not round-trip'


def emit(name, pairing, expect_delta, check_usa, note):
    print('\n--- %s ---' % name)
    base, stage = build(pairing, expect_delta, check_usa)
    isd = open(INT_STAGE, 'rb').read()
    lba = stage_lba(int_disc(), isd, 'movie')
    # `base` is the COMPOSITE (retail + vr_en_missions), so the diff is only the
    # caption delta. merge_gap=0 keeps each record to the bytes that actually
    # change: with the default 64 they span unchanged bytes too and overlap
    # vr_en_missions' records by ~750 bytes, which would leave the result
    # depending on which PPF Ketchup applied last. Exact records leave overlap
    # only where this patch deliberately overrides a byte vr_en_missions wrote,
    # and there it must win - Ketchup loads a folder in name order and
    # INTEGRAL_vr_en_missions.ppf sorts before INTEGRAL_vr_en_movie.ppf.
    # (Cleanest long-term fix: fold the captions into vr_windows.py so one patch
    # owns the stage. Not done blind - regenerating vr_en_missions would rewrite
    # 3.3 MB of verified output.)
    recs = inplace_records(lba, base, stage, merge_gap=0)
    write_ppf(_os.path.join(WORK, name), recs, DESC)
    print('%s: %d records, %d bytes  %s' % (name, len(recs), sum(len(d) for _, d in recs), note))
    return stage


def main():
    # the safe subset: the E3 caption alone, structure untouched
    safe_delta = None
    isd, usd = open(INT_STAGE, 'rb').read(), open(USA_STAGE, 'rb').read()
    _i, _p, _c, _f, ig = stage_gcx(composite(isd))
    _i2, _p2, _c2, _f2, ug = stage_gcx(stage_bytes(usd, 'movie'))
    ib, _b, _o, ir = captions(ig)
    ub, _b2, _o2, ur = captions(ug)
    safe_delta = (ur[4].end - ur[4].pos) - (ir[2].end - ir[2].pos)
    s = emit(SAFE_NAME, SAFE_PAIRING, safe_delta, False, '<- SAFE, deployable')
    open(_os.path.join(WORK, 'vr_movie_e3_stage.bin'), 'wb').write(s)
    # the full port: both TGS captions become two lines each
    s = emit(PPF_NAME, PAIRING, EXPECT_DELTA, True, '<- FULL, needs one in-game check')
    open(_os.path.join(WORK, 'vr_movie_stage.bin'), 'wb').write(s)
    print("""
Two builds, and only the first is safe to ship blind:

  %s
      The E3 caption only, one record for one record, so the record count and
      order stay exactly retail's. Correct under ANY clip->line mapping.

  %s
      Both TGS captions become USA's two lines each, -t byte-identical to USA.
      Correct IF the actor selects a clip's lines by walking the records; if it
      indexes line = clip, clips B and E3 show the wrong English line, which is
      worse than leaving them Japanese. ONE LAUNCH DECIDES IT: deploy it, open
      EXTRA -> MOVIE with vr_unlock in place and check ALL THREE clips.
      If clip B is wrong, the answer is the 'f'/'m' option variables, not this
      chain edit - see this module's docstring.""" % (SAFE_NAME, PPF_NAME))


if __name__ == '__main__':
    main()
