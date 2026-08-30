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

# Horizontal: Integral's whole briefing panel sits 20 game px right of USA's
# (the vertical rule measures x 2101 vs 1921, 180 display px / 9). The label xl
# constants differ by only 16-17, so the labels sit ~4 px left of where USA has
# them relative to their own rule. Setting xl = USA's xl + that offset puts them
# exactly where USA has them; xr follows because the canvas is xl + USA's width.
LINE_DELTA = 20
S00_X_ADDRS = (0x800C7674, 0x800C76A4)      # br_s00's animated x0 and x1 base

def xl_patches(int_ovl, usa_ovl):
    from quadscan import scan
    U = {n: xl for a, n, xl, yt, xr, yb, sa in scan(usa_ovl, 0x800C5970, 0x800CC1D8) if n}
    out = {}
    for a, n, xl, yt, xr, yb, sa in scan(int_ovl, BASEADDR, 0x800C983C):
        if not n or not n.startswith('br_s') or n == 'br_s00': continue
        if xl is None or sa is None or U.get(n) is None: continue
        new = U[n] + LINE_DELTA
        if new != xl: out[n] = (sa, xl, new)
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
# brf_800C69B4 draws every br_sNN into a quad of one hardcoded height
# (`addiu v1, a2, 13` at 800C69D0).  Padding keeps art 1:1 at ANY quad height,
# so raising it to 20 lets the two-line labels (br_s02 20 rows, br_s12/s13 19)
# render full size while the single-line ones are unaffected - their extra rows
# are transparent and the row positions come from y, which does not change.
ROW_H_ADDR, ROW_H_OLD, ROW_H = 0x800C69D0, 13, 20
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
XL = xl_patches(pi[0], pu[0])
for n, (addr, old, new) in XL.items():
    if n in quads: quads[n]['xl'] = [new, addr]     # xr is derived from this

gid = {}
for n, g in quads.items(): gid.setdefault(g['xr'][1], []).append(n)
newimm = {addr: max(quads[n]['xl'][0] + geo(U[strcode(n)])['w'] for n in members)
          for addr, members in gid.items()}
target = {}
for n, g in quads.items():
    target[strcode(n)] = (newimm[g['xr'][1]] - g['xl'][0],
                          17 if n.startswith('br_f') else ROW_H)
# br_s00's right edge is computed at runtime (x1 = t0 + 26, an animated reveal),
# so it has no patchable quad and keeps Integral's slot.
ALL = ['br_s%02d' % i for i in range(16)] + ['br_f%02d' % i for i in range(4)]
for n in ALL:
    t = strcode(n)
    assert t in U and t in I0, 'missing %s' % n
    WIDEN[t] = n
    if t not in target:
        g = geo(I0[t])
        # br_s00's animated width is patched to USA's below
        w = geo(U[t])['w'] if n == 'br_s00' else g['w']
        target[t] = (w, 17 if n.startswith('br_f') else ROW_H)
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
