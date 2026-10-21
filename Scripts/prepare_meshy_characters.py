"""Blender preparation: simplify source meshes while preserving UVs for rig fitting."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
(P/'Saved/RiggingQA').mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(P/'Saved/ArtMigration/Prototype.fbx'))
a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
report={'bones':{b.name:{'head':list(a.matrix_world@b.head_local),'matrix':[list(row) for row in b.matrix_local]} for b in a.data.bones}}
print('BONE_NAMES',list(report['bones']))
for token,label in [('Night_Vision_Operativ','Spy'),('Midnight_Sentinel','Merc')]:
 before=set(bpy.data.objects)
 f=next((P/'Art/MeshySource/2026-10-20').rglob('*'+token+'*.fbx'))
 bpy.ops.import_scene.fbx(filepath=str(f))
 m=next(o for o in set(bpy.data.objects)-before if o.type=='MESH')
 print(label,'TRANSFORM',m.matrix_world,'SIZE',m.dimensions)
 mod=m.modifiers.new('Prototype simplification','DECIMATE');mod.ratio=80000/len(m.data.polygons);mod.use_collapse_triangulate=True
 bpy.context.view_layer.objects.active=m;bpy.ops.object.modifier_apply(modifier=mod.name)
 m.name=label
 print(label,'OPTIMIZED',len(m.data.vertices),len(m.data.polygons))
 report[label]={'vertices':len(m.data.vertices),'triangles':len(m.data.polygons),'bounds': [list(m.matrix_world@v.co) for v in m.data.vertices]}
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'Saved/RiggingQA'/(label+'_optimized.blend')))
(P/'Saved/RiggingQA/source_geometry.json').write_text(json.dumps(report))
