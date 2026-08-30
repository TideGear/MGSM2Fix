"""Build the brf stage: nine labels widened to USA proportions (quad immediates
patched in the overlay + USA texture placed with VRAM room), the remaining
seven kept fitted to their Integral slot."""
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
quads = json.load(open('work/brf_quads.json'))
place = {int(k, 16): tuple(v) for k, v in json.load(open('work/brf_widen.json')).items()}
WIDEN = {strcode(n): n for n in quads}
LAB = set(range(0x1D82, 0x1D8C)) | set(range(0x1DA2, 0x1DA8))
# the four FILE NN labels down the left; their draw rects are zero at the
# call site (set elsewhere), so these are fitted to the Integral slot.
LAB |= {0xE981, 0xE982, 0xE983, 0xE984}

# ---- overlay: patch the quad immediates -------------------------------------
ovl = bytearray(pi[0])
patched = []
for name, g in quads.items():
    tid = strcode(name)
    ug = geo(U[tid])
    xl, _ = g['xl']; yt, _ = g['yt']
    new_xr = xl + ug['w']; new_yb = yt + ug['h']
    for key, val in (('xr', new_xr), ('yb', new_yb)):
        old, addr = g[key]
        off = addr - BASEADDR
        w = struct.unpack('<I', ovl[off:off+4])[0]
        assert (w >> 26) == 9 and ((w >> 21) & 31) == 0, 'not addiu rt,zero at %08X' % addr
        assert (w & 0xFFFF) == (old & 0xFFFF), 'immediate mismatch at %08X' % addr
        struct.pack_into('<I', ovl, off, (w & 0xFFFF0000) | (val & 0xFFFF))
        patched.append((name, key, old, val))
print('patched %d quad immediates:' % len(patched))
for name, key, old, new in patched:
    print('   %-8s %s %5d -> %-5d' % (name, key, old, new))

# ---- archive: widened labels at USA size, the rest fitted to their slot ------
for e in ei:
    if e[0] not in LAB or e[0] not in U: continue
    ig = geo(e[3]); ug = geo(U[e[0]])
    if e[0] in place:                                   # widened: USA art verbatim
        src = bytearray(U[e[0]])
        npx, npy = place[e[0]]
        struct.pack_into('<7H', src, 74, 12345, ug['fl'], npx, npy, ig['cx'], ig['cy'], ug['nc'])
    else:                                               # unwidened: fit the slot
        iw, ih, _, _ = pcx4.decode(e[3])
        uw, uh, upal, urows = pcx4.decode(U[e[0]])
        im = Image.new('P', (uw, uh)); im.putdata([v for r in urows for v in r])
        px = list(im.resize((iw, ih), Image.NEAREST).getdata())
        rows = [px[y*iw:(y+1)*iw] for y in range(ih)]
        src = bytearray(pcx4.encode(U[e[0]], iw, ih, upal, rows))
        struct.pack_into('<7H', src, 74, 12345, ug['fl'], ig['px'], ig['py'], ig['cx'], ig['cy'], ug['nc'])
    while len(src) % 4: src.append(0)
    e[3] = bytes(src); e[2] = len(src)

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
rects = []
for e in e2:
    g = geo(e[3]); u = units(g['w'], g['bpp'])
    # only the labels we place must respect the page limit; some original
    # background textures already straddle one and the game copes.
    if e[0] in LAB:
        assert (g['px'] % 64) + u <= 64, '0x%04X crosses a texture page' % e[0]
    rects.append((g['px'], g['py'], u, g['h'], e[0]))
for i in range(len(rects)):
    for j in range(i+1, len(rects)):
        a, b = rects[i], rects[j]
        if a[0] < b[0]+b[2] and b[0] < a[0]+a[2] and a[1] < b[1]+b[3] and b[1] < a[1]+a[3]:
            raise SystemExit('VRAM overlap 0x%04X / 0x%04X' % (a[4], b[4]))
for name, g in quads.items():
    tid = strcode(name); ug = geo(U[tid]); tg = geo(dict((e[0], e[3]) for e in e2)[tid])
    xl, _ = g['xl']; yt, _ = g['yt']
    off = g['xr'][1] - BASEADDR
    qw = (struct.unpack('<I', ovl[off:off+4])[0] & 0xFFFF) - xl
    assert qw == tg['w'] == ug['w'], '%s quad %d vs texture %d' % (name, qw, tg['w'])
print('verified: quads match textures, no page crossings, no overlaps; %d sectors' % nsect)
open('work/brf_en.bin', 'wb').write(bytes(out))
