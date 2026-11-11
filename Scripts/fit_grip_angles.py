"""Fit finger closures to the actual rifle surface, within joint limits.

Uses the rendered glove skin (linear blend skinning), not socket distances.
Writes reusable original poses; it does not change the reference skeleton.
"""
import bpy,json,math,itertools,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
source=(P/'Scripts/measure_hand_contact.py').read_text();exec(compile(source[:source.index('report={}')],str(P/'Scripts/measure_hand_contact.py'),'exec'),globals())
s=(P/'Scripts/prepare_grab_animations.py').read_text();exec(s[s.index('def ease('):s.index('def animate(')],globals())
rig,mesh=characters[1];rest_inverse={b.name:b.matrix_local.inverted() for b in rig.data.bones}
result={};stats={}
def sampler(finger,side):
 names={g.index for g in mesh.vertex_groups if g.name.startswith(finger+'_') and g.name.endswith('_'+side)}
 ids=[v.index for v in mesh.data.vertices if any(g.group in names and g.weight>.05 for g in v.groups)][::2]
 coords=np.array([(*mesh.data.vertices[i].co,1.) for i in ids]);weights={}
 for k,i in enumerate(ids):
  for g in mesh.data.vertices[i].groups:
   name=mesh.vertex_groups[g.group].name
   if name not in weights:weights[name]=np.zeros(len(ids))
   weights[name][k]=g.weight
 def skin():
  out=np.zeros((len(ids),3))
  for name,w in weights.items():out+=(coords@np.array(rig.pose.bones[name].matrix@rest_inverse[name]).T)[:,:3]*w[:,None]
  return (np.column_stack((out,np.ones(len(ids))))@np.array(mesh.matrix_world).T)[:,:3]
 return skin
def score(skin,reference,angles):
 distances=[];depth=[]
 for point in skin():
  location,normal,_,distance=gun_tree.find_nearest(Vector(point));signed=(Vector(point)-location).dot(normal)
  depth.append(max(0,-signed-.05));distances.append(distance)
 # Strong separation constraint, with a smaller contact and pose preference.
 depth=np.array(depth);near=sorted(distances)[:max(1,len(distances)//5)]
 return float(5000*np.mean(depth*depth)+20*max(depth)**2+np.mean(np.square(near))*.8+sum(((a-b)/90)**2 for a,b in zip(angles,reference))*.025)
def pose(finger,side,angles):
 for i in [1,2,3]:rig.pose.bones[f'{finger}_{i:02}_{side}'].matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();df=Vector((0,-1,0) if side=='r' else (-1,0,0));axis=Vector((0,0,1) if side=='r' else (0,1,0));total=0
 for i,angle in enumerate(angles,1):
  total+=angle;orient_digit(rig,f'{finger}_{i:02}_{side}',Matrix.Rotation(math.radians(total),3,axis)@df)
for side in ['r','l']:
 result[side]={'angles':{}}
 for finger in ['index','middle','ring','pinky']:
  reference=(10,20,20) if side=='r' and finger=='index' else (85,35,25) if side=='r' and finger=='pinky' else (85,60,25) if side=='r' else (90,10,50)
  skin=sampler(finger,side);pose(finger,side,reference);best=(score(skin,reference,reference),reference)
  grid=itertools.product([0,15,30,45],[0,20,40,60],[0,20,40]) if side=='r' and finger=='index' else itertools.product([30,45,60,75,90,105],[0,25,50,75,100],[0,25,50,70])
  for angles in grid:
   if sum(angles)>205:continue
   pose(finger,side,angles);cost=score(skin,reference,angles)
   if cost<best[0]:best=(cost,angles)
  for step in [8,3]:
   for iteration in range(3):
    previous=best
    for joint in range(3):
     for sign in [-1,1]:
      angles=list(best[1]);angles[joint]+=sign*step
      if min(angles)<0 or angles[0]>105 or angles[1]>100 or angles[2]>75 or sum(angles)>205:continue
      pose(finger,side,angles);cost=score(skin,reference,angles)
      if cost<best[0]:best=(cost,tuple(angles))
    if previous==best:break
  pose(finger,side,best[1]);result[side]['angles'][finger]=list(best[1]);stats[side+finger]={'cost':best[0],'angles':best[1]};print('FINGER_FIT',side,finger,best,flush=True)
path=P/'Art/FittedCharacters/grip-poses.json';path.write_text(json.dumps(result,indent=2)+'\n')
(P/'Saved/HandContactQA/grip-fit.json').write_text(json.dumps(stats,indent=2));print('GRIP_POSES_SAVED',path,flush=True)
