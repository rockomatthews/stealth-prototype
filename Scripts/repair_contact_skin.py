"""Separate fused scan bridges that connect independently moving body parts.

Only writes derived meshes. UVs and all surviving skin weights are preserved.
"""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];OUT=P/'Art/ContactCharacters';OUT.mkdir(parents=True,exist_ok=True)
report={}
for label in ['Spy','Merc']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/RiggedCharacters'/f'{label}_rigged.blend'))
 mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 with bpy.data.libraries.load(str(P/'Art/Grab'/f'{label}Hold.blend'),link=False) as (src,dst):dst.actions=[n for n in src.actions if n.startswith(label+'Hold')]
 if not dst.actions:raise RuntimeError('Contact pose action missing')
 rig.animation_data_create();rig.animation_data.action=dst.actions[0];bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
 evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=evaluated.to_mesh();bad=set()
 for edge in mesh.data.edges:
  a,b=edge.vertices;before=(mesh.data.vertices[a].co-mesh.data.vertices[b].co).length;after=(posed.vertices[a].co-posed.vertices[b].co).length
  if after>18 and after>max(.1,before)*4:bad.add(tuple(sorted((a,b))))
 evaluated.to_mesh_clear()
 bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
 faces=[f for f in bm.faces if any(tuple(sorted((e.verts[0].index,e.verts[1].index))) in bad for e in f.edges)]
 count=len(faces);bmesh.ops.delete(bm,geom=faces,context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 # Seal each resulting boundary locally; no vertices are welded across limbs.
 boundary=[e for e in bm.edges if e.is_boundary]
 result=bmesh.ops.holes_fill(bm,edges=boundary,sides=0) if boundary else {'faces':[]}
 bmesh.ops.triangulate(bm,faces=list(result['faces']))
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh.data);bm.free();mesh.data.update()
 rig.animation_data_clear()
 for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
 bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{label}_contact.blend'))
 bpy.ops.export_scene.fbx(filepath=str(OUT/f'{label}_contact.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 report[label]={'removed_bridge_faces':count,'bad_edges':len(bad),'sealed_boundaries':len(boundary),'source':f'Art/RiggedCharacters/{label}_rigged.blend','diagnostic_pose':f'Art/Grab/{label}Hold.blend'}
(OUT/'skin-repair.json').write_text(json.dumps(report,indent=2));print('CONTACT_SKIN',json.dumps(report))
