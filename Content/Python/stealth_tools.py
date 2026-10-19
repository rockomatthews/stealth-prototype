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
                expire, near_complete, network_lag or network_reset.
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
