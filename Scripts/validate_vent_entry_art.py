"""Validate actual Blender FK supports and the mantle/crawl pose handoff."""
import json,math
from pathlib import Path
P=Path(__file__).resolve().parents[1];samples=json.loads((P/'Art/Actions/vent-entry-contacts.json').read_text());handoff=json.loads((P/'Art/Actions/vent-entry-handoff.json').read_text());checks=[]
for bone,a,b,forward,x in [('hand_r',.5,1.75,60,-18),('hand_l',.5,1.4,60,18),('hand_l',1.75,2.2,115,18),('hand_r',2.15,3.2,165,-18)]:
 errors=[math.sqrt((s[bone]['x']-x)**2+(s[bone]['forward']-forward)**2+(s[bone]['z']-790)**2) for s in samples if a<=s['time']<=b];assert errors and max(errors)<2.5,(bone,a,b,max(errors));checks.append({'contact':bone,'start':a,'end':b,'max_error_cm':max(errors)})
assert handoff['max_position_cm']<.01 and handoff['max_rotation_degrees']<.01,handoff
assert min(s['pelvis']['z'] for s in samples if s['time']<1.4)>720,'Pelvis drops before pulling up'
assert max(s['head']['z']+19 for s in samples if s['head']['forward']>60)<885,'Headgear clips ceiling'
knee=[s['calf_r'] for s in samples if 1.4<=s['time']<=2.1];assert all(abs(s['z']-790)<2 and abs(s['forward']-68)<2 for s in knee),'Planted knee slides'
result={'hand_contacts':checks,'handoff':handoff,'supported_knee':True,'ceiling_clear':True,'no_initial_body_drop':True};(P/'Art/Actions/vent-entry-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
