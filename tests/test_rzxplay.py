import os
from textwrap import dedent
from unittest.mock import patch

from skoolkittest import SkoolKitTestCase, RZX
from skoolkit import VERSION, SkoolKitError, rzxplay

def mock_run(*args):
    global run_args
    run_args = args

def mock_write_snapshot(fname, ram, registers, state):
    global s_fname, s_memory, s_banks, s_reg, s_state
    s_fname = fname
    if len(ram) == 8:
        s_banks = ram
        page = 0
        for spec in state:
            if spec.startswith('7ffd='):
                page = int(spec[5:]) % 8
                break
        s_memory = [0] * 16384 + ram[5] + ram[2] + ram[page]
    else:
        s_banks = None
        s_memory = [0] * 16384 + ram
    s_reg = registers
    s_state = state

class RzxplayTest(SkoolKitTestCase):
    def _test_rzx(self, rzx, exp_output, options='', exp_trace=None, outfile=None):
        rzxfile = self.write_rzx_file(rzx)
        logfile = 'trace.log'
        if exp_trace:
            options += f' --trace {logfile}'
        args = f'{options} {rzxfile}'
        if outfile:
            args += f' {outfile}'
        output, error = self.run_rzxplay(args)
        self.assertEqual(error, '')
        self.assertEqual(dedent(exp_output).lstrip(), output)
        if exp_trace:
            self.assertTrue(os.path.isfile(logfile))
            with open(logfile) as f:
                trace = f.read()
            self.assertEqual(dedent(exp_trace).lstrip(), trace)

    @patch.object(rzxplay, 'run', mock_run)
    def test_default_option_values(self):
        rzxplay.main(['test.rzx'])
        rzxfile, options = run_args
        self.assertEqual(rzxfile, 'test.rzx')
        self.assertFalse(options.force)
        self.assertEqual(options.fps, 50)
        self.assertTrue(options.screen)
        self.assertFalse(options.quiet)
        self.assertEqual(options.scale, 2)
        self.assertIsNone(options.stop)
        self.assertIsNone(options.trace)

    def test_sna(self):
        ram = [0] * 0xC000
        header = [0] * 27
        sp = 0x8000
        pc = 0xC000
        header[23:25] = (sp % 256, sp // 256)
        ram[0x4000:0x4002] = (pc % 256, pc // 256)
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        sna = header + ram
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(sna, 'sna', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v1(self):
        ram = [0] * 0xC000
        pc = 0xD000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=1, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v2(self):
        ram = [0] * 0xC000
        pc = 0xE000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=2, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_z80v3(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_szx(self):
        ram = [0] * 0xC000
        pc = 0x8000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        szxdata = self.write_szx(ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_compressed_snapshot(self):
        ram = [0] * 0xC000
        header = [0] * 27
        sp = 0x8000
        pc = 0x6000
        header[23:25] = (sp % 256, sp // 256)
        ram[0x4000:0x4002] = (pc % 256, pc // 256)
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        sna = header + ram
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(sna, 'sna', frames, flags=2)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_repeated_port_readings(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE)
            0xDB, 0xFE, # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191]), (1, 65535, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_input_recording_before_snapshot(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        rzx.add_snapshot(None, None)
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--quiet --no-screen')

    def test_multiple_snapshots(self):
        pc = 0xC000
        code = (
            [0xAF], # XOR A
            [0xA8], # XOR B
        )
        frames = (
            [(1, 0, [])],
            [(1, 0, [])]
        )
        rzx = RZX()
        for c, f in zip(code, frames):
            ram = [0] * 0xC000
            ram[pc - 0x4000:pc - 0x4000 + len(c)] = c
            registers = {'PC': pc, 'iff1': 1}
            z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
            rzx.add_snapshot(z80data, 'z80', f)
        exp_output = ''
        exp_trace = """
            F:0 T:00000 C:00001 I:00000 $C000 XOR A
            F:0 T:00000 C:00001 I:00000 $C000 XOR B
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_halt_waits_for_rzx_frame_boundary(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0x76, # HALT
            0x76, # HALT
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'iff1': 1}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(2, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames, tstates=69886)
        exp_output = ''
        exp_trace = """
            F:0 T:69886 C:00002 I:00000 $C000 HALT
            F:0 T:69890 C:00001 I:00000 $C000 HALT
            F:1 T:00013 C:00001 I:00000 $0038 PUSH AF
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ei_does_not_block_interrupt(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xFB, # EI
            0xAF, # XOR A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 T:00000 C:00001 I:00000 $C000 EI
            F:1 T:00013 C:00001 I:00000 $0038 PUSH AF
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_ld_r_a_counts_as_two_fetches(self):
        ram = [0] * 0xC000
        pc = 0xC000
        a = 1
        code = (
            0xED, 0x4F, # LD R,A
            0xAF,       # XOR A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc, 'a': a}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 T:00000 C:00003 I:00000 $C000 LD R,A
            F:0 T:00009 C:00001 I:00000 $C002 XOR A
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_bank_switching(self):
        ram = [0] * 0xC000
        pc = 0xBFFE
        a = 7
        bc = 0x7FFD
        code = (
            0xED, 0x79, # $BFFE OUT (C),A
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        pages = {a: [0] * 0x4000}
        pages[a][0] = 0xAF # $C000 XOR A
        registers = {'A': a, 'B': bc // 256, 'C': bc % 256, 'PC': pc, 'iff1': 1}
        z80data = self.write_z80_file(None, ram, machine_id=4, out7ffd=4, pages=pages, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(3, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 T:00000 C:00003 I:00000 $BFFE OUT (C),A
            F:0 T:00012 C:00001 I:00000 $C000 XOR A
        """
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', exp_trace)

    def test_printing_progress(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = "[0.0%]\x08\x08\x08\x08\x08\x08[50.0%]\x08\x08\x08\x08\x08\x08\x08"
        self._test_rzx(rzx, exp_output, '--no-screen')

    @patch.object(rzxplay, 'write_snapshot', mock_write_snapshot)
    def test_write_snapshot(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = [
            0xDB, 0xFE, # IN A,($FE)
        ]
        end = pc + len(code)
        ram[pc - 0x4000:end - 0x4000] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        outfile = 'out.z80'
        exp_output = f'Wrote {outfile}\n'
        self._test_rzx(rzx, exp_output, '--quiet --no-screen', outfile=outfile)
        self.assertEqual(s_fname, outfile)
        self.assertLessEqual({'A=191', f'PC={end}'}, set(s_reg))
        self.assertIn('tstates=0', s_state)
        self.assertIsNone(s_banks)
        self.assertEqual(code, s_memory[pc:end])

    def test_z80v2_unsupported_machine(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=2, machine_id=4, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported machine type')

    def test_z80v3_unsupported_machine(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, machine_id=5, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported machine type')

    def test_z80v3_unsupported_machine_with_hardware_modifier(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, machine_id=5, modify=True, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported machine type')

    def test_szx_unsupported_block(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        if1 = [0] * 19
        if1[:3] = [ord(c) for c in 'IF1']
        if1[4] = 11 # Block size
        szxdata = self.write_szx(ram, machine_id=4, registers=registers, blocks=[if1], ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported block(s) (IF1) in SZX snapshot')

    def test_szx_unsupported_machine(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = [0] * 37
        registers[22:24] = (pc % 256, pc // 256)
        szxdata = self.write_szx(ram, machine_id=4, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(szxdata, 'szx', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported machine type')

    def test_too_many_port_readings(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE)
            0x00,       # NOP
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(2, 2, [191, 191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], '1 port reading(s) left for frame 0')

    def test_too_few_port_readings(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE, # IN A,($FE)
            0xDB, 0xFE, # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(2, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Port readings exhausted for frame 0')

    def test_invalid_rzx_file(self):
        data = [0, 1, 2, 4]
        rzxfile = self.write_bin_file(data, suffix='.rzx')
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Not an RZX file')

    def test_nonexistent_rzx_file(self):
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen nonexistent.rzx')
        self.assertEqual(cm.exception.args[0], 'nonexistent.rzx: file not found')

    def test_external_snapshot(self):
        rzx = RZX()
        esdata = [0] * 4 + [ord(c) for c in 'external.sna'] + [0]
        rzx.add_snapshot(esdata, 'sna', flags=1)
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Missing snapshot (external file)')

    def test_unsupported_snapshot(self):
        rzx = RZX()
        sdata = [0xFF] * 10
        rzx.add_snapshot(sdata, 'slt')
        rzxfile = self.write_rzx_file(rzx)
        with self.assertRaises(SkoolKitError) as cm:
            self.run_rzxplay(f'--quiet --no-screen {rzxfile}')
        self.assertEqual(cm.exception.args[0], 'Unsupported snapshot type')

    def test_invalid_option(self):
        output, error = self.run_rzxplay('-x test.rzx', catch_exit=2)
        self.assertEqual(output, '')
        self.assertTrue(error.startswith('usage: rzxplay.py'))

    def test_option_force(self):
        ram = [0] * 0xC000
        pc = 0xC000
        code = (
            0xDB, 0xFE # IN A,($FE)
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, version=3, machine_id=5, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 1, [191])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        self._test_rzx(rzx, exp_output, '--force --quiet --no-screen')

    def test_option_stop(self):
        ram = [0] * 0xC000
        pc = 0xF000
        code = (
            0xAF, # XOR A
            0xA8, # XOR B
            0xA9, # XOR C
        )
        ram[pc - 0x4000:pc - 0x4000 + len(code)] = code
        registers = {'PC': pc}
        z80data = self.write_z80_file(None, ram, registers=registers, ret_data=True)
        rzx = RZX()
        frames = [(1, 0, []), (1, 0, []), (1, 0, [])]
        rzx.add_snapshot(z80data, 'z80', frames)
        exp_output = ''
        exp_trace = """
            F:0 T:00000 C:00001 I:00000 $F000 XOR A
            F:1 T:00000 C:00001 I:00000 $F001 XOR B
        """
        self._test_rzx(rzx, exp_output, '--stop 2 --quiet --no-screen', exp_trace)

    def test_option_V(self):
        for option in ('-V', '--version'):
            output, error = self.run_rzxplay(option, catch_exit=0)
            self.assertEqual(output, f'SkoolKit {VERSION}\n')
