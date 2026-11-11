"""Project-scoped native MCP tools; no arbitrary code or filesystem endpoints."""
import json
from pathlib import Path
import unreal
import toolset_registry

@unreal.uclass()
class StealthProjectTools(unreal.ToolsetDefinition):
    """Inspect the stealth prototype and run bounded development playtests."""
    @toolset_registry.tool_call
    @staticmethod
    def identity() -> str:
        """Read the project, loaded map and selection before editor operations."""
        level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_selected_level_actors()
        return json.dumps({'project':unreal.Paths.get_project_file_path(),'world':world.get_path_name(),'selected':[a.get_name() for a in actors]})
    @toolset_registry.tool_call
    @staticmethod
    def runtime_report() -> str:
        """Read actual role, health, match and traversal state across all PIE worlds."""
        return unreal.SPDiagnostics.runtime_report()
    @toolset_registry.tool_call
    @staticmethod
    def exercise(player_index: int, action: str) -> str:
        """Request an allowlisted editor test action on the owning player client.

        Args:
            player_index: Player join order, 0 through 3.
            action: place_ledge, place_vault, place_terminal, place_open, traverse,
                drop, hack, release, fire, role, crouch, nightvision, damage,
                expire, near_complete, network_lag, network_reset, vent_review_camera,
                review_slow, review_freeze, review_normal or review_player_view.
        """
        return unreal.SPDiagnostics.exercise(player_index,action)
    @toolset_registry.tool_call
    @staticmethod
    def configure_playtest(clients: int) -> str:
        """Configure the next in-process PIE session, either solo or 2v2.

        Args:
            clients: 1 for practice or 4 for competitive network validation.
        """
        if clients not in (1,4): raise ValueError('Use 1 or 4 clients')
        settings=unreal.get_default_object(unreal.load_class(None,'/Script/UnrealEd.LevelEditorPlaySettings'))
        settings.set_editor_property('PlayNumberOfClients',clients)
        settings.set_editor_property('RunUnderOneProcess',True)
        settings.set_editor_property('PlayNetMode',unreal.PlayNetMode.PIE_STANDALONE if clients==1 else unreal.PlayNetMode.PIE_LISTEN_SERVER)
        settings.set_editor_property('NewWindowWidth',640)
        settings.set_editor_property('NewWindowHeight',360)
        return str(clients)+' PIE clients configured'
    @toolset_registry.tool_call
    @staticmethod
    def save_project() -> bool:
        """Save dirty project maps and assets before a bulk operation or shutdown."""
        return unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
    @toolset_registry.tool_call
    @staticmethod
    def prepare_assets() -> str:
        """Run the fixed, version-controlled project asset bootstrap script."""
        script=Path(unreal.Paths.project_dir())/'Scripts'/'bootstrap_editor.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Project asset bootstrap completed'

    @toolset_registry.tool_call
    @staticmethod
    def import_merc_utility() -> str:
        """Import the fixed original heavy merc rifle and grip clips; PIE stopped."""
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_merc_utility.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Merc utility rifle imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def import_equipment() -> str:
        """Import the fixed project equipment build and validate its saved assets."""
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None: raise RuntimeError('Stop PIE before importing')
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_equipment.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Equipment imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def import_camera_assets() -> str:
        """Create the fixed original camera audio and gas material with PIE stopped."""
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None: raise RuntimeError('Stop PIE before importing')
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_camera_assets.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Camera assets imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def import_grab_animations() -> str:
        """Import fixed original paired grab clips and finisher audio with PIE stopped."""
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None: raise RuntimeError('Stop PIE before importing')
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_grab_animations.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Grab animations imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def import_specialty_animations() -> str:
        """Import only the five original specialty clips; preserve base assets and sounds."""
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None: raise RuntimeError('Stop PIE first')
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_grab_animations.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__','SPECIALTY_ONLY':True})
        return 'Specialty animations imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def repair_character_presentation() -> str:
        """Import only the repaired derived spy face and merc gripping poses; PIE stopped."""
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None: raise RuntimeError('Stop PIE first')
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_presentation_repair.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Repaired spy face and rifle grips imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def prepare_specialty_fx() -> str:
        """Update the existing original blast material for warehouse exposure; PIE stopped."""
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_specialty_fx.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Specialty blast material saved'

    @toolset_registry.tool_call
    @staticmethod
    def prepare_warehouse() -> str:
        """Import original warehouse art/actions and save the new Warehouse map; PIE stopped."""
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_warehouse.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Warehouse assets and map imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def prepare_recovery_fx() -> str:
        """Create and save the fixed original recovery electrical material; PIE stopped."""
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_recovery_fx.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Recovery electricity material saved'

    @toolset_registry.tool_call
    @staticmethod
    def prepare_vent_entry() -> str:
        """Import only the fixed vent mantle/crawl clips and refresh their saved map preview."""
        script=Path(unreal.Paths.project_dir())/'Scripts'/'import_vent_entry.py'
        exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__'})
        return 'Vent mantle and matching crawl imported and saved'

    @toolset_registry.tool_call
    @staticmethod
    def open_map(map_name: str) -> str:
        """Open a fixed project map with PIE stopped: Warehouse or Prototype QA."""
        if map_name not in ('Warehouse','Prototype'): raise ValueError('Unknown project map')
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None: raise RuntimeError('Stop PIE first')
        if not unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level('/Game/Maps/'+map_name): raise RuntimeError('Map did not load')
        return map_name+' loaded'
