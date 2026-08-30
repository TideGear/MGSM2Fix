"""Linear register simulation over a brf overlay: report the arguments of every
call to the row positioner.  Tracks immediates and register-to-register moves,
and the stack slots written before each call, so nothing has to be guessed."""
import struct
def run(path, base, fn, nregs=32):
    return run_bytes(open(path,'rb').read(), base, fn, nregs)

def run_bytes(b, base, fn, nregs=32):
    W=list(struct.unpack('<%dI'%(len(b)//4), b[:len(b)//4*4]))
    jal=0x0C000000 | ((fn>>2)&0x03FFFFFF)
    reg=[None]*nregs; reg[0]=0
    stack={}
    out=[]
    pending=None
    for i,w in enumerate(W):
        a=base+4*i
        op=w>>26; rs=(w>>21)&31; rt=(w>>16)&31; rd=(w>>11)&31; fn6=w&0x3F
        imm=w&0xFFFF; simm=imm-0x10000 if imm>=0x8000 else imm
        if pending is not None:            # previous insn was the jal: this is its delay slot
            pass
        if op==9:                                  # addiu rt, rs, imm
            reg[rt] = simm if rs==0 else (reg[rs]+simm if reg[rs] is not None else None)
        elif op==0 and fn6==0x21:                  # addu rd, rs, rt
            if rs==0: reg[rd]=reg[rt]
            elif rt==0: reg[rd]=reg[rs]
            else: reg[rd]=None
        elif op==0x2B and rs==29:                  # sw rt, imm(sp)
            stack[simm]=reg[rt]
        elif op==0x0F:                             # lui
            reg[rt]=None
        elif op==0:                                # other SPECIAL writes rd
            if fn6 not in (8,9): reg[rd]=None
        elif op in (0x20,0x21,0x23,0x24,0x25,0x0C,0x0D,0x0E,0x0A,0x0B):
            reg[rt]=None
        if pending is not None:
            out.append((pending, reg[5], reg[7], stack.get(16), stack.get(20)))
            pending=None
            for r in (1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,24,25): reg[r]=None
        if w==jal: pending=a                       # args finalise after the delay slot
    return out
