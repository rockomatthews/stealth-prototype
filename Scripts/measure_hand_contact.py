"""Measure rendered glove surface samples against the actual rifle/merc mesh."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];OUT=P/'Saved/HandContactQA';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);characters=[]
for label in ['Spy','Merc']:
 with bpy.data.libraries.load(str(P/'Art/Grab'/f'{label}Hold.blend'),link=False) as (src,dst):dst.objects=src.objects
 for obj in dst.objects:
  if obj:bpy.context.scene.collection.objects.link(obj)
 rig=next(o for o in dst.objects if o and o.type=='ARMATURE');rig.location.y=-40 if label=='Merc' else 0
 mesh=next(o for o in dst.objects if o and o.type=='MESH');characters.append((rig,mesh))
bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def tree_from(objs):
 verts=[];faces=[]
 for obj in objs:
  evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh();offset=len(verts)
  verts.extend(obj.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(offset+i for i in f.vertices) for f in mesh.polygons);evaluated.to_mesh_clear()
 return BVHTree.FromPolygons(verts,faces)
with bpy.data.libraries.load(str(P/'Art/UtilityRifle/MercUtility.blend'),link=False) as (src,dst):dst.objects=src.objects
for obj in dst.objects:
 if obj:bpy.context.scene.collection.objects.link(obj)
gun=next(o for o in dst.objects if o and o.type=='ARMATURE');gun.animation_data_clear();merc=characters[1][0]
palm=merc.matrix_world@((merc.pose.bones['hand_r'].head+merc.pose.bones['middle_01_r'].head)*.5);rotation=Matrix.Rotation(-math.pi/2,4,'Z')
gun.matrix_world=Matrix.Translation(palm+rotation.to_3x3()@Vector((1,3.55,0))-rotation.to_3x3()@(Vector((-4.5,-2,-4.5))*.75))@rotation@Matrix.Scale(.75,4);bpy.context.view_layer.update()
gun_tree=tree_from([o for o in dst.objects if o and o.type=='MESH']);merc_tree=tree_from([characters[1][1]])
report={}
for label,(rig,mesh),tree in [('Merc',characters[1],gun_tree),('Spy',characters[0],merc_tree)]:
 ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());surface=ev.to_mesh()
 for side in ['r','l']:
  groups={g.index for g in mesh.vertex_groups if g.name.endswith('_'+side) and g.name.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_'))}
  samples=[]
  for v in mesh.data.vertices:
   if sum(g.weight for g in v.groups if g.group in groups)<.8:continue
   point=mesh.matrix_world@surface.vertices[v.index].co;near,normal,_,distance=tree.find_nearest(point)
   signed=(point-near).dot(normal);weights={mesh.vertex_groups[g.group].name:round(g.weight,3) for g in v.groups if g.weight>.05}
   samples.append({'vertex':v.index,'point':list(point),'signed':signed,'distance':distance,'weights':weights})
  penetration=[s for s in samples if s['signed']<-.15]
  penetration.sort(key=lambda s:s['signed']);contact=[s for s in samples if -.15<=s['signed']<=.6]
  report[label+side]={'samples':len(samples),'penetrating':len(penetration),'worst_depth':-penetration[0]['signed'] if penetration else 0,'near_contact':len(contact),'worst':penetration[:12]}
 ev.to_mesh_clear()
(OUT/'surface-contact.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:{n:v for n,v in d.items() if n!='worst'} for k,d in report.items()},indent=2))
