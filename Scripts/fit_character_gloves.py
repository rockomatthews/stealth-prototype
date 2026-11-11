"""Derived articulated gloves and coherent sleeve skinning; source scans untouched.

The scanned fingers were fused and already flexed. New continuous finger loops
are weighted to the actual phalanges. UVs are sampled from the original glove.
"""
import bpy,bmesh,math,json
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/FittedCharacters';OUT.mkdir(parents=True,exist_ok=True)
report={}
def smooth(a,b,x):
 t=max(0,min(1,(x-a)/(b-a)));return t*t*(3-2*t)
def active(o):
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
for label in ['Spy','Merc']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'Art/ContactCharacters'/f'{label}_contact.blend'))
 scene=bpy.context.scene;scene.unit_settings.scale_length=.01
 rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear()
 for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 body=next(o for o in scene.objects if o.type=='MESH');original=body.data.copy();original.calc_loop_triangles()
 source_vertices=[v.co.copy() for v in original.vertices];triangles=list(original.loop_triangles)
 tree=BVHTree.FromPolygons(source_vertices,[tuple(t.vertices) for t in triangles],all_triangles=True)
 source_uv=original.uv_layers.active;uv_name=source_uv.name
 def uv_at(point):
  nearest,_,index,_=tree.find_nearest(point);tri=triangles[index];coords=[source_vertices[i] for i in tri.vertices]
  values=[Vector((*source_uv.data[i].uv,0)) for i in tri.loops]
  return barycentric_transform(nearest,*coords,*values).xy
 new=[];stats={}
 for side in ['r','l']:
  bones=rig.data.bones;w=bones['hand_'+side].head_local.copy();f=(bones['middle_01_'+side].head_local-w).normalized()
  a=bones['index_01_'+side].head_local-bones['pinky_01_'+side].head_local;a=(a-f*a.dot(f)).normalized();n=a.cross(f).normalized()
  # Cut the old glove on an exact wrist plane, underneath the new cuff.
  bm=bmesh.new();bm.from_mesh(body.data)
  nearby=[face for face in bm.faces if (face.calc_center_median()-w).length<24]
  geom=set(nearby)
  for face in nearby:geom.update(face.edges);geom.update(face.verts)
  bmesh.ops.bisect_plane(bm,geom=list(geom),dist=.0001,plane_co=w-f*.8,plane_no=f,clear_outer=True,clear_inner=False)
  bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(body.data);bm.free()
  verts=[];faces=[];weights=[]
  def vertex(point,influences):
   verts.append(tuple(point));weights.append(influences);return len(verts)-1
  def loft(points,radii,axis,weight_at,segments=20):
   start=len(verts)
   for i,(center,radius) in enumerate(zip(points,radii)):
    direction=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized();u=(axis-direction*axis.dot(direction)).normalized();v=direction.cross(u).normalized()
    for j in range(segments):
     angle=2*math.pi*j/segments;vertex(center+radius*(u*math.cos(angle)+v*math.sin(angle)),weight_at(i))
   for i in range(len(points)-1):
    for j in range(segments):
     x=start+i*segments+j;y=start+i*segments+(j+1)%segments;faces.append((x,y,y+segments,x+segments))
   faces.append(tuple(reversed([start+j for j in range(segments)])));faces.append(tuple(start+(len(points)-1)*segments+j for j in range(segments)))
  # Rounded palm, narrowed wrist and padded back panel. A small overlap at the
  # finger roots is internal to the palm; fingers are never welded together.
  profile=[(-2,3.6,2.2),(0,3.0,1.65),(2,3.4,1.6),(4,3.9,1.6),(6,4.0,1.45),(7.5,3.9,1.25),(8.7,3.5,1.05),(9.4,2.7,.7),(9.7,.25,.15)]
  segments=40;start=len(verts)
  for distance,width,depth in profile:
   hand=smooth(-1.8,.3,distance)
   for j in range(segments):
    angle=2*math.pi*j/segments
    point=w+f*distance+a*(-.65+width*math.cos(angle))+n*(.25+depth*math.sin(angle))
    vertex(point,{'hand_'+side:hand,'lowerarm_'+side:1-hand})
  for i in range(len(profile)-1):
   for j in range(segments):
    x=start+i*segments+j;y=start+i*segments+(j+1)%segments;faces.append((x,y,y+segments,x+segments))
  faces.append(tuple(start+(len(profile)-1)*segments+j for j in range(segments)))
  for finger in ['index','middle','ring','pinky','thumb']:
   names=[f'{finger}_{i:02}_{side}' for i in [1,2,3]];joints=[bones[name].head_local.copy() for name in names]
   tip=joints[-1]+(joints[-1]-joints[-2]).normalized()*bones[names[-1]].length
   joints.append(tip);lengths=[(b-c).length for c,b in zip(joints,joints[1:])];bounds=[0,lengths[0],lengths[0]+lengths[1],sum(lengths)]
   centers=[];radii=[];arcs=[];base={'index':.92,'middle':1.,'ring':.94,'pinky':.78,'thumb':1.1}[finger]
   for section in range(3):
    for ring in range(7):
     t=ring/7;centers.append(joints[section].lerp(joints[section+1],t));arc=bounds[section]+lengths[section]*t;arcs.append(arc)
     radii.append(base*(1-.28*arc/bounds[-1]))
   direction=(joints[-1]-joints[-2]).normalized();radius=base*.72
   for j in range(5):
    t=j/4;centers.append(tip+direction*radius*math.sin(t*math.pi/2));radii.append(max(.025,radius*math.cos(t*math.pi/2)));arcs.append(bounds[-1]+radius*t)
   def finger_weights(i):
    arc=arcs[i]
    if arc<.8:
     q=smooth(0,.8,arc);return {'hand_'+side:1-q,names[0]:q}
    for joint in [1,2]:
     if arc<bounds[joint]+.65:
      q=smooth(bounds[joint]-.65,bounds[joint]+.65,arc);return {names[joint-1]:1-q,names[joint]:q}
    return {names[2]:1}
   loft(centers,radii,a,finger_weights)
  data=bpy.data.meshes.new(label+' articulated glove '+side);data.from_pydata(verts,[],faces);data.update();obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);glove_mat=body.data.materials[0].copy();glove_mat.name=label+'_GloveRepair';data.materials.append(glove_mat);uv=data.uv_layers.new(name=uv_name)
  for face in data.polygons:
   face.use_smooth=True
   for loop in face.loop_indices:uv.data[loop].uv=uv_at(data.vertices[data.loops[loop].vertex_index].co)
  for i,groups in enumerate(weights):
   for name,value in groups.items():
    if value>1e-5:(obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)).add([i],value,'REPLACE')
  # Keep outward normals consistent on the palm and every closed finger.
  bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
  new.append(obj);stats[side]={'glove_vertices':len(verts),'glove_faces':len(faces)}
 # Reweight sleeves to coherent anatomical segments. Removing random twist/
 # torso influences avoids fabric spikes when elbows and wrists rotate.
 changed=0
 for vertex in body.data.vertices:
  side='l' if vertex.co.x>0 else 'r';arm=sum(g.weight for g in vertex.groups if body.vertex_groups[g.group].name.endswith('_'+side) and body.vertex_groups[g.group].name.startswith(('upperarm_','lowerarm_','hand_')))
  if arm<.01:continue
  shoulder,elbow,wrist=[rig.data.bones[name+'_'+side].head_local for name in ['upperarm','lowerarm','hand']]
  u=(elbow-shoulder).normalized();v=(wrist-elbow).normalized();l1=(elbow-shoulder).length;l2=(wrist-elbow).length
  tu=max(0,min(l1,(vertex.co-shoulder).dot(u)));tl=max(0,min(l2,(vertex.co-elbow).dot(v)))
  arc=tu if (vertex.co-shoulder-u*tu).length<(vertex.co-elbow-v*tl).length else l1+tl
  lower=smooth(l1-4,l1+4,arc);hand=smooth(l1+l2-3,l1+l2+1,arc)
  torso=[(g.group,g.weight) for g in vertex.groups if body.vertex_groups[g.group].name.startswith(('spine_','clavicle_'))]
  torso_total=sum(value for _,value in torso)
  amount=smooth(17,29,abs(vertex.co.x))
  for index in [g.group for g in vertex.groups]:body.vertex_groups[index].remove([vertex.index])
  if amount<1:
   if torso_total>.001:
    torso=sorted(torso,key=lambda item:item[1],reverse=True)[:2];torso_total=sum(value for _,value in torso)
    for index,value in torso:body.vertex_groups[index].add([vertex.index],(1-amount)*value/torso_total,'REPLACE')
   else:
    name=min((b for b in rig.data.bones if b.name.startswith('spine_')),key=lambda bone:abs(bone.head_local.z-vertex.co.z)).name
    (body.vertex_groups.get(name) or body.vertex_groups.new(name=name)).add([vertex.index],1-amount,'REPLACE')
  for name,value in [('upperarm_'+side,(1-lower)*amount),('lowerarm_'+side,lower*(1-hand)*amount),('hand_'+side,lower*hand*amount)]:
   if value>1e-5:(body.vertex_groups.get(name) or body.vertex_groups.new(name=name)).add([vertex.index],value,'REPLACE')
  changed+=1
 for face in body.data.polygons:
  if all(any(body.vertex_groups[g.group].name.startswith(('upperarm_','lowerarm_')) and g.weight>.1 for g in body.data.vertices[i].groups) for i in face.vertices):face.use_smooth=True
 active(body)
 for obj in new:obj.select_set(True)
 bpy.ops.object.join();body.name='SK_'+label
 active(body);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
 active(rig);body.select_set(True);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'{label}_fitted.blend'))
 bpy.ops.export_scene.fbx(filepath=str(OUT/f'{label}_fitted.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,mesh_smooth_type='FACE',axis_forward='-Y',axis_up='Z',armature_nodetype='ROOT')
 report[label]={'hands':stats,'sleeve_vertices_reweighted':changed,'vertices':len(body.data.vertices),'triangles':sum(len(f.vertices)-2 for f in body.data.polygons)}
(OUT/'glove-fit.json').write_text(json.dumps(report,indent=2));print('FITTED_GLOVES',json.dumps(report))
