import struct
from sys import stdin, stdout

class Syscall:
    def __init__(self, context):
        self.context = context
        self.calls = ['exit', 'read', 'write', 'readuint', 'writeuint']
        scallno = struct.unpack('<I', bytes(context.registers['rax']))[0]
        self.syscall = getattr(self, self.calls[scallno])

    def call(self):
        self.syscall()

    def exit(self):
        self.context.running = False

    def read(self):
        to = struct.unpack('<I', bytes(self.context.registers['rbx']))[0]
        size = struct.unpack('<I', bytes(self.context.registers['rcx']))[0]
        data = [ord(x) for x in stdin.read(size)]
        for x in range(size):
            self.context.memory[to + x] = data[x]

    def write(self):
        fr = struct.unpack('<I', bytes(self.context.registers['rbx']))[0]
        size = struct.unpack('<I', bytes(self.context.registers['rcx']))[0]
        stdout.write(''.join(list(map(chr,self.context.memory[fr:fr+size]))))
        stdout.flush()

    def readuint(self):
        to = struct.unpack('<I', bytes(self.context.registers['rbx']))[0]
        data = int(input())
        data = struct.pack('<I',data)
        for x in range(4):
            self.context.memory[to + x] = data[x]

    def writeuint(self):
        to = struct.unpack('<I', bytes(self.context.registers['rbx']))[0]
        print(to)
