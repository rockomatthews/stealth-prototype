"""Identify bind-weight discontinuities using deformed edge lengths."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/Grab/SpyHold.blend'))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');bpy.context.scene.frame_set(1)
deformed=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh();worst=[]
for e in mesh.data.edges:
 a,b=e.vertices;old=(mesh.data.vertices[a].co-mesh.data.vertices[b].co).length;new=(deformed.vertices[a].co-deformed.vertices[b].co).length
 if old>.05 and new>old*4 and new>8:
  worst.append({'ratio':new/old,'length':new,'vertices':[{'id':i,'bind':list(mesh.data.vertices[i].co),'pose':list(deformed.vertices[i].co),'weights':{mesh.vertex_groups[g.group].name:g.weight for g in mesh.data.vertices[i].groups if g.weight>.01}} for i in [a,b]]})
worst.sort(key=lambda e:e['length'],reverse=True)
(P/'Saved/ContactQA/skin-stretch.json').write_text(json.dumps(worst[:20],indent=2));print(json.dumps(worst[:4],indent=2))
