# TIMESTAMP START 2026-11-02T16:00:43-05:00 | REVISION R004813
"""Withdraw porch assemblies along real joint directions, retaining obstacles.

Every proposed translation is checked against the current complete scene before
it is appended. A blocked stage stops the phase and reports its actual obstacle;
the planner never hides, teleports or silently omits a physical piece.
"""
from pathlib import Path
import json
import numpy as np
from plan_architectural_disassembly import check_stage, apply_stage

ROOT=Path(__file__).resolve().parents[1]

def apply_porch_phases(scene,skip_cover=False):
    fit=json.loads((ROOT/'src/mudroom-joinery-fit.json').read_text())
    center=(np.asarray(scene.parts['P2']['center'])+np.asarray(scene.parts['P3']['center']))/2;center[1]=0
    tangent=np.asarray(scene.parts['P3']['center'])-np.asarray(scene.parts['P2']['center']);tangent[1]=0;tangent/=np.linalg.norm(tangent)
    basis=np.array([tangent,[0,1,0],center/np.linalg.norm(center)])
    start=len(scene.stages);blocked=[]
    class Blocked(Exception):pass
    def move(ids,delta,label):
        ids=list(ids);world=np.asarray(delta)@basis
        proof=check_stage(scene,ids,world,stop_first=True)
        if proof['status']!='PASS':
            blocked.append({'label':label,'member_ids':ids,'delta_m':world.tolist(),'proof':proof})
            raise Blocked(label)
        apply_stage(scene,ids,world,proof=proof,label=label,stage_id='porch-'+str(len(scene.stages)+1).zfill(3))
    def ids(prefix):return [pid for pid in scene.parts if pid.startswith(prefix)]
    try:
        cover=[pid for pid,p in scene.parts.items() if p.get('roofLayer')]
        if not skip_cover:
            move(cover,[0,6,0],'Lift porch roof cover')
            move(cover,[0,0,8],'Park porch roof cover outward')
        rafters=ids('MUD-RAFTER-')+[j['peg_id'] for j in fit['joints'] if j['family']=='pegged apex half lap']
        move(rafters,[0,.3,0],'Lift complete rafter pairs off birdsmouths')
        move(rafters,[0,0,10],'Park complete rafter pairs outward')
        tie_pegs=[j['peg_id'] for j in fit['joints'] if j['family']=='open top cross half lap']
        move(tie_pegs,[0,.3,0],'Withdraw transverse-tie pegs vertically')
        move(tie_pegs,[0,1,0],'Raise released tie pegs clear of later work')
        move(tie_pegs,[0,0,6],'Park tie pegs outward')
        move(ids('MUD-ROOF-TIE-'),[0,.3,0],'Lift transverse ties from open seats')
        move(ids('MUD-ROOF-TIE-'),[0,0,6],'Park transverse ties outward')
        brace_joints=[j for j in fit['joints'] if j['family']=='face-housed pegged knee brace']
        peg_left=[j['peg_id'] for j in brace_joints if '-SIDE-L-' in j['donor']]
        peg_right=[j['peg_id'] for j in brace_joints if '-SIDE-R-' in j['donor']]
        peg_front=[j['peg_id'] for j in brace_joints if j['donor'].startswith('MUD-BRACE-FRONT-')]
        move(peg_left,[-.2,0,0],'Withdraw left knee-brace pegs')
        move(peg_right,[.2,0,0],'Withdraw right knee-brace pegs')
        move(peg_front,[0,0,.2],'Withdraw front knee-brace pegs')
        brace_pegs=peg_left+peg_right+peg_front
        move(brace_pegs,[0,0,4],'Move brace pegs outside porch')
        move(brace_pegs,[0,1.2,0],'Park brace pegs above framing path')
        brace_left=ids('MUD-BRACE-SIDE-L-');brace_right=ids('MUD-BRACE-SIDE-R-');brace_front=ids('MUD-BRACE-FRONT-')
        move(brace_left,[-.15,0,0],'Withdraw left braces normal to their housings')
        move(brace_right,[.15,0,0],'Withdraw right braces normal to their housings')
        move(brace_left+brace_right,[0,0,3],'Park side braces outward')
        move(brace_front,[0,0,.15],'Withdraw front braces normal to their housings')
        move(brace_front,[0,0,3],'Park front braces outward')
        head_joints=[j for j in fit['joints'] if j['donor'].startswith('MUD-POST-') and j['receiver'].startswith('MUD-PLATE-')]
        head_left=[j['peg_id'] for j in head_joints if 'POST-L-' in j['donor']]
        head_right=[j['peg_id'] for j in head_joints if 'POST-R-' in j['donor']]
        move(head_left,[-.2,0,0],'Withdraw left post-head pegs')
        move(head_right,[.2,0,0],'Withdraw right post-head pegs')
        move(head_left+head_right,[0,.2,0],'Lift released post-head pegs')
        move(head_left+head_right,[0,0,2],'Move post-head pegs outward')
        move(head_left+head_right,[0,.5,0],'Park post-head pegs above beam route')
        header_pegs=[j['peg_id'] for j in fit['joints'] if j['donor']=='MUD-HEADER-FRONT']
        roof_u=['MUD-PLATE-L','MUD-PLATE-R','MUD-HEADER-FRONT']+header_pegs
        move(roof_u,[0,.1,0],'Lift roof-beam U off post tenons')
        move(roof_u,[0,0,2],'Park roof-beam U outward')
        move(header_pegs,[0,.2,0],'Withdraw header pegs from parked beam assembly')
        move(header_pegs,[0,.8,0],'Park header pegs above their joint')
        move(['MUD-PLATE-L'],[-.2,0,0],'Separate left roof beam from header tenon')
        move(['MUD-PLATE-R'],[.2,0,0],'Separate right roof beam from header tenon')
        move(brace_left,[-1,0,0],'Park left braces beside the bent route')
        move(brace_right,[1,0,0],'Park right braces beside the bent route')
        move(['MUD-PLATE-L'],[-1,0,0],'Move left roof beam beyond the bent route')
        move(['MUD-PLATE-R'],[1,0,0],'Move right roof beam beyond the bent route')
        guard_prefixes=('MUD-POST-','MUD-GUARD-TOP-','MUD-GUARD-PICKET-','MUD-SILL-','MUD-FRONT-GUARD-','MUD-FRONT-PICKET-','MUD-FRONT-SILL-','MUD-ENTRY-GUARD-POST-')
        guard_members=[pid for pid in scene.parts if pid.startswith(guard_prefixes)]
        guard_pegs=[j['peg_id'] for j in fit['joints'] if j.get('peg_id') and j['donor'] in guard_members and j['receiver'] in guard_members]
        move(guard_members+guard_pegs,[0,.1,0],'Lift the joined guard frame clear of the porch pan')
        outer_front_pegs=[j['peg_id'] for j in fit['joints'] if j['donor'].startswith('MUD-FRONT-GUARD-') and j['receiver'].startswith('MUD-POST-')]
        move(outer_front_pegs,[0,0,.2],'Withdraw front-panel pegs from the outer posts')
        move(outer_front_pegs,[0,0,1],'Park released front-panel pegs outward')
        side_bents={}
        for side,sign in [('L',-1),('R',1)]:
            members=[pid for pid in guard_members if pid.startswith(('MUD-POST-'+side+'-','MUD-GUARD-TOP-'+side,'MUD-GUARD-PICKET-'+side+'-','MUD-SILL-'+side+'-'))]
            members += [j['peg_id'] for j in fit['joints'] if j.get('peg_id') and j['donor'] in members and j['receiver'] in members]
            side_bents[side]=members
            move(members,[sign*.2,0,0],'Separate '+side+' side bent from front-panel tenons')
        move(side_bents['L']+side_bents['R'],[0,0,2],'Park the side bents outward')
        front_panels=[pid for pid in guard_members+guard_pegs if pid not in side_bents['L']+side_bents['R']+outer_front_pegs]
        move(front_panels,[0,.9,0],'Lift front guard panels above the landing rails')
        move(front_panels,[0,0,1.5],'Park front guard panels outward')
        # The bents are now parked with clear access on both sides. Release
        # pegs before lifting posts/top rails off their vertical tenons.
        for side,sign in [('L',-1),('R',1)]:
            post_ids=ids('MUD-POST-'+side+'-');top='MUD-GUARD-TOP-'+side
            foot_pegs=[j['peg_id'] for j in fit['joints'] if j.get('peg_id') and j['donor'] in post_ids and j['receiver'].startswith('MUD-SILL-')]
            rail_pegs=[j['peg_id'] for j in fit['joints'] if j.get('peg_id') and j['donor']==top]
            move(foot_pegs,[sign*.2,0,0],'Withdraw '+side+' post-foot pegs from the parked bent')
            move(rail_pegs,[sign*.2,0,0],'Withdraw '+side+' top-rail pegs from the parked bent')
            move(rail_pegs,[0,.2,0],'Park '+side+' rail pegs above the released rail')
            move(post_ids+[top],[0,.05,0],'Lift '+side+' posts and top rail off base and picket tenons')
            move(['MUD-POST-'+side+'-BACK'],[0,0,-.1],'Withdraw '+side+' back post from the rail tenon')
            move(['MUD-POST-'+side+'-FRONT'],[0,0,.1],'Withdraw '+side+' front post from the rail tenon')
            move([top],[sign*.4,0,0],'Separate '+side+' top rail from the picket line')
            move(ids('MUD-GUARD-PICKET-'+side+'-'),[0,.05,0],'Lift '+side+' pickets from base-rail mortises')
            move(['MUD-SILL-'+side+'-FRONT'],[0,0,.05],'Separate '+side+' front base-rail segment')
        front_inner_pegs=[j['peg_id'] for j in fit['joints'] if j.get('peg_id') and ((j['donor'].startswith('MUD-FRONT-GUARD-') and j['receiver'].startswith('MUD-ENTRY-')) or j['donor'].startswith('MUD-ENTRY-'))]
        move(front_inner_pegs,[0,0,.2],'Withdraw the front-panel post and rail pegs')
        front_posts=ids('MUD-ENTRY-GUARD-POST-');front_tops=ids('MUD-FRONT-GUARD-')
        move(front_posts+front_tops,[0,.05,0],'Lift front posts and rails off the panel-base and picket tenons')
        move(['MUD-ENTRY-GUARD-POST-L'],[.1,0,0],'Release left entry post from its rail tenon')
        move(['MUD-ENTRY-GUARD-POST-R'],[-.1,0,0],'Release right entry post from its rail tenon')
        move(front_tops,[0,0,-.2],'Move the released front rails off the picket line')
        move(ids('MUD-FRONT-PICKET-'),[0,.05,0],'Lift front pickets from their base mortises')
        apex_pegs=[j['peg_id'] for j in fit['joints'] if j['family']=='pegged apex half lap']
        move(apex_pegs,[0,0,.15],'Withdraw apex pegs from the parked rafter pairs')
        move(apex_pegs,[0,.3,0],'Park apex pegs above the released rafters')
        move(ids('MUD-RAFTER-L-'),[0,0,-.15],'Open the apex half-laps in the parked rafter pairs')
        move(ids('MUD-RAFTER-L-'),[-.3,0,0],'Separate the left rafter halves')
        move(ids('MUD-RAFTER-R-'),[.3,0,0],'Separate the right rafter halves')
        grate=ids('MUD-GRATE-BAR-')+ids('MUD-GRATE-RAIL-')
        move(grate,[0,2.3,0],'Lift the walking-grate assembly clear for inspection')
        move(grate,[0,0,1.5],'Park the walking grate above the cleared aisle')
        for side in ['L','R']:
            bench=['MUD-BENCH-'+side,'MUD-SHOE-SHELF-'+side]+[pid for pid in ids('MUD-BENCH-LEG-') if '-'+side+'-' in pid]
            move(bench,[0,.25,0],'Lift '+side+' bench and shoe-shelf assembly off the sloped pan')
            move(bench,[0,0,4],'Park '+side+' bench assembly outward')
        coat=ids('MUD-COAT-BOARD-')+ids('MUD-HOOK-')
        move(coat,[0,0,3],'Withdraw and park the coat-rack assemblies')
        stair_guards=[pid for pid in scene.parts if pid.startswith(('MUD-LANDING-RAIL-','MUD-LANDING-PICKET-','MUD-STAIR-RAIL-','MUD-STAIR-PICKET-'))]
        move(stair_guards,[0,.05,0],'Lift the exterior stair guards off their modeled bearings')
        move(stair_guards,[0,0,8],'Park exterior stair guards beyond the porch')
        # Concrete/plumbing components are one schematic support assembly here.
        # This geometric separation is not a construction demolition sequence.
        remaining=[pid for pid,p in scene.parts.items() if p.get('schematicKind')=='mudroom' and np.linalg.norm(scene.offsets[pid])<1e-12]
        assert all(scene.parts[pid].get('mudroomRole') in ['floor','drain','stair','foundation'] for pid in remaining),remaining
        move(remaining,[0,0,8],'Separate the schematic porch pan, threshold and support assembly')
    except Blocked:
        pass
    moved={pid for stage in scene.stages[start:] for pid in stage['member_ids']}
    unmoved=[pid for pid,p in scene.parts.items() if p.get('schematicKind')=='mudroom' and pid not in moved and np.linalg.norm(scene.offsets[pid])<1e-12]
    return {'status':'PARTIAL' if blocked or unmoved else 'PASS','stages_added':len(scene.stages)-start,'blocked':blocked,'unmoved_ids':unmoved,'scope':'Porch joint release and parking; the complete global planner must check its live scene before claiming all pieces can separate.'}
# TIMESTAMP END 2026-11-02T16:00:43-05:00 | REVISION R004813
