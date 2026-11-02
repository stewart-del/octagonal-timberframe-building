"""Owner-reference construction fixture display. Never a fabrication/erection design.

Only this steel assembly is rebuilt. Existing timber meshes must not be regenerated.
In local inches X is radial, Y is vertical, Z is strap thickness; output is metres.
"""
import copy, hashlib, json, math
from pathlib import Path
import numpy as np
import manifold3d as m

FIXTURE_ID='M-TMP'
LEGACY_IDS=[f'M-TMP{k}' for k in range(8)]
INCH=.0254
SPAN_IN=90.0
STRAP_DEPTH_IN=4.0
OUTER_LEG_HEIGHT_IN=14.0
# Explicit visualization assumptions, NOT drill/cut/weld/fastener dimensions.
THICKNESS_IN=.125
HOLE_DIAMETER_IN=.375
HOLE_RADIUS_STATION_IN=43.0
HOLE_DROPS_IN=(2.0,7.0,12.0)
DEFAULT_TOP_IN=85.0


def fixture_solid(top_m):
    beam=m.Manifold.cube((SPAN_IN/2,STRAP_DEPTH_IN,THICKNESS_IN)).translate((0,-STRAP_DEPTH_IN,-THICKNESS_IN/2))
    leg=m.Manifold.cube((STRAP_DEPTH_IN,OUTER_LEG_HEIGHT_IN,THICKNESS_IN)).translate((SPAN_IN/2-STRAP_DEPTH_IN,-OUTER_LEG_HEIGHT_IN,-THICKNESS_IN/2))
    arm=beam+leg
    for drop in HOLE_DROPS_IN:
        bore=m.Manifold.cylinder(THICKNESS_IN+1,HOLE_DIAMETER_IN/2,circular_segments=32,center=True).translate((HOLE_RADIUS_STATION_IN,-drop,0))
        arm=arm-bore
    assembly=m.Manifold()
    for k in range(8):assembly=assembly+arm.rotate((0,k*45,0))
    return assembly.scale((INCH,INCH,INCH)).translate((0,top_m,0))


def make_fixture(top_m=DEFAULT_TOP_IN*INCH):
    solid=fixture_solid(top_m)
    assert str(solid.status())=='Error.NoError' and len(solid.decompose())==1
    mesh=solid.to_mesh64();v=np.asarray(mesh.vert_properties)[:,:3];tri=mesh.tri_verts.tolist()
    lo=v.min(axis=0);hi=v.max(axis=0);center=((lo+hi)/2).tolist()
    dimension_status={
      'overall_span_in':'owner confirmed 90 in opposite outer ends; not cupola diameter',
      'strap_depth_in':'4 in reference drawing callout',
      'outer_leg_height_in':'14 in reference drawing callout; modeled total top-to-bottom height',
      'outer_leg_radial_width_in':'illustrative constant 4 in strap-width interpretation',
      'steel_thickness_in':'illustrative display assumption; stock unspecified',
      'hole_diameter_in':'illustrative display assumption; not a screw or drilling specification',
      'hole_centers_m':'illustrative display positions; not validated hole/edge distances',
      'top_elevation_m':'illustrative retained old fixture top / lower-tie underside datum; erection placement unverified',
      'central_join':'connected display union only; weld configuration, sequencing and capacity unspecified'}
    reference={'overall_span_in':SPAN_IN,'strap_depth_in':STRAP_DEPTH_IN,'outer_leg_height_in':OUTER_LEG_HEIGHT_IN,'radial_strap_count':8,'holes_per_strap':3,'total_holes':24}
    assumptions={'outer_leg_radial_width_in':STRAP_DEPTH_IN,'steel_thickness_in':THICKNESS_IN,'hole_diameter_in':HOLE_DIAMETER_IN,'hole_radius_station_in':HOLE_RADIUS_STATION_IN,'hole_drops_below_top_in':list(HOLE_DROPS_IN),'top_elevation_m':top_m,'top_elevation_in':top_m/INCH,'bore_facets':32,'weld_beads_modeled':False,'screws_modeled':False}
    holes=[]
    for k in range(8):
      a=k*math.pi/4
      for j,drop in enumerate(HOLE_DROPS_IN):
        holes.append({'id':f'M-TMP-ARM{k}-DISPLAY-HOLE{j+1}','arm_index':k,'center_m':[HOLE_RADIUS_STATION_IN*math.cos(a)*INCH,top_m-drop*INCH,-HOLE_RADIUS_STATION_IN*math.sin(a)*INCH],'axis':[math.sin(a),0,math.cos(a)],'diameter_in':HOLE_DIAMETER_IN,'status':'ILLUSTRATIVE DISPLAY ONLY — NOT DRILLING OR FASTENER SPECIFICATION'})
    dims={'length_m':SPAN_IN*INCH,'width_m':SPAN_IN*INCH,'depth_m':OUTER_LEG_HEIGHT_IN*INCH,'length_ft':SPAN_IN/12,'width_in':SPAN_IN,'depth_in':OUTER_LEG_HEIGHT_IN,'length_display':'7 ft 6 in overall reference span','section_display':'Assembly of 8 L straps; not stock','status':'Assembly envelope only; no fabrication dimensions valid.'}
    return {'id':FIXTURE_ID,'name':'Temporary welded central support · 8 L straps · display only','group':'temporary_fixture','temporary':True,'material':'steel','is_timber':False,'assembly_id':'CENTRAL-SUPPORT','assembly_quantity':1,'legacy_ids':LEGACY_IDS,'vertices':v.tolist(),'triangles':tri,'faces':tri,'center':center,'label_position':center,'axis_start':[-SPAN_IN/2*INCH,top_m,0],'axis_end':[SPAN_IN/2*INCH,top_m,0],'axis_direction':[1,0,0],'exploded_offset':[0,-1.5,0],'dimensions':dims,'nominal_dimensions':copy.deepcopy(dims),'angles':{k:None for k in ['axis_inclination_deg','azimuth_deg','display_end_cut_off_square_deg','display_end_A_off_square_deg','display_end_B_off_square_deg','display_end_face_to_axis_deg','modeled_vertical_bevel_deg','conditional_plan_miter_off_square_deg','fabrication_end_A_cut_deg','fabrication_end_B_cut_deg','fabrication_bevel_deg']},'cut_status':'DISPLAY CONCEPT ONLY — NOT A CUT DRILL WELD OR ERECTION SPECIFICATION','provenance':'Owner supplied central-support diagram and building image, 2 November 2026; 90 in overall span explicitly confirmed separately from the 88 in cupola.','notes':['One temporary welded assembly is represented by 8 joined radial vertical-plane L straps and 3 display holes per outer leg, 24 total. No permanent structural load credit.','Reference dimensions: 90 in opposite-end overall span, 4 in horizontal strap depth and 14 in total outer-leg height. The cupola stays 88 in outside.','Illustrative display assumptions ONLY: 1/8 in thickness, 3/8 in holes, hole center radius 43 in, 2/7/12 in below top, constant 4 in outer-leg radial width. These are NOT drilling, screw, cut or weld specifications.',f'Placement retains the old top elevation at {top_m/INCH:g} in above the provisional model base. Fit, erection-stage support, attachments, welds, screws, material grade and removal sequence are unverified.','Connected mesh at the center represents the intended welded assembly, not a weld detail or structural capacity. Do not fabricate or load from this display.'],'label_lines':[FIXTURE_ID,'TEMPORARY ASSEMBLY','DISPLAY ONLY'],'label_short':[FIXTURE_ID,'8 L STRAPS','NOT FABRICATION'],'color':[.12,.15,.17,1],'source_geometry_metadata':{'revision':'central-support-display-1','reference_dimensions':reference,'illustrative_display_assumptions':assumptions,'dimension_status':dimension_status},'reference_dimensions':reference,'display_assumptions':assumptions,'dimension_status':dimension_status,'geometry_purpose':'illustrative construction aid display only','fabrication_dimensions_valid':False,'plan_dimension_policy':'Suppress drilling cut weld and fastening dimensions; clearly labeled owner reference dimensions only','display_holes':holes,'fit_geometry':{'volume_m3':solid.volume(),'structural_design_status':'NOT DESIGNED','machining_clearance_m':None},'fitted_axial_extent_inches':SPAN_IN,'joint_cut_faces':[],'reference_end_faces':[],'stock_frame':{'axis':[1,0,0],'width':[0,0,-1],'depth':[0,1,0]},'geometry_planes_inches':[],'geometry_planes_inches_status':'Nonconvex display assembly mesh only; no stock, cutting or drilling planes.'}


def consolidate_fixture(parts):
    existing=[p for p in parts if p['group']=='temporary_fixture']
    if len(existing)==1 and existing[0]['id']==FIXTURE_ID:return parts
    assert {p['id'] for p in existing}==set(LEGACY_IDS),'Unexpected legacy fixture set'
    tops=[max(v[1] for v in p['vertices']) for p in existing]
    assert max(tops)-min(tops)<1e-10
    fixture=make_fixture(tops[0]);result=[]
    for p in parts:
      if p['group']!='temporary_fixture':result.append(p)
      elif p['id']==LEGACY_IDS[0]:result.append(fixture)
    return result


def migrate(root):
    # Reuse the scoped migration: it preserves timber byte content and updates
    # every current source-bound metadata file without running the full generator.
    from cupola_panel import migrate as migrate_panel
    return migrate_panel(root)

if __name__=='__main__':print(migrate(Path(__file__).resolve().parents[1]))
