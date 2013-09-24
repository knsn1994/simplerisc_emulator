#!/usr/bin/env python
import warnings
import re
import numpy as NP
import sys
warnings.filterwarnings("ignore") #just to mute the warnings
I8,I16,UI16,I32,UI32 = NP.uint8, NP.int16, NP.uint16, NP.int32, NP.uint32  #some integer types
memory = NP.zeros(4096,I8)              #4096 bytes memory
register = {'r0':I32(0), 'r1':I32(0), 'r2':I32(0), 'r3':I32(0), 'r4':I32(0), 'r5':I32(0), 'r6':I32(0), 'r7':I32(0), 'r8':I32(0), 'r9':I32(0), 'r10':I32(0), 'r11':I32(0), 'r12':I32(0),'r13':I32(0),'r14':I32(4096),'r15':I32(0)}		#all the register
E,GT = False,False 				#flags
def reg(a):
	if a == 'pc':return 'r13'
	if a == 'sp':return 'r14'
	if a == 'ra':return 'r15'
	return a
def getInt(a): 		#deals with white spaces and base
	if a == '':return 0
	try: return I16(int("".join(a)))
	except: 
		try: return I16(int("".join(a),16))
		except : return register[reg("".join(a))]
def get32(a,c):
	if c == 'h': return (I32(getInt(a)) << 16)
	if c == 'u': return I32(UI16(getInt(a)))
	if(''.join(a)[0]!='r'): I32(getInt(a))
	return I32(getInt(a))
def getIdx(l):
	s = "".join(l)
	s = s.replace(' ','').replace(']','')
	parts = s.split('[')
	return getInt(parts[1]) + getInt(parts[0])
op = {}
op['add'] = lambda x,y : x+y
op['sub'] = lambda x,y : x-y
op['mul'] = lambda x,y : x*y
op['div'] = lambda x,y : x/y
op['mod'] = lambda x,y : x%y
op['and'] = lambda x,y : x & y
op['or'] = lambda x,y : x | y
op['lsl'] = lambda x,y : x<<y
op['asr'] = lambda x,y : x>>y
op['lsr'] = lambda x,y : I32((UI32(x))>>y)

f = open(sys.argv[1],"r")
CODE = f.read().replace(':',':\n').split('\n')
f.close()							#file read and formatted to our convnience
lines = len(CODE)
register['r13'] = lines << 2
labels = {}
for i in range(lines):  			#hashing the labels
	CODE[i] = re.sub(r'//.*$', "", CODE[i]).lower().replace('\t',' ')
	if len(CODE[i]) > 0 and CODE[i][-1] == ':' :
		 labels[CODE[i].replace(' ','')[:-1]] = (i<<2) + 4
register['r13'] = labels['.main'] 	   #start with .main label
def compute(idx):
	global register,memory,GT,E
	FLAG  = True
	parts = CODE[idx].replace(',',' ').split()
	if len(parts) > 0: 
		fun = parts[0]
		if fun == 'beq': 
			if E:
				register['r13'] = labels[parts[1]]
				FLAG = False
		elif fun == 'bgt':
			if GT :
				register['r13'] = labels[parts[1]]
				FLAG = False
		elif fun == 'b' : 
			register['r13'] = labels[parts[1]]
			FLAG = False	
		elif fun == 'call' :
			register['r15'] = register['r13'] + 4
			register['r13'] = labels[parts[1]]
			FLAG = False
		elif fun == 'ret':
			register['r13'] = register['r15']
			FLAG = False
		elif fun == 'ld':
			i = getIdx(parts[2:])
			register[reg(parts[1])] = I32(memory[i] + (memory[i+1]<<8) + (memory[i+2]<<16) + (memory[i+2]<<24))
		elif fun == 'st':
			i = getIdx(parts[2:])
			x = register[reg(parts[1])]
			memory[i],memory[i+1],memory[i+2],memory[i+3] = I8(x),I8(x>>8),I8(x>>16),I8(x>>24)
		elif fun.strip('u').strip('h') == 'mov':
			register[reg(parts[1])] = get32(parts[2:],fun[-1])
		elif fun.strip('h').strip('u') == 'cmp' :
			E,GT = (register[reg(parts[1])] == get32(parts[2:],fun[-1])),(register[reg(parts[1])] > get32(parts[2:],fun[-1]))
		elif fun == 'not':
			register[reg(parts[1])] = NP.bitwise_not(get32(parts[2:],fun[-1]))
		elif fun == '.print':
			for x in parts[1:]:print getInt(x),
			print
		elif fun.strip('h').strip('u') in op :
			register[reg(parts[1])] = op[fun.strip('h').strip('u')](register[reg(parts[2])],get32(parts[3:],fun[-1]))
	if FLAG : register['r13'] += 4
lines <<= 2
while register['r13'] < lines : 	
	compute(register['r13']>>2)