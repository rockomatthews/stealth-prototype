"""Actual textured arms through the shoulders; no exposed elbow cap in view."""
import bpy,bmesh
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/FittedCharacters/Merc_fitted.blend'))
scene=bpy.context.scene;scene.unit_settings.scale_length=.01
arms=next(o for o in scene.objects if o.type=='MESH');rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
allowed={g.index for g in arms.vertex_groups if g.name.startswith(('upperarm_','lowerarm_','hand_','index_','middle_','ring_','pinky_','thumb_'))}
keep={v.index for v in arms.data.vertices if abs(v.co.x)>17 and sum(g.weight for g in v.groups if g.group in allowed)>.65}
bm=bmesh.new();bm.from_mesh(arms.data);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[f for f in bm.faces if any(v.index not in keep for v in f.verts)],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(arms.data);bm.free()
for vertex in arms.data.vertices:
 weights=[(g.group,g.weight) for g in vertex.groups if g.group in allowed];total=sum(w for _,w in weights)
 for index in [g.group for g in vertex.groups]:arms.vertex_groups[index].remove([vertex.index])
 for group,weight in weights:arms.vertex_groups[group].add([vertex.index],weight/total,'REPLACE')
OUT=P/'Art/UtilityRifle';OUT.mkdir(parents=True,exist_ok=True)
arms.name='SK_MercUtilityArms';bpy.ops.object.select_all(action='DESELECT');arms.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(OUT/'MercUtilityArms.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'MercUtilityArms.blend'))
print('UTILITY_ARMS_BUILT',sum(len(p.vertices)-2 for p in arms.data.polygons))
