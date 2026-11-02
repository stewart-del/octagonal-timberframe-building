"""Union display sectors into one panel assembly, not a commercial sheet schedule."""
import copy, hashlib, json
import numpy as np
import manifold3d as m
PANEL_ID='PLY'
LEGACY_IDS=[f'PLY{k}' for k in range(8)]
def solid(p):
 return m.Manifold(m.Mesh64(np.asarray(p['vertices'],dtype=float),np.asarray(p['triangles'],dtype=np.uint64))).set_tolerance(1e-9)
def consolidate(parts):
 sectors=[p for p in parts if p['group']=='cupola_plywood']
 if len(sectors)==1 and sectors[0]['id']==PANEL_ID:return parts
 assert {p['id'] for p in sectors}==set(LEGACY_IDS)
 union=m.Manifold()
 for p in sectors:union=union+solid(p)
 # The fitted sectors form a convex outline; hull removes internal radial seams.
 hull=m.Manifold.hull_points(np.asarray([v for p in sectors for v in p['vertices']]))
 assert (hull-union).volume()<1e-10 and (union-hull).volume()<1e-10, 'Nonconvex cutout: do not fill it'
 union=hull
 assert str(union.status())=='Error.NoError' and len(union.decompose())==1
 assert abs(union.volume()-sum(solid(p).volume() for p in sectors))<1e-10
 mesh=union.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];lo=v.min(0);hi=v.max(0);c=(lo+hi)/2
 p=copy.deepcopy(sectors[0]);p.update(id=PANEL_ID,name='Continuous octagonal cupola panel assembly · 1/2 in',vertices=v.tolist(),triangles=mesh.tri_verts.tolist(),faces=mesh.tri_verts.tolist(),center=c.tolist(),label_position=c.tolist(),exploded_offset=[0,6.2,0],axis_start=[float(lo[0]),float(c[1]),0],axis_end=[float(hi[0]),float(c[1]),0],axis_direction=[1,0,0],reference_end_faces=[],joint_cut_faces=[],geometry_planes_inches=[],label_lines=[PANEL_ID,'PANEL ASSEMBLY','½ IN THICK'],label_short=[PANEL_ID,'ASSEMBLY','SEAMS TBD'])
 p['legacy_ids']=LEGACY_IDS
 p['notes']=['One continuous panel representation replaces PLY0–PLY7 display sectors; outline, elevation, thickness and timber cutouts are preserved.','This assembly is not a claim that one commercial sheet can span it. Fabrication seams, sheet sizing, grade, blocking, fasteners and diaphragm capacity remain undesigned.']
 p['fit_geometry']['volume_m3']=union.volume()
 length=float(hi[0]-lo[0]);width=float(hi[2]-lo[2]);depth=float(hi[1]-lo[1])
 p['dimensions']={'length_m':length,'width_m':width,'depth_m':depth,'length_ft':length/.3048,'width_in':width/.0254,'depth_in':depth/.0254,'length_display':f'{length/.0254:.3f} in overall','section_display':'Octagonal assembly × ½ in','status':'Overall bounds, not stock or a sheet-cut schedule.'}
 p['nominal_dimensions']=p['dimensions'].copy();p['fitted_axial_extent_inches']=length/.0254
 p['stock_frame']={'axis':[1,0,0],'width':[0,0,-1],'depth':[0,1,0]}
 p['angles']={k:(0 if k in ['axis_inclination_deg','azimuth_deg'] else None) for k in p['angles']}
 p['source_geometry_metadata']={'revision':'continuous-panel-display','legacy_ids':LEGACY_IDS,'status':'Union of existing sector solids; no fabrication seams inferred.'}
 p['geometry_planes_inches_status']='Assembly union mesh is authoritative; old sector division planes retired.'
 result=[]
 for old in parts:
  if old['group']!='cupola_plywood':result.append(old)
  elif old['id']==LEGACY_IDS[0]:result.append(p)
 return result

def migrate(root):
 path=root/'src/model-data.json';d=json.loads(path.read_text());d['parts']=consolidate(d['parts'])
 from construction_aids import consolidate_aids,update_metadata,update_materials
 d['parts']=consolidate_aids(d['parts'])
 d.setdefault('component_id_history',{}).update({old:PANEL_ID for old in LEGACY_IDS})
 update_metadata(d)
 for g in d['groups']:g['count']=sum(p['group']==g['id'] for p in d['parts'])
 for key in ['r01','source_dimensions']:d[key]['surface_count']=8;d[key]['sheet_goods_count']=1
 d['notes']=[n.replace('Eight half-inch horizontal plywood sectors are separate sheet goods.','One continuous half-inch horizontal plywood assembly represents sheet goods; fabrication seams remain undesigned.') for n in d['notes']]
 path.write_text(json.dumps(d,separators=(',',':'))+'\n');sha=hashlib.sha256(path.read_bytes()).hexdigest()
 for filename,key in [('material-groups.json','source_sha256'),('cavity-data.json','source_model_sha256'),('load-review-data.json','source_model_sha256')]:
  path=root/'src'/filename;data=json.loads(path.read_text());data[key]=sha
  if filename=='material-groups.json':
   data['item_count']=len(d['parts'])
   update_materials(data)
   for g in data['groups']:
    if any(i in LEGACY_IDS for i in g['member_ids']):g.update(member_ids=[PANEL_ID],representative_id=PANEL_ID,quantity=1,label='Continuous cupola panel assembly; fabrication seams undesigned')
  path.write_text((json.dumps(data,indent=2) if filename!='cavity-data.json' else json.dumps(data,separators=(',',':')))+'\n')
 path=root/'docs/joinery-verification.json';data=json.loads(path.read_text());data['source_model_sha256']=sha;data['sheet_goods_count']=1;path.write_text(json.dumps(data,indent=2)+'\n')
 return sha
if __name__=='__main__':
 from pathlib import Path
 print(migrate(Path(__file__).resolve().parents[1]))
