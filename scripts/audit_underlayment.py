# TIMESTAMP START 2026-11-05T12:32:16+00:00 | REVISION R000040
"""Fresh actual-sheet stock, bore, bearing and spacing proof; no capacity rating."""
from pathlib import Path
import argparse,hashlib,itertools,json
import numpy as np
from floor_bearing_audit import FloorContext,Rules,audit_floor,meaningful_adversaries,read_source,polygons
ROOT=Path(__file__).resolve().parents[1]
I=.0254;TOL=1e-6*I**3

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def drawing(ctx):
 out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 970">','<!-- TIMESTAMP START 2026-11-05T12:32:16+00:00 | REVISION R000040 -->','<rect width="900" height="970" fill="#faf9f4"/>','<g font-family="sans-serif" fill="#143d43"><text x="28" y="34" font-size="22">Floor deck · real cut 4 × 8 sheets</text><text x="28" y="60" font-size="14">GP actual .703 × 47.875 × 95.875 in · 1/8 in joints · 28 cut panels</text>']
 def path(poly):
  def ring(coords):return 'M'+' L'.join(f'{450+float(x)*1.8:.3f},{475-float(y)*1.8:.3f}' for x,y in coords)+' Z'
  return ring(poly.exterior.coords)+''.join(ring(r.coords) for r in poly.interiors)
 for index,pid in enumerate(ctx.sheet_ids):
  profile=ctx.profiles[pid]['upper']
  for poly in polygons(profile):out.append(f'<path d="{path(poly)}" fill="{["#e4c49c","#d9b58a"][index%2]}" stroke="#785e42" stroke-width=".7" fill-rule="evenodd"/>')
  c=profile.representative_point();out.append(f'<text x="{450+c.x*1.8:.3f}" y="{475-c.y*1.8:.3f}" font-size="9" text-anchor="middle">{pid.rsplit("-",1)[-1]}</text>')
 out+=['<text x="28" y="911" font-size="13">6 in maximum edge interval · 12 in maximum field interval, independently checked</text>','<text x="28" y="934" font-size="13">Separate edge backing, actual screws and matching bores retained in physical data.</text>','<text x="28" y="955" font-size="12">Geometric support and product cut layout only; capacity and site loads remain unqualified.</text></g>','<!-- TIMESTAMP END 2026-11-05T12:32:16+00:00 | REVISION R000040 -->','</svg>']
 return '\n'.join(out)+'\n'

def inspect(data,fixture=None):
 ctx=FloorContext(data,{'scope':'Current in-memory occupied geometry'},Rules());proof=audit_floor(ctx)
 assert proof['status']=='PASS', {k:proof[k][:3] for k in ['geometry_failures','screw_failures','bearing_failures','edge_spacing_failures','field_spacing_failures']}
 return proof

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=ROOT/'src/floor-foundation-solids.json');parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');parser.add_argument('--adversaries',action='store_true');args=parser.parse_args()
 data,provenance=read_source(args.source);ctx=FloorContext(data,provenance,Rules());proof=audit_floor(ctx)
 if args.adversaries and proof['status']=='PASS':proof['adversaries']=meaningful_adversaries(ctx,proof)
 assert proof['status']=='PASS', {k:proof[k][:3] for k in ['geometry_failures','screw_failures','bearing_failures','edge_spacing_failures','field_spacing_failures']}
 source_files=['scripts/audit_underlayment.py','scripts/floor_bearing_audit.py','scripts/physical_data.py','scripts/build_floor_solids.py','scripts/floor_edge_supports.py','scripts/fixtures/floor-supports.json.gz','scripts/floor_sheet_panels.py','scripts/floor_surface_normalization.py','src/floor-foundation.js']
 if args.source.resolve().is_relative_to(ROOT):source_files.append(str(args.source.resolve().relative_to(ROOT)))
 for q in data.get('geometryArchives',[]) or [{'path':data['geometryArchive']}]:
  archive=args.source.parent/q['path']
  if archive.resolve().is_relative_to(ROOT):source_files.append(str(archive.resolve().relative_to(ROOT)))
 image=ROOT/'public/review/underlayment-sheets.svg';svg=drawing(ctx)
 summary={'revision':'R000040','timestamp':'2026-11-05T12:32:16+00:00','status':proof['status'],'sheetCount':len(ctx.sheet_ids),'stockSizeFt':[8,4],'actualStockSizeIn':[95.875,47.875,.703],'thicknessIn':.703,'jointGapIn':.125,'sources':{p:digest(ROOT/p) for p in source_files},'image':{'path':str(image.relative_to(ROOT)),'sha256':hashlib.sha256(svg.encode()).hexdigest()},'counts':proof['counts'],'maximumEdgeIntervalIn':proof['maximum_edge_interval_in'],'maximumFieldIntervalIn':proof['maximum_field_interval_in'],'minimumPanelSetbackIn':proof['minimum_panel_setback_in'],'minimumReceivingPenetrationIn':proof['minimum_receiving_penetration_in'],'adversaries':proof.get('adversaries'),'capacity_verified':False,'scope':proof['scope']}
 if args.write:
  image.write_text(svg);(ROOT/'docs/underlayment-sheet-audit.json').write_text(json.dumps(summary,indent=2)+'\n');(ROOT/'docs/floor-support-audit.json').write_text(json.dumps(proof,separators=(',',':'))+'\n')
 if args.check:
  saved=json.loads((ROOT/'docs/underlayment-sheet-audit.json').read_text())
  assert saved['status']=='PASS' and saved['sources']==summary['sources'],'Saved underlayment source/code bindings are stale'
  assert saved['counts']==summary['counts'] and image.read_text()==svg,'Saved underlayment drawing/quantities are stale'
 print('PASS:',len(ctx.sheet_ids),'actual .703in cut panels;',proof['counts']['valid_deck_screws'],'actual deck screws; maximum edge/field gaps',proof['maximum_edge_interval_in'],proof['maximum_field_interval_in'],'in. No capacity rating.',flush=True)
if __name__=='__main__':main()
# TIMESTAMP END 2026-11-05T12:32:16+00:00 | REVISION R000040
