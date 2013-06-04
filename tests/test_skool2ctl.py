# -*- coding: utf-8 -*-
import unittest

from skoolkittest import SkoolKitTestCase
from skoolkit import skool2ctl, VERSION

ELEMENTS = 'btdrmsc'

TEST_SKOOL = """; Test skool file for skool2ctl testing
c32768 RET
"""

class MockCtlWriter:
    def __init__(self, *args):
        global mock_ctl_writer
        self.args = args
        self.write_called = False
        mock_ctl_writer = self

    def write(self):
        self.write_called = True

class Skool2CtlTest(SkoolKitTestCase):
    def test_no_arguments(self):
        output, error = self.run_skool2ctl(catch_exit=True)
        self.assertEqual(len(output), 0)
        self.assertTrue(error.startswith('usage: skool2ctl.py'))

    def test_invalid_arguments(self):
        for args in ('-h', '-x test.skool'):
            output, error = self.run_skool2ctl(args, catch_exit=True)
            self.assertEqual(len(output), 0)
            self.assertTrue(error.startswith('usage: skool2ctl.py'))

    def test_default_option_values(self):
        self.mock(skool2ctl, 'CtlWriter', MockCtlWriter)
        skoolfile = 'test.skool'
        skool2ctl.main((skoolfile,))
        infile, elements, write_hex, write_asm_dirs = mock_ctl_writer.args
        self.assertEqual(infile, skoolfile)
        self.assertEqual(elements, ELEMENTS)
        self.assertFalse(write_hex)
        self.assertTrue(write_asm_dirs)
        self.assertTrue(mock_ctl_writer.write_called)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_skool2ctl(option, err_lines=True, catch_exit=True)
            self.assertEqual(len(output), 0)
            self.assertEqual(len(error), 1)
            self.assertEqual(error[0], 'SkoolKit {}'.format(VERSION))

    def test_option_w(self):
        self.mock(skool2ctl, 'CtlWriter', MockCtlWriter)
        skoolfile = 'test.skool'
        for w in ('b', 't', 'd', 'r', 'm', 's', 'c', 'btd', ELEMENTS):
            for option in ('-w', '--write'):
                skool2ctl.main((option, w, skoolfile))
                infile, elements, write_hex, write_asm_dirs = mock_ctl_writer.args
                self.assertEqual(infile, skoolfile)
                self.assertEqual(elements, w)
                self.assertFalse(write_hex)
                self.assertTrue(write_asm_dirs)
                self.assertTrue(mock_ctl_writer.write_called)

    def test_option_h(self):
        self.mock(skool2ctl, 'CtlWriter', MockCtlWriter)
        skoolfile = 'test.skool'
        for option in ('-h', '--hex'):
            skool2ctl.main((option, skoolfile))
            infile, elements, write_hex, write_asm_dirs = mock_ctl_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(elements, ELEMENTS)
            self.assertTrue(write_hex)
            self.assertTrue(write_asm_dirs)
            self.assertTrue(mock_ctl_writer.write_called)

    def test_option_a(self):
        self.mock(skool2ctl, 'CtlWriter', MockCtlWriter)
        skoolfile = 'test.skool'
        for option in ('-a', '--no-asm-dirs'):
            skool2ctl.main((option, skoolfile))
            infile, elements, write_hex, write_asm_dirs = mock_ctl_writer.args
            self.assertEqual(infile, skoolfile)
            self.assertEqual(elements, ELEMENTS)
            self.assertFalse(write_hex)
            self.assertFalse(write_asm_dirs)
            self.assertTrue(mock_ctl_writer.write_called)

    def test_run(self):
        skoolfile = self.write_text_file(TEST_SKOOL, suffix='.skool')
        output, error = self.run_skool2ctl(skoolfile)
        self.assertEqual(len(error), 0)
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'c 32768 Test skool file for skool2ctl testing')

if __name__ == '__main__':
    unittest.main()
