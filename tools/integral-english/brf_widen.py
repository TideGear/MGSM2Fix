"""Widen the briefing menu labels to USA proportions.

Two edits that must land together:
  * the draw quad, hardcoded as immediates in GetResources
    (asm/overlays/brf/brf_800C99C0.s) - patched in the overlay image
  * the texture, swapped to USA's artwork at its native size, given VRAM room

VRAM units are ceil(w * bpp / 16); the archive mixes 4bpp and 8bpp textures.
A texture must also fit inside one 64-unit texture page.
"""
import struct, json, sys
sys.path.insert(0, '.')

BASEADDR = 0x800C3208

def pad(x, a=2048): return (x + a - 1) // a * a

def ents(d):
    h = struct.unpack('<I', d[:4])[0]; o = []
    for p in range(4, h + 12, 12):
        n = d[p:p+8].rstrip(b'\x00')
        if n: o.append((n.decode('latin1', 'replace'), struct.unpack('<I', d[p+8:p+12])[0]))
    return o

def stage(path, name='brf'):
    d = open(path, 'rb').read(); base = dict(ents(d))[name] * 2048
    ver, pdb, sect = struct.unpack('<BBh', d[base:base+4])
    tags = []; p = base + 4
    while True:
        tid, mode, ext, sz = struct.unpack('<HBBi', d[p:p+8])
        if mode == 0: break
        tags.append([tid, mode, ext, sz]); p += 8
    FILE = [k for k, t in enumerate(tags) if not (chr(t[1]) == 'c' and chr(t[2]) in 'klhg')]
    off, pay = 2048, {}
    for k in FILE:
        pay[k] = d[base+off:base+off+tags[k][3]]; off += pad(tags[k][3])
    assert off == sect * 2048, 'layout mismatch'
    return sect, tags, FILE, pay

def parse(b):
    out = []; p = 0
    while p + 8 <= len(b):
        tid, ext, size = struct.unpack('<HhI', b[p:p+8])
        if size <= 0 or p + 8 + size > len(b): break
        out.append([tid, ext, size, b[p+8:p+8+size]]); p += 8 + size
    return out, b[p:]

def geo(b):
    bpp = b[3] * b[65]
    maxx, maxy = struct.unpack('<HH', b[8:12]); minx, miny = struct.unpack('<HH', b[4:8])
    st, fl, px, py, cx, cy, nc = struct.unpack('<7H', b[74:88])
    assert st == 12345
    return dict(w=maxx-minx+1, h=maxy-miny+1, bpp=bpp, px=px, py=py, cx=cx, cy=cy, nc=nc, fl=fl)

def units(w, bpp): return (w * bpp + 15) // 16

def ufits(px, w, bpp):
    """DG_SetTexture stores off_x = (px % 64) * (16 / bpp) TEXELS and
    tex->w = w - 1, and brf_800C983C sets poly->u1 = off_x + tex->w + 1 into a
    u_char.  So the limit is off_x + w <= 255; over that the U wraps and the
    quad samples across the page as vertical stripes."""
    return (px % 64) * (16 // bpp) + w <= 255

def vfits(py, h):
    """Same on the other axis: off_y = py % 256, tex->h = h - 1, and
    poly->v2 = off_y + tex->h + 1.  This also keeps a texture inside one
    256-row tpage half, which the tpage field cannot express otherwise."""
    return (py % 256) + h <= 255

def strcode(s):
    i = 0
    for ch in s.encode(): i = (((i << 5) | (i >> 11)) & 0xFFFF); i = (i + ch) & 0xFFFF
    return i

si, ti, Fi, pi = stage('work/int1_stage.dir')
su, tu, Fu, pu = stage('work/us1_stage.dir')
ni = [k for k, t in enumerate(ti) if chr(t[1]) + chr(t[2]) == 'nd'][0]
nu = [k for k, t in enumerate(tu) if chr(t[1]) + chr(t[2]) == 'nd'][0]
ei, taili = parse(pi[ni]); eu, _ = parse(pu[nu])
U = {e[0]: e[3] for e in eu}
quads = json.load(open('work/brf_quads_all.json'))

# Horizontal: DO NOT shift xl.  Integral's vertical rule sits 20 game px right
# of USA's (measured 2101 vs 1921, 180 display px / 9) while its label xl
# constants are only 16-17 right, so the labels sit ~4 px left of USA's
# label-to-rule offset.  Matching that offset (xl = USA's xl + 20) puts
# `the terrorists' armament`, 128 px wide, at 30..158 - and the panel spans
# -160..160, so the final `t` touches the screen edge.  USA only fits it
# because its rule is at 0: 10..138, 22 px of margin.  Integral's native xl
# keeps 6 px of margin, so the 4 px offset stays and the text stays on screen.
# Moving the rule instead would need whatever positions it - it is not a poly
# either game writes, and the DG_PRIM world matrix is set in undecompiled asm.
LINE_DELTA = 0
# The panel spans -160..160.  Integral's indents were sized for the narrower
# Japanese art, so USA's longest labels run off the right edge at them:
# br_s10 is 120 px at family-B's xl 46 -> 166.  Clamp each family's xl so its
# widest member ends by RIGHT_LIMIT, keeping the indent uniform within a family.
RIGHT_LIMIT = 156

# Two pairs share one xr immediate, so the narrower member gets the wider one's
# quad - and since the selection highlight follows the quad, its highlight runs
# far past its text (br_s06, Dr. Naomi, was 112 wide against USA's 52).  USA
# gives each its own xr.  Un-sharing needs one spare slot per block and there is
# none - except that the rewritten positioner now overwrites all four poly y
# values every frame, which makes the GetResources yt/yb *dead* for every
# br_sNN.  Their loads are the spare slots.  All four rows are unconditional,
# so the positioner always runs and the y really is always replaced.
UNSHARE = ['br_s02', 'br_s06', 'br_s09', 'br_s11']

def unshare_patches(xl_of, w_of):
    def li(rt, v): return 0x24000000 | (rt << 16) | (v & 0xFFFF)
    def sw(rt, o): return 0xAFA00000 | (rt << 16) | o
    T0, S1, S4, S5 = 8, 17, 20, 21
    x02 = xl_of('br_s02') + w_of('br_s02'); x06 = xl_of('br_s06') + w_of('br_s06')
    x09 = xl_of('br_s09') + w_of('br_s09'); x11 = xl_of('br_s11') + w_of('br_s11')
    return [
        # br_s02: its own xr in t0, and s5 left holding br_s06's xr for later
        (0x800C9EF8,
         [0x2408FFD1, 0x24150056, 0xAFA80010, 0x2408FFDE, 0xAFB50014, 0xAFA80018, 0xAFB1001C],
         [li(T0, x02), li(S5, x06), sw(T0, 16), sw(T0, 20), sw(T0, 24), sw(S1, 28), 0],
         'br_s02 xr=%d, leaves s5=%d for br_s06' % (x02, x06)),
        # br_s06 reads that s5 unchanged; br_s09 just needs its own immediate
        (0x800CA134, [0x2414007A], [li(S4, x09)], 'br_s09 xr=%d' % x09),
        # br_s11 no longer reads s4
        (0x800CA1C8,
         [0x2408FFE5, 0xAFA80010, 0x2408FFF2, 0xAFB40014, 0xAFA80018, 0xAFB1001C],
         [li(T0, x11), sw(T0, 16), sw(T0, 20), sw(T0, 24), sw(S1, 28), 0],
         'br_s11 xr=%d' % x11),
    ]
S00_X_ADDRS = (0x800C7674, 0x800C76A4)      # br_s00's animated x0 and x1 base

# Selection highlight (brf_800C6930, decompiled in b_select.c).  Integral draws
# a box [base_y-4, base_y+10] plus a 1px bar [base_y+10, base_y+11] - 15 rows.
# USA's equivalent takes `above` as a stack argument and draws [y-above, y+3]
# plus [y+3, y+4], i.e. above+4 = 6 rows, with its top ON the text top.  Our
# text top is y (we pad rather than offset by `above`), so the same-sized
# highlight aligned to our text is [y, y+5] plus [y+5, y+6].
# The operation-outline submenu's vertical rule.  Integral draws it centred,
# top = (-41 - v1) - 2 and bottom = v1 - 38 with v1 = (20n - 7)/2, so its length
# is 2*v1 + 5 = 20n - 2 - the 20 being Integral's original row advance.  For the
# one drawn item that is 17 game px; USA measures 12.6.  The bottom constant is
# independent of the row start (s0 = -41 - v1), so shortening it moves the rule
# without moving any text: 2*v1 + 0 = 12 for n = 1.
RULE = [(0x800C6F3C, -38, -43, 'operation-outline rule bottom')]

HILITE = [(0x800C6944, 10,  5, 'bar top / box bottom'),
          (0x800C6950, 11,  6, 'bar bottom'),
          (0x800C698C, -4,  0, 'box top')]

def xl_patches(int_ovl, usa_ovl):
    from quadscan import scan
    U = {n: xl for a, n, xl, yt, xr, yb, sa in scan(usa_ovl, 0x800C5970, 0x800CC1D8) if n}
    out = {}
    for a, n, xl, yt, xr, yb, sa in scan(int_ovl, BASEADDR, 0x800C983C):
        if not n or not n.startswith('br_s') or n == 'br_s00': continue
        if xl is None or sa is None or U.get(n) is None: continue
        new = U[n] + LINE_DELTA
        if LINE_DELTA and new != xl: out[n] = (sa, xl, new)
    return out
WIDEN = {strcode(n): n for n in quads}
for t in WIDEN: assert t in U, 'missing %s in USA archive' % WIDEN[t]
I0 = {e[0]: e[3] for e in ei}

# ---- target quads -----------------------------------------------------------
# b_select.c: brf_800C983C does setXY4(poly, xl, yt, xr, yb) with the UVs
# spanning the whole texture, so the texture is *stretched* to the quad.  The
# rendered size is therefore the quad's, and a texture only draws at its true
# size when its canvas equals the quad.  Several labels share an immediate
# (same store address), so a group gets one quad sized to its largest member
# and the smaller members are padded out to match.
# Only xr is ever patched.  The quad height is 13 for every br_sNN - retail's
# yb immediates all give exactly 13, and brf_800C69B4 forces 13 at runtime from
# 16 call sites regardless - and 17 for the FILE labels.  Measured against USA:
# the art must be PADDED into that height, never stretched to it, or the label
# renders 13/art_h too tall (the terrorists' armament came out 1.88x).
# brf_800C69B4 drew every br_sNN into a quad of ONE hardcoded height
# (`addiu v1, a2, 13`).  The selection highlight follows that quad, so a fixed
# height gives a fixed highlight - USA's varies because it sizes each box to its
# own label (`above + below + 5` = the texture height, for all 16).
#
# The exact per-label height is already in the poly and the positioner never
# touches it: brf_800C983C sets v0 = tex->off_y and v2 = tex->off_y + tex->h + 1,
# and tex->h is height-1, so **v2 - v0 is the texture height**.  Reading it needs
# four instructions, and the function has them: its x normalisation is entirely
# redundant (setXY4 already leaves x2 == x0 and x1 == x3), so the two `lh` and
# the two `sh` that copy x are dead, as is the nop.  Unlike the poly's y, the
# UVs are stable across frames, so this cannot accumulate.
ROW_H_ADDR = 0x800C69C8
ROW_H_OLD = [0x84440008,   # lh   a0,  8(v0)      x0   <- redundant
             0x84450020,   # lh   a1, 32(v0)      x3   <- redundant
             0x24C3000D,   # addiu v1, a2, 13     the fixed height
             0xA446000A,   # sh   a2, 10(v0)      y0
             0xA4460012,   # sh   a2, 18(v0)      y1
             0xA443001A,   # sh   v1, 26(v0)      y2
             0xA4430022,   # sh   v1, 34(v0)      y3
             0xA4440008,   # sh   a0,  8(v0)      x0 = x0  <- redundant
             0xA4450010,   # sh   a1, 16(v0)      x1 = x3  <- redundant
             0xA4440018,   # sh   a0, 24(v0)      x2 = x0  <- redundant
             0xA4450020]   # sh   a1, 32(v0)      x3 = x3  <- redundant
ROW_H_NEW = [0x9044001D,   # lbu  a0, 29(v0)      v2
             0x9045000D,   # lbu  a1, 13(v0)      v0
             0x00851823,   # subu v1, a0, a1      v1 = texture height
             0x00C31821,   # addu v1, a2, v1      v1 = y + height
             0xA446000A,   # sh   a2, 10(v0)      y0
             0xA4460012,   # sh   a2, 18(v0)      y1
             0xA443001A,   # sh   v1, 26(v0)      y2
             0xA4430022,   # sh   v1, 34(v0)      y3
             0x00000000,
             0x00000000,
             0x00000000]
# br_s00 has no stored quad: its right edge is animated as x1 = 52n/6 + 26,
# with the 52 baked into a shift/add chain at 800C7658.  Rebuilding the chain
# as 100n (using $at as scratch, same five slots) gives it USA's 100 px width.
S00_ADDR = 0x800C7658
S00_OLD = [0x00051040, 0x00451021, 0x00021080, 0x00451021, 0x00021080]
S00_NEW = [0x00050940, 0x00051180, 0x00411021, 0x00050880, 0x00411021]
# Row advance: read USA's own constants, never guessed.  Rows are laid out by
# accumulating the positioner's return value y + h, where h is its 4th argument.
# USA reworked that function - it takes the box extents as extra stack arguments
# where Integral hardcodes 13 - but the call structure is identical, so USA's
# advances transfer directly.  Both tables are extracted by simulating the
# registers over each overlay (see rowargs.py), so this follows the discs.
INT_FN, USA_BASE, USA_FN = 0x800C69B4, 0x800C5970, 0x800C9194

def advance_patches(int_ovl, usa_ovl):
    from rowargs import run_bytes
    usa = {idx: adv for _, idx, adv, _, _ in run_bytes(usa_ovl, USA_BASE, USA_FN)}
    W = list(struct.unpack('<%dI' % (len(int_ovl)//4), int_ovl[:len(int_ovl)//4*4]))
    def at(a): return W[(a - BASEADDR)//4]
    out = []
    for a, idx, adv, _, _ in run_bytes(int_ovl, BASEADDR, INT_FN):
        want = usa.get(idx)
        if want is None or want == adv: continue
        for x in [a+4] + list(range(a, a-0x80, -4)):        # incl. the delay slot
            w = at(x); op = w >> 26
            if op == 9 and ((w >> 16) & 31) == 7: out.append((x, adv, want, idx)); break
            if op == 0 and (w & 0x3F) == 0x21 and ((w >> 11) & 31) == 7:
                out.append((x, adv, want, idx)); break
    return out      # the reason for unanimous approval
from rowargs import run_bytes as _rb
USA_ADV = {}
for _a, _i, _adv, _ab, _be in _rb(pu[0], USA_BASE, USA_FN):
    if _i is not None and 9 <= _i <= 24: USA_ADV[strcode('br_s%02d' % (_i - 9))] = _adv
assert len(USA_ADV) == 16 and all(v for v in USA_ADV.values()), 'USA advances incomplete'

XL = dict(xl_patches(pi[0], pu[0]))
# clamp per family (labels sharing an xl value) so the widest one fits
from quadscan import scan as _scan
_sites = {n: (xl, sa) for a, n, xl, yt, xr, yb, sa in _scan(pi[0], BASEADDR, 0x800C983C)
          if n and n.startswith('br_s') and xl is not None and sa is not None}
_fam = {}
for n, (xl, sa) in _sites.items(): _fam.setdefault(xl, []).append(n)
for xl, members in _fam.items():
    widest = max(geo(U[strcode(n)])['w'] for n in members)
    room = RIGHT_LIMIT - widest
    if room < xl:
        for n in members: XL[n] = (_sites[n][1], xl, room)
        print('xl clamp: family at %d -> %d (widest %s is %d px)'
              % (xl, room, max(members, key=lambda m: geo(U[strcode(m)])['w']), widest))
for n, (addr, old, new) in XL.items():
    if n in quads: quads[n]['xl'] = [new, addr]     # xr is derived from this

gid = {}
for n, g in quads.items():
    if n not in UNSHARE: gid.setdefault(g['xr'][1], []).append(n)
newimm = {addr: max(quads[n]['xl'][0] + geo(U[strcode(n)])['w'] for n in members)
          for addr, members in gid.items()}
target = {}
for n, g in quads.items():
    if n.startswith('br_f'):
        h = 17
    else:
        h = geo(U[strcode(n)])['h']       # the quad now IS the texture height
    # un-shared labels get their own xr, so the quad is exactly USA's width
    w = geo(U[strcode(n)])['w'] if n in UNSHARE else newimm[g['xr'][1]] - g['xl'][0]
    target[strcode(n)] = (w, h)
# br_s00's right edge is computed at runtime (x1 = t0 + 26, an animated reveal),
# so it has no patchable quad and keeps Integral's slot.
ALL = ['br_s%02d' % i for i in range(16)] + ['br_f%02d' % i for i in range(4)]
for n in ALL:
    t = strcode(n)
    assert t in U and t in I0, 'missing %s' % n
    WIDEN[t] = n
    if t not in target:
        g = geo(I0[t])
        # br_s00 too: its height comes from the same per-label rule
        # br_s00's animated width is patched to USA's below
        w = geo(U[t])['w'] if n == 'br_s00' else g['w']
        target[t] = (w, 17 if n.startswith('br_f') else geo(U[t])['h'])
assert len(target) == 20, 'expected all 20 labels, got %d' % len(target)
json.dump({hex(k): list(v) for k, v in target.items()}, open('work/brf_target.json', 'w'))
json.dump({hex(k): v for k, v in newimm.items()}, open('work/brf_imm.json', 'w'))

# ---- VRAM occupancy from everything that is NOT being widened ---------------
grid = bytearray(1024 * 512)
def mark(px, py, uw, h):
    for y in range(py, min(512, py + h)):
        row = y * 1024
        for x in range(px, min(1024, px + uw)): grid[row + x] = 1
def busy(px, py, uw, h):
    if px + uw > 1024 or py + h > 512: return True
    for y in range(py, py + h):
        row = y * 1024
        if any(grid[row + x] for x in range(px, px + uw)): return True
    return False

for e in ei:
    g = geo(e[3])
    if e[0] not in WIDEN: mark(g['px'], g['py'], units(g['w'], g['bpp']), g['h'])
    if g['cy'] < 512: mark(g['cx'], g['cy'], 16, 1)

# ---- place each widened label ----------------------------------------------
place = {}
def tgt(t):
    w, h = target[t]; return w, h, units(w, geo(U[t])['bpp'])
for tid in sorted(WIDEN, key=lambda t: -tgt(t)[2]):
    ig = geo(I0[tid]); tw, th, need = tgt(tid)
    bpp = geo(U[tid])['bpp']
    if ufits(ig['px'], tw, bpp) and vfits(ig['py'], th)        and not busy(ig['px'], ig['py'], need, th):
        place[tid] = (ig['px'], ig['py'])
    else:
        found = None
        for page in (896, 960, 832, 768, 704, 640, 576, 512):
            for ny in range(0, 512 - th):
                for nx in range(page, page + 64 - need + 1):
                    if ufits(nx, tw, bpp) and vfits(ny, th) and not busy(nx, ny, need, th):
                        found = (nx, ny); break
                if found: break
            if found: break
        assert found, 'no VRAM room for %s (%d units x %d rows)' % (WIDEN[tid], need, th)
        place[tid] = found
    mark(place[tid][0], place[tid][1], need, th)

print('%-8s %-9s %-14s %-11s %-11s %s' % ('label', 'where', 'VRAM', 'quad', 'USA art', 'fit'))
for tid in sorted(place, key=lambda t: WIDEN[t]):
    ig, ug = geo(I0[tid]), geo(U[tid]); tw, th, _ = tgt(tid)
    tag = 'in place' if place[tid] == (ig['px'], ig['py']) else 'moved'
    fit = 'exact' if (ug['w'], ug['h']) == (tw, th) else (
          'pad %+d,%+d' % (tw - ug['w'], th - ug['h']) if ug['w'] <= tw and ug['h'] <= th
          else 'SCALE to fit')
    print('  %-8s %-9s (%3d,%3d)     %3dx%-3d    %3dx%-3d    %s'
          % (WIDEN[tid], tag, place[tid][0], place[tid][1], tw, th, ug['w'], ug['h'], fit))
json.dump({hex(k): list(v) for k, v in place.items()}, open('work/brf_widen.json', 'w'))
print('placed %d widened labels' % len(place))
