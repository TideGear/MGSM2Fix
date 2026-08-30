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
import struct, json, sys
sys.path.insert(0, '.')
import pcx4
from PIL import Image
from brf_widen import (stage, parse, geo, units, strcode, pad, BASEADDR)

si, ti, Fi, pi = stage('work/int1_stage.dir')
su, tu, Fu, pu = stage('work/us1_stage.dir')
ni = [k for k, t in enumerate(ti) if chr(t[1]) + chr(t[2]) == 'nd'][0]
nu = [k for k, t in enumerate(tu) if chr(t[1]) + chr(t[2]) == 'nd'][0]
ei, taili = parse(pi[ni]); eu, _ = parse(pu[nu])
U = {e[0]: e[3] for e in eu}
quads  = json.load(open('work/brf_quads_all.json'))
target = {int(k, 16): tuple(v) for k, v in json.load(open('work/brf_target.json')).items()}
place  = {int(k, 16): tuple(v) for k, v in json.load(open('work/brf_widen.json')).items()}
newimm = {int(k, 16): v for k, v in json.load(open('work/brf_imm.json')).items()}
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
    if uw <= cw and uh <= ch:                      # true size, padded
        rows = [[(urows[y][x] if y < uh and x < uw else bg) for x in range(cw)]
                for y in range(ch)]
        how = 'exact' if (uw, uh) == (cw, ch) else 'pad'
    else:                                          # quad too small - scale down
        im = Image.new('P', (uw, uh)); im.putdata([v for r in urows for v in r])
        px = list(im.resize((cw, ch), Image.NEAREST).getdata())
        rows = [px[y*cw:(y+1)*cw] for y in range(ch)]
        how = 'scaled'
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
    if tid in LAB: assert (g['px'] % 64) + u <= 64, '0x%04X crosses a texture page' % tid
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
    qw = imm16(g['xr'][1]) - g['xl'][0]
    # families B and C get no yb immediate: the height is forced at runtime
    qh = g['fixed_h'] if 'fixed_h' in g else imm16(g['yb'][1]) - g['yt'][0]
    assert (qw, qh) == (G2[tid]['w'], G2[tid]['h']), \
        '%s quad %dx%d vs texture %dx%d' % (name, qw, qh, G2[tid]['w'], G2[tid]['h'])
print('\nlabel textures:')
for tid, uw, uh, cw, ch, how in sorted(report):
    print('   %04X  USA %3dx%-3d -> canvas %3dx%-3d  %s' % (tid, uw, uh, cw, ch, how))
print('\nverified: every quad equals its texture, no page crossings, no overlaps; %d sectors' % nsect)
open('work/brf_en.bin', 'wb').write(bytes(out))
