#!/usr/bin/env python
"""Option -> SCREEN: draw USA's sc_text texture, making the brightness paragraph
pixel-exact instead of re-wrapped font text.

WHY A TEXTURE. USA never renders this paragraph with the font. It draws one
232x70 4bpp texture, `sc_text`, on a quad:
    Init_Res(work, GV_StrCode("sc_text"), poly, -121, 2, 111, 72, 0, 0)
We draw that same texture whole, on USA's own quad constants.
An earlier build cropped it to 46 rows and moved the quad to (-121,14)-(111,60),
because the Master Collection's USA shows only lines 1-4, 12 rows lower than
USA's constant puts them. Both are the COLLECTION's doing: it ships four CD-ROM
patches replacing `sc_text` in USA's option stage with a 4-line version on the
same 232x70 canvas, centred - dropping the O-button sentence (platform-specific
button name) and shifting the block down 12 rows. With the collection's patches
disabled its USA draws all six lines at SwanStation's position, so USA's own
constants are correct and the measurement had been fitted to replaced art.
Integral has no such texture and no code naming it, so it renders the paragraph
as KCB font text from chain records 13-16/24/27. That path cannot reproduce
USA's line breaks: `rect.w = kcb->max_width` is a single byte and one 4bpp tpage
is 256 texels, while USA's second line is 256 px. Hence the re-wrap to 36
characters that shipped before this. Drawing USA's own texture removes the
limit entirely - USA's artwork, USA's quad, USA's line breaks.

WHAT THIS TOUCHES

1. DAR: append the entry, 8-byte header ('<HhI', id, ext, size) + payload, and
   move one existing texture out of the way. Lookup is by id (LoadDataArchives
   -> GV_LoadInit -> DG_LoadInitPcx -> DG_SetTexture into a 512-slot table keyed
   by id), so append order is irrelevant; there is no count or terminator, the
   walk is purely length-driven (remaining -= size + 8 until <= 0). Payload
   sizes must be 4-aligned because `size` is read as an int at tag+4 - true of
   all 20,836 DAR entries across Integral disc 1.

2. VRAM: mirror USA. sc_text at (512,256); key_pad (0xDE60) moved from (512,256)
   to (512,326) - exactly the relocation USA itself made to free that space. Both
   are PCXINFO rewrites at payload+74, no code change, since every UV here comes
   from DG_TEX via SetPacketTexture. sc_text's CLUT goes to (1008,237): of the
   16-aligned 16-entry CLUT slots in rows 233-237 that is the only free one,
   because Integral carries five Japanese text textures USA lacks.
       ufits: off_x = (512 % 64) * (16/4) = 0, 0 + 232 <= 255
       vfits: off_y = 256 % 256 = 0,          0 +  70 <= 255
       58 units wide from a 64-aligned x, so one tpage, no page split.

3. Stage size: the DAR grows 121680 -> 127540, taking the stage 75 -> 78 sectors.
   The option stage has ZERO slack in place (it ends at STAGE.DIR sector 27210
   and `camera` begins at 27211), so it must be relocated - the same DUMMY3M.DAT
   parking that `preope` already uses.

4. DUMMY3M slot. NOT sector 90. preope holds 0..89 and **brf holds 128..266** -
   a 78-sector stage at 90 would silently overwrite 40 sectors of the shipped
   briefing stage, and a blankness check against the pristine image would not
   catch it because PPFs are applied at runtime and never written back. This
   script composites the deployed PPFs to build the real occupancy map and
   asserts disjointness. Slot 384 leaves brf 256 sectors of growth room.

5. Overlay: the fifth quad. `work->field_2C` is GM_MakePrim(..., 4, ...) so the
   prim needs a fifth pack; field_5D4 and f2AFC grow to 5 and the existing copy
   loop carries it, which avoids a per-frame 40-byte struct copy (that variant
   measured +64 over the ceiling; this one is -12 under). Growing f2AFC shifts
   which f2B0C slots retail's key-config overrun zeroes - from [3..12] to
   [2..11] - which is harmless because entering KEY CONFIG explicitly re-stamps
   all 17 of f2B0C[0..16] before the screen draws. Six now-dead
   option_800C3B3C calls in case 7 pay for the addition.

6. The chain is left EXACTLY as the font-text build shipped it, taken from
   CHAIN_PPF (not from whatever option PPF is deployed - see the note at the
   constant). Records 13-16/24/27 keep their English text; nothing draws them
   any more. verify() asserts the records it depends on, because after
   relocation the old PPFs write to a stage the game no longer reads, so
   anything they contributed has to already be in the image this script builds.

usage: optsctext.py [--deploy]      (writes work/ always; PPFs only with --deploy)
"""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RETAIL   = 'work/int1_stage.dir'
OVL      = 'D:/mgsbuild/d/obj/option.bin'
USA      = 'work/usa1_stage.dir'
OUT      = 'work/option_sctext_stage.bin'
JP       = 'D:/Steam/SteamApps/common/MGS1/windata/dlc/dlc_japan.bin'
MODS     = 'D:/Steam/SteamApps/common/MGS1/mods/INTEGRAL/INTEGRAL'
DESC     = b'MGS Integral: option screen text'

HDR      = 24            # mode 2 form 1
SLOT     = 384           # DUMMY3M sector index: past preope 0..89 and brf 128..266
SC_TEXT  = 0x2FBD        # GV_StrCode('sc_text')
KEY_PAD  = 0xDE60
DISCS = [dict(disc=0, sd=136654, du=292330, ppf='INTEGRAL_disc1_en_option.ppf'),
         dict(disc=1, sd=105178, du=303436, ppf='INTEGRAL_disc2_en_option.ppf')]
IMG   = {0: 0x0, 1: 0x2AE54800}
DU_SECTORS = 13500
OPTION_ENTRY_FO = 744    # STAGE.DIR file offset of the `option` entry's u32 sector

# The chain edits (records 3/7 blanked, 4/5/12/26/13-16/24 English) come from the
# last FONT-TEXT option build, optbright.py's output, kept here as a fixed input.
# They are NOT taken from the deployed option PPF: once this script has shipped,
# the deployed option PPF is our own output, whose entry repoint would send
# composite() following the relocated pointer out of the file - and skipping it
# silently reverts every one of those records to retail Japanese (shipped once,
# 2026-09-02: 'use directional buttons to test' came back as Japanese).
CHAIN_PPF = 'work/fonttext_disc%d_option.ppf'
EXPECT_CHAIN = {3: b' \x00', 7: b'\x80:\x00',
                4: b'screen brightness setup\x00', 5: b'key configuration setup\x00',
                12: b'use directional buttons to test\x00', 26: b'use directional buttons to test\x00',
                13: b'Adjust the monitor brightness so the\x00', 24: b'Press the \x90\x1b button to return to the\x00',
                27: b'option screen.         \x00'}
# Records the port owns. Every other record must equal retail byte for byte -
# the font-text build had written an 'e' and a space into record 6 (the EXIT
# row's help line, which then rendered two wrong glyphs) and blanked record 7
# (the colon Integral's Japanese help lines use: 字幕設定：オン). Both are
# repaired from retail in repair_chain(); 27's padding absorbs the +1 byte so
# the chain length, and every container field after it, stays put.
PORTED_RECORDS = {3, 4, 5, 12, 13, 14, 15, 16, 24, 26, 27}
CHAIN_OFF, CHAIN_TAG = 0x1B8, 6

# where the two textures go
SCT_VRAM, SCT_CLUT = (512, 256), (1008, 237)
PAD_VRAM           = (512, 326)
SC_ROWS            = 70          # USA's whole texture: all six lines (see the docstring)

# KEY CONFIG: swap in USA's eight label textures. Four of the quads change too
# (see opt.c); the other four already carry USA's constants, and for three of
# those USA's art is smaller than the quad, so USA stretches it - keeping the
# quad reproduces that stretch, which is what matching USA means here.
# VRAM and CLUT slots come from tools scratch `kcplace.py`, which frees
# Integral's eight slots, then places USA's largest-first inside the option
# stage's own texture band, clear of the framebuffers (0,0)/(0,256) 320x240 and
# of the option screen's font KCBs (x 768..960, y 256..344, opt.c line ~160).
KEY_LABELS = {                    # id: (name, vram, clut)
    0x32C8: ('key_button',  (464, 460), (336, 233)),
    0xAC43: ('key_sykan',   (336, 460), (320, 233)),
    0xAF48: ('key_syukan',  (486, 460), (352, 233)),
    0x2CA5: ('key_normal',  (364, 460), (400, 233)),
    0xC627: ('key_reverse', ( 16, 504), (384, 233)),
    0x03A8: ('key_action',  (374, 460), (416, 233)),
    0x1D5E: ('key_buki',    (108, 504), (368, 233)),
    0x41E9: ('key_hohuku',  (512, 460), (432, 233)),
}
# Nothing needs padding: opt.c now carries USA's own rectangles, and every one
# of those is exactly its art's size.
KEY_PAD_TO = {}


def pad(x, a=2048): return (x + a - 1) // a * a


def ents(d):
    h = struct.unpack('<I', d[:4])[0]; o = []
    for p in range(4, h + 12, 12):
        n = d[p:p+8].rstrip(b'\x00')
        if n: o.append((n.decode('latin1'), struct.unpack('<I', d[p+8:p+12])[0], p))
    return o


def read_ppf(path):
    d = open(path, 'rb').read()
    assert d[:5] == b'PPF30', d[:8]
    p, out = 1084 if d[57] else 60, []
    while p < len(d):
        off = struct.unpack_from('<Q', d, p)[0]; p += 8
        n = d[p]; p += 1
        out.append((off, d[p:p+n])); p += n
        if d[58]: p += n
    return out


def img_off(lba, within): return (lba + within // 2048) * 2352 + HDR + within % 2048


def composite(disc):
    """Retail STAGE.DIR with every PPF's STAGE.DIR writes applied, from a FIXED
    list of sources: the deployed PPFs other than the option one, plus CHAIN_PPF.

    After relocation the old option/menu PPF writes land on a stage the game no
    longer reads, so whatever they contributed must already be in the image we
    park in DUMMY3M.  Building from the composite is what carries records 4/5
    ('screen brightness setup', 'key configuration setup', which come from
    menu.ppf, not from our option builder) and 3/7/12/13-16/24/26 (CHAIN_PPF)
    forward.  Any write to the option entry's sector pointer is a hard error:
    that would be this script's own output being fed back in.
    """
    base = bytearray(open(RETAIL, 'rb').read())
    sd = DISCS[disc]['sd']
    lo = img_off(sd, 0); hi = img_off(sd + len(base) // 2048, 0)
    d = os.path.join(MODS, str(disc))
    sources = [os.path.join(d, name) for name in sorted(os.listdir(d))
               if name.endswith('.ppf') and name != DISCS[disc]['ppf']]
    sources.append(CHAIN_PPF % (disc + 1))
    applied = {}
    for path in sources:
        n = 0
        for off, data in read_ppf(path):
            if not (lo <= off < hi): continue
            sec, within = divmod(off - HDR, 2352)
            fo = (sec - sd) * 2048 + within
            if fo < 0 or fo + len(data) > len(base): continue
            assert not (fo <= OPTION_ENTRY_FO < fo + len(data)),                 '%s repoints the option entry - it is a relocated build, not a source' % path
            base[fo:fo+len(data)] = data; n += len(data)
        assert n or not path.endswith('_option.ppf'), '%s contributed nothing' % path
        if n: applied[os.path.basename(path)] = n
    return bytes(base), applied


def chain_records(scr, off=CHAIN_OFF):
    """The option stage's text records: 07 <len> <payload incl. NUL> at `off`."""
    p, out = off, []
    while p < len(scr) and scr[p] == 7:
        n = scr[p+1]; out.append(bytes(scr[p+2:p+2+n])); p += 2 + n
    return out, p


def repair_chain(scr, retail_scr):
    """Restore every record the port does not own to retail, keeping the chain
    length constant by trading the difference against record 27's padding."""
    recs, end = chain_records(scr); ret, _ = chain_records(retail_scr)
    assert len(recs) == len(ret) == 31
    fixed = []
    for i, (r, o) in enumerate(zip(recs, ret)):
        if i not in PORTED_RECORDS and r != o:
            fixed.append(i); recs[i] = o
    if 7 in fixed or recs[7] != ret[7]:
        pass
    # record 7: the colon, restored from retail (it is "owned" only in the sense
    # that the font-text build blanked it; the port has no English for it)
    if recs[7] != ret[7]:
        fixed.append(7); recs[7] = ret[7]
    body = b''.join(bytes([7, len(r)]) + r for r in recs)
    delta = len(body) - (end - CHAIN_OFF)
    if delta:
        pad = recs[27]
        assert pad.endswith(b' \x00') and pad.count(b' ') > delta, 'record 27 cannot absorb %+d' % delta
        recs[27] = pad[:-1 - delta] + b'\x00'
        body = b''.join(bytes([7, len(r)]) + r for r in recs)
    assert len(body) == end - CHAIN_OFF, 'chain length changed'
    out = bytearray(scr); out[CHAIN_OFF:end] = body
    return bytes(out), fixed


def stage_of(d, name):
    base = [s for n, s, _p in ents(d) if n == name][0] * 2048
    ver, _p, sect = struct.unpack('<BBh', d[base:base+4])
    tags, p = [], base + 4
    while True:
        tid, mode, ext, sz = struct.unpack('<HBBi', d[p:p+8])
        if mode == 0: break
        tags.append([tid, mode, ext, sz]); p += 8
    return base, sect, tags


def dar_entries(blob):
    out, p = [], 0
    while p + 8 <= len(blob):
        tid, ext, size = struct.unpack('<HhI', blob[p:p+8])
        if size <= 0 or p + 8 + size > len(blob): break
        out.append([tid, ext, blob[p+8:p+8+size]]); p += 8 + size
    assert p == len(blob), 'DAR has %d tail bytes' % (len(blob) - p)
    return out


def set_pcxinfo(payload, px, py, cx, cy):
    b = bytearray(payload)
    stamp, flag, _px, _py, _cx, _cy, nc = struct.unpack_from('<7H', b, 74)
    assert stamp == 12345, 'not a PCXINFO payload'
    struct.pack_into('<7H', b, 74, 12345, flag, px, py, cx, cy, nc)
    return bytes(b), (_px, _py, _cx, _cy, nc, flag)


def build_stage():
    comp, applied = composite(0)
    print('composited base: ' + ', '.join('%s %d bytes' % kv for kv in applied.items()))
    base, sect, tags = stage_of(comp, 'option')
    print('option stage: base sector %d, %d sectors, tags %s'
          % (base // 2048, sect, [(chr(t[1]) + chr(t[2]) if 32 <= t[2] < 127 else chr(t[1]) + '?', t[3]) for t in tags]))
    FILE = [k for k, t in enumerate(tags) if not (chr(t[1]) == 'c' and chr(t[2]) in 'klhg')]
    off, pay = 2048, {}
    for k in FILE:
        pay[k] = comp[base+off:base+off+tags[k][3]]; off += pad(tags[k][3])
    assert off == sect * 2048, 'layout %d != %d' % (off, sect * 2048)

    # --- chain: everything the port does not own must be retail
    rbase, _rs, rtags = stage_of(open(RETAIL, 'rb').read(), 'option')
    roff = 2048
    for kk in FILE:
        if kk == CHAIN_TAG: break
        roff += pad(rtags[kk][3])
    retail_scr = open(RETAIL, 'rb').read()[rbase+roff:rbase+roff+rtags[CHAIN_TAG][3]]
    pay[CHAIN_TAG], fixed = repair_chain(pay[CHAIN_TAG], retail_scr)
    print('chain: records restored to retail: %s' % (fixed or 'none'))

    # --- overlay
    ovl = open(OVL, 'rb').read()
    assert len(ovl) <= 25842, 'overlay %d exceeds retail 25842 - menu rows will freeze' % len(ovl)
    print('overlay: %d -> %d (retail 25842, %+d)' % (tags[0][3], len(ovl), len(ovl) - 25842))
    pay[0] = ovl; tags[0][3] = len(ovl)

    # --- DAR: move key_pad, append sc_text
    de = dar_entries(pay[1])
    print('DAR: %d entries, %d bytes' % (len(de), len(pay[1])))
    assert not any(e[0] == SC_TEXT for e in de), 'sc_text already present'
    hit = [e for e in de if e[0] == KEY_PAD]
    assert len(hit) == 1, 'key_pad found %d times' % len(hit)
    kp = hit[0]
    _s, _f, opx, opy, ocx, ocy, onc = struct.unpack_from('<7H', kp[2], 74)
    kp[2], _old = set_pcxinfo(kp[2], PAD_VRAM[0], PAD_VRAM[1], ocx, ocy)   # CLUT unchanged
    print('  key_pad  vram(%d,%d) -> (%d,%d), clut (%d,%d) unchanged, %d colours'
          % (opx, opy, PAD_VRAM[0], PAD_VRAM[1], ocx, ocy, onc))

    ue = dar_entries(stage_payload(USA, 'option', 1))
    src = [e for e in ue if e[0] == SC_TEXT]
    assert len(src) == 1, 'sc_text not found in USA option DAR'
    ext, blob = src[0][1], src[0][2]
    assert len(blob) % 4 == 0, 'sc_text payload %d not 4-aligned' % len(blob)
    # SC_ROWS is USA's full height: all six lines. (It was 46 while the port was
    # matching the collection's replacement texture.) Re-encode anyway, and prove
    # the round-trip, so a future crop cannot ship unverified.
    import pcx4
    w, h, pal, rows = pcx4.decode(blob)
    assert (w, h) == (232, 70), (w, h)
    blob = pcx4.encode(blob, w, SC_ROWS, pal, rows[:SC_ROWS])
    blob += bytes((-len(blob)) % 4)
    cw, ch, cpal, crows = pcx4.decode(blob)
    assert (cw, ch) == (232, SC_ROWS) and crows == rows[:SC_ROWS] and cpal == pal, 'crop does not round-trip'
    print('  sc_text  cropped 232x70 -> 232x%d (%d bytes), decode round-trips' % (SC_ROWS, len(blob)))
    newblob, old = set_pcxinfo(blob, SCT_VRAM[0], SCT_VRAM[1], SCT_CLUT[0], SCT_CLUT[1])
    print('  sc_text  USA vram(%d,%d) clut(%d,%d) %d colours flag 0x%X'
          % (old[0], old[1], old[2], old[3], old[4], old[5]))
    print('           ours vram(%d,%d) clut(%d,%d), ext 0x%04X, %d bytes payload'
          % (SCT_VRAM[0], SCT_VRAM[1], SCT_CLUT[0], SCT_CLUT[1], ext, len(newblob)))
    de.append([SC_TEXT, ext, newblob])

    # --- KEY CONFIG: replace the eight label textures with USA's
    ue = {e[0]: e for e in dar_entries(stage_payload(USA, 'option', 1))}
    used_vram, used_clut = [], {}
    for tid, (name, vram, clut) in KEY_LABELS.items():
        mine = [e for e in de if e[0] == tid]
        assert len(mine) == 1, '%s found %d times in the Integral DAR' % (name, len(mine))
        assert tid in ue, '%s missing from the USA DAR' % name
        src = ue[tid][2]
        iw, ih, _p, _r = pcx4.decode(mine[0][2])
        uw, uh, upal, urows = pcx4.decode(src)
        padded = ''
        if name in KEY_PAD_TO:
            want = KEY_PAD_TO[name]
            assert want >= uw, '%s: cannot pad %d down to %d' % (name, uw, want)
            bg = max(set(v for r in urows for v in r), key=lambda v: sum(r.count(v) for r in urows))
            urows = [list(r) + [bg] * (want - uw) for r in urows]
            src = pcx4.encode(src, want, uh, upal, urows)
            src += bytes((-len(src)) % 4)
            padded = '  padded %d -> %d wide with index %d' % (uw, want, bg)
            uw = want
            rw, rh, _rp, rr = pcx4.decode(src)
            assert (rw, rh) == (uw, uh) and rr == urows, '%s padding does not round-trip' % name
        blob, old = set_pcxinfo(src, vram[0], vram[1], clut[0], clut[1])
        assert len(blob) % 4 == 0, '%s payload %d not 4-aligned' % (name, len(blob))
        # UVs are 8-bit: SetPacketTexture computes u1 = off_x + w and
        # v1 = off_y + h, where off_x = (px % 64) * 4 and off_y = py % 256
        # (DG_SetTexture). Reaching 256 wraps to 0 and the quad then samples the
        # whole texture page, which renders as garbage - this shipped once.
        assert (vram[0] % 64) * 4 + uw <= 255, '%s: u1 = %d overflows 8-bit UV' % (name, (vram[0] % 64) * 4 + uw)
        assert vram[1] % 256 + uh <= 255, '%s: v1 = %d overflows 8-bit UV' % (name, vram[1] % 256 + uh)
        rw, rh, rpal, rrows = pcx4.decode(blob)
        assert (rw, rh) == (uw, uh) and rrows == urows and rpal == upal, '%s does not round-trip' % name
        for (ox, oy, ow, oh, on) in used_vram:
            if not (vram[0] + (uw + 3) // 4 <= ox or vram[0] >= ox + ow
                    or vram[1] + uh <= oy or vram[1] >= oy + oh):
                raise AssertionError('%s overlaps %s in VRAM' % (name, on))
        used_vram.append((vram[0], vram[1], (uw + 3) // 4, uh, name))
        assert clut not in used_clut, '%s shares a CLUT slot with %s' % (name, used_clut.get(clut))
        used_clut[clut] = name
        mine[0][2] = blob
        print('  %-12s Integral %dx%d -> USA %dx%d  vram(%d,%d) clut(%d,%d)%s'
              % (name, iw, ih, uw, uh, vram[0], vram[1], clut[0], clut[1], padded))

    newdar = b''.join(struct.pack('<HhI', t, x, len(b)) + b for t, x, b in de)
    print('DAR: %d -> %d bytes (+%d), %d entries' % (tags[1][3], len(newdar), len(newdar) - tags[1][3], len(de)))
    pay[1] = newdar; tags[1][3] = len(newdar)

    # --- re-emit the stage block
    total = 2048 + sum(pad(tags[k][3]) for k in FILE)
    newsect = total // 2048
    out = bytearray(total)
    struct.pack_into('<BBh', out, 0, 1, 0, newsect)
    p = 4
    for t in tags:
        struct.pack_into('<HBBi', out, p, t[0], t[1], t[2], t[3]); p += 8
    o = 2048
    for k in FILE:
        out[o:o+len(pay[k])] = pay[k]; o += pad(tags[k][3])
    assert o == total
    print('stage: %d -> %d sectors (%d bytes)' % (sect, newsect, total))
    return bytes(out), newsect


def stage_payload(path, name, tagidx):
    d = open(path, 'rb').read()
    base, sect, tags = stage_of(d, name)
    FILE = [k for k, t in enumerate(tags) if not (chr(t[1]) == 'c' and chr(t[2]) in 'klhg')]
    off = 2048
    for k in FILE:
        if k == tagidx: return d[base+off:base+off+tags[k][3]]
        off += pad(tags[k][3])
    raise KeyError(tagidx)


def occupancy(disc):
    """Which DUMMY3M sector indices the deployed PPFs already write."""
    du, sd = DISCS[disc]['du'], DISCS[disc]['sd']
    lo, hi = img_off(du, 0), img_off(du + DU_SECTORS + 1, 0)
    used = {}
    d = os.path.join(MODS, str(disc))
    for name in sorted(os.listdir(d)):
        if not name.endswith('.ppf'): continue
        idx = set()
        for off, data in read_ppf(os.path.join(d, name)):
            if lo <= off < hi:
                idx.add((off - HDR) // 2352 - du)
        if idx: used[name] = (min(idx), max(idx), len(idx))
    return used


def verify(stage, newsect):
    """Read the built block back the way the loader would."""
    ver, _p, sect = struct.unpack('<BBh', stage[:4])
    assert sect == newsect, 'header says %d sectors, block is %d' % (sect, newsect)
    tags, p = [], 4
    while True:
        tid, mode, ext, sz = struct.unpack('<HBBi', stage[p:p+8])
        if mode == 0: break
        tags.append((tid, chr(mode), chr(ext) if 32 <= ext < 127 else '?', sz)); p += 8
    FILE = [k for k, t in enumerate(tags) if not (t[1] == 'c' and t[2] in 'klhg')]
    off, pay = 2048, {}
    for k in FILE:
        pay[k] = stage[off:off+tags[k][3]]; off += pad(tags[k][3])
    assert off == sect * 2048
    # loader-style DAR walk: remaining must land exactly on zero
    remaining, q, n = tags[1][3], 0, 0
    while remaining > 0:
        tid, ext, size = struct.unpack('<HhI', pay[1][q:q+8])
        assert size % 4 == 0, 'entry %d size %d not 4-aligned' % (n, size)
        q += 8 + size; remaining -= size + 8; n += 1
    assert remaining == 0, 'DAR walk overshot by %d' % -remaining
    got = {t: (x, b) for t, x, b in dar_entries(pay[1])}
    assert SC_TEXT in got, 'sc_text missing after rebuild'
    g = struct.unpack_from('<7H', got[SC_TEXT][1], 74)
    assert (g[2], g[3], g[4], g[5]) == (SCT_VRAM[0], SCT_VRAM[1], SCT_CLUT[0], SCT_CLUT[1]), g
    import pcx4
    sw, sh, _pal, _rows = pcx4.decode(got[SC_TEXT][1])
    assert (sw, sh) == (232, SC_ROWS), 'sc_text in the built DAR is %dx%d' % (sw, sh)
    k = struct.unpack_from('<7H', got[KEY_PAD][1], 74)
    assert (k[2], k[3]) == PAD_VRAM, k
    assert pay[0] == open(OVL, 'rb').read(), 'overlay payload mismatch'
    # the text records the KCB entries draw: 07 <len> <payload> 00 at 0x1B8 in tag 6
    scr, q, recs = pay[6], 0x1B8, []
    while q < len(scr) and scr[q] == 7:
        n = scr[q+1]; recs.append(scr[q+2:q+2+n]); q += 2 + n
    assert len(recs) == 31, 'chain has %d records' % len(recs)
    for i, want in EXPECT_CHAIN.items():
        assert recs[i] == want, 'chain record %d is %r, want %r (composite lost the font-text edits?)' % (i, recs[i], want)
    rbase, _rs, rtags = stage_of(open(RETAIL, 'rb').read(), 'option')
    roff = 2048
    for kk in FILE:
        if kk == CHAIN_TAG: break
        roff += pad(rtags[kk][3])
    rrecs, _ = chain_records(open(RETAIL, 'rb').read()[rbase+roff:rbase+roff+rtags[CHAIN_TAG][3]])
    for i in range(31):
        if i not in PORTED_RECORDS:
            assert recs[i] == rrecs[i], 'chain record %d differs from retail: %r vs %r' % (i, recs[i], rrecs[i])
    print('verify: %d sectors, DAR walk consumed %d entries with remaining exactly 0,'
          ' sc_text at (%d,%d) clut (%d,%d), key_pad at (%d,%d), overlay matches, %d chain records English/blank as expected'
          % (sect, n, g[2], g[3], g[4], g[5], k[2], k[3], len(EXPECT_CHAIN)))
    return True


def emit(stage, deploy):
    need = len(stage) // 2048
    assert need * 2048 == len(stage)
    f = open(JP, 'rb')
    for D in DISCS:
        disc, sd, du = D['disc'], D['sd'], D['du']
        used = occupancy(disc)
        clash = []
        for name, (a, b, cnt) in used.items():
            if name == D['ppf']: continue          # our own previous build: this replaces it
            if not (b < SLOT or a >= SLOT + need): clash.append('%s uses %d..%d' % (name, a, b))
        print('disc %d DUMMY3M occupancy: %s' % (disc + 1,
              '; '.join('%s %d..%d (%d)' % (n, a, b, c) for n, (a, b, c) in used.items())))
        assert not clash, 'slot %d..%d collides with %s' % (SLOT, SLOT + need - 1, clash)
        assert SLOT + need <= DU_SECTORS, 'slot runs past DUMMY3M'
        writes, blank = [], 0
        for s in range(need):
            page = stage[s*2048:(s+1)*2048]
            f.seek(IMG[disc] + img_off(du + SLOT + s, 0))
            assert f.read(2048) == bytes(2048), 'DUMMY3M idx %d not blank' % (SLOT + s)
            lo, hi = 0, 2048
            while lo < hi and not page[lo]: lo += 1
            while hi > lo and not page[hi-1]: hi -= 1
            if lo < hi: writes.append((img_off(du + SLOT + s, lo), page[lo:hi]))
            blank += 2048 - (hi - lo)
        eo = img_off(sd + OPTION_ENTRY_FO // 2048, OPTION_ENTRY_FO % 2048)
        f.seek(IMG[disc] + eo)
        cur = struct.unpack('<I', f.read(4))[0]
        assert cur == 27136, 'option entry reads %d, expected retail 27136' % cur
        writes.append((eo, struct.pack('<I', du + SLOT - sd)))
        out = bytearray(b'PPF30' + bytes([2]) + DESC.ljust(50, b'\x00') + bytes(4))
        n = 0
        for off, data in writes:
            for k in range(0, len(data), 255):
                c = data[k:k+255]
                out += struct.pack('<Q', off + k) + bytes([len(c)]) + c; n += 1
        print('disc %d: option sector %d -> %d (DUMMY3M idx %d), %d zero bytes skipped, %d records, %d bytes'
              % (disc + 1, cur, du + SLOT - sd, SLOT, blank, n, len(out)))
        if deploy:
            p = os.path.join(MODS, str(disc), D['ppf'])
            open(p, 'wb').write(bytes(out)); print('   -> %s' % p)
        else:
            p = 'work/option_sctext_disc%d.ppf' % (disc + 1)
            open(p, 'wb').write(bytes(out)); print('   -> %s  (staged, NOT deployed)' % p)


def main():
    deploy = '--deploy' in sys.argv
    stage, newsect = build_stage()
    open(OUT, 'wb').write(stage)
    print('wrote %s' % OUT)
    verify(stage, newsect)
    emit(stage, deploy)
    if not deploy:
        print('\nNOT DEPLOYED. Re-run with --deploy to install.')


if __name__ == '__main__':
    main()
