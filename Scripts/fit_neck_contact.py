"""Fit the paired neck hold to both the merc surface and his carried rifle."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
s=(P/'Scripts/measure_hand_contact.py').read_text();exec(compile(s[:s.index('report={}')],str(P/'Scripts/measure_hand_contact.py'),'exec'),globals())
s=(P/'Scripts/prepare_grab_animations.py').read_text();exec(s[s.index('def ease('):s.index('def animate(')],globals())
rig,mesh=characters[0];rest_inverse={b.name:b.matrix_local.inverted() for b in rig.data.bones};targets={'r':Vector((-7,-57,151)),'l':Vector((6,-55.5,159))};poles={'r':Vector((-35,-65,151)),'l':Vector((35,-55,151))}
ids=[v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if mesh.vertex_groups[g.group].name.startswith(('lowerarm_','hand_','index_','middle_','ring_','pinky_','thumb_')))>.65][::3]
coords=np.array([(*mesh.data.vertices[i].co,1) for i in ids]);weights={}
for k,i in enumerate(ids):
 for g in mesh.data.vertices[i].groups:
  name=mesh.vertex_groups[g.group].name
  if name not in weights:weights[name]=np.zeros(len(ids))
  weights[name][k]=g.weight
def skin():
 out=np.zeros((len(ids),3))
 for name,w in weights.items():out+=(coords@np.array(rig.pose.bones[name].matrix@rest_inverse[name]).T)[:,:3]*w[:,None]
 return out
def apply(xshift,yshift,zshift,angle_r,angle_l):
 for side,angle in [('r',angle_r),('l',angle_l)]:
  for name in ['upperarm','lowerarm','hand']:rig.pose.bones[name+'_'+side].matrix_basis=Matrix.Identity(4)
  bpy.context.view_layer.update();shoulder=rig.pose.bones['upperarm_'+side].head.copy();target=targets[side]+Vector((xshift,yshift,zshift));axis=(target-shoulder).normalized();pole=shoulder+Matrix.Rotation(math.radians(angle),3,axis)@(poles[side]-shoulder)
  limb(rig,'upperarm_'+side,'lowerarm_'+side,'hand_'+side,target,pole);neck_hand(rig,side)
def score(parameters):
 apply(*parameters);depth=[];contact=[]
 for point in skin():
  if point[2]<140:continue
  point=Vector(point);dist=[]
  for tree in [merc_tree,gun_tree]:
   near,normal,_,distance=tree.find_nearest(point);signed=(point-near).dot(normal);depth.append(max(0,-signed-.06));dist.append(distance)
  contact.append(min(dist))
 depth=np.array(depth);contact.sort()
 if not np.all(np.isfinite(depth)):return float('inf')
 return float(4000*np.mean(depth**2)+25*max(depth,default=0)**2+np.mean(np.square(contact[:max(1,len(contact)//8)]))*.5+sum((v/10)**2 for v in parameters[:3])*.02+sum((v/60)**2 for v in parameters[3:])*.01)
best=(score((0,0,0,0,0)),(0,0,0,0,0))
for sweep in range(3):
 previous=best
 for index,steps in [(0,[-6,0,6,9,12,15]),(1,[-10,-7,-5,-3,-1,0]),(2,[0,3,4.5,6,8]),(3,[-60,-40,-20,0,20,40,60]),(4,[-60,-40,-20,0,20,40,60])]:
  for value in steps:
   trial=list(best[1]);trial[index]=value;cost=score(trial)
   if cost<best[0]:best=(cost,tuple(trial))
 if previous==best:break
print('NECK_CONTACT_FIT',best,flush=True)
(P/'Art/FittedCharacters/neck-contact.json').write_text(json.dumps({'cost':best[0],'offset':list(best[1][:3]),'pole_angles':list(best[1][3:]),'contact_reference':'actual merc body plus carried rifle'},indent=2)+'\n')
