import pickle
import os
import struct
import re
import sys
from config import regs, ops


class Compiler:
    def __init__(self, infile, outfile, op_ver='1'):
        self.infile = infile
        self.outfile = outfile
        with open(os.path.join('optables', op_ver + '.optbl'),'rb') as f:
            self.op_table = pickle.load(f)


    def get_opcode(self,s):
        template = ''.join([i for i in s if not i.isdigit()])
        for i, op in enumerate(self.op_table):
            if template == op[-1]:
                return i, op
        raise Exception('Template not found, incorrect line ' + s)


    def compile(self):
        lines = [x.strip() for x in open(self.infile, 'r').read().split('\n') if x.strip() != '']

        # retrieve symbols
        text_begin, text_end = self.get_section(lines, 'text')
        text_lines = lines[text_begin:text_end]
        text_symbol_names = self.get_text_symbol_names(text_lines)
        bss_begin, bss_end = self.get_section(lines, 'bss')
        bss_lines = lines[bss_begin:bss_end]
        bss_symbols, compiled_bss = self.compile_bss(bss_lines)
        all_symbol_names = text_symbol_names + list(bss_symbols.keys())

        # substitute symbols
        lines_with_offsets = self.get_text_line_offsets(text_lines, all_symbol_names)

        all_symbols = self.retrieve_all_symbols(lines_with_offsets, bss_symbols)
        code_clean = self.substitute_symbols(text_lines, all_symbols)
        compiled_text = self.compile_text(code_clean)

        header = self.generate_header(len(compiled_text), len(compiled_bss))
        outbuf = header + compiled_text + compiled_bss
        with open(self.outfile, 'wb') as f:
            f.write(outbuf)

    def generate_header(self, text_size, bss_size):
        return b'MK' + struct.pack('<III', text_size, bss_size, 0)


    def get_section(self, lines, section):
        text_begin = lines.index('section .' + section) + 1
        text_end = len(lines)
        for line in range(text_begin + 1, len(lines)):
            if re.match('^section \.[a-z]+$', lines[line]):
                text_end = line
                break
        return text_begin, text_end

    def get_text_symbol_names(self, lines):
        symbols = []
        for line in lines:
            if line[0] == '.':
                name = line[1:]
                if name in ops + regs:
                    raise Exception("Reserved symbol name")
                symbols.append(name)
        return symbols

    def parse_bss_line(self, line):
        if line[0] == '.':
            tokens_first = line.split()
            name = tokens_first[0][1:]
            m_type = tokens_first[1]
            if m_type == 'uint':
                value = struct.pack('<I', int(tokens_first[2]))
            elif m_type == 'str':
                start = line.index('"') + 1
                end = line.rfind('"')
                value = line[start: end].encode()
            return name, m_type, value


    def compile_bss(self, lines):
        m_dict = {}
        outbuf = b''
        for line in lines:
            name, m_type, value = self.parse_bss_line(line)
            m_dict[name] = len(outbuf)
            outbuf += value
        return m_dict, outbuf

    def get_text_line_offsets(self, lines, symbols):
        res = []
        cur_pos = 0
        for line in lines:
            res.append([cur_pos, line])

            if line[0] == '.':
                continue

            cur_pos += 2

            tokens = line.split()[1:]
            for token in tokens:
                nodigit = ''.join([i for i in token if not i.isdigit()])
                if nodigit in regs:
                    if 10 <= regs.index(nodigit) <= 11:
                        cur_pos += 4
                elif token[1:] in symbols:
                    cur_pos += 4
                else:
                    raise Exception("Unknown symbol in line:\n" + line)
        res.append([cur_pos, ''])
        return res

    def retrieve_all_symbols(self, lines_with_offsets, bss_symbols):
        symbols = bss_symbols.copy()
        for k in symbols:
            symbols[k] += lines_with_offsets[-1][0]

        for line in lines_with_offsets:
            if line[1] != '' and line[1][0] == '.':
                name = line[1][1:]
                if name in symbols:
                    raise Exception('Duplicate symbol:', name)
                symbols[name] = line[0]
        return symbols

    def substitute_symbols(self, lines, symbols):
        res = []
        for line in lines:
            if line[0] == '.':
                continue
            tokens = line.split()
            line_res = [tokens[0]]
            for i in range(1, len(tokens)):
                if tokens[i][1:] in symbols:
                    line_res.append(tokens[i][0] + str(symbols[tokens[i][1:]]))
                else:
                    line_res.append(tokens[i])
            res.append(' '.join(line_res))
        return res


    def compile_text(self, lines):
        outbuf = b''
        for line in lines:
            line = line.strip()
            if line != '':
                tokens = [x for x in line.split() if x != '']
                opcode, opinfo = self.get_opcode(line)
                args = []
                for i, arg in zip(range(opinfo[1]), tokens[1:]):
                    optype = opinfo[2 + i]
                    if 10 <= optype <= 11:
                        args.append(struct.pack('<I', int(arg[1:])))
                opcode = struct.pack('<H', opcode)
                # print(line)
                # print(opcode,args)
                outbuf += opcode
                for a in args:
                    outbuf += a
        # print(outbuf)
        return outbuf


if __name__ == '__main__':
    c = Compiler(sys.argv[1], sys.argv[2])
    c.compile()
