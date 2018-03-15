import os
import pickle
import struct
from config import ops, regs
import re
import sys

class Decompiler:
    def __init__(self, prog_code, op_ver='1'):
        with open(os.path.join('optables',op_ver+'.optbl'),'rb') as f:
            self.op_table = pickle.load(f)
        self.prog_code = prog_code
        self.rip = 0

    def do_decompile(self):
        text_size, bss_size = struct.unpack('<II', self.prog_code[2:10])
        self.text_body = self.prog_code[14:14 + text_size]
        self.bss_body = self.prog_code[14 + text_size: 14 + text_size + bss_size]

        instrs = []
        while self.rip < len(self.text_body):
            instrs.append(self.decompile_instr())
        instrs = self.jumploc_generate(instrs, text_size)
        instrs = self.calloc_generate(instrs, text_size)
        bss_instrs = self.bss_split(instrs, self.bss_body, text_size, bss_size)
        return self.beautify(instrs, bss_instrs)


    def jumploc_generate(self, instrs, text_size):
        to_add = []
        for ins in instrs:
            op = ins[2][0]
            if op in ['je', 'jg', 'jge', 'jl', 'jle', 'jmp', 'jne']:
                loc = ins[2][1]
                if 'jumploc' in loc:
                    continue
                num = int(loc[1:])
                if num >= text_size:
                    continue

                ins[2][1] = loc[0] + 'jumploc_'+str(num)
                to_add.append('.jumploc_'+str(num))
        to_add = list(set(to_add))
        to_add = [[int(x.split('_')[1]), b'', [x]] for x in to_add]

        return sorted(instrs + to_add, key=lambda x: (x[0],len(x[1])))

    def calloc_generate(self, instrs, text_size):
        to_add = []
        for ins in instrs:
            op = ins[2][0]
            if op in ['call']:
                loc = ins[2][1]
                if 'function' in loc:
                    continue
                num = int(loc[1:])
                if num >= text_size:
                    continue

                ins[2][1] = loc[0] + 'function_'+str(num)
                to_add.append('.function_'+str(num))
        to_add = list(set(to_add))
        to_add = [[int(x.split('_')[1]), b'', [x]] for x in to_add]

        return sorted(instrs + to_add, key=lambda x: (x[0], len(x[1])))

    def bss_split(self, instrs, bss_body, text_size, bss_size):
        bss_labels = []
        for ins in instrs:
            operands = ins[2][1:]
            for i, oper in enumerate(operands):
                if re.match('^[\$%]\d+$', oper):
                    num = int(oper[1:])
                    if text_size <= num < text_size + bss_size:
                        label = 'bss_'+str(num)
                        ins[2][1 + i] = oper[0]+label
                        bss_labels.append([num - text_size, ['.' + label,'str']])

        for lab, end in zip(range(len(bss_labels)), [x[0] for x in bss_labels][1:] + [bss_size]):
            t = bss_body[bss_labels[lab][0]:end]
            compiled = '"{}"'.format(t.decode())
            bss_labels[lab][1].append(compiled)
        return bss_labels

    def beautify(self, text, bss):
        ret = 'section .text\n\n'

        for t in text:
            t = ' '.join(t[2])
            if '.function' in t:
                ret += '\n\n'
            ret += t + '\n'
        ret += '\n\nsection .bss\n\n'
        for t in bss:
            t = ' '.join(t[1])
            ret += t + '\n'
        return ret

    def decompile_instr(self):
        rip = self.rip
        op_code = struct.unpack('<H', bytes(self.text_body[rip:rip + 2]) )[0]
        rip += 2
        op_info = self.op_table[op_code]
        op_args = [ops[op_info[0]]]
        for i in range(op_info[1]):  # for each argument
            arg_code = op_info[2 + i]
            value = 0
            if 10 <= arg_code <= 11:
                value = struct.unpack('<I', bytes(self.text_body[rip:rip + 4]))[0]
                rip += 4
                op_args.append(regs[arg_code] + str(value))
            else:
                op_args.append(regs[arg_code])
        op_first = op_args
        ret = [self.rip, self.text_body[self.rip:rip], op_first]
        self.rip = rip
        return ret


if __name__ == '__main__':
    decompiled = Decompiler(open(sys.argv[1], 'rb').read(), ).do_decompile()
    open(sys.argv[2], 'w').write(decompiled)
