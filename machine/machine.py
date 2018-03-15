import pickle
import struct
import os
import sys
from context import Context
from operations import MemOperand, Operation

class Machine:
    def __init__(self, mem_size, prog_code, op_ver='1'):
        self.context = Context(mem_size)
        with open(os.path.join('optables', op_ver + '.optbl'), 'rb') as f:
            self.op_table = pickle.load(f)
        self.prog_code = prog_code
        self.load()

    def load(self):
        for i in range(len(self.prog_code[14:])):
            entrypoint = struct.unpack('<I', bytes(self.prog_code[10:14]))[0]
            self.context.memory[i] = self.prog_code[14 + i]
            self.context.registers['rip'] = entrypoint

    def run_loop(self):
        while True and self.context.running:
            self.run_cycle()

    def run_steps(self, steps):
        for i in range(steps):
            if self.context.running:
                self.run_cycle()

    def run_cycle(self):
        rip = self.context.registers['rip']
        op_code = struct.unpack('<H', bytes(self.context.memory[rip:rip + 2]))[0]
        rip += 2
        try:
            op_info = self.op_table[op_code]
        except:
            print('Unknown opcode')
            print(self.context.registers)
            print(self.context.memory[self.context.registers['rip']:self.context.registers['rip']+10])
            print(self.context.memory)
            exit()
        op_args = []
        for i in range(op_info[1]): # for each argument
            arg_code = op_info[2 + i]
            value = 0
            if 10 <= arg_code <= 11:
                value = self.context.memory[rip:rip + 4] # struct.unpack('<I', bytes(self.context.memory[rip:rip + 4]))
                rip += 4
            op_args.append(MemOperand(self.context, arg_code, value))
        operation = Operation(self.context, op_info[0])
        self.context.registers['rip'] = rip
        operation.exec(op_args)

if __name__ == '__main__':

    code = open(sys.argv[1], 'rb').read()
    m = Machine(int(sys.argv[2]), code)
    m.run_loop()
