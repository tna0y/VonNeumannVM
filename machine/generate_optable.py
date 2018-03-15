import pickle
import os
from config import regs, ops
lines = open('instructions.txt', 'r').read().split('\n')
try:
    os.mkdir('optables')
except:
    pass

version = lines.pop(0)

optable = []
lines = list(filter(lambda x: x != '', lines))


for line in lines:
    tokens = line.split()
    op = ops.index(tokens.pop(0))
    op_len = len(tokens)
    tokens = list(map(lambda x: regs.index(x), tokens))
    optable.append([op, op_len] + tokens + [line])
for op in optable:
    print(op)

pickle.dump(optable, open(os.path.join('optables',version+'.optbl'),'wb'))
