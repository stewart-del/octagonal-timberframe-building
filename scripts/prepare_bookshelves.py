# TIMESTAMP START 2026-11-05T06:36:54+00:00 | REVISION R000029
"""Publish normalized furniture records; floor cuts are composed by its builder.

The immutable input retains the complete bounded geometry and its stock. Fresh
whole-scene and construction audits remain required after integration.
"""
from pathlib import Path
import copy,gzip,hashlib,json
from physical_data import readable
ROOT=Path(__file__).resolve().parents[1]

def build():
    path=ROOT/'scripts/fixtures/bookshelf-input.json.gz';fixture=json.loads(gzip.decompress(path.read_bytes()))
    candidate=fixture['candidate'];parts=copy.deepcopy(candidate['parts'])
    assert len(parts)==214 and len(candidate['joints'])==106 and candidate['capacity_verified'] is False
    mapping=candidate['fastener_receiver_mapping']
    for p in parts:
        p['framingRole']=p['kind'];p['assemblyId']='BOOKCASE-'+p['face']
        # Matching is explicit: candidate joints do not contain a peg key.
        linked={(r['donor'],r['receiver']) for r in mapping if r['fastener']==p['id']}
        p['joinery_connections']=[j for j in candidate['joints'] if p['id'] in [j['donor'],j['receiver']] or (j['donor'],j['receiver']) in linked]
        if p['id'].startswith('BOOK-SCREW-'):
            p['is_fastener']=True;p['parentId']=p['donor']
            p['receiverIds']=[p['donor']]+[r['part_id'] for r in p['receivers']]
            p['fastenerSpec']={'manufacturer':'GRK','partNumber':'113077','lengthIn':2,'majorDiameterIn':.153,'shankDiameterIn':.114,'headDiameterIn':.423,'drive':'T15','material':'Coated steel cabinet screw',
                'installation':'Four per foot. Model head is flush in a .071-inch seat: .571-inch plywood penetration. Deck-only anchorage; joist purchase and overturning capacity unqualified.',
                'sourceURL':'https://www.grkfasteners.com/grk-products/finish/low-profile-cabinet-screw'}
            p['withdrawal_direction']=[0,1,0];p['withdrawal_distance_m']=2*.0254+.01
        elif p['id'].startswith('BOOK-PEG-'):
            p['is_fastener']=True
            rows=[r for r in mapping if r['fastener']==p['id']]
            p['receiverIds']=sorted({r[k] for r in rows for k in ['donor','receiver'] if r.get(k)})
            p['fastenerSpec']={'manufacturer':'Site-made hardwood joinery peg','partNumber':'BOOK-PEG-1/4',
                'majorDiameterIn':.25,'lengthIn':4 if '-FOOT-' in p['id'] else 1.5,'material':'Hardwood; species/load capacity to specify',
                'installation':'Nominal 1/4-inch peg in modeled .252-inch bore; crosses the actual housed tongue and receiving stock. Furniture joints are separate from three-inch structural tenons.'}
        else:p['is_joinery_member']=True
    return {'revision':'R000029','timestamp':'2026-11-05T06:36:54+00:00','source_fixture_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'source_normalized_candidate_sha256':fixture['source_sha256'],'capacity_verified':False,'parts':parts,
        'replacedSchematicIds':candidate['removed_ids'],'joints':candidate['joints'],'fastenerReceiverMapping':mapping,
        'caseWidthIn':104,'clearShelfSpanIn':23.5,'expansionGapIn':.5,
        'scope':'Normalized individual furniture members/pegs/screws and stock. Fresh composed floor/whole-scene motion checks required before release.'}

if __name__=='__main__':
    value=build();(ROOT/'src/bookshelf-solids.json').write_text(readable(value)+'\n')
    print('Prepared',len(value['parts']),'individual furniture pieces; floor gaps and anchor bores compose into current floor source.')
# TIMESTAMP END 2026-11-05T06:36:54+00:00 | REVISION R000029
