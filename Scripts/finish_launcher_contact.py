"""Add launcher-only grip correctives after the paired hold/cloth bake."""
from pathlib import Path
P=Path(__file__).resolve().parents[1]
p=P/'Scripts/finish_contact_correctives.py'
exec(compile(p.read_text(),str(p),'exec'),{'__file__':str(p),'CASE_OVERRIDE':[('Launcher',P/'Art/Equipment/SpyEquipmentBase.blend',P/'Art/Equipment/SpyEquip.blend',22,P/'Art/Equipment/SpyEquipment.fbx')]})
