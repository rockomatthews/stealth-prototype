"""Derive camera-friendly forearms; keep the original full-body merc untouched."""
import bpy,bmesh,json,math
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Equipment'
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters/Merc_rigged.blend'))
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
arms=next(o for o in scene.objects if o.type=='MESH');rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
for bone in rig.pose.bones:bone.matrix_basis.identity()
names={b.name for b in rig.data.bones if b.name.startswith(('upperarm_','lowerarm_','hand_','index_','middle_','ring_','pinky_','thumb_'))}
allowed={g.index for g in arms.vertex_groups if g.name in names}
# Restrict the camera mesh to forearms/hands; shoulders cross the near plane.
keep=set()
for v in arms.data.vertices:
 side='l' if v.co.x>0 else 'r';elbow=rig.data.bones['lowerarm_'+side].head_local;wrist=rig.data.bones['hand_'+side].head_local
 axis=(wrist-elbow).normalized();along=(v.co-elbow).dot(axis);closest=elbow+axis*max(0,min((wrist-elbow).length,along))
 if along>(wrist-elbow).length-2 and (v.co-closest).length<15 and sum(g.weight for g in v.groups if g.group in allowed)>.8:keep.add(v.index)
bm=bmesh.new();bm.from_mesh(arms.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[f for f in bm.faces if any(v.index not in keep for v in f.verts)],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(arms.data);bm.free()
# Use anatomical same-side forearm weights. Residual torso/opposite-arm
# influences in the automatic full-body bind are particularly visible in FP.
for v in arms.data.vertices:
 side='l' if v.co.x>0 else 'r';elbow=rig.data.bones['lowerarm_'+side].head_local;wrist=rig.data.bones['hand_'+side].head_local
 axis=(wrist-elbow).normalized();along=(v.co-elbow).dot(axis);length=(wrist-elbow).length
 fingers=[(g.group,g.weight) for g in v.groups if arms.vertex_groups[g.group].name.endswith('_'+side) and arms.vertex_groups[g.group].name.startswith(('index_','middle_','ring_','pinky_','thumb_'))]
 finger_weight=sum(w for _,w in fingers)
 for index in [g.group for g in v.groups]:arms.vertex_groups[index].remove([v.index])
 if finger_weight>.25 and along>length-2:
  for group,weight in fingers:arms.vertex_groups[group].add([v.index],weight/finger_weight,'REPLACE')
 else:
  hand_weight=max(0,min(1,(along-(length-5))/10));elbow_weight=max(0,min(.45,(4-along)/12))
  for name,weight in [('upperarm_'+side,elbow_weight),('lowerarm_'+side,(1-elbow_weight)*(1-hand_weight)),('hand_'+side,(1-elbow_weight)*hand_weight)]:
   if weight>0:(arms.vertex_groups.get(name) or arms.vertex_groups.new(name=name)).add([v.index],weight,'REPLACE')
# Clean closed sleeves for the extreme first-person perspective. Preserve the
# user's textured gloves; the world character continues using the full source.
sleeve_mat=bpy.data.materials.new('FPSleeve');sleeve_mat.diffuse_color=(.018,.028,.05,1)
for side in ['l','r']:
 hand=rig.data.bones['hand_'+side];target=Vector((-12,-26,133) if side=='r' else (-10,-43,133));q=(hand.tail_local-hand.head_local).rotation_difference(Vector((0,-1,0)));ready=Matrix.Translation(target)@q.to_matrix().to_4x4()@hand.matrix_local.to_quaternion().to_matrix().to_4x4();to_rest=hand.matrix_local@ready.inverted()
 sign=-1 if side=='r' else 1;p0=target;p1=target+Vector((sign*14,15,-32));p2=target+Vector((sign*30,42,-85));verts=[];faces=[];rings=13;segments=24
 for ring in range(rings):
  t=ring/(rings-1);center=(1-t)**2*p0+2*(1-t)*t*p1+t*t*p2;axis=(2*(1-t)*(p1-p0)+2*t*(p2-p1)).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized();radius=3.5+2.5*t
  for j in range(segments):
   a=j/segments*math.pi*2;verts.append(to_rest@(center+radius*(u*math.cos(a)+v*math.sin(a))))
 for ring in range(rings-1):
  for j in range(segments):
   a=ring*segments+j;b=ring*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
 faces.append(tuple(reversed(range(segments))));faces.append(tuple((rings-1)*segments+j for j in range(segments)))
 mesh=bpy.data.meshes.new('Camera sleeve '+side);mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Sleeve '+side,mesh);scene.collection.objects.link(obj);obj.data.materials.append(sleeve_mat)
 for face in mesh.polygons:face.use_smooth=len(face.vertices)==4
 group=obj.vertex_groups.new(name='hand_'+side);group.add(list(range(len(verts))),1,'REPLACE');obj.parent=rig;mod=obj.modifiers.new('Skeleton','ARMATURE');mod.object=rig
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);arms.select_set(True);bpy.context.view_layer.objects.active=arms;bpy.ops.object.join()
arms.name='SK_MercArms';bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);arms.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'MercArms.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MercArms.blend'))
report={'triangles':sum(len(p.vertices)-2 for p in arms.data.polygons),'vertices':len(arms.data.vertices),'source':'Art/RiggedCharacters/Merc_rigged.blend','forearms_only':True,'closed_procedural_sleeves':True,'arm_weights_normalized':True};(OUT/'first-person-arms-build.json').write_text(json.dumps(report,indent=2));print('FIRST_PERSON_ARMS',json.dumps(report))
