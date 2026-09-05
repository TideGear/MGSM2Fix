"""Build the brf stage with the briefing labels at USA proportions.

b_select.c shows brf_800C983C doing setXY4(poly, xl, yt, xr, yb) while the UVs
span the whole texture, so the texture is *stretched to the quad*: rendered size
is the quad's, and a label only draws at its true size when its canvas equals
its quad.  So each label gets a canvas of exactly its quad and USA's artwork
pasted into it 1:1, padded with the palette's black entry.

The quad immediates live in GetResources (asm/overlays/brf/brf_800C99C0.s) and
several labels share one - the compiler keeps 122 in s4 across two call sites.
A shared immediate is sized to the largest member of its group; the smaller
members are simply padded out, so they still render at their own true width.
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from workdir import WORK
import struct, json, sys
sys.path.insert(0, '.')
import pcx4
from PIL import Image
from brf_widen import (stage, parse, geo, units, ufits, vfits, strcode, pad, BASEADDR,
                       ROW_H_ADDR, ROW_H_OLD, ROW_H_NEW, S00_ADDR, S00_OLD, S00_NEW,
                       advance_patches, INT_FN, xl_patches, S00_X_ADDRS, LINE_DELTA,
                       quads, UNSHARE, unshare_patches, RULE, START_Y,
                       DETAIL_ADDR, DETAIL_OLD, DETAIL_NEW, FRAME_ADDR, FRAME_OLD,
                       FRAME_NEW, USA_ABOVE, OUTLINE_T8_ADDR, OUTLINE_T8_OLD, OUTLINE_T8_NEW,
                       MEMBER_ADDR, MEMBER_OLD, MEMBER_NEW, MEMBER_ADV, CONNECTOR_X,
                       S01_ADDR, S01_OLD, S01_NEW, CONNECTOR_END,
                       RULE_X, RULE_S4, S00_X_OLD, S00_X_NEW, GROUP_DX, ANIM_X)

si, ti, Fi, pi = stage(WORK + '/int1_stage.dir')
su, tu, Fu, pu = stage(WORK + '/usa1_stage.dir')
ni = [k for k, t in enumerate(ti) if chr(t[1]) + chr(t[2]) == 'nd'][0]
nu = [k for k, t in enumerate(tu) if chr(t[1]) + chr(t[2]) == 'nd'][0]
ei, taili = parse(pi[ni]); eu, _ = parse(pu[nu])
U = {e[0]: e[3] for e in eu}
target = {int(k, 16): tuple(v) for k, v in json.load(open(WORK + '/brf_target.json')).items()}
place  = {int(k, 16): tuple(v) for k, v in json.load(open(WORK + '/brf_widen.json')).items()}
newimm = {int(k, 16): v for k, v in json.load(open(WORK + '/brf_imm.json')).items()}
LAB = set(range(0x1D82, 0x1D8C)) | set(range(0x1DA2, 0x1DA8)) | {0xE981, 0xE982, 0xE983, 0xE984}

# ---- overlay: patch the quad immediates -------------------------------------
ovl = bytearray(pi[0])
old = {}
for name, g in quads.items():
    for key in ('xr', 'yb'):
        if key in g: old[g[key][1]] = g[key][0]
patched = []
for addr, val in sorted(newimm.items()):
    off = addr - BASEADDR
    w = struct.unpack('<I', ovl[off:off+4])[0]
    if (w >> 26) == 9 and ((w >> 21) & 31) == 0:          # addiu rt, zero, imm
        assert (w & 0xFFFF) == (old[addr] & 0xFFFF), 'immediate mismatch at %08X' % addr
        struct.pack_into('<I', ovl, off, (w & 0xFFFF0000) | (val & 0xFFFF))
    elif w == 0x00E01021:                                  # addu v0,a3,zero -> addiu
        struct.pack_into('<I', ovl, off, 0x24020000 | (val & 0xFFFF))
    else:
        raise SystemExit('unexpected instruction 0x%08X at %08X' % (w, addr))
    users = sorted(n for n, g in quads.items()
                   if addr in (g['xr'][1], g.get('yb', (0, None))[1]))
    patched.append((addr, old[addr], val, users))
# the single row-height constant every br_sNN is drawn with
_off = ROW_H_ADDR - BASEADDR
_have = list(struct.unpack('<11I', ovl[_off:_off+44]))
assert _have == ROW_H_OLD, 'row positioner not as expected: %s' % [hex(x) for x in _have]
struct.pack_into('<11I', ovl, _off, *ROW_H_NEW)
print('row box    @%08X: [y, y+13] -> [y - above, y - above + texture height], above = py %% 8'
      % ROW_H_ADDR)
# br_s00's animated width: rebuild the 52n shift/add chain as 100n
_o = S00_ADDR - BASEADDR
_have = list(struct.unpack('<5I', ovl[_o:_o+20]))
assert _have == S00_OLD, 'br_s00 width chain not at %08X: %s' % (S00_ADDR, [hex(x) for x in _have])
struct.pack_into('<5I', ovl, _o, *S00_NEW)
print('br_s00 width chain @%08X: 52n -> 100n  (x1 = w*n/6 + 26)' % S00_ADDR)
from brf_widen import XL as _XL
for n, (addr, old_v, new_v) in sorted(_XL.items()):
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    assert (w >> 26) == 9 and (w & 0xFFFF) == old_v, 'xl %08X: %08X' % (addr, w)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | (new_v & 0xFFFF))
    print('label xl  @%08X: %2d -> %-2d  %s' % (addr, old_v, new_v, n))
for addr in S00_X_ADDRS:                     # br_s00's animated x follows the labels
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    assert (w >> 26) == 9 and (w & 0xFFFF) == S00_X_OLD, 'br_s00 x @%08X: %08X' % (addr, w)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | S00_X_NEW)
    print('label xl  @%08X: %d -> %d  br_s00 (animated)' % (addr, S00_X_OLD, S00_X_NEW))

_xl = lambda n: quads[n]['xl'][0]
_w  = lambda n: geo(U[strcode(n)])['w']
for addr, oldw, neww, what in unshare_patches(_xl, _w):
    o = addr - BASEADDR
    have = list(struct.unpack('<%dI' % len(oldw), ovl[o:o+4*len(oldw)]))
    assert have == oldw, 'unshare %08X: %s' % (addr, [hex(x) for x in have])
    struct.pack_into('<%dI' % len(neww), ovl, o, *neww)
    print('unshare   @%08X: %s' % (addr, what))

for addr, old_v, new_v, what in ANIM_X:
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    cur = w & 0xFFFF; cur -= 0x10000 if cur >= 0x8000 else 0
    assert (w >> 26) == 9 and cur == old_v, 'anim x %08X: %08X (want %d)' % (addr, w, old_v)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | (new_v & 0xFFFF))
    print('anim x    @%08X: %+d -> %+d  (%s)' % (addr, old_v, new_v, what))

for addr, old_v, new_v, what in RULE_X:
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    cur = w & 0xFFFF; cur -= 0x10000 if cur >= 0x8000 else 0
    assert (w >> 26) == 9 and cur == old_v, 'rule x %08X: %08X' % (addr, w)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | (new_v & 0xFFFF))
    print('group x   @%08X: %+d -> %+d  (%s)' % (addr, old_v, new_v, what))
_a, _old, _new, _what = RULE_S4
_o = _a - BASEADDR
assert struct.unpack('<I', ovl[_o:_o+4])[0] == _old, 's4 not at %08X' % _a
struct.pack_into('<I', ovl, _o, _new)
print('group x   @%08X: addu s4,a3,zero -> addiu s4,zero,%d  (%s)'
      % (_a, (20 + GROUP_DX), _what))

for addr, old_v, new_v, what in RULE:
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    cur = w & 0xFFFF; cur -= 0x10000 if cur >= 0x8000 else 0
    assert (w >> 26) == 9 and cur == old_v, 'rule %08X: %08X' % (addr, w)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | (new_v & 0xFFFF))
    print('rule      @%08X: %+d -> %+d  (%s)' % (addr, old_v, new_v, what))

for addr, old_v, new_v, what in START_Y:
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    cur = w & 0xFFFF; cur -= 0x10000 if cur >= 0x8000 else 0
    assert (w >> 26) == 9 and cur == old_v, 'start y %08X: %08X' % (addr, w)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | (new_v & 0xFFFF))
    print('start y   @%08X: %+d -> %+d  (%s)' % (addr, old_v, new_v, what))
for label, addr, oldw, neww in (('detailed start: 9 - (16n + 10d - 11)/2, USA', DETAIL_ADDR, DETAIL_OLD, DETAIL_NEW),
                                ('frame polys 27-38: USA geometry, K = t8 (+8 / 14) + member helper', FRAME_ADDR, FRAME_OLD, FRAME_NEW),
                                ('outline: t8 = 10 (frame K base)', OUTLINE_T8_ADDR, OUTLINE_T8_OLD, OUTLINE_T8_NEW),
                                ('member block: USA two-branch layout, advance in t9', MEMBER_ADDR, MEMBER_OLD, MEMBER_NEW),
                                ('br_s01 reveal: x0 29, x1 = 29 + 52*step/6 (USA)', S01_ADDR, S01_OLD, S01_NEW)):
    o = addr - BASEADDR
    have = list(struct.unpack('<%dI' % len(oldw), ovl[o:o+4*len(oldw)]))
    assert have == oldw, '%s: block at %08X not as expected: %s' % (label, addr, [hex(x) for x in have])
    struct.pack_into('<%dI' % len(neww), ovl, o, *neww)
    print('rewrite   @%08X: %d words  (%s)' % (addr, len(neww), label))

for addr, old_w, new_w, what in MEMBER_ADV:
    o = addr - BASEADDR
    assert struct.unpack('<I', ovl[o:o+4])[0] == old_w, 'member adv %08X' % addr
    struct.pack_into('<I', ovl, o, new_w)
    print('row advance @%08X: 20 -> t9 (20 | 17)  %s' % (addr, what))
for addr, old_w, new_w, what in CONNECTOR_END:
    o = addr - BASEADDR
    assert struct.unpack('<I', ovl[o:o+4])[0] == old_w, 'connector end %08X' % addr
    struct.pack_into('<I', ovl, o, new_w)
    print('connector @%08X: %s  (USA)' % (addr, what))
for addr, old_v, new_v in CONNECTOR_X:
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    assert (w >> 26) == 9 and ((w >> 21) & 31) == 0 and (w & 0xFFFF) == old_v, 'connector x %08X: %08X' % (addr, w)
    struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | new_v)
    print('connector @%08X: %d -> %d  (L-connector polys 27-38, USA)' % (addr, old_v, new_v))
NM = {9+i: 'br_s%02d' % i for i in range(16)}
for addr, old_v, new_v, idx in advance_patches(bytes(pi[0]), pu[0]):
    o = addr - BASEADDR
    w = struct.unpack('<I', ovl[o:o+4])[0]
    if (w >> 26) == 9 and ((w >> 16) & 31) == 7:                 # addiu a3, zero, N
        assert (w & 0xFFFF) == old_v, 'advance %08X: %d != %d' % (addr, w & 0xFFFF, old_v)
        struct.pack_into('<I', ovl, o, (w & 0xFFFF0000) | new_v)
    else:                                                        # addu a3, a1, zero
        assert w == 0x00A03821, 'unexpected a3 def at %08X: %08X' % (addr, w)
        struct.pack_into('<I', ovl, o, 0x24070000 | new_v)
    print('row advance @%08X: %2d -> %-2d  %s  (USA)' % (addr, old_v, new_v, NM.get(idx, idx)))
print('patched %d quad immediates:' % len(patched))
for addr, o, n, users in patched:
    print('   %08X  %5d -> %-5d  %s' % (addr, o, n, ', '.join(users)))

# ---- archive: USA art pasted 1:1 into a canvas the size of the quad ----------
report = []
for e in ei:
    if e[0] not in LAB: continue
    assert e[0] in U and e[0] in target, 'label %04X not covered' % e[0]
    ig, ug = geo(e[3]), geo(U[e[0]])
    cw, ch = target[e[0]]
    uw, uh, upal, urows = pcx4.decode(U[e[0]])
    bg = next((i for i in range(len(upal)) if tuple(upal[i]) == (0, 0, 0)), 0)
    # Squash only the axis that does not fit; pad the other, so the art keeps
    # 1:1 wherever the quad allows it.
    sw, sh = min(uw, cw), min(uh, ch)
    if (sw, sh) != (uw, uh):
        im = Image.new('P', (uw, uh)); im.putdata([v for r in urows for v in r])
        px = list(im.resize((sw, sh), Image.NEAREST).getdata())
        urows = [px[y*sw:(y+1)*sw] for y in range(sh)]
        how = 'squashed %s' % ('x' if sw != uw else 'y')
    else:
        how = 'exact' if (uw, uh) == (cw, ch) else 'pad'
    rows = [[(urows[y][x] if y < sh and x < sw else bg) for x in range(cw)]
            for y in range(ch)]
    npx, npy = place.get(e[0], (ig['px'], ig['py']))
    src = bytearray(pcx4.encode(U[e[0]], cw, ch, upal, rows))
    struct.pack_into('<7H', src, 74, 12345, ug['fl'], npx, npy, ig['cx'], ig['cy'], ug['nc'])
    while len(src) % 4: src.append(0)
    e[3] = bytes(src); e[2] = len(src)
    report.append((e[0], uw, uh, cw, ch, how))

newdar = b''.join(struct.pack('<HhI', t, x, s) + b for t, x, s, b in ei) + taili
ti[ni][3] = len(newdar); pi[ni] = newdar; pi[0] = bytes(ovl); ti[0][3] = len(ovl)
nsect = (2048 + sum(pad(len(pi[k])) for k in Fi)) // 2048
hdr = bytearray(2048); struct.pack_into('<BBh', hdr, 0, 1, 0, nsect)
for k, t in enumerate(ti): struct.pack_into('<HBBi', hdr, 4 + 8*k, *t)
out = bytearray(hdr)
for k in Fi: out += pi[k] + bytes(pad(len(pi[k])) - len(pi[k]))
assert len(out) == nsect * 2048

# ---- verify -----------------------------------------------------------------
e2, rest = parse(bytes(out)[2048+pad(ti[0][3]):2048+pad(ti[0][3])+len(newdar)])
assert len(e2) == len(ei) and len(rest) == len(taili)
assert all(x[2] % 4 == 0 for x in e2), 'unaligned entry'
G2 = {e[0]: geo(e[3]) for e in e2}
rects = []
for tid, g in G2.items():
    u = units(g['w'], g['bpp'])
    if tid in LAB:
        assert ufits(g['px'], g['w'], g['bpp']),             '0x%04X: u1 = %d > 255, the U coordinate would wrap' % (
                tid, (g['px'] % 64) * (16 // g['bpp']) + g['w'])
        assert vfits(g['py'], g['h']),             '0x%04X: v2 = %d > 255, the V coordinate would wrap' % (
                tid, (g['py'] % 256) + g['h'])
        if tid in USA_ABOVE:                              # the positioner reads it back as py % 8
            assert g['py'] % 8 == USA_ABOVE[tid], '0x%04X: py %d encodes above %d, USA has %d' % (
                tid, g['py'], g['py'] % 8, USA_ABOVE[tid])
    rects.append((g['px'], g['py'], u, g['h'], tid))
for i in range(len(rects)):
    for j in range(i+1, len(rects)):
        a, b = rects[i], rects[j]
        if a[0] < b[0]+b[2] and b[0] < a[0]+a[2] and a[1] < b[1]+b[3] and b[1] < a[1]+a[3]:
            raise SystemExit('VRAM overlap 0x%04X / 0x%04X' % (a[4], b[4]))
def imm16(addr):
    v = struct.unpack('<I', ovl[addr-BASEADDR:addr-BASEADDR+4])[0] & 0xFFFF
    return v - 0x10000 if v >= 0x8000 else v
for name, g in quads.items():                     # quad == canvas, for every label
    tid = strcode(name)
    # an un-shared label's xr lives in a rewritten block, not a lone immediate
    qw = target[tid][0] if name in UNSHARE else imm16(g['xr'][1]) - g['xl'][0]
    # families B and C get no yb immediate: the height is forced at runtime
    qh = 17 if name.startswith('br_f') else target[tid][1]   # per-label = texture height
    assert (qw, qh) == (G2[tid]['w'], G2[tid]['h']), \
        '%s quad %dx%d vs texture %dx%d' % (name, qw, qh, G2[tid]['w'], G2[tid]['h'])
print('\nlabel textures:')
for tid, uw, uh, cw, ch, how in sorted(report):
    print('   %04X  USA %3dx%-3d -> canvas %3dx%-3d  %s' % (tid, uw, uh, cw, ch, how))
print('\nverified: every quad equals its texture, no page crossings, no overlaps; %d sectors' % nsect)
open(WORK + '/brf_en.bin', 'wb').write(bytes(out))
