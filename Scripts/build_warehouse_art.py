"""Original modular warehouse assets, centimeter scale. No external asset downloads."""
import bpy,math,random,json
import numpy as np
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1];OUT=P/'Art/Warehouse';OUT.mkdir(parents=True,exist_ok=True)
rng=random.Random(42);report={}
def reset():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.01
reset()
mats={}
for name,color in [('Wood',(.32,.22,.12,1)),('Steel',(.12,.14,.15,1)),('Concrete',(.36,.35,.32,1)),('Duct',(.34,.37,.4,1)),('Canvas',(.15,.18,.12,1)),('Yellow',(.62,.4,.08,1)),('Black',(.02,.025,.03,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=color;mats[name]=m
parts=[]
def box(loc,size,material='Steel',rotation=None,bevel=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=size
 if rotation:o.rotation_euler=rotation
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mats[material]);parts.append(o)
 if bevel:
  mod=o.modifiers.new('Edge wear','BEVEL');mod.width=bevel;mod.segments=1;bpy.ops.object.modifier_apply(modifier=mod.name)
 return o
def cyl(loc,radius,depth,material='Steel',rotation=None,vertices=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation or (0,0,0));o=bpy.context.object;o.data.materials.append(mats[material]);parts.append(o);return o
def finish(name):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=name
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
 bpy.ops.export_scene.fbx(filepath=str(OUT/(name+'.fbx')),use_selection=True,object_types={'MESH'},bake_anim=False,axis_forward='-Y',axis_up='Z')
 report[name]={'triangles':sum(len(f.vertices)-2 for f in o.data.polygons),'dimensions_cm':list(o.dimensions)}
 bpy.data.objects.remove(o,do_unlink=True);parts.clear()
# Individual boards, cleats, straps and bolt heads give crates a real silhouette.
for i in range(8):
 x=-43.75+i*12.5
 for y in [-48,48]:box((x,y,50),(11.9,3.5,96),'Wood',bevel=.25)
 for z in [2,98]:box((x,0,z),(11.9,96,3.5),'Wood',bevel=.25)
 y=-43.75+i*12.5
 for x in [-48,48]:box((x,y,50),(3.5,11.9,96),'Wood',bevel=.25)
for y in [-51,51]:
 for z in [10,90]:box((0,y,z),(104,5,9),'Wood',bevel=.4)
 for x in [-42,42]:box((x,y,50),(9,5,100),'Wood',bevel=.4)
 for x in [-30,30]:
  box((x,y*1.025,50),(3,1,100),'Steel')
  for z in [9,91]:cyl((x,y*1.04,z),1.25,1,'Steel',(math.pi/2,0,0),8)
for x in [-51,51]:
 for z in [10,90]:box((x,0,z),(5,104,9),'Wood',bevel=.4)
finish('SM_Crate')
for i in range(7):box((-43+i*14.3,0,11),(12,100,3),'Wood',bevel=.3)
for x in [-40,0,40]:box((x,0,5),(12,100,9),'Wood')
finish('SM_Pallet')
cyl((0,0,50),49,96,'Steel',vertices=24)
for z in [4,30,70,96]:
 bpy.ops.mesh.primitive_torus_add(major_radius=48,minor_radius=2,major_segments=24,minor_segments=6,location=(0,0,z));o=bpy.context.object;o.data.materials.append(mats['Steel']);parts.append(o)
cyl((16,0,100),5,1,'Black',vertices=12);finish('SM_Barrel')
# H-section supports. Basis units deliberately suit simple instance scaling.
for x in [-9,9]:box((x,0,50),(3,24,100))
box((0,0,50),(16,3,100));box((0,0,3),(32,32,6));finish('SM_Column')
for z in [-6,6]:box((0,0,z),(100,16,2))
box((0,0,0),(100,2,10));finish('SM_Beam')
for y in [-48,48]:box((0,y,0),(100,4,8))
for x in [-48,48]:box((x,0,0),(4,100,8))
for x in range(-42,44,10):box((x,0,0),(2,92,5))
for y in range(-40,44,20):box((0,y,0),(92,1.4,4))
finish('SM_Grate')
for x in [-48,48]:cyl((x,0,55),2.2,110,vertices=8)
for z in [52,106]:cyl((0,0,z),2.2,100,rotation=(0,math.pi/2,0),vertices=10)
box((0,0,8),(100,3,15));finish('SM_Rail')
# Shade and bulb; lighting is authored separately in Unreal.
bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=23,radius2=7,depth=20,location=(0,0,0));o=bpy.context.object;o.data.materials.append(mats['Black']);parts.append(o)
cyl((0,0,15),4,12);cyl((0,0,-11),11,2,'Yellow');finish('SM_Lamp')
# Braided static rope. Three helical strands plus central core, repeat every meter.
for strand in range(3):
 curve=bpy.data.curves.new('Hemp strand','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=.65;curve.bevel_resolution=1
 sp=curve.splines.new('POLY');sp.points.add(80)
 for i,pt in enumerate(sp.points):
  z=i*1.25;a=2*math.pi*(i/20+strand/3);pt.co=(math.cos(a)*1.2,math.sin(a)*1.2,z,1)
 o=bpy.data.objects.new('Strand',curve);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o=bpy.context.object;o.data.materials.append(mats['Wood']);parts.append(o)
finish('SM_Rope')
# Drape with folds and a slightly irregular hem; original canvas mesh.
verts=[];faces=[];N=16
for j in range(N+1):
 for i in range(N+1):
  u=(i/N-.5)*120;v=(j/N-.5)*120;z=8+2*math.sin(u*.18)+1.4*math.cos(v*.17)
  if abs(u)>48:z-=max(0,abs(u)-48)*1.8
  if abs(v)>48:z-=max(0,abs(v)-48)*1.8
  verts.append((u,v,z))
for j in range(N):
 for i in range(N):a=j*(N+1)+i;faces.append((a,a+1,a+N+2,a+N+1))
mesh=bpy.data.meshes.new('Canvas');mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new('Canvas',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(mats['Canvas']);parts.append(o);finish('SM_Canvas')
# Reproducible tileable base-color, normal and roughness maps.
size=512;randoms=np.random.default_rng(27);Y,X=np.mgrid[:size,:size]
def noise(n):
 small=randoms.random((n,n));coords=np.linspace(0,n,size,endpoint=False);lo=coords.astype(int)%n;hi=(lo+1)%n;t=coords%1;t=t*t*(3-2*t)
 a=small[lo[:,None],lo[None,:]]*(1-t[None,:])+small[lo[:,None],hi[None,:]]*t[None,:]
 b=small[hi[:,None],lo[None,:]]*(1-t[None,:])+small[hi[:,None],hi[None,:]]*t[None,:]
 return a*(1-t[:,None])+b*t[:,None]
def png(name,data):
 if data.ndim==2:data=np.repeat(data[:,:,None],3,axis=2)
 a=np.concatenate((np.clip(data,0,1),np.ones((size,size,1))),axis=2).astype(np.float32)
 image=bpy.data.images.new(name,width=size,height=size,alpha=True);image.pixels.foreach_set(a.reshape(-1));image.filepath_raw=str(OUT/(name+'.png'));image.file_format='PNG';image.save();bpy.data.images.remove(image)
for name,color in [('Wood',(.38,.26,.13)),('Steel',(.18,.20,.22)),('Concrete',(.40,.39,.36)),('Duct',(.43,.46,.48)),('Canvas',(.18,.21,.14))]:
 n=noise(4)*.45+noise(20)*.3+noise(120)*.25
 if name=='Wood':n=n*.65+(.5+.5*np.sin(X*.26+noise(6)*24+noise(18)*3))*.35
 if name=='Concrete':n-=((np.sin(X*.05+noise(8)*4)>.997)&(noise(12)>.45))*.18
 if name=='Duct':n=n*.65+noise(50)*.35
 base=np.array(color)[None,None,:]*(.6+n[:,:,None]*.8)
 png('T_'+name,base);png('T_'+name+'_R',np.clip(.5+n*.35,0,1))
 dx=(np.roll(n,-1,1)-np.roll(n,1,1))*(.8 if name!='Wood' else 1.6);dy=(np.roll(n,-1,0)-np.roll(n,1,0))*.8
 normal=np.stack((-dx,-dy,np.ones_like(n)),axis=2);normal/=np.linalg.norm(normal,axis=2)[:,:,None];png('T_'+name+'_N',normal*.5+.5)
(OUT/'asset_build.json').write_text(json.dumps(report,indent=2));print('WAREHOUSE_ART_BUILT',json.dumps(report))
