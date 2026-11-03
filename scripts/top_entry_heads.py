# TIMESTAMP START 2026-11-02T20:42:47-05:00 | REVISION R004871
# Restore the original six-inch cupola and remove the R004869 four-inch trial.
"""Representative top-entry J/R head proposal, separate from released V13.
Chosen dimensions describe a new/raw-stock design, not a repair of cut timbers.
No load/connection capacity or safe assembly/erection certification.
"""
from pathlib import Path
import copy,hashlib,itertools,json,sys
import numpy as np
import manifold3d as m
from step_lap import I,solid,mesh,resolved,original_stock,inside_band,contacts,section,volume_centroid,close_bounds
R=Path(__file__).resolve().parents[1]
def vertical_sweep(shape,height):
 # Exact union-of-translations construction: any newly occupied point crosses
 # a boundary triangle during translation. Union initial solid and each full
 # triangle prism; unlike a convex hull of the entire member this preserves
 # concave notches and does not create false swept material.
 q=mesh(shape);v=np.asarray(q['vertices']);pieces=[shape]
 for tri in q['triangles']:
  points=v[tri];prism=m.Manifold.hull_points(np.vstack([points,points+[0,height,0]]))
  if prism.volume()>1e-15:pieces.append(prism)
 assert all(str(p.status())=='Error.NoError' for p in pieces)
 return pieces # Check every covering prism directly; avoid a fragile coplanar union.

def section_polygons(shape,origin,width,depth,axis):
 rot=np.array([width,depth,axis]);tf=np.column_stack((rot,-rot@origin))
 return [(np.asarray(p)/I).tolist() for p in shape.transform(tf.tolist()).slice(0).to_polygons()]

def build_representative(data,sha):
 P={p['id']:p for p in data['parts']};S={k:solid(p) for k,p in P.items() if p['is_timber']};Q=S.copy()
 hip='R0';names=['J0-0','J7-2'];rp=P[hip];ro=np.array(rp['axis_end']);rd=np.array(rp['stock_frame']['depth']);rw=np.array(rp['stock_frame']['width']);ra=np.array(rp['stock_frame']['axis']);rs=original_stock(rp)
 penetration=2.;seat_drop=4.;floor_d=rp['dimensions']['depth_in']/2-seat_drop;floor=float(rd@ro+floor_d*I)
 tongues={};extended_stocks={};cutters={};upper=[]
 for name in names:
  jp=P[name];extended=copy.deepcopy(jp)
  for plane in extended['geometry_planes_inches']:
   if plane['end']=='B':plane['constant']+=penetration
  stock=original_stock(extended);extended_stocks[name]=stock
  # Full nominal J section is preserved through the short extended end, then
  # given an inclined lower landing parallel to the main hip's original top.
  side=1 if np.array(jp['axis_end'])@rw>0 else -1
  nose=stock^rs.translate(tuple(side*rw*.01*I))
  nose=nose.trim_by_plane(tuple(rd),floor)
  nose=inside_band(nose,side*rw,(4-penetration)*I,4.01*I)
  nose=resolved(nose);assert nose.volume()>0
  outside=S[name].trim_by_plane(tuple(side*rw),4*I)
  Q[name]=resolved(outside+nose)
  nose=resolved(nose^rs);tongues[name]=nose
  assert str(Q[name].status())=='Error.NoError' and len(Q[name].decompose())==1,(name,str(Q[name].status()),len(Q[name].decompose()),outside.volume()/I**3,nose.volume()/I**3,(outside^nose).volume()/I**3,contacts(outside,nose))
  assert (Q[name]-stock).volume()<1e-10,(name,'outside extended stock')
  nv=np.array(mesh(nose)['vertices']);sweep=m.Manifold.hull_points(np.vstack([nv,nv+[0,24*I,0]])).set_tolerance(1e-9)
  cutters[name]=resolved(sweep^rs)
  upper.append({'owner':name,'receiver':hip,'side_sign':side,'stock_extension_along_J_axis_in':penetration/abs(np.array(jp['stock_frame']['axis'])@rw),'proposed_nose':dict(id=name+'-top-entry-nose',**mesh(nose)),'top_open_cutter':dict(id=name+'-top-entry-opening',**mesh(cutters[name]))})
 # Reconstitute only the old pair-of-heads region from an uncut R blank. This
 # is replacement/new-stock design, NOT gluing wood back into a cut member.
 # Radial window55..85in is clear of cupola head and all perimeter feet.
 repair=inside_band(rs,[1,0,0],55*I,85*I)
 restored=resolved(S[hip]+repair)
 Q[hip]=resolved(restored-cutters[names[0]]-cutters[names[1]])
 assert str(Q[hip].status())=='Error.NoError' and len(Q[hip].decompose())==1
 changed={hip,*names};overlaps=[];lost=[];neighbors=[]
 for a,b in itertools.combinations(Q,2):
  if not ({a,b}&changed) or not close_bounds(Q[a],Q[b]):continue
  inter=(Q[a]^Q[b]).volume()/I**3
  if inter>1e-6:overlaps.append({'a':a,'b':b,'volume_in3':inter})
  old=contacts(S[a],S[b]);new=contacts(Q[a],Q[b]);oa=sum(x['area_in2'] for x in old);na=sum(x['area_in2'] for x in new)
  if oa>.001 or na>.001:neighbors.append({'a':a,'b':b,'baseline_area_in2':oa,'proposed_area_in2':na,'proposed_faces':new})
  if oa>.01 and na<.01:lost.append({'a':a,'b':b})
 for v in upper:
  name=v['owner'];v['contact_faces']=contacts(Q[name],Q[hip]);v['vertical_translation_checks']=[]
  for lift in [0,.01,.125,.25,.5,1,2,4,8,12,24]:
   moved=Q[name].translate((0,lift*I,0));hits=[]
   for other,s in Q.items():
    if other==name or not close_bounds(moved,s):continue
    vol=(moved^s).volume()/I**3
    if vol>1e-6:hits.append({'member':other,'overlap_in3':vol})
   v['vertical_translation_checks'].append({'lift_in':lift,'interferences':hits})
  center=np.array(volume_centroid(tongues[name])['centroid_m']);o=ro+ra*((center-ro)@ra)
  v['named_R_section']={'origin_m':o.tolist(),'normal':ra.tolist(),'stock_area_in2':section(rs,o,ra),'V13_area_in2':section(S[hip],o,ra),'proposed_area_in2':section(Q[hip],o,ra)}
  v['bearing_faces']=[f for f in v['contact_faces'] if f['normal_on_rafter'][1]<-.01]
  v['minimum_hip_bottom_remaining_normal_in']=10-seat_drop
  v['remaining_gap_between_inner_end_planes_in']=8-2*penetration
  v['new_member_geometry']=[dict(id=k,**volume_centroid(Q[k])) for k in [name,hip]]
 # Continuous24in vertical sweep is tested against all modeled timbers,
 # including each released perimeter foot, not just sampled local head poses.
 sweep_checks=[]
 for name in names:
  swept=vertical_sweep(Q[name],24*I);hits=[];max_upper_bound=0.;prism_checks=0
  for other,shape in Q.items():
   if other==name:continue
   prism_overlaps=[]
   for prism in swept:
    if not close_bounds(prism,shape):continue
    prism_checks+=1;prism_overlaps.append(max(0.,(prism^shape).volume()/I**3))
   vol=sum(prism_overlaps);max_upper_bound=max(max_upper_bound,vol)
   if vol>1e-6:hits.append({'member':other,'summed_overlap_upper_bound_in3':vol})
  # TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
  sweep_checks.append({'member':name,'translation_world_m':[0,24*I,0],'method':'Initial solid plus every nonzero boundary-triangle vertical prism covers the continuous sweep within a1e-15m3 per-prism numerical cutoff. Sum of per-prism intersections bounds swept overlap from above; no coplanar union or sampled-path substitution.','covering_solids':len(swept),'prism_intersection_checks':prism_checks,'maximum_summed_overlap_upper_bound_in3':max_upper_bound,'discarded_prism_volume_bound_in3':len(mesh(Q[name])['triangles'])*1e-15/I**3,'maximum_total_overlap_bound_in3':max_upper_bound+len(mesh(Q[name])['triangles'])*1e-15/I**3,'interferences':hits,'scope':'Entire member against all112 modeled timbers. Roof cover/envelopes, tool access, lifting gear, tolerances and safe erection are not modeled.'})
  # TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
 samples=[]
 for radial in np.linspace(55,85,121):
  distance=(radial*I-ro[0])/ra[0];origin=ro+ra*distance
  samples.append({'radial_station_in':float(radial),'V13_area_in2':section(S[hip],origin,ra),'proposed_area_in2':section(Q[hip],origin,ra)})
 diagram_origin=np.array(upper[0]['named_R_section']['origin_m'])
 diagram_sections={'origin_m':diagram_origin.tolist(),'horizontal':'R transverse width inches','vertical':'R normal depth inches','stock':section_polygons(rs,diagram_origin,rw,rd,ra),'V13':section_polygons(S[hip],diagram_origin,rw,rd,ra),'candidate':section_polygons(Q[hip],diagram_origin,rw,rd,ra)}
 rec={'schema_version':'top-entry-head-proposal-1','source_model_sha256':sha,'status':'REPRESENTATIVE CONCEPT — NOT FABRICATION APPROVED','node':{'hip':hip,'side_members':names},'chosen_dimensions':{'J_nominal_section_in':[4,8],'R_nominal_section_in':[8,10],'side_normal_penetration_in':penetration,'seat_drop_normal_to_R_top_in':seat_drop,'R_original_stock_reconstitution_window_radial_inches':[55,85],'dimensions_basis':'Chosen trial geometry, not measured reference-image dimensions or approved structural proportions. Raw/longer J stock and uncut R blank required.'},'interfaces':upper,'geometry_audit':{'changed_member_ids':sorted(changed),'all_affected_timber_pairs':sum(bool({a,b}&changed) for a,b in itertools.combinations(Q,2)),'interferences':overlaps,'lost_neighbor_contacts':lost,'neighbors':neighbors,'capacity_checked':False,'continuous_vertical_sweeps':sweep_checks,'R_named_region_section_samples':samples,'minimum_sampled_R_section_in2':min(x['proposed_area_in2'] for x in samples)},'diagram_sections':diagram_sections,'baseline_parts':[P[k] for k in [hip,*names]],'proposed_parts':[dict(P[k],**{z:mesh(Q[k])[z] for z in ['vertices','triangles']}) for k in [hip,*names]],'limitations':['Top-entry and gravity bearing do not establish positive uplift retention, capacity, or safe erection.','Continuous24in vertical timber-only sweeps are geometric clearance checks, not a raising sequence, tolerance, tool-access or safe erection proof.','A replacement/new-stock design restores old mortise region before new cuts; not repair instructions for cut timber.','Released24 perimeter feet/axes/roof elevations stay unchanged.','The two ends intentionally do not meet; a4in central transverse gap remains.']}
 for p in rec['proposed_parts']:
  p['faces']=p['triangles'];p['fit_geometry']=dict(p['fit_geometry'],volume_m3=volume_centroid(Q[p['id']])['volume_m3']);p['cut_status']='REPRESENTATIVE TOP-ENTRY HEAD — NOT FABRICATION APPROVED';p['geometry_purpose']='representative top-entry trial, not the V13 head cut'
 return rec,Q,extended_stocks

def build_all(data,sha):
 rep,seed_shapes,seed_stocks=build_representative(data,sha)
 P={p['id']:p for p in data['parts']};S={k:solid(p) for k,p in P.items() if p['is_timber']};Q=S.copy();interfaces=[];stock_records={};isometry=[]
 for bay in range(8):
  angle=bay*45;theta=bay*np.pi/4;c=np.cos(theta);s=np.sin(theta);rot=np.array([[c,0,s],[0,1,0],[-s,0,c]])
  mapping={'R0':f'R{bay}','J0-0':f'J{bay}-0','J7-2':f'J{(bay-1)%8}-2'}
  for seed,target in mapping.items():
   expected=S[seed].rotate((0,angle,0));actual=S[target];err=((actual-expected).volume()+(expected-actual).volume())/I**3
   assert abs(err)<1e-6,(target,'V13 family not isometric',err)
   Q[target]=resolved(seed_shapes[seed].rotate((0,angle,0)))
   isometry.append({'seed':seed,'member':target,'rotation_deg':angle,'V13_symmetric_difference_in3':err})
   if target.startswith('J'):
    pp=copy.deepcopy(P[target])
    for plane in pp['geometry_planes_inches']:
     if plane['end']=='B':plane['constant']+=rep['chosen_dimensions']['side_normal_penetration_in']
    stock_records[target]=pp['geometry_planes_inches']
  for v in rep['interfaces']:
   owner=mapping[v['owner']];receiver=mapping[v['receiver']];faces=contacts(Q[owner],Q[receiver]);entry={'id':owner+'_'+receiver,'owner':owner,'receiver':receiver,'bay':bay,'seed_owner':v['owner'],'stock_extension_along_J_axis_in':v['stock_extension_along_J_axis_in'],'chosen_dimensions':rep['chosen_dimensions'],'contact_faces':faces,'bearing_area_in2':sum(f['area_in2'] for f in faces if f['normal_on_rafter'][1]<-.01),'nominal_contact_gap_m':Q[owner].min_gap(Q[receiver],.01),'baseline_parts':[copy.deepcopy(P[k]) for k in [receiver,owner]],'proposed_parts':[]}
   for label in ['proposed_nose','top_open_cutter']:
    entry[label]=dict(id=owner+'-'+label,**mesh(solid(v[label]).rotate((0,angle,0))))
   interfaces.append(entry)
 changed={k for k in Q if k.startswith(('J','R'))};overlaps=[];lost=[];neighbors=[];max_overlap=0.;checks=0
 for a,b in itertools.combinations(Q,2):
  if not ({a,b}&changed) or not close_bounds(Q[a],Q[b]):continue
  checks+=1;vol=max(0.,(Q[a]^Q[b]).volume()/I**3);max_overlap=max(max_overlap,vol)
  if vol>1e-6:overlaps.append({'a':a,'b':b,'overlap_in3':vol})
  old=contacts(S[a],S[b]);new=contacts(Q[a],Q[b]);oa=sum(x['area_in2'] for x in old);na=sum(x['area_in2'] for x in new)
  if oa>.001 or na>.001:neighbors.append({'a':a,'b':b,'V13_contact_area_in2':oa,'proposed_contact_area_in2':na,'proposed_faces':new})
  if oa>.01 and na<.01:lost.append({'a':a,'b':b,'old_area_in2':oa})
 sweep_checks=[];sweep_cache={}
 for entry in interfaces:
  name=entry['owner'];bay=entry['bay'];seed=entry['seed_owner']
  if seed not in sweep_cache:sweep_cache[seed]=vertical_sweep(seed_shapes[seed],24*I)
  cover=[p.rotate((0,bay*45,0)) for p in sweep_cache[seed]];hits=[];max_upper=0.;count=0
  for other,shape in Q.items():
   if other==name:continue
   values=[]
   for prism in cover:
    if not close_bounds(prism,shape):continue
    count+=1;values.append(max(0.,(prism^shape).volume()/I**3))
   amount=sum(values);max_upper=max(max_upper,amount)
   if amount>1e-6:hits.append({'member':other,'overlap_upper_bound_in3':amount})
  sweep_checks.append({'member':name,'lift_in':24,'covering_solids':len(cover),'narrow_phase_checks':count,'maximum_overlap_upper_bound_in3':max_upper,'discarded_prism_volume_bound_in3':len(mesh(Q[name])['triangles'])*1e-15/I**3,'maximum_total_overlap_bound_in3':max_upper+len(mesh(Q[name])['triangles'])*1e-15/I**3,'interferences':hits})
 # Prove the released outer parts, including every perimeter foot, unchanged.
 foot_checks=[]
 for name in sorted(changed):
  bay=int(name[1]);radial=np.array([np.cos(bay*np.pi/4),0,-np.sin(bay*np.pi/4)])
  # For the handed J in bay k, its head is on R(k+1), but all feet remain far
  # outside this conservative100in radial plane on their own bay's R direction.
  before=S[name].trim_by_plane(tuple(radial),100*I);after=Q[name].trim_by_plane(tuple(radial),100*I)
  err=((before-after).volume()+(after-before).volume())/I**3
  assert abs(err)<1e-6,(name,'released lower geometry changed',err)
  foot_checks.append({'member':name,'outer_region_start_in':100,'symmetric_difference_in3':err})
 clones={}
 for name in changed:
  p=copy.deepcopy(P[name]);geometry=mesh(Q[name]);p.update(vertices=geometry['vertices'],triangles=geometry['triangles'],faces=geometry['triangles'])
  p['fit_geometry']=dict(p['fit_geometry'],volume_m3=geometry['volume_m3'],nominal_fit='Top-entry upper head plus unchanged released perimeter foot; geometric review only')
  p['geometry_purpose']='proposed top-entry upper-head and perimeter step-lap design';p['cut_status']='PROPOSED TOP-ENTRY HEAD — NOT FABRICATION APPROVED';p['fabrication_dimensions_valid']=False
  p['reference_end_faces']=[];p['joint_cut_faces']=[];p['new_stock_requirements']={'status':'New/raw-stock proposal; not modification of an already-cut timber','head_seat_depth_normal_in':4,'head_side_penetration_in':2,'main_hip_bottom_depth_normal_in':6,'main_hip_central_web_width_in':4}
  p['notes']=list(p['notes'])+['Upper head is a top-entry trial with inclined bearing. Two ends need not meet. Gravity bearing does not establish uplift retention or connection capacity.']
  if name.startswith('J'):
   p['proposed_stock_planes_inches']=stock_records[name];p['new_stock_requirements']['added_axis_length_in']=next(x['stock_extension_along_J_axis_in'] for x in interfaces if x['owner']==name)
   p['geometry_planes_inches_status']='Legacy reference envelope only; this longer-head proposal uses proposed_stock_planes_inches as its chosen raw-stock envelope.'
   vertices=np.array(p['vertices']);axis=np.array(p['stock_frame']['axis']);p['fitted_axial_extent_inches']=float(np.ptp(vertices@axis)/I)
  else:
   p['new_stock_requirements']['requires_uncut_hip_blank']=True
   p['new_stock_requirements']['preserved_legacy_inner_tenon_projection_in']=2.0
   p['proposed_stock_planes_inches']=copy.deepcopy(p['geometry_planes_inches'])
   for plane in p['proposed_stock_planes_inches']:
    if plane['end']=='B':plane['constant']+=2.0
   p['geometry_planes_inches_status']='Legacy reference envelope excludes the existing2in cupola-end tongue. proposed_stock_planes_inches records a replacement blank retaining that unchanged allowance; not evidence of an original physical blank.'
  clones[name]=p
 for entry in interfaces:entry['proposed_parts']=[clones[k] for k in [entry['receiver'],entry['owner']]]
 # TIMESTAMP START 2026-11-02T15:15:55-05:00 | REVISION R004802
 audit={'timber_count':112,'upper_node_count':8,'interface_count':16,'changed_member_ids':sorted(changed),'affected_pairs_considered':sum(bool({a,b}&changed) for a,b in itertools.combinations(Q,2)),'narrow_phase_pair_checks':checks,'maximum_positive_overlap_in3':max_overlap,'intersection_tolerance_in3':1e-6,'interferences':overlaps,'lost_neighbor_contacts':lost,'neighbors':neighbors,'family_isometry_checks':isometry,'perimeter_preservation':foot_checks,'continuous_vertical_sweeps':sweep_checks,'maximum_head_contact_gap_m':max(x['nominal_contact_gap_m'] for x in interfaces),'capacity_checked':False,'numeric_policy':{'solid_kernel_distance_tolerance_m':1e-9,'positive_overlap_limit_in3':1e-6,'nominal_face_gap_limit_m':1e-8,'per_boundary_prism_discard_limit_m3':1e-15,'per_prism_discard_sum_accounted':True,'scope':'Numerical nominal CAD fit, not physical zero clearance or fabrication tolerance'},'sweep_scope':'WholeJ translation0..24in againstall112timbers; initialsolid+boundaryprisms covers continuouspath within1e-15m3 cutoff perprism. Other construction components, clearance tolerances, lifting equipment and safe raising not modeled.'}
 # TIMESTAMP END 2026-11-02T15:15:55-05:00 | REVISION R004802
 audit['geometry_status']='PASS' if not overlaps and not lost and not any(x['interferences'] for x in sweep_checks) else 'HOLD'
 full=copy.deepcopy(data);full['parts']=[clones.get(p['id'],p) for p in full['parts']];full['title']='Proposed top-entry upper heads with released perimeter step laps';full['revision']='TOP-ENTRY-PROPOSED';full['source_model']='Separate top-entry model derived from V13 perimeter model '+sha;full['status']='PROPOSED TOP-ENTRY HEADS — NOT FABRICATION APPROVED';full['prior_perimeter_review']=full.pop('proposed_review');full['prior_perimeter_review']['status']='Historical V13 review; use top_entry_review for current head contacts and selected-model mass data.';full['top_entry_review']={'source_model_sha256':sha,'chosen_dimensions':rep['chosen_dimensions'],'geometry_audit':audit,'limitations':rep['limitations']};full['proposed_member_volume_centroids']=[dict(id=k,**volume_centroid(s)) for k,s in Q.items()]
 full['joinery_verification']={'status':'PROPOSED GEOMETRY ONLY','scope':'All16upperheads plus unchanged24perimeterfeet; no strength, retention or safe erection verification.'};full['fit_audit']={'status':'PROPOSED GEOMETRY ONLY','capacity_checked':False}
 result={'schema_version':'top-entry-head-proposal-2','status':full['status'],'source_model_sha256':sha,'chosen_dimensions':rep['chosen_dimensions'],'interfaces':interfaces,'representative':rep,'geometry_audit':audit,'V13_timber_volume_m3':sum(s.volume() for s in S.values()),'proposed_timber_volume_m3':sum(s.volume() for s in Q.values()),'limitations':rep['limitations']}
 # TIMESTAMP START 2026-11-02T17:13:08-05:00 | REVISION R004818
 from cupola_foot import apply as apply_cupola_foot
 result['cupola_foot_review']=apply_cupola_foot(full)
 result['proposed_timber_volume_m3']=sum(solid(p).volume() for p in full['parts'] if p['is_timber'])
 full['title']='Proposed top-entry heads and bottom-entry cupola dovetails'
 full['status']='PROPOSED TOP-ENTRY AND DOVETAIL JOINERY — NOT FABRICATION APPROVED'
 result['status']=full['status']
 # TIMESTAMP END 2026-11-02T17:13:08-05:00 | REVISION R004818
 return result,full

def main():
 raw=(R/'src/step-lap-proposed-model.json').read_bytes();data=json.loads(raw);sha=hashlib.sha256(raw).hexdigest();proposal,full=build_all(data,sha)
 (R/'src/top-entry-proposal.json').write_text(json.dumps(proposal,separators=(',',':'))+'\n');(R/'src/top-entry-proposed-model.json').write_text(json.dumps(full,separators=(',',':'))+'\n')
 assert (R/'src/step-lap-proposed-model.json').read_bytes()==raw
 out=Path('/workspace/scratch/88cf16df239d/upper-node-review');(out/'representative-top-entry-candidate.json').write_text(json.dumps(proposal['representative'],indent=2))
 print(json.dumps({k:v for k,v in proposal['geometry_audit'].items() if k not in ['neighbors','family_isometry_checks','perimeter_preservation']},indent=2));print('TOTAL',proposal['proposed_timber_volume_m3'])
 if proposal['geometry_audit']['geometry_status']!='PASS':raise SystemExit('HOLD: all-node geometry audit failed')
if __name__=='__main__':main()

# TIMESTAMP END 2026-11-02T20:42:47-05:00 | REVISION R004871
