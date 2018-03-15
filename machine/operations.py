from config import regs, ops
import struct
from syscalls import Syscall

class MemOperand:
    def __init__(self, context, op_type, value=[0,0,0,0]):
        self.context = context
        self.op_type = op_type
        self.value = value

    def load(self):
        if 0 <= self.op_type <= 4:  # 'rax', 'rbx', 'rcx', 'rsp', 'rbp'
            return self.context.registers[regs[self.op_type]]
        elif 5 <= self.op_type <= 9:  # '%rax', '%rbx', '%rcx', '%rsp', '%rbp'
            reg = regs[self.op_type][1:]
            addr = struct.unpack('<I', bytes(self.context.registers[reg]))[0]
            return self.context.memory[addr:addr + 4]
        elif 10 == self.op_type:  # $
            return self.value
        elif 11 == self.op_type:  # %
            addr = struct.unpack('<I', bytes(self.value))[0]
            return self.context.memory[addr:addr + 4]
        else:
            raise Exception('Unknown operand type')

    def store(self, value, size=4):
        if 0 <= self.op_type <= 4:  # 'rax', 'rbx', 'rcx', 'rsp', 'rbp'
            self.context.registers[regs[self.op_type]] = value[:size] + [0] * (4 - size)
        elif 5 <= self.op_type <= 9:  # '%rax', '%rbx', '%rcx', '%rsp', '%rbp'
            reg = regs[self.op_type][1:]
            addr = struct.unpack('<I', bytes(self.context.registers[reg]))[0]
            for x in range(size):
                self.context.memory[addr + x] = value[x]
        elif 10 == self.op_type:  # $
            raise Exception('Can\'t assign to value not address')
        elif 11 == self.op_type:  # %
            for x in range(size):
                self.context.memory[self.value + x] = value[x]
        else:
            raise Exception('Unknown operand type')


class Operation:
    def __init__(self, context, op_type):
        self.context = context
        self.op_type = op_type
        self.operation = getattr(self, ops[op_type])

    def push(self, arg1): # unsafe?
        self.context.registers['rsp'] = list(struct.pack('<I', struct.unpack('<I', bytes(self.context.registers['rsp']))[0] - 4))
        destination = MemOperand(self.context, regs.index('%rsp'))
        destination.store(arg1.load())

    def pop(self, arg1):  # unsafe?
        destination = MemOperand(self.context, regs.index('%rsp'))
        arg1.store(destination.load())
        self.context.registers['rsp'] = list(struct.pack('<I', struct.unpack('<I', bytes(self.context.registers['rsp']))[0] + 4))

    def mov(self, arg1, arg2):
        arg2.store(arg1.load())

    def movb(self, arg1, arg2):
        arg2.store(arg1.load(), size=1)

    def jmp(self, arg1):
        intval = struct.unpack('<I', bytes(arg1.load()))[0]
        self.context.registers['rip'] = intval

    def jge(self, arg1):
        if self.context.registers['cf'] >= 0:
            intval = struct.unpack('<I', bytes(arg1.load()))[0]
            self.context.registers['rip'] = intval

    def jg(self, arg1):
        if self.context.registers['cf'] > 0:
            intval = struct.unpack('<I', bytes(arg1.load()))[0]
            self.context.registers['rip'] = intval

    def jle(self, arg1):
        if self.context.registers['cf'] <= 0:
            intval = struct.unpack('<I', bytes(arg1.load()))[0]
            self.context.registers['rip'] = intval

    def jl(self, arg1):
        if self.context.registers['cf'] < 0:
            intval = struct.unpack('<I', bytes(arg1.load()))[0]
            self.context.registers['rip'] = intval

    def je(self, arg1):
        if self.context.registers['cf'] == 0:
            intval = struct.unpack('<I', bytes(arg1.load()))[0]
            self.context.registers['rip'] = intval

    def jne(self, arg1):
        if self.context.registers['cf'] != 0:
            intval = struct.unpack('<I', bytes(arg1.load()))[0]
            self.context.registers['rip'] = intval

    def call(self, arg1):
        intval = struct.unpack('<I', bytes(arg1.load()))[0]
        # push rip
        ripbts = struct.pack('<I', self.context.registers['rip'])
        self.push(MemOperand(self.context, regs.index('$'), ripbts))
        # push ebp
        self.push(MemOperand(self.context, regs.index('rbp')))
        # mov esp ebp
        self.mov(MemOperand(self.context, regs.index('rsp')), MemOperand(self.context, regs.index('rbp')))
        self.jmp(arg1)

    def ret(self):
        # mov ebp esp
        self.mov(MemOperand(self.context, regs.index('rbp')), MemOperand(self.context, regs.index('rsp')))
        # pop ebp
        self.pop(MemOperand(self.context, regs.index('rbp')))

        # pop rip
        retloc = MemOperand(self.context, regs.index('%rsp')).load()
        self.context.registers['rsp'] = list(struct.pack('<I', struct.unpack('<I', bytes(self.context.registers['rsp']))[0] + 4))
        intval = struct.unpack('<I', bytes(retloc))[0]
        self.context.registers['rip'] = intval

    def add(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        res = ( val1 + val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def sub(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        if arg1.op_type == 10:
            res = ( val2 - val1 ) % (2**32)
        else:
            res = ( val1 - val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def mul(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        res = ( val1 * val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def div(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        if arg1.op_type == 10:
            res = ( val2 // val1 ) % (2**32)
        else:
            res = ( val1 // val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def xor(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        res = ( val1 ^ val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def oor(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        res = ( val1 | val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def aand(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        res = ( val1 & val2 ) % (2**32)
        arg2.store(list(struct.pack('<I', res)))

    def cmp(self, arg1, arg2):
        val1 = struct.unpack('<I', bytes(arg1.load()))[0]
        val2 = struct.unpack('<I', bytes(arg2.load()))[0]
        self.context.registers['cf'] = val1 - val2

    def nop(self):
        pass

    def syscall(self):
        Syscall(self.context).call()

    def exec(self, arguments):
        self.operation(*arguments)
        # print('executed', ops[self.op_type])
        # print(self.context.registers)
        # print(self.context.memory)
        # print()
