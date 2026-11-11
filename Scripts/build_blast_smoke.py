"""Deterministic original soft smoke alpha, four octaves plus radial falloff."""
import zlib,struct
import random,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];rng=random.Random(631);N=256
layers=[]
for size in [5,9,17,33]:layers.append([[rng.random() for x in range(size)] for y in range(size)])
def noise(g,x,y):
 n=len(g)-1;x=x*n;y=y*n;i=min(n-1,int(x));j=min(n-1,int(y));a=x-i;b=y-j;a=a*a*(3-2*a);b=b*b*(3-2*b)
 return (g[j][i]*(1-a)+g[j][i+1]*a)*(1-b)+(g[j+1][i]*(1-a)+g[j+1][i+1]*a)*b
pixels=[]
for y in range(N):
 for x in range(N):
  u=x/(N-1);v=y/(N-1);r=math.hypot((u-.5)*2,(v-.5)*2)
  n=sum(noise(g,u,v)*w for g,w in zip(layers,[.5,.25,.15,.1]))
  alpha=max(0,1-r*r)**2*max(0,min(1,(n-.17)*1.6))
  pixels.append((255,255,255,round(alpha*255)))
def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
raw=b''.join(b'\x00'+bytes(c for pixel in pixels[y*N:(y+1)*N] for c in pixel) for y in range(N))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',N,N,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
(P/'Art/Grab/Blast/T_BlastSmoke.png').write_bytes(png)

# Fire uses broken high-contrast density, rather than stacking soft smoke discs.
fire=[]
for y in range(N):
 for x in range(N):
  u=x/(N-1);v=y/(N-1);r=math.hypot((u-.5)*2,(v-.5)*2)
  n=sum(noise(g,u,v)*w for g,w in zip(layers,[.25,.30,.25,.20]))
  radial=max(0,1-r*r);a=max(0,min(1,(n-.43)*7))**1.5*radial
  hot=max(0,min(1,(n-.52)*5))*radial
  fire.append((255,round(40+120*hot),round(2+30*hot),round(a*255)))
raw=b''.join(b'\x00'+bytes(c for pixel in fire[y*N:(y+1)*N] for c in pixel) for y in range(N))
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',N,N,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
(P/'Art/Grab/Blast/T_BlastFire.png').write_bytes(png)
