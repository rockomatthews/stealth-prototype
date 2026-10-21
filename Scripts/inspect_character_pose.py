"""Read-only live PIE pose diagnostics, executed from the Unreal Python console."""
import unreal,json,math
from pathlib import Path
report=[]
for world in unreal.EditorLevelLibrary.get_pie_worlds(False):
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world,unreal.SPCharacter):
        mesh=actor.get_component_by_class(unreal.SkeletalMeshComponent)
        bounds=unreal.SystemLibrary.get_component_bounds(mesh)
        head=mesh.get_socket_transform('head')
        position=actor.get_actor_location()
        distance=math.sqrt(sum((getattr(head.translation,a)-getattr(position,a))**2 for a in ['x','y','z']))
        report.append({'actor':actor.get_path_name(),'transform':str(mesh.get_socket_transform('')),
            'bounds':[str(x) for x in bounds],'head':str(mesh.get_socket_transform('head')),
            'pelvis':str(mesh.get_socket_transform('pelvis')),
            'scale':str(mesh.get_editor_property('relative_scale3d')),
            'owner_no_see':mesh.get_editor_property('owner_no_see')})
        report[-1]['head_distance_cm']=distance
        report[-1]['head_scale']=[head.scale3d.x,head.scale3d.y,head.scale3d.z]
Path(unreal.Paths.project_saved_dir(),'RiggingQA/live_pose.json').write_text(json.dumps(report,indent=2))
unreal.log('CHARACTER_POSE '+json.dumps(report))
for item in report:
    if item['head_distance_cm']>250 or max(item['head_scale'])>2:
        raise RuntimeError('Animated rig has invalid scale: '+item['actor'])
