"""One reusable symbolic green aid and one owner-reference black display assembly."""
import copy
from central_support import consolidate_fixture,FIXTURE_ID,LEGACY_IDS,SPAN_IN
RETIRED_SPACERS=[f'M-SP{k}' for k in range(1,8)]
def consolidate_aids(parts):
 out=[]
 for old in parts:
  if old['id'] in RETIRED_SPACERS:continue
  p=copy.deepcopy(old) if old['id']=='M-SP0' else old
  if p['id']=='M-SP0':
   p.update(temporary=True,name='Reusable green construction spacer · symbolic geometry',assembly_id='GREEN-AID',assembly_quantity=1)
   p['notes']=['One reusable construction aid, not eight permanently installed spacers. Its existing shape remains symbolic; the separate black central-support diagram does not establish the green aid shape.','Position, thickness, terminals, fastening, erection capacity and removal sequence are unresolved. No permanent structural load credit.']
  out.append(p)
 return consolidate_fixture(out)

def update_metadata(d):
 history=d.setdefault('component_id_history',{})
 history.update({old:'M-SP0' for old in RETIRED_SPACERS})
 history.update({old:FIXTURE_ID for old in LEGACY_IDS})
 for key in ['r01','source_dimensions']:
  d[key]['metal_count']=2;d[key]['central_support_overall_span_in']=SPAN_IN
  d[key]['central_support_status']='One temporary display assembly; fabrication, fastening, weld and erection design unresolved.'
 for g in d['groups']:
  if g['id']=='metal_spacers':g.update(label='One reusable green construction spacer · symbolic',default_visible=False)
  if g['id']=='temporary_fixture':g.update(label='Temporary central support · 8 L straps · display only',default_visible=False,assembly_count=1)

def update_materials(data):
 for g in data['groups']:
  if g['family']=='metal_spacers':g.update(member_ids=['M-SP0'],representative_id='M-SP0',quantity=1,label='One reusable construction spacer')
  if g['family']=='temporary_fixture':g.update(member_ids=[FIXTURE_ID],representative_id=FIXTURE_ID,quantity=1,assembly_quantity=1,label='One temporary welded support display assembly · 8 L straps · 24 holes',status='Display reference only; no cut drilling weld fastening or erection specification',method='Owner reference outline with explicitly illustrative thickness hole positions and elevation')
