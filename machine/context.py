from config import ops, regs
import struct
class Context:
    def __init__(self, mem_size, entrypoint=0):
        self.memory = [0 for x in range(mem_size)]
        self.running = True
        stack = list(struct.pack('<I', mem_size-1))
        self.registers = {'rip': entrypoint, 'rax': [0,0,0,0], 'rbx': [0,0,0,0], 'rcx': [0,0,0,0], 'rbp': stack[::],
                          'rsp': stack[::], 'cf': 0}

