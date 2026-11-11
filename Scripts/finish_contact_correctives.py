"""Bake garment relaxation and glove contact shaping as pose correctives.

Correctives are mapped back through the actual skinning transforms, exported
as morph targets, and activated only in the corresponding in-game pose.
"""
import bpy,json,math,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from pathlib import Path
P=Path(__file__).resolve().parents[1];report={}
def tree_of(objects):
 vertices=[];faces=[]
 for obj in objects:
  ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();offset=len(vertices)
  vertices.extend(obj.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(offset+i for i in f.vertices) for f in mesh.polygons);ev.to_mesh_clear()
 return BVHTree.FromPolygons(vertices,faces)
def append(path,kind='objects'):
 with bpy.data.libraries.load(str(path),link=False) as (src,dst):setattr(dst,kind,getattr(src,kind))
 result=getattr(dst,kind)
 if kind=='objects':
  for obj in result:
   if obj:bpy.context.scene.collection.objects.link(obj)
 return result
cases=[('Spy',P/'Art/Equipment/SpyEquipmentBase.blend',P/'Art/Grab/SpyHold.blend',1,P/'Art/Equipment/SpyEquipment.fbx'),('Merc',P/'Art/FittedCharacters/Merc_fitted.blend',P/'Art/UtilityRifle/MercUtilityEquip.blend',22,P/'Art/FittedCharacters/Merc_fitted.fbx'),('View',P/'Art/UtilityRifle/MercUtilityArms.blend',P/'Art/UtilityRifle/MercUtilityEquipView.blend',22,P/'Art/UtilityRifle/MercUtilityArms.fbx')]
cases=globals().get('CASE_OVERRIDE',cases)
for label,base,pose_path,frame,fbx in cases:
 prefix='LauncherGrip' if label=='Launcher' else 'ContactCloth'
 bpy.ops.wm.open_mainfile(filepath=str(base));scene=bpy.context.scene
 rig=next(o for o in scene.objects if o.type=='ARMATURE');body=next(o for o in scene.objects if o.type=='MESH')
 if body.data.shape_keys:
  names={key.name for key in body.data.shape_keys.key_blocks}
  if names-{'Basis','ContactClothR','ContactClothL','LauncherGripR','LauncherGripL'}:raise RuntimeError('Unknown author shape keys; preserve them')
  if label=='Launcher':
   for key in list(body.data.shape_keys.key_blocks):
    key.value=0
    if key.name.startswith('LauncherGrip'):body.shape_key_remove(key)
  else:body.shape_key_clear()
 # Keep glove leather distinct from the surrounding uniform cloth.
 glove=next((m for m in body.data.materials if m and 'GloveRepair' in m.name),None)
 if glove is None:
  glove=body.data.materials[0].copy();glove.name=label+'_GloveRepair';body.data.materials.append(glove)
 glove_index=list(body.data.materials).index(glove)
 glove_groups={g.index for g in body.vertex_groups if g.name.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_'))}
 for face in body.data.polygons:
  if all(sum(g.weight for g in body.data.vertices[i].groups if g.group in glove_groups)>.65 for i in face.vertices):face.material_index=glove_index
 actions=append(pose_path,'actions');action=next(a for a in actions if a and a.name.startswith(pose_path.stem));rig.animation_data_create();rig.animation_data.action=action
 if action.slots:rig.animation_data.action_slot=action.slots[0]
 scene.frame_set(frame);bpy.context.view_layer.update()
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();base_skin=np.array([tuple(v.co) for v in posed.vertices]);ev.to_mesh_clear()
 if label=='Spy':
  reference=append(P/'Art/Grab/MercHold.blend');partner=next(o for o in reference if o and o.type=='ARMATURE');partner.location.y=-40;bpy.context.view_layer.update();tree=tree_of([o for o in reference if o and o.type=='MESH'])
 else:
  reference=append(P/('Art/Equipment/Launcher.blend' if label=='Launcher' else 'Art/UtilityRifle/MercUtility.blend'));gun=next(o for o in reference if o and o.type=='ARMATURE');gun.animation_data_clear()
  palm=(rig.pose.bones['hand_r'].head+rig.pose.bones['middle_01_r'].head)*.5;rotation=Matrix.Rotation(-math.pi/2,4,'Z')
  gun.matrix_world=Matrix.Translation(palm+rotation.to_3x3()@Vector((1,4.1 if label=='Launcher' else 3.55,0))-rotation.to_3x3()@(Vector((-1,0,-4)) if label=='Launcher' else Vector((-4.5,-2,-4.5))*.75))@rotation@Matrix.Scale(1 if label=='Launcher' else .75,4);bpy.context.view_layer.update();tree=tree_of([o for o in reference if o and o.type=='MESH'])
 rest=np.array([tuple(v.co) for v in body.data.vertices]);count=len(rest);garment=np.zeros(count);contact=np.zeros(count,dtype=bool)
 for vertex in body.data.vertices:
  groups={body.vertex_groups[g.group].name:g.weight for g in vertex.groups};upper=sum(w for name,w in groups.items() if name.startswith('upperarm_'));lower=sum(w for name,w in groups.items() if name.startswith('lowerarm_'));hands=sum(w for name,w in groups.items() if name.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_')))
  x,y,z=vertex.co
  if 13<abs(x)<40 and 116<z<153:garment[vertex.index]=min(1,upper*1.5)
  contact[vertex.index]=hands>.8 or (lower>.5 and (label=='Spy' and base_skin[vertex.index][2]>140))
 # Taubin relaxation removes sharp skinning folds without shrinking the sleeve.
 edges=np.array([tuple(e.vertices) for e in body.data.edges]);ii=np.concatenate((edges[:,0],edges[:,1]));jj=np.concatenate((edges[:,1],edges[:,0]));degree=np.bincount(ii,minlength=count).clip(1)
 relaxed=base_skin.copy()
 for iteration in range(16):
  for factor in [.48,-.50]:
   average=np.zeros_like(relaxed);np.add.at(average,ii,relaxed[jj]);average/=degree[:,None];relaxed+=(average-relaxed)*(garment*factor)[:,None]
 delta=relaxed-base_skin;length=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,4.5/np.maximum(length,.00001))[:,None]
 target=base_skin+delta;before=0;worst=0;pushes=0
 for index in np.flatnonzero(contact):
  for iteration in range(8):
   point=Vector(target[index]);near,normal,_,distance=tree.find_nearest(point);signed=(point-near).dot(normal)
   if signed>=.025:break
   if iteration==0:before+=1;worst=max(worst,-signed);pushes+=1
   target[index]+=np.array(normal)*min(4.0,.035-signed)
 # Invert linear blend skinning for the corrective, preserving the bind pose.
 inverse={b.name:b.matrix_local.inverted() for b in rig.data.bones};skin_matrices={name:np.array(rig.pose.bones[name].matrix@inv)[:3,:3] for name,inv in inverse.items()}
 body.shape_key_add(name='Basis',from_mix=False) if not body.data.shape_keys else None;changes=target-base_skin;max_delta=0
 for side,sign in [('R',-1),('L',1)]:
  key=body.shape_key_add(name=prefix+side,from_mix=False)
  for vertex in body.data.vertices:
   index=vertex.index
   if rest[index,0]*sign<=0 or np.linalg.norm(changes[index])<.00001:continue
   matrix=sum((skin_matrices[body.vertex_groups[g.group].name]*g.weight for g in vertex.groups),np.zeros((3,3)))
   local=np.linalg.solve(matrix,changes[index]);size=np.linalg.norm(local)
   if size>12:local*=12/size
   key.data[index].co=vertex.co+Vector(local);max_delta=max(max_delta,np.linalg.norm(local))
  key.value=1
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh();remaining=[]
 for index in np.flatnonzero(contact):
  point=posed.vertices[index].co;near,normal,_,_=tree.find_nearest(point);signed=(point-near).dot(normal)
  if signed<-.05:remaining.append(float(-signed))
 ev.to_mesh_clear();report[label]={'garment_vertices':int(np.count_nonzero(garment)),'contact_vertices':int(np.count_nonzero(contact)),'contact_corrections':pushes,'worst_before_cm':worst,'remaining_deeper_than_half_mm':len(remaining),'worst_after_cm':max(remaining,default=0),'maximum_bind_corrective_cm':float(max_delta),'worst_before_vertices':[{ 'id':int(index),'groups':{body.vertex_groups[g.group].name:g.weight for g in body.data.vertices[index].groups},'push_cm':float(np.linalg.norm(changes[index]))} for index in np.argsort(np.linalg.norm(changes,axis=1))[-8:] if contact[index]]}
 for obj in list(scene.objects):
  if obj not in [body,rig]:bpy.data.objects.remove(obj,do_unlink=True)
 rig.animation_data_clear()
 for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 for key in body.data.shape_keys.key_blocks:key.value=0
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.wm.save_as_mainfile(filepath=str(base))
 bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},use_mesh_modifiers=False,add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 print('CONTACT_CORRECTIVE',label,json.dumps(report[label]),flush=True)
(P/('Art/FittedCharacters/launcher-correctives.json' if cases[0][0]=='Launcher' else 'Art/FittedCharacters/contact-correctives.json')).write_text(json.dumps(report,indent=2)+'\n')
