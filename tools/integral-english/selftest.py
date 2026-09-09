"""Tests for the parts of the toolchain that need no game data.

    py selftest.py            run them
    py selftest.py -v         say what each one checks

Until 2026-09-07 the only test this port had was `rebuild.py`, which needs an
installed collection, four retail executables, a decomp checkout and the PSY-Q
toolchain, and takes minutes. That is the right test for the *build*, and it is
no test at all for the pieces underneath it: a PPF emitter that must split runs
at two different boundaries, a texture codec with a run-length cap that was once
one short, a checksum with a rounding step that is easy to get subtly wrong.
Those are pure functions over bytes and they can be checked in a second.

What this deliberately does NOT do is check the algorithms against ground truth
- that needs the real discs. `py cdecc.py` is where the EDC/ECC is proved, by
recomputing retail sectors and matching what is stored on them, and `rebuild.py
--compare-deployed` is where the whole build is. This file checks the algebra
those rest on: round trips, boundary conditions, and the invariants each module
documents about itself.
"""
import os
import struct
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cdecc
import pad2
import pcx4
import portio
import widths


class Ppf(unittest.TestCase):
    """portio's PPF3 emitter and reader"""

    def test_round_trip(self):
        records = [(0x1000, b'hello'), (0x2000, bytes(range(200)))]
        blob = portio.ppf(records, 'test')
        path = _tmp('rt.ppf', blob)
        self.assertEqual(portio.read_ppf(path), records)

    def test_runs_split_at_255(self):
        """A record's length is one byte, so nothing may exceed 255."""
        blob = portio.ppf([(0, bytes(1000))], 'long')
        path = _tmp('long.ppf', blob)
        out = portio.read_ppf(path)
        self.assertTrue(all(len(d) <= 255 for _, d in out))
        self.assertEqual(sum(len(d) for _, d in out), 1000)
        self.assertEqual(out[0][0], 0)

    def test_map_runs_never_crosses_a_payload_boundary(self):
        """Ketchup drops the part of a record that lands in a sector's 304-byte
        tail while still logging success - the fault that silently cost
        `en_savemsg` 142 of 442 bytes. `map_runs` must split there."""
        for start in (0, 1, 2000, 2047, 2048, 4095):
            for length in (1, 2, 255, 256, 5000):
                for offset, data in portio.map_runs(100, [(start, bytes(length))]):
                    within = offset % 2352
                    self.assertGreaterEqual(within, 24)
                    self.assertLessEqual(within + len(data), 24 + 2048,
                                         'run at %d+%d crosses a payload boundary' % (start, length))
                    self.assertLessEqual(len(data), 255)

    def test_image_offset_is_2352_byte_geometry(self):
        """A PPF offset is (lba + off//2048)*2352 + 24 + off%2048. Dividing by
        2048 instead made a finished VR port look unported for twenty minutes."""
        self.assertEqual(portio.image_offset(0, 0), 24)
        self.assertEqual(portio.image_offset(0, 2047), 24 + 2047)
        self.assertEqual(portio.image_offset(0, 2048), 2352 + 24)
        self.assertEqual(portio.image_offset(10, 0), 10 * 2352 + 24)

    def test_description_must_fit_50_bytes(self):
        """`ljust(50)` pads but never truncates; a 60-byte description once
        shifted every record offset and filled a 306 MB log."""
        with self.assertRaises(AssertionError):
            portio.ppf([(0, b'x')], 'y' * 51)

    def test_blockcheck_is_transparent_to_the_reader(self):
        records = [(0x40, b'abcd')]
        block = bytes(range(256)) * 4
        with_bc = portio.ppf(records, 'bc', blockcheck=block)
        plain = portio.ppf(records, 'bc')
        self.assertEqual(len(with_bc) - len(plain), 1024)
        self.assertEqual(with_bc[57], 1)
        self.assertEqual(portio.read_ppf(_tmp('bc.ppf', with_bc)), records)
        self.assertEqual(portio.add_blockcheck(plain, block), with_bc)


class Records(unittest.TestCase):
    """the 07-length-payload record chain every text patch rewrites"""

    def test_round_trip(self):
        items = [b'one\0', b'two\0', b'\0']
        blob = portio.encode_records(items)
        out, end = portio.records(blob, 0)
        self.assertEqual(out, items)
        self.assertEqual(end, len(blob))

    def test_every_record_must_be_nul_terminated(self):
        with self.assertRaises(AssertionError):
            portio.encode_records([b'no terminator'])

    def test_changed_runs_reports_only_differences(self):
        a = bytes(10)
        b = bytearray(a)
        b[2] = 1
        b[3] = 1
        b[8] = 1
        self.assertEqual(list(portio.changed_runs(a, bytes(b))),
                         [(2, b'\x01\x01'), (8, b'\x01')])


class Ecc(unittest.TestCase):
    """cdecc's algebra. Ground truth is `py cdecc.py`, against the real discs."""

    def sector(self, payload=None, submode=0x08):
        raw = bytearray(2352)
        raw[0:12] = b'\x00' + b'\xff' * 10 + b'\x00'
        raw[12:16] = bytes((0x00, 0x02, 0x00, 0x02))
        raw[16:24] = bytes((0, 0, submode, 0)) * 2
        raw[24:2072] = (payload or bytes(2048))
        return bytes(raw)

    def test_fixed_sector_verifies(self):
        s = cdecc.fixed(self.sector(bytes(range(256)) * 8))
        self.assertTrue(cdecc.verify(s))

    def test_tail_is_280_bytes_and_only_the_tail_changes(self):
        s = self.sector(b'\x5a' * 2048)
        f = cdecc.fixed(s)
        self.assertEqual(len(cdecc.tail(s)), 280)
        self.assertEqual(f[:2072], s[:2072])

    def test_payload_changes_the_tail(self):
        a = self.sector(bytes(2048))
        b = bytearray(a)
        b[24] = 1
        self.assertNotEqual(cdecc.tail(a), cdecc.tail(bytes(b)))

    def test_subheader_is_covered_by_the_edc(self):
        """The EDC runs from byte 16, not byte 24. Getting that wrong passes
        every test that only ever changes user data."""
        a = self.sector(bytes(2048))
        b = bytearray(a)
        b[17] = b[21] = 3
        self.assertNotEqual(cdecc.tail(a)[:4], cdecc.tail(bytes(b))[:4])

    def test_address_is_not_covered_by_the_ecc(self):
        """In Mode 2 the header is zeroed before the parity is computed, so two
        sectors differing only in their address have identical parity. A build
        that protected the address would fail on every disc ever pressed."""
        a = self.sector(b'\x11' * 2048)
        b = bytearray(a)
        b[12:16] = bytes((0x00, 0x03, 0x10, 0x02))
        self.assertEqual(cdecc.tail(a)[4:], cdecc.tail(bytes(b))[4:])

    def test_idempotent(self):
        s = cdecc.fixed(self.sector(b'\x7e' * 2048))
        self.assertEqual(cdecc.fixed(s), s)

    def test_form_2_is_refused(self):
        with self.assertRaises(AssertionError):
            cdecc.tail(self.sector(submode=0x28))       # bit 5 set: Form 2
        self.assertEqual(cdecc.form(self.sector(submode=0x28)), 2)
        self.assertEqual(cdecc.form(self.sector()), 1)


class Pcx(unittest.TestCase):
    """the 4-plane RLE PCX the texture loader expects"""

    def template(self, w, h, nplanes=4):
        stride = (w + 7) // 8
        head = bytearray(128)
        struct.pack_into('<HHHH', head, 4, 0, 0, w - 1, h - 1)
        head[65] = nplanes
        struct.pack_into('<H', head, 66, stride)
        return bytes(head)

    def test_round_trip(self):
        w, h = 32, 4
        pal = [(i * 8, i * 4, i * 2) for i in range(16)]
        rows = [[(x + y) % 16 for x in range(w)] for y in range(h)]
        blob = pcx4.encode(self.template(w, h), w, h, pal, rows)
        w2, h2, pal2, rows2 = pcx4.decode(blob)
        self.assertEqual((w2, h2), (w, h))
        self.assertEqual(rows2, rows)
        self.assertEqual(pal2, pal)

    def test_run_cap_is_a_parameter_and_63_is_legal(self):
        """PCX_RLE_CODE + run allows 63; the original call site capped at 62 and
        the VR option archive needed the last byte back. The default stays 62 so
        every shipped patch still rebuilds byte for byte."""
        data = b'\xaa' * 63
        self.assertLessEqual(len(pcx4._rle(data, maxrun=63)), len(pcx4._rle(data)))
        with self.assertRaises(AssertionError):
            pcx4._rle(data, maxrun=64)


class Widths(unittest.TestCase):
    """widths.py's measuring and the window budget derived from the decomp"""

    W = {c: 8 for c in range(32, 128)}

    def test_ascii_is_one_byte_and_zenkaku_two(self):
        self.assertEqual(widths.width(b'AB', self.W), 16)
        self.assertEqual(widths.width(b'\x9a\x01', self.W), 12)
        self.assertEqual(widths.width(b'A\x9a\x01B', self.W), 28)

    def test_lead_byte_0x80_is_a_pair_not_an_ascii_advance(self):
        """Codes 0x8080..0x80FF exist; a `>= 0x81` test would read the lead byte
        as ASCII and under-measure the line."""
        self.assertEqual(widths.width(b'\x80\x90', self.W), 12)

    def test_window_budget_matches_the_worked_example(self):
        """-w 32 53 256 118 gives 20 whole cells, 240 px, 228 px of room."""
        self.assertEqual(widths.window_budget([32, 53, 256, 118]), 228)

    def test_budget_rounds_down_to_whole_cells(self):
        for w in range(200, 260):
            self.assertEqual(widths.window_budget([0, 0, w, 0]) % 12, 0)

    def test_split_lines_finds_the_pool_separator(self):
        self.assertEqual(widths.split_lines(b'A\x80\x7cB'), [b'A', b'B'])
        self.assertEqual(widths.split_lines(b'AB'), [b'AB'])


class Pad2(unittest.TestCase):
    """pad2.py's slot fill: USA's line into Integral's longer slot"""

    SLOT = bytes(range(1, 55)) + bytes(1)        # 55 bytes, NUL-terminated
    EN = b'PLUG CONTROLLER INTO | CONTROLLER PORT 1.' + bytes(1)

    def test_terminator_immediately_follows_the_text(self):
        """The trap: pad BEFORE the terminator and the spaces are drawn.
        `font_print_string` measures what it draws and jimaku centres on that
        width, so trailing spaces would pull the line off centre.
        """
        out = pad2.fill(self.SLOT, self.EN)
        self.assertEqual(out[:len(self.EN)], self.EN)
        self.assertEqual(out.index(0), len(self.EN) - 1)

    def test_length_and_final_nul_are_preserved(self):
        """Nothing may move: the record's length byte is not rewritten, and
        `portio.records` requires the payload's last byte to be NUL.
        """
        out = pad2.fill(self.SLOT, self.EN)
        self.assertEqual(len(out), len(self.SLOT))
        self.assertEqual(out[-1], 0)

    def test_dead_tail_is_spaces(self):
        out = pad2.fill(self.SLOT, self.EN)
        tail = out[len(self.EN):-1]
        self.assertEqual(tail, b' ' * (len(self.SLOT) - len(self.EN) - 1))

    def test_refuses_a_replacement_that_does_not_leave_the_final_nul(self):
        """A replacement as long as the slot would need no padding and is out
        of scope: this port only ever writes a shorter line.
        """
        with self.assertRaises(AssertionError):
            pad2.fill(self.SLOT, bytes(len(self.SLOT) - 1) + bytes(1))

    def test_refuses_an_unterminated_replacement(self):
        with self.assertRaises(AssertionError):
            pad2.fill(self.SLOT, b'NO TERMINATOR')


_TMP = os.path.join(os.environ.get('TEMP') or '/tmp', 'integral-english-selftest')


def _tmp(name, data):
    os.makedirs(_TMP, exist_ok=True)
    path = os.path.join(_TMP, name)
    with open(path, 'wb') as handle:
        handle.write(data)
    return path


if __name__ == '__main__':
    unittest.main(verbosity=2 if '-v' in sys.argv else 1,
                  argv=[a for a in sys.argv if a != '-v'])
