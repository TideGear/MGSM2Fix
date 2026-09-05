#!/usr/bin/env python
"""Port MGS1 (USA) English item/weapon descriptions into MGS Integral disc 1 & 2.

Reads the two boot executables, repacks the English strings into Integral's
Japanese text arenas, rewrites the two pointer tables, and emits PPF3 patches
addressed at the raw (2352-byte sector) CD images for Ketchup / MGSM2Fix.
"""
import struct, os, sys
from workdir import WORK

TADDR   = 0x80010000
HDR     = 0x800          # PS-EXE header; file 0x800 == RAM 0x80010000

# --- donor: MGS1 (USA), SLUS_005.94 / SLUS_007.76 (identical on both discs)
US_ITEM_TAB, US_WEAP_TAB = 0x800A0B38, 0x800A0D24
US_OUTLIER               = 0x0913A0          # "Mine Detector / HARD or EXTREME"
# --- target: MGS Integral, SLPM_862.47 / SLPM_862.48 (identical on both discs)
IN_ITEM_TAB, IN_WEAP_TAB = 0x8009E3E4, 0x8009E5CC
IN_OUTLIER               = 0x08EC4C
IN_OUTLIER_LUI           = 0x02BEB0          # lui  reg,hi16
IN_OUTLIER_ADDIU         = 0x02BEB4          # addiu reg,reg,lo16
N_ITEM, N_WEAP           = 26, 10
ARENA_A = (0x0016AC, 0x001E74)               # item description pool
ARENA_B = (0x001EE8, 0x002304)               # weapon description pool

# Ketchup disk descriptors: image offset of RAM 0x80010000 for each disc
INTEGRAL_BASE = {0: 0x131D2238, 1: 0x0EB38078}
SECTOR_DATA, SECTOR_RAW = 0x800, 0x930

ram  = lambda fo: TADDR + fo - HDR
fofs = lambda a:  a - TADDR + HDR

def cstr(d, fo):
    e = d.find(b'\x00', fo)
    return d[fo:e + 1]

def read_table(d, tab, n):
    base = fofs(tab)
    return [struct.unpack_from('<I', d, base + i * 4)[0] for i in range(n)]

def image_offset(base, fo):
    k = fo - HDR
    return base + (k // SECTOR_DATA) * SECTOR_RAW + (k % SECTOR_DATA)

def ppf3(records, desc):
    out = bytearray()
    out += b'PPF30'
    out += bytes([2])                                    # method: PPF3.0
    out += desc.encode('ascii')[:50].ljust(50, b'\x00')  # description
    out += bytes([0, 0, 0, 0])                           # imagetype, blockcheck, undo, dizfile
    assert len(out) == 60
    for off, data in records:
        for i in range(0, len(data), 255):
            chunk = data[i:i + 255]
            out += struct.pack('<Q', off + i) + bytes([len(chunk)]) + chunk
    return bytes(out)

def main():
    us  = open(os.path.join(WORK, 'us1.exe'), 'rb').read()
    ino = open(os.path.join(WORK, 'int1.exe'), 'rb').read()
    new = bytearray(ino)

    us_items = [cstr(us, fofs(a)) for a in read_table(us, US_ITEM_TAB, N_ITEM)]
    us_weaps = [cstr(us, fofs(a)) for a in read_table(us, US_WEAP_TAB, N_WEAP)]
    outlier  = cstr(us, US_OUTLIER)

    in_items = read_table(ino, IN_ITEM_TAB, N_ITEM)
    in_weaps = read_table(ino, IN_WEAP_TAB, N_WEAP)

    # lay strings out in the same order they appear in the original image
    def pack(arena, strings, order, extra=()):
        lo, hi = arena
        for a in range(lo, hi):
            new[a] = 0
        cur = lo
        placed = {}
        for k in order:
            s = strings[k]
            if cur + len(s) > hi:
                raise SystemExit('arena 0x%06X overflow at entry %d' % (lo, k))
            new[cur:cur + len(s)] = s
            placed[k] = ram(cur)
            cur = (cur + len(s) + 3) & ~3
        tail = []
        for s in extra:
            if cur + len(s) > hi:
                raise SystemExit('arena 0x%06X overflow on extra string' % lo)
            new[cur:cur + len(s)] = s
            tail.append(ram(cur))
            cur = (cur + len(s) + 3) & ~3
        return placed, tail, hi - cur

    order_i = sorted(range(N_ITEM), key=lambda i: in_items[i])
    order_w = sorted(range(N_WEAP), key=lambda i: in_weaps[i])
    new_i, _,  slack_a = pack(ARENA_A, us_items, order_i)
    new_w, tail, slack_b = pack(ARENA_B, us_weaps, order_w, extra=(outlier,))
    out_ram = tail[0]

    for i in range(N_ITEM):
        struct.pack_into('<I', new, fofs(IN_ITEM_TAB) + i * 4, new_i[i])
    for i in range(N_WEAP):
        struct.pack_into('<I', new, fofs(IN_WEAP_TAB) + i * 4, new_w[i])

    # repoint the HARD/EXTREME mine-detector message (lui/addiu pair)
    lui   = struct.unpack_from('<I', new, IN_OUTLIER_LUI)[0]
    addiu = struct.unpack_from('<I', new, IN_OUTLIER_ADDIU)[0]
    assert lui >> 26 == 0x0F and addiu >> 26 == 0x09
    lo16 = out_ram & 0xFFFF
    hi16 = ((out_ram >> 16) + (1 if lo16 & 0x8000 else 0)) & 0xFFFF
    struct.pack_into('<I', new, IN_OUTLIER_LUI,   (lui   & 0xFFFF0000) | hi16)
    struct.pack_into('<I', new, IN_OUTLIER_ADDIU, (addiu & 0xFFFF0000) | lo16)

    open(os.path.join(WORK, 'int1_en.exe'), 'wb').write(new)
    print('arena A slack: %d bytes   arena B slack: %d bytes' % (slack_a, slack_b))
    print('HARD/EXTREME message relocated to %08X' % out_ram)

    # ---- diff -> byte runs
    runs, i = [], 0
    while i < len(ino):
        if new[i] != ino[i]:
            j = i
            while j < len(ino) and new[j] != ino[j]:
                j += 1
            runs.append((i, bytes(new[i:j])))
            i = j
        else:
            i += 1
    print('%d changed runs, %d changed bytes' % (len(runs), sum(len(r[1]) for r in runs)))

    # ---- split runs at 2048-byte data-page boundaries, map to image offsets
    for disc, base in INTEGRAL_BASE.items():
        recs = []
        for fo, data in runs:
            p = 0
            while p < len(data):
                page_end = ((fo + p - HDR) // SECTOR_DATA + 1) * SECTOR_DATA + HDR
                n = min(len(data) - p, page_end - (fo + p))
                recs.append((image_offset(base, fo + p), data[p:p + n]))
                p += n
        blob = ppf3(recs, 'MGS Integral: English item text (disc %d)' % (disc + 1))
        name = os.path.join(WORK, 'INTEGRAL_disc%d_en_items.ppf' % (disc + 1))
        os.makedirs(os.path.dirname(name), exist_ok=True)
        open(name, 'wb').write(blob)
        print('%s: %d records, %d bytes' % (name, len(recs), len(blob)))

if __name__ == '__main__':
    main()
