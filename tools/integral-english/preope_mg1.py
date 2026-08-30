"""Metal Gear recap in English, re-wrapped to Integral's render width.

The USA release's lines run to 53 characters; Integral's recap texture clips
around 50, so USA's own line breaks cannot be used verbatim. The words are
untouched - paragraphs are rejoined (including across the USA build's
hyphenated word breaks, so FOX- / HOUND becomes FOX-HOUND) and re-wrapped to
45 characters, which measured safe on screen and yields 94 lines against the
96 slots that 12 pages provide.
"""
import struct, sys
sys.path.insert(0,'.')
from gclparse import parse_script, containers_over, be16, be32
from gcldec import chain_at
def pad(x,a=2048): return (x+a-1)//a*a
WIDTH=45
INT=bytearray(open('work/int1_stage_menu2.dir','rb').read())
REF=open('work/int1_stage.dir','rb').read()
US =open('work/us1_stage.dir','rb').read()
NEW_ND=open('D:/mgsbuild/d/obj/preope.bin','rb').read()
IB,UB=0x6A71*2048,0x7659*2048
ND,CK,SCRIPT=24911,113716,21732
scr=2048+pad(ND)+pad(CK); body=IB+scr+0x172
assert len(NEW_ND)==ND

ci=chain_at(REF,IB+scr+0x1B8); cu=chain_at(US,UB+scr+0x1B8)
raw=[cu[k][2].decode('latin1') for k in range(4,95)]
paras=[]; cur=''
for line in raw:
    if not line.strip():
        if cur: paras.append(cur); cur=''
        paras.append(None); continue
    if not cur: cur=line
    elif cur.endswith('-'): cur+=line
    else: cur+=' '+line
if cur: paras.append(cur)
def wrap(t,w):
    out=[];ln=''
    for word in t.split(' '):
        if not ln: ln=word
        elif len(ln)+1+len(word)<=w: ln+=' '+word
        else: out.append(ln); ln=word
    if ln: out.append(ln)
    return out
lines=[]
for p in paras:
    lines += [''] if p is None else wrap(p,WIDTH)
assert len(lines)<=96, len(lines)
print('MG1 re-wrapped to <=%d chars: %d lines into 96 slots, longest %d'
      %(WIDTH,len(lines),max(len(l) for l in lines)))

def rec(r): return bytes([0x07,r[1]])+r[2]+bytes(1)
def mk(s): b=s.encode('latin1'); return bytes([0x07,len(b)+1])+b+bytes(1)
new = b''.join(rec(ci[k]) for k in range(0,4)) \
    + b''.join(mk(l) for l in lines) + bytes([0x07,0x01,0x00])*(96-len(lines)) \
    + b''.join(rec(ci[k]) for k in range(76,188)) \
    + b''.join(rec(ci[k]) for k in range(188,191))
span_i=sum(2+r[1] for r in ci); D=len(new)-span_i
print('chain %d -> %d bytes (D=%+d); chunk %d padded %d, headroom %d'
      %(span_i,len(new),D,SCRIPT,pad(SCRIPT),pad(SCRIPT)-SCRIPT))
assert SCRIPT+D<=pad(SCRIPT)

root,slen=parse_script(REF,body)
cov=containers_over(root,IB+scr+0x1B8,IB+scr+0x1B8+span_i)
INT[IB+0x800:IB+0x800+ND]=NEW_ND
cs=IB+scr+0x1B8
tail=bytes(INT[cs+span_i: IB+scr+pad(SCRIPT)])
INT[cs:IB+scr+pad(SCRIPT)]=(new+tail)[:pad(SCRIPT)-0x1B8]
for c in cov:
    o=c.size_at
    if c.size_bits==32: struct.pack_into('>I',INT,o,be32(INT,o)+D)
    else:               struct.pack_into('>H',INT,o,be16(INT,o)+D)
root2,s2=parse_script(INT,body); c2=chain_at(INT,cs)
assert s2==slen+D and root2.kids[0].end==body+s2 and len(c2)==215 and len(INT)==len(REF)
print('VERIFY: re-parse PASS, %d records, script_len %d->%d, stage still 87 sectors'%(len(c2),slen,s2))
print('  first %r'%c2[4][2]); print('  last  %r'%c2[4+len(lines)-1][2])
open('work/int1_stage_preope_mg1.dir','wb').write(bytes(INT))
