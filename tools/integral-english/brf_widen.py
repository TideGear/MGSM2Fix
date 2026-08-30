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
gid = {}
for n, g in quads.items():
    for key in ('xr', 'yb'):
        if key in g: gid.setdefault((key, g[key][1]), []).append(n)
newimm = {}
for (key, addr), members in gid.items():
    lo_key = 'xl' if key == 'xr' else 'yt'
    dim = 'w' if key == 'xr' else 'h'
    newimm[addr] = max(quads[n][lo_key][0] + geo(U[strcode(n)])[dim] for n in members)
target = {}
for n, g in quads.items():
    w = newimm[g['xr'][1]] - g['xl'][0]
    # Families B and C never get a yb immediate: the height is forced at runtime
    # (13 rows by brf_800C69B4, 17 for the FILE labels), so the canvas must use
    # that height and taller USA art is scaled down to it.
    h = g['fixed_h'] if 'fixed_h' in g else newimm[g['yb'][1]] - g['yt'][0]
    target[strcode(n)] = (w, h)
# br_s00's right edge is computed at runtime (x1 = t0 + 26, an animated reveal),
# so it has no patchable quad and keeps Integral's slot.
ALL = ['br_s%02d' % i for i in range(16)] + ['br_f%02d' % i for i in range(4)]
for n in ALL:
    t = strcode(n)
    assert t in U and t in I0, 'missing %s' % n
    WIDEN[t] = n
    if t not in target: g = geo(I0[t]); target[t] = (g['w'], g['h'])
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
    if (ig['px'] % 64) + need <= 64 and not busy(ig['px'], ig['py'], need, th):
        place[tid] = (ig['px'], ig['py'])
    else:
        found = None
        for page in (896, 960, 832, 768, 704, 640, 576, 512):
            for ny in range(0, 512 - th):
                for nx in range(page, page + 64 - need + 1):
                    if not busy(nx, ny, need, th): found = (nx, ny); break
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
