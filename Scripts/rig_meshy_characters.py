"""Blender 4.5 background rig build. Keeps original Meshy imports unchanged.

Fit a duplicate mannequin to the Meshy neutral pose, interpolate its skin
weights, then bake the fitted bind pose back to the original animation rig.
"""
import bpy, json
from pathlib import Path
from mathutils import Vector, Matrix

PROJECT=Path(__file__).resolve().parents[1]
WORK=PROJECT/'Saved/RiggingQA'
OUTPUT=PROJECT/'Art/RiggedCharacters'
OUTPUT.mkdir(parents=True,exist_ok=True)
report=[]

def active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True);bpy.context.view_layer.objects.active=obj

def descendants(bone, ancestor):
    return bone.name==ancestor or any(p.name==ancestor for p in bone.parent_recursive)

def segment_map(old_a,old_b,new_a,new_b):
    rotation=(old_b-old_a).rotation_difference(new_b-new_a).to_matrix().to_4x4()
    # Preserve bone scale to keep animation translations compatible.
    return Matrix.Translation(new_a)@rotation@Matrix.Translation(-old_a)

for label in ['Spy','Merc']:
    bpy.ops.wm.open_mainfile(filepath=str(WORK/(label+'_optimized.blend')))
    mesh=bpy.data.objects[label]
    rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    reference=bpy.data.objects['SKM_Manny_Simple_LOD0']
    # Unreal FBX has a 0.01 scale on its parent LOD group. Preserve world
    # transforms before removing those containers, then bake into meter units.
    rig_world=rig.matrix_world.copy();reference_world=reference.matrix_world.copy()
    rig.parent=None;rig.matrix_world=rig_world
    reference.parent=None;reference.matrix_world=reference_world
    for obj in list(bpy.context.scene.objects):
        if obj not in [mesh,rig,reference]:bpy.data.objects.remove(obj,do_unlink=True)
    active(rig);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    active(reference);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    active(mesh);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    fitted=rig.copy();fitted.data=rig.data.copy();bpy.context.collection.objects.link(fitted)
    fitted.name='FittedRig'
    reference.parent=None
    for mod in reference.modifiers:
        if mod.type=='ARMATURE':mod.object=fitted
    targets={b.name:b.matrix_local.copy() for b in rig.data.bones}
    for side,sign in [('l',1),('r',-1)]:
        shoulder=Vector((sign*.190,.035,1.445))
        elbow=Vector((sign*.315,.035,1.205))
        wrist=Vector((sign*(.393 if label=='Spy' else .385),-.04 if label=='Spy' else -.06,.965))
        old_s=rig.data.bones['upperarm_'+side].head_local
        old_e=rig.data.bones['lowerarm_'+side].head_local
        old_w=rig.data.bones['hand_'+side].head_local
        upper=segment_map(old_s,old_e,shoulder,elbow)
        lower=segment_map(old_e,old_w,elbow,wrist)
        hand=Matrix.Translation(wrist)@lower.to_quaternion().to_matrix().to_4x4()@Matrix.Translation(-old_w)
        for b in rig.data.bones:
            if descendants(b,'hand_'+side):transform=hand
            elif descendants(b,'lowerarm_'+side):transform=lower
            elif descendants(b,'upperarm_'+side):transform=upper
            else:continue
            targets[b.name]=transform@b.matrix_local
    for bone in fitted.pose.bones:
        bone.matrix=targets[bone.name]
        bpy.context.view_layer.update()
    active(reference)
    for mod in list(reference.modifiers):
        if mod.type=='ARMATURE':bpy.ops.object.modifier_apply(modifier=mod.name)
    active(fitted);bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
    active(mesh)
    transfer=mesh.modifiers.new('Transfer mannequin skin weights','DATA_TRANSFER')
    transfer.object=reference;transfer.use_vert_data=True;transfer.data_types_verts={'VGROUP_WEIGHTS'}
    transfer.vert_mapping='POLYINTERP_NEAREST'
    transfer.layers_vgroup_select_src='ALL';transfer.layers_vgroup_select_dst='NAME'
    bpy.ops.object.datalayout_transfer(modifier=transfer.name)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    deform=mesh.modifiers.new('Bake matching animation bind pose','ARMATURE');deform.object=fitted
    for bone in fitted.pose.bones:
        bone.matrix=rig.data.bones[bone.name].matrix_local.copy()
        bpy.context.view_layer.update()
    active(mesh);bpy.ops.object.modifier_apply(modifier=deform.name)
    bpy.ops.object.vertex_group_limit_total(limit=4)
    bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    # Fill any isolated unweighted vertices rather than leaving them at origin.
    fallback=mesh.vertex_groups.get('pelvis') or mesh.vertex_groups.new(name='pelvis')
    unweighted=[v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups)<.0001]
    if unweighted:fallback.add(unweighted,1.,'REPLACE')
    deform=mesh.modifiers.new('Runtime skeleton','ARMATURE');deform.object=rig
    mesh.parent=rig;mesh.matrix_parent_inverse=rig.matrix_world.inverted()
    height=max(v.co.z for v in mesh.data.vertices)-min(v.co.z for v in mesh.data.vertices)
    if not 1.6<height<2.1:raise RuntimeError('Invalid rigged mesh height '+str(height))
    bpy.data.objects.remove(reference,do_unlink=True);bpy.data.objects.remove(fitted,do_unlink=True)
    # Export a centimeter rig with unit object scale. A meter-scene FBX puts
    # scale 100 on the root node, which multiplies Unreal animation tracks.
    world=mesh.matrix_world.copy();mesh.parent=None;mesh.matrix_world=world
    active(rig);rig.scale*=100;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    active(mesh);mesh.scale*=100;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mesh.parent=rig;mesh.matrix_parent_inverse=rig.matrix_world.inverted()
    bpy.context.scene.unit_settings.system='METRIC'
    bpy.context.scene.unit_settings.scale_length=.01
    rig.name='root';mesh.name='SK_'+label
    active(mesh);rig.select_set(True)
    target=OUTPUT/(label+'_rigged.fbx')
    bpy.ops.export_scene.fbx(filepath=str(target),use_selection=True,object_types={'ARMATURE','MESH'},
        add_leaf_bones=False,use_armature_deform_only=False,bake_anim=False,mesh_smooth_type='FACE',
        use_mesh_modifiers=True,axis_forward='-Y',axis_up='Z',path_mode='AUTO',armature_nodetype='ROOT')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT/(label+'_rigged.blend')))
    info={'label':label,'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),
          'vertices':len(mesh.data.vertices),'bones':len(rig.data.bones),'unweighted_before_fill':len(unweighted),
          'max_influences':max(len(v.groups) for v in mesh.data.vertices),'fbx':str(target)}
    report.append(info);print('RIG_BUILT',json.dumps(info),flush=True)
(OUTPUT/'rig_build_report.json').write_text(json.dumps(report,indent=2))
