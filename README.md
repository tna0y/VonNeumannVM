# Von Neumann architecture VM

My extremely slow Von Neumann VM. Was never designed for perfomance yet it is extremely easy to modify the istruction set.


## Assembly

Architecture was inspired by x86, but has little in common except some command names;

Machine is little-endian.
Stack grows towards smaller addresses.

### General rules
All registers are 4-byte,  arithmetics is unsigned only.

#### Registers:
- General purpose: rax, rbx, rcx
- Stack frame: rsp, rbp
- Utility(no direct access): rip, sf

To access value in register use it's name like 

    push rax

To access value pointed by register use %

    push %rax

##### Numeric values:

To use numbers you have to show first whether it is a number '$' or an address which machine has to follow '%':

For example to push 1 on stack you:

    push $1
  
But to push value at memory location 1 you:

    push %1
    
#### Labels

You can use labels at any place in code:

Make a label

    .label
    
refer to a label like to a number (direct or address)

    je $hello
    jne %bye

#### Instruction set

Assembly syntax is simmilar to AT&T in terms of order "instruction from to"

All availible instructions are:

- xor – arithmetics below
- oor
- aand
- add
- sub
- mul
- div
- mov - move 4 bytes from one location to another
- movb – moves only 1 byte instead of 4
- nop – No operation
- pop – pop from stack
- push – push item on stack
- call – jump with new stack frame
- ret – return to the calling procedure
- cmp – comparison operator
- je – conditional jumps below
- jg
- jge
- jl
- jle
- jmp
- jne
- syscall – used for IO

#### Syscalls:

syscall num in rax, params in rbx and rcx:

Syscall nums:
- 0 - exit
- 1 - read(rbx - to, rcx - len)  (stdio)
- 2 - write(rbx - from, rcx - len) (stdio)

#### Sections

Two sections are supported:
- text for code
- bss for data

Entrypoint is always at the begining of the text section

#### Example code:

Package includes a program in file 'fib.mkasm' which calculates nth fibonacci number for a given n.

Note that code won't compile since comments are not supported.

    section .text ; code section
    
    sub $4 rsp ; substract 4 from stack pointer
    mov $2 rax ; put 2 in rax (write syscall)
    mov $hw rbx ; put string address to rbx
    mov %hwsize rcx ; put string len to rcx. Note we have to use % to put the value but not it's address
    syscall ; perform the syscall
    mov $0 rax ; exit syscall
    syscall ; perform the syscall


    section .bss ; data section
    .hw str "Hello, world!" ; strings identified by str label
    .hwsize uint 13 ; uints identified by uint


## Compiling code

    python3 compiler.py fib.mkasm fib.out


## Running compiled binary

    python3 machine.py fib.out 65536
where 65536 is machine memory size.


## Decompiling already compiled binary:
Featuers:
- Function detection based on calls.
- Label detection based on jumps.
- Data section separation based on usage in code.


    python3 decompiler.py fib.out decompiled.mkasm
