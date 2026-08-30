"""Metal Gear 2: Solid Snake recap in English.

Same method as the Metal Gear port: paragraphs are rejoined from the USA
build (including across its hyphenated word breaks) and re-wrapped to the
width Integral's recap texture can show without clipping.  No wording is
changed - only the page count and the line breaks.

Metal Gear stays Japanese here.  The two recaps cannot both be English:
the stage is fixed at 87 sectors and the script chunk has 796 bytes of
slack, so the pair needs 734 bytes that do not exist anywhere in the stage.
"""
import struct, sys
sys.path.insert(0,'.')
from gclparse import parse_script, containers_over, be16, be32
from gcldec import chain_at
def pad(x,a=2048): return (x+a-1)//a*a

WIDTH=46
INT=bytearray(open('work/int1_stage_menu2.dir','rb').read())
REF=open('work/int1_stage.dir','rb').read()
US =open('work/us1_stage.dir','rb').read()
NEW_ND=open('D:/mgsbuild/d/obj/preope.bin','rb').read()
IB,UB=0x6A71*2048,0x7659*2048
ND,CK,SCRIPT=24911,113716,21732
scr=2048+pad(ND)+pad(CK); body=IB+scr+0x172

# growth is only safe while the chunk keeps the same padded span, otherwise
# every chunk after it moves.
assert pad(len(NEW_ND))==pad(ND), 'overlay crossed a 2048 boundary: %d'%len(NEW_ND)
print('overlay %d -> %d bytes (both pad to %d, no chunk shifts)'%(ND,len(NEW_ND),pad(ND)))

ci=chain_at(REF,IB+scr+0x1B8); cu=chain_at(US,UB+scr+0x1B8)
raw=[cu[k][2].decode('latin1') for k in range(95,228)]      # MG2 recap in USA
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
while lines and not lines[-1].strip(): lines.pop()
PAGES=(len(lines)+7)//8; SLOTS=PAGES*8
print('MG2 re-wrapped to <=%d chars: %d lines -> %d pages (%d slots), longest %d'
      %(WIDTH,len(lines),PAGES,SLOTS,max(len(l) for l in lines)))

def rec(r): return bytes([0x07,r[1]])+r[2]+bytes(1)
def mk(s): b=s.encode('latin1'); return bytes([0x07,len(b)+1])+b+bytes(1)
new = b''.join(rec(ci[k]) for k in range(0,76)) \
    + b''.join(mk(l) for l in lines) + bytes([0x07,0x01,0x00])*(SLOTS-len(lines)) \
    + b''.join(rec(ci[k]) for k in range(188,191))
span_i=sum(2+r[1] for r in ci); D=len(new)-span_i
print('chain %d -> %d bytes (D=%+d); chunk %d padded %d, headroom %d'
      %(span_i,len(new),D,SCRIPT,pad(SCRIPT),pad(SCRIPT)-SCRIPT))
assert SCRIPT+D<=pad(SCRIPT), 'OVER BUDGET by %d bytes'%(SCRIPT+D-pad(SCRIPT))

root,slen=parse_script(REF,body)
cov=containers_over(root,IB+scr+0x1B8,IB+scr+0x1B8+span_i)
INT[IB+0x800:IB+0x800+len(NEW_ND)]=NEW_ND
struct.pack_into('<I',INT,IB+8,len(NEW_ND))
cs=IB+scr+0x1B8
tail=bytes(INT[cs+span_i: IB+scr+pad(SCRIPT)])
INT[cs:IB+scr+pad(SCRIPT)]=(new+tail)[:pad(SCRIPT)-0x1B8]
for c in cov:
    o=c.size_at
    if c.size_bits==32: struct.pack_into('>I',INT,o,be32(INT,o)+D)
    else:               struct.pack_into('>H',INT,o,be16(INT,o)+D)
root2,s2=parse_script(INT,body); c2=chain_at(INT,cs)
assert s2==slen+D and root2.kids[0].end==body+s2 and len(INT)==len(REF)
print('VERIFY: re-parse PASS, %d records, script_len %d->%d, stage still 87 sectors'%(len(c2),slen,s2))
print('  MG1[76] still Japanese: %s'%c2[76][2][:12].hex(' '))
print('  MG2 first %r'%c2[76][2] if False else '  MG2 first %r'%lines[0])
print('  MG2 last  %r'%lines[-1])
open('work/int1_stage_preope_mg2.dir','wb').write(bytes(INT))
print('wrote work/int1_stage_preope_mg2.dir  (PAGES=%d -> pre_met2.c PAGE_COUNT)'%PAGES)
