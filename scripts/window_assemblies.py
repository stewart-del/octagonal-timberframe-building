# TIMESTAMP START 2026-11-05T17:09:28+00:00 | REVISION R000057
"""Published purchased window envelopes, separate illustrative display surfaces.

Factory rail sections, glazing thickness and fourbar hardware are not public
machining CAD. Keep those references distinct from the conservative whole-unit
collision envelope and from the real purchased-unit/screen takeoff.
"""
from pathlib import Path
import copy,gzip,hashlib,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];FIXTURE=ROOT/'scripts/fixtures/window-assembly-inputs.json.gz';I=.0254

def inputs():
 raw=FIXTURE.read_bytes();data=json.loads(gzip.decompress(raw));assert data['schema']=='real-awning-window-inputs-1';result={}
 for key,r in data['files'].items():
  assert hashlib.sha256(r['content'].encode()).hexdigest()==r['content_sha256'],('Changed window input',key);result[key]=json.loads(r['content'])
 return result

def build():
 data=inputs();components=data['components'];opening=data['opening'];reference_by_id={r['id']:r for r in components['components']};poses={r['unitId']:r for r in opening['units']};parts=[]
 for unit in components['units']:
  uid=unit['id'];reference=reference_by_id[uid+'-FRAME'];pose=poses[uid];B=np.asarray(pose['localFrame3x4'])[:,:3];origin=np.asarray(pose['localFrame3x4'])[:,3];front=unit['full_depth_local_bounds_m'][1];outer=unit['published']['frame'];sash=unit['published']['sash'];glass=unit['published']['visible_glass'];screen=unit['published']['screen'];center_y=(unit['ro'][1]+unit['ro'][3])/2;role='cupolaWindow' if unit['level']=='cupola' else 'wall'
  spec={'manufacturer':'Andersen','productFamily':'A-Series awning','partNumber':unit['model'],'frameDimensionsIn':outer,'frameApproxDepthIn':reference['publishedApproxOverallDepthIn'],'sashDimensionsIn':sash,'publishedVisibleGlassIn':glass,'screenDimensionsIn':screen,'sourceURL':reference['sourceURL'],'profileStatus':'Real purchased unit dimensions and conservative outside envelope. Display rails/glazing are planar illustrations; factory sections, glass thickness and articulated hinge trajectory are not fabrication CAD.'}
  common={'unitId':uid,'parentId':uid,'windowSpec':spec,'windowDisplayRole':role,'material':'Purchased Andersen A-Series awning assembly','is_timber':False,'constructionPhase':'Cupola windows' if unit['level']=='cupola' else 'Main windows after siding','group':'purchased_windows','geometryProfile':spec['profileStatus'],'publishedDimensionsIn':outer+[reference['publishedApproxOverallDepthIn']]}
  parts.append({**common,'id':uid,'name':unit['model']+' awning window · '+unit['face'],**copy.deepcopy(reference['externalEnvelopeMesh']),'displayRole':role,'collisionEnvelopeOnly':True,'isPurchasedAssemblyProxy':True,'product':spec,'displayOpacity':.05})
  def rectangle(width_height,normal):
   w,h=np.asarray(width_height)*I/2;return [[-w,center_y-h,normal],[w,center_y-h,normal],[w,center_y+h,normal],[-w,center_y+h,normal]]
  def display(suffix,vertices,triangles,name,*,moving=False,opacity=1.,color=None,count=False,dimensions=None):
   local=np.asarray(vertices,float);p={**common,'id':uid+suffix,'name':name,'referenceAssemblyId':uid,'displayRole':'reference','windowReference':True,'isPhysicalPart':False,'vertices':(local@B.T+origin).tolist(),'triangles':triangles,'volumeM3':0.,'displayOpacity':opacity,'color':color or [.86,.86,.82],'windowMotion':'sash' if moving else 'fixed','windowLocalVertices':local.tolist(),'windowFrame3x4':pose['localFrame3x4'],'windowPivotLocalM':pose['displayPivotLocalM'],'maximumIllustrativeAngleDegrees':pose['maximumIllustrativeAngleDegrees'],'manufacturerMaximumAngle':None,'countAsPurchasedItem':count,'publishedDimensionsIn':dimensions or common['publishedDimensionsIn']}
   if count:
    p['windowSpec']={**spec,'partNumber':unit['model']+' conventional insect screen (order by Product ID)','sourceURL':reference_by_id[uid+'-SCREEN']['sourceURL'],'installation':'One separately purchased OEM screen per window; finish and Product ID confirm the order. Factory fabric/rail manufacturing cuts are unavailable.'};p['material']='OEM insect-screen assembly';p['product']=p['windowSpec']
   parts.append(p)
  def border(outer_size,inner_size,n):
   return rectangle(outer_size,n)+rectangle(inner_size,n),[[k,(k+1)%4,4+(k+1)%4] for k in range(4)]+[[k,4+(k+1)%4,4+k] for k in range(4)]
  v,t=border(outer,sash,front);display('-DISPLAY-FRAME',v,t,unit['model']+' published frame outline')
  v,t=border(sash,glass,front);display('-SASH',v,t,unit['model']+' opening sash reference',moving=True)
  display('-GLASS',rectangle(glass,front),[[0,1,2],[0,2,3]],unit['model']+' published visible glass reference',moving=True,opacity=.23,color=[.44,.66,.71],dimensions=glass)
  # Screen is a bought assembly, not fabricated mesh/rail section geometry.
  display('-SCREEN',rectangle(screen,unit['full_depth_local_bounds_m'][0]),[[0,1,2],[0,2,3]],unit['model']+' OEM insect screen',opacity=.12,color=[.34,.39,.39],count=True,dimensions=screen)
 return {'parts':parts,'opening':opening,'componentReferences':components,'report':{'status':'PASS','scope':'Published purchased-unit/screen dimensions and explicitly illustrative planar appearance/opening data. No factory machining, maximum-angle or installed airtighness certification.','fixture_sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'purchased_windows':14,'purchased_screens':14,'whole_unit_collision_envelopes':14,'illustrative_display_surfaces':56,'service_part_references':182,'factory_profiles_available':False}}
# TIMESTAMP END 2026-11-05T17:09:28+00:00 | REVISION R000057
