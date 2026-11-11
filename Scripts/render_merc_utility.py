"""Studio views of the actual utility-rifle mesh; no gameplay tests."""
import bpy,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];OUT=P/'Art/UtilityRifle/Review';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(P/'Art/UtilityRifle/MercUtility.blend'));scene=bpy.context.scene
scene.frame_set(1);rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.scale=(.01,)*3
scene.unit_settings.scale_length=1
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
scene.view_settings.exposure=-1.7;scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.world=bpy.data.worlds.new('Studio world');scene.world.color=(.22,.22,.22)
def material(name,color,rough):
 m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;return m
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.111));floor=bpy.context.object;floor.data.materials.append(material('Studio graphite',(.055,.063,.072),.65))
def point(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,loc,power,size,color):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color;o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=loc;point(o,(.08,0,.04))
light('Large soft key',(.15,-.8,1.3),150,1.3,(.86,.92,1));light('Warm edge',(-.35,.5,.9),190,1,(1,.86,.69));light('Front strip',(1,-.1,.55),65,.7,(.8,.9,1));light('Soft fill',(-.4,-.6,.25),25,.9,(1,1,1))
data=bpy.data.cameras.new('Studio camera');cam=bpy.data.objects.new('Studio camera',data);scene.collection.objects.link(cam);scene.camera=cam;data.lens=60
for o in scene.objects:
 if o.type=='MESH' and o!=floor:
  for f in o.data.polygons:f.use_smooth=False
for name,loc,target,ortho in [('hero',(1.08,-1.45,.72),(.085,-.02,.06),None),('rear-utility',(-.9,1.05,.55),(.02,-.02,.07),None),('right',(.085,-2,.075),(.085,-.02,.075),1.02),('left',(.085,2,.075),(.085,-.02,.075),1.02),('front',(1.7,-.12,.16),(.25,-.02,.07),.65)]:
 cam.location=loc;point(cam,target);data.type='ORTHO' if ortho else 'PERSP'
 if ortho:data.ortho_scale=ortho
 scene.render.filepath=str(OUT/('warden-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('WARDEN_STUDIO_RENDERED')
