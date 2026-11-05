# TIMESTAMP START 2026-11-05T12:32:16+00:00 | REVISION R000040
#!/usr/bin/env python3
"""Portable actual-solid floor bearing/contact and fastening-pattern audit.

Dependencies: numpy, manifold3d, shapely. No repository imports or saved expected
hashes/counts. Load functions with runpy.run_path(), or run the CLI on any fresh
metadata file plus its lossless geometry archive. This does not rate capacity.
"""
from pathlib import Path
from dataclasses import dataclass
import argparse,copy,gzip,hashlib,json,math,sys
import numpy as np
import manifold3d as m
from shapely.geometry import Polygon,LineString,Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import make_valid

INCH=.0254
@dataclass(frozen=True)
class Rules:
    volume_tolerance_in3:float=1e-6
    plan_coincidence_in:float=1e-7
    section_offset_in:float=1e-5
    contact_height_coincidence_in:float=1e-6
    report_length_epsilon_in:float=1e-4
    report_area_epsilon_in2:float=1e-4
    interval_roundoff_in:float=1e-7
    minimum_panel_setback_in:float=.375
    edge_association_maximum_setback_in:float=.75
    bearing_band_in:float=.375
    edge_interval_in:float=6.
    field_interval_in:float=12.
    receiving_penetration_in:float=1.375
    sheet_thickness_in:float=.703
    stock_length_in:float=95.875
    stock_width_in:float=47.875
    stock_gap_in:float=.125

def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_source(path):
    """Resolve mesh instances later, and verify/read a lossless archive here."""
    path=Path(path);data=json.loads(path.read_text());provenance={'metadata_path':str(path.resolve()),'metadata_sha256':sha256(path)}
    archives=data.get('geometryArchives') or ([{'path':data['geometryArchive'],'sha256':data['geometryArchiveSha256']}] if data.get('geometryArchive') else [])
    # Resolve declared geometry_ref records even if a producer retained a
    # geometryResolved flag while re-archiving its output.
    if archives:
        geometry={};archive_provenance=[]
        for descriptor in archives:
            archive=path.parent/descriptor['path'];raw=archive.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            if digest!=descriptor['sha256']:raise ValueError('Geometry archive hash mismatch')
            decoded=json.loads(gzip.decompress(raw))['parts']
            if set(decoded).intersection(geometry):raise ValueError('Repeated physical geometry across archives')
            geometry.update(decoded);archive_provenance.append({'path':str(archive.resolve()),'sha256':digest})
        parts=[]
        for p in data['parts']:
            if p.get('geometry_ref'):
                if p['geometry_ref']!=p['id'] or p['id'] not in geometry:raise ValueError('Missing physical geometry '+p['id'])
                p={**p,**geometry[p['id']]};p.pop('geometry_ref',None)
            parts.append(p)
        data={**data,'parts':parts,'geometryResolved':True};provenance['geometry_archives']=archive_provenance
        if len(archive_provenance)==1:provenance.update(geometry_archive_path=archive_provenance[0]['path'],geometry_archive_sha256=archive_provenance[0]['sha256'])
    return data,provenance

def sections_to_polygon(section):
    positive=[];negative=[]
    for loop in section.to_polygons():
        q=np.asarray(loop,float)
        if len(q)<3:continue
        signed=np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))/2
        p=Polygon(q)
        # A zero-area point/edge touch from serialized caps can make a native
        # Clipper region non-simple to GEOS. Regularize topology only, then
        # compare the occupied region back in native CrossSection arithmetic.
        if not p.is_valid:p=make_valid(p)
        (positive if signed>0 else negative).append(p)
    p=unary_union(positive)
    p=p.difference(unary_union(negative)) if negative else p
    p=unary_union(polygons(p));contours=[]
    for poly in polygons(p):contours.append(list(poly.exterior.coords)[:-1]);contours.extend(list(r.coords)[:-1] for r in poly.interiors)
    rebuilt=m.CrossSection(contours) if contours else m.CrossSection()
    error=(section-rebuilt).area()+(rebuilt-section).area()
    if error>1e-8:raise ValueError('Plan topology regularization changes occupied area: '+str(error)+'in2')
    return p
def polygons(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [orient(g,sign=1.)]
    return [p for q in getattr(g,'geoms',[]) for p in polygons(q)]
def lines(g):
    if g.is_empty:return []
    if g.geom_type in ['LineString','LinearRing']:return [g]
    return [l for q in getattr(g,'geoms',[]) for l in lines(q)]
def bounding_boxes_overlap(a,b):return all(a[k+3]>b[k]+1e-10 and b[k+3]>a[k]+1e-10 for k in range(3))
def clipped_segment_ranges(original,clipped):
    # Never reintersect already-clipped floating-point rotated lines: GEOS can
    # erase those nearly-collinear intervals. Project their endpoints directly.
    result=[]
    for q in lines(clipped):
        values=[original.project(Point(p)) for p in q.coords]
        if values:result.append([float(min(values)),float(max(values))])
    return sorted(result)
def station_gaps(stations,length,closed):
    values=sorted(set(round(float(s),9) for s in stations))
    if not values:return [{'start_in':0.,'end_in':float(length),'length_in':float(length),'terminal':True}]
    pairs=list(zip(values,values[1:]))
    pairs=pairs+[(values[-1],values[0]+length)] if closed else [(0.,values[0])]+pairs+[(values[-1],length)]
    return [{'start_in':float(a),'end_in':float(b),'length_in':float(b-a),'terminal':bool(not closed and (a==0 or b==length))} for a,b in pairs]
def ray_intervals(shape,origin,axis,length):
    result=[];start=None
    for hit in shape.ray_cast(np.asarray(origin).tolist(),(np.asarray(origin)+np.asarray(axis)*length).tolist()):
        direction=float(np.dot(hit.normal,axis));distance=float(hit.distance*length)
        if direction<-1e-8:start=max(0.,distance)
        elif direction>1e-8 and start is not None:result.append([start,distance]);start=None
    if start is not None:result.append([start,length])
    return result

class FloorContext:
    """Immutable source geometry; optional installation changes are audit inputs."""
    def __init__(self,data,provenance=None,rules=Rules()):
        self.data=data;self.provenance=provenance or {};self.rules=rules;self.parts={p['id']:p for p in data['parts']}
        if len(self.parts)!=len(data['parts']):raise ValueError('Duplicate physical identifiers')
        self.sheet_ids=[pid for pid,p in self.parts.items() if p.get('floorRole')=='underlayment_sheet']
        if not self.sheet_ids:raise ValueError('No actual underlayment sheets')
        first=self.parts[self.sheet_ids[0]]['sheet_stock'];east=np.asarray(first['longAxisM'],float);north=np.asarray(first['shortAxisM'],float);up=np.array([0.,1.,0.]);self.basis=np.column_stack([east,north,up])
        if not np.allclose(self.basis.T@self.basis,np.eye(3),rtol=0,atol=1e-9):raise ValueError('Floor stock frame is not orthonormal')
        self.to_local=np.column_stack([self.basis.T/INCH,np.zeros(3)]).tolist()
        layer=next(p for p in data['layout']['layers'] if p['id']=='SUBFLOOR');self.top=layer['topY_M']/INCH;self.bottom=(layer['topY_M']-layer['thicknessM'])/INCH
        self.screw_ids=[pid for pid,p in self.parts.items() if p.get('floorRole')=='deck_screw']
        self.fastener_ids=[pid for pid,p in self.parts.items() if p.get('is_fastener')]
        self.steel_ids=[pid for pid,p in self.parts.items() if pid.startswith('POST-BEARING-STAND')]
        roles={'panel_edge_blocking','panel_edge_ledger','notch_backing'}
        self.support_ids=[pid for pid,p in self.parts.items() if not p.get('is_fastener') and (p.get('floorRole') in roles or pid.startswith(('FLOOR-JOIST-','FLOOR-RIM-','FLOOR-BEAM-')) or pid=='FLOOR-CENTRAL-HUB')]
        longest=max(self.parts[pid]['fastenerSpec']['lengthIn'] for pid in self.screw_ids)
        self.support_ids=[pid for pid in self.support_ids if np.asarray(self.parts[pid]['vertices'])[:,1].max()/INCH>=self.top-longest-rules.contact_height_coincidence_in]
        self.backer_ids=[pid for pid in self.support_ids if self.parts[pid].get('floorRole') in {'panel_edge_ledger','notch_backing'}]
        self._native={};self._local={};self.envelopes={};self.geometry_failures=[];self.reconstruction=[];self._screw_validation_cache={}
        self.bore_ids={pid:set(p.get('fastenerBoreIds',[])) for pid,p in self.parts.items()}
        for fid in self.fastener_ids:
            for receiver in self.parts[fid].get('receiverIds',[]):self.bore_ids.setdefault(receiver,set()).add(fid)
        self.contact_masks={};self.contact_heights=[];self.profiles={};self.stock_checks=[]
        fastener_boxes={fid:self.local(fid).bounding_box() for fid in self.fastener_ids}
        for pid in self.support_ids+self.sheet_ids:
            p=self.parts[pid]
            if not p.get('display_mesh',{}).get('vertices'):
                self.geometry_failures.append({'part':pid,'code':'MISSING_PREBORE_ENVELOPE'});continue
            envelope=self.record_solid(p['display_mesh']).transform(self.to_local);self.envelopes[pid]=envelope
            actual=self.local(pid);box=envelope.bounding_box();centre=(np.asarray(box[:3])+box[3:])/2
            # Condition the actual source solids by one rigid translation.
            # A batch union of almost-touching cutters at east160in was
            # numerically order-sensitive in the uncentred global frame.
            e=envelope.translate((-centre).tolist());a=actual.translate((-centre).tolist())
            candidate_ids=sorted(fid for fid,b in fastener_boxes.items() if bounding_boxes_overlap(box,b))
            mapped=[self.local(fid).translate((-centre).tolist()) for fid in candidate_ids]
            extra=max(0.,(a-e).volume());missing=e-a
            forward=max(0.,(missing-m.Manifold.batch_boolean(mapped,m.OpType.Add)).volume()) if mapped else max(0.,missing.volume())
            reverse=max(0.,(missing-m.Manifold.batch_boolean(list(reversed(mapped)),m.OpType.Add)).volume()) if mapped else max(0.,missing.volume())
            unexplained=max(forward,reverse)
            unlisted=[]
            for fid,tool in zip(candidate_ids,mapped):
                if fid not in self.bore_ids.get(pid,set()):
                    volume=(tool^missing).volume()
                    if volume>rules.volume_tolerance_in3:unlisted.append({'fastener':fid,'actual_missing_stock_engagement_in3':float(volume)})
            rec={'part':pid,'actual_extra_in3':extra,'actual_removed_stock_in3':float(missing.volume()),'unexplained_removed_in3':unexplained,'forward_unexplained_in3':forward,'reverse_unexplained_in3':reverse,'recorded_bore_count':len([fid for fid in self.bore_ids.get(pid,[]) if fid in self.parts and self.parts[fid].get('is_fastener')]),'nearby_actual_hardware_count':len(candidate_ids),'unlisted_actual_bore_hardware':unlisted,'conditioning':'Exact current occupied/envelope/tool meshes, translated to the actual part stock centre in inches. Both forward and reverse sorted actual-cutter unions must pass.'};self.reconstruction.append(rec)
            if extra>rules.volume_tolerance_in3 or unexplained>rules.volume_tolerance_in3:self.geometry_failures.append({'part':pid,'code':'UNEXPLAINED_OCCUPIED_WOOD_DIFFERENCE',**rec})
        for pid in self.support_ids:
            if pid not in self.envelopes:continue
            e=self.envelopes[pid];gap=self.bottom-e.bounding_box()[5];self.contact_heights.append({'part':pid,'deck_underside_minus_support_top_in':float(gap)})
            if abs(gap)<=rules.contact_height_coincidence_in:self.contact_masks[pid]=sections_to_polygon(e.slice(self.bottom-rules.section_offset_in))
        for pid in self.sheet_ids:
            if pid not in self.envelopes:continue
            p=self.parts[pid];e=self.envelopes[pid];stock=p['sheet_stock'];v=np.asarray(e.to_mesh64().vert_properties)[:,:3];bounds=e.bounding_box()
            errors=[]
            for key,target in [('lengthM',rules.stock_length_in),('widthM',rules.stock_width_in),('thicknessM',rules.sheet_thickness_in),('gapM',rules.stock_gap_in)]:
                if abs(stock[key]/INCH-target)>rules.contact_height_coincidence_in:errors.append(key)
            if max(abs(bounds[2]-self.bottom),abs(bounds[5]-self.top),abs(bounds[5]-bounds[2]-rules.sheet_thickness_in))>rules.contact_height_coincidence_in:errors.append('actual_mesh_thickness_or_elevation')
            for axis,actualkey,gridkey,nominal in [(0,'eastBoundsM','gridEastBoundsM',96),(1,'northBoundsM','gridNorthBoundsM',48)]:
                lo,hi=np.array(stock[actualkey])/INCH;glo,ghi=np.array(stock[gridkey])/INCH
                if max(lo-v[:,axis].min(),v[:,axis].max()-hi)>rules.contact_height_coincidence_in:errors.append('occupied_mesh_outside_'+actualkey)
                if max(abs(ghi-glo-nominal),abs(lo-glo-.0625),abs(ghi-hi-.0625))>rules.contact_height_coincidence_in:errors.append('grid_spacing_'+actualkey)
            self.stock_checks.append({'sheet':pid,'status':'PASS' if not errors else 'FAIL','errors':errors,'actual_thickness_in':float(bounds[5]-bounds[2]),'stock_length_in':stock['lengthM']/INCH,'stock_width_in':stock['widthM']/INCH,'nominal_grid_gap_in':stock['gapM']/INCH})
            if errors:self.geometry_failures.append({'part':pid,'code':'SHEET_STOCK_OR_GRID_DIMENSIONS','details':errors})
            self.profiles[pid]={label:sections_to_polygon(e.slice(y)).simplify(rules.plan_coincidence_in,preserve_topology=True) for label,y in [('upper',self.top-rules.section_offset_in),('lower',self.bottom+rules.section_offset_in)]}
        points=np.asarray(data['layout']['sourcePostCenters'])@self.basis/INCH;self.perimeter=LineString(np.vstack([points[:,:2],points[:1,:2]]))
        self.joists={p['id']:float(np.asarray(p['startM'])@east/INCH) for p in data['layout']['members'] if p['kind']=='joist' and p['id'] in self.support_ids}
    def record_solid(self,record):
        if record.get('mesh_instance'):
            inst=record['mesh_instance'];return self.record_solid(self.data['prototypes'][inst['prototype']]).transform(inst['transform'])
        s=m.Manifold(m.Mesh64(np.asarray(record['vertices'],np.float64),np.asarray(record['triangles'],np.uint64)))
        if str(s.status())!='Error.NoError':raise ValueError('Native occupied solid rejected')
        return s
    def native(self,pid):
        if pid not in self._native:self._native[pid]=self.record_solid(self.parts[pid])
        return self._native[pid]
    def local(self,pid):
        if pid not in self._local:self._local[pid]=self.native(pid).transform(self.to_local)
        return self._local[pid]
    def screw_position(self,pid,translation_in=None):
        p=self.parts[pid];inst=p.get('mesh_instance')
        if not inst:raise ValueError('Deck screw needs explicit prototype origin '+pid)
        matrix=np.asarray(inst['transform']);point=self.basis.T@matrix[:,3]/INCH;axis=self.basis.T@matrix[:,2];axis/=np.linalg.norm(axis)
        return point+(np.asarray(translation_in) if translation_in is not None else 0),axis

def validate_screws(ctx,omitted_screw_ids=(),screw_translations_in=None,excluded_support_ids=()):
    rules=ctx.rules;omitted=set(omitted_screw_ids);excluded=set(excluded_support_ids);translations=screw_translations_in or {};records={};failures=[]
    active_support=[pid for pid in ctx.support_ids if pid not in excluded and pid in ctx.envelopes]
    for fid in ctx.screw_ids:
        if fid in omitted:continue
        key=(fid,tuple(float(x) for x in translations.get(fid,[0,0,0])),tuple(sorted(excluded)))
        cached=ctx._screw_validation_cache.get(key)
        if cached is None and excluded and fid not in translations:
            base=ctx._screw_validation_cache.get((fid,(0.,0.,0.),()))
            if base and not excluded.intersection(base['actual_occupied_receiving_ids']) and not excluded.intersection(base['actual_ray_receivers_in']):cached=base
        if cached is not None:
            records[fid]=cached
            if not cached['valid']:failures.append(cached)
            continue
        p=ctx.parts[fid];sheet=p.get('parentId');point,axis=ctx.screw_position(fid,translations.get(fid));q=point[:2];issues=[];setback=-1.
        if sheet not in ctx.profiles:issues.append('NO_ACTUAL_SHEET')
        else:
            for profile in ctx.profiles[sheet].values():
                distance=profile.boundary.distance(Point(q));setback=distance if setback<0 else min(setback,distance)
                if not profile.covers(Point(q)) or distance+rules.plan_coincidence_in<rules.minimum_panel_setback_in:issues.append('OUTSIDE_REAL_PANEL_OR_EDGE_SETBACK')
        if abs(point[2]-ctx.top)>rules.contact_height_coincidence_in or np.linalg.norm(axis-[0,0,-1])>1e-8:issues.append('HEAD_ELEVATION_OR_AXIS')
        receivers={};receiver_intervals={};actual_receiving=[]
        screw=ctx.local(fid)
        if fid in translations:screw=screw.translate(np.asarray(translations[fid]).tolist())
        occupied_vertices=np.asarray(screw.to_mesh64().vert_properties)[:,:3];axial=(occupied_vertices-point)@axis;amount=float(axial.max())
        if abs(float(axial.min()))>rules.contact_height_coincidence_in:issues.append('ACTUAL_HEAD_FRONT_NOT_AT_PROTOTYPE_ORIGIN')
        box=screw.bounding_box();maximum_wood_overlap=0.;engagement=0.
        for wid in active_support:
            stock=ctx.envelopes[wid]
            if not bounding_boxes_overlap(box,stock.bounding_box()):continue
            intervals=ray_intervals(stock,point,axis,amount)
            # Receiving wood must begin at the actual underside and continue
            # for the required length; disjoint lower intervals cannot add up.
            entry=point[2]-ctx.bottom
            length=max((b-a for a,b in intervals if abs(a-entry)<=rules.contact_height_coincidence_in),default=0.)
            if length>rules.interval_roundoff_in:receivers[wid]=float(length);receiver_intervals[wid]=intervals
            stock_volume=(screw^stock).volume()
            if stock_volume>rules.volume_tolerance_in3:
                actual_receiving.append(wid);engagement+=stock_volume
                maximum_wood_overlap=max(maximum_wood_overlap,max(0.,(screw^ctx.local(wid)).volume()))
        receiving_length=max(receivers.values(),default=0.)
        if receiving_length+rules.interval_roundoff_in<rules.receiving_penetration_in:issues.append('INSUFFICIENT_ACTUAL_RECEIVING_WOOD')
        if engagement<=rules.volume_tolerance_in3:issues.append('NO_OCCUPIED_RECEIVER_ENGAGEMENT')
        if maximum_wood_overlap>rules.volume_tolerance_in3:issues.append('MISSING_MATCHING_RECEIVER_BORE')
        sheet_overlap=0.
        if sheet in ctx.profiles:
            sheet_overlap=max(0.,(screw^ctx.local(sheet)).volume())
            if sheet_overlap>rules.volume_tolerance_in3:issues.append('MISSING_MATCHING_PANEL_BORE')
        steel=[]
        for sid in ctx.steel_ids:
            if bounding_boxes_overlap(box,ctx.local(sid).bounding_box()):
                vol=(screw^ctx.local(sid)).volume()
                if vol>rules.volume_tolerance_in3:steel.append({'steel':sid,'overlap_in3':float(vol)})
        if steel:issues.append('STEEL_INTERFERENCE')
        record={'screw':fid,'sheet':sheet,'east_north_in':q.tolist(),'head_height_in':float(point[2]),'setback_in':float(setback),'actual_axial_screw_length_in':amount,'actual_ray_receivers_in':receivers,'actual_ray_intervals_in':receiver_intervals,'minimum_required_penetration_in':rules.receiving_penetration_in,'maximum_receiving_length_in':float(receiving_length),'declared_receiver_ids':p.get('receiverIds',[]),'actual_occupied_receiving_ids':actual_receiving,'receiver_stock_engagement_in3':float(engagement),'maximum_actual_wood_overlap_in3':float(maximum_wood_overlap),'actual_panel_overlap_in3':float(sheet_overlap),'steel_conflicts':steel,'issues':sorted(set(issues)),'valid':not issues}
        records[fid]=record
        ctx._screw_validation_cache[key]=record
        if issues:failures.append(record)
    return records,failures

def edge_station_associations(ring,poly,screws,rules):
    coords=np.asarray(ring.coords);associated=[];station=0.
    for a,b in zip(coords,coords[1:]):
        length=np.linalg.norm(b-a)
        if length==0:continue
        u=(b-a)/length
        for fid,screw in screws.items():
            q=np.asarray(screw['east_north_in']);along=float((q-a)@u);distance=float(u[0]*(q-a)[1]-u[1]*(q-a)[0])
            if -rules.plan_coincidence_in<=along<=length+rules.plan_coincidence_in and rules.minimum_panel_setback_in-rules.plan_coincidence_in<=distance<=rules.edge_association_maximum_setback_in+rules.plan_coincidence_in and poly.covers(Point(q)):
                associated.append({'screw':fid,'station_in':float(station+min(length,max(0.,along))),'setback_from_segment_in':distance})
        station+=length
    return associated

def audit_floor(ctx,excluded_support_ids=(),omitted_screw_ids=(),screw_translations_in=None,validate_hardware=True):
    rules=ctx.rules;excluded=set(excluded_support_ids);masks={pid:g for pid,g in ctx.contact_masks.items() if pid not in excluded};support=unary_union(list(masks.values()))
    screw_records,screw_failures=validate_screws(ctx,omitted_screw_ids,screw_translations_in,excluded) if validate_hardware else ({},[])
    valid={fid:r for fid,r in screw_records.items() if r['valid']};sheets=[];bearing_failures=[];edge_failures=[];field_failures=[];edge_max=0.;field_max=0.
    for sheet,profiles in ctx.profiles.items():
        owned={fid:r for fid,r in valid.items() if r['sheet']==sheet};detail={'sheet':sheet,'valid_deck_screws':len(owned),'profiles':{},'field_lines':[]}
        for label,profile in profiles.items():
            profile_rows=[]
            for pi,poly in enumerate(polygons(profile)):
                for ri,rawring in enumerate([poly.exterior,*poly.interiors]):
                    ring=LineString(rawring.coords);coords=np.asarray(ring.coords);associated=edge_station_associations(ring,poly,owned,rules);gaps=station_gaps([q['station_in'] for q in associated],ring.length,True);maximum=max(q['length_in'] for q in gaps);edge_max=max(edge_max,maximum);bad=[g for g in gaps if g['length_in']>rules.edge_interval_in+rules.interval_roundoff_in];rid=f'{sheet}/{label}/{pi}/{ri}'
                    if bad:edge_failures.append({'ring':rid,'gaps':bad})
                    segments=[];station=0.
                    for ei,(a,b) in enumerate(zip(coords,coords[1:])):
                        line=LineString([a,b]);length=line.length
                        if length==0:continue
                        u=(b-a)/length;inside=np.array([-u[1],u[0]]);band=Polygon([a,b,b+inside*rules.bearing_band_in,a+inside*rules.bearing_band_in]).intersection(poly)
                        uncovered=line.difference(support.buffer(rules.plan_coincidence_in));ranges=clipped_segment_ranges(line,uncovered);missing_band=band.difference(support.buffer(rules.plan_coincidence_in));stock=ctx.parts[sheet]['sheet_stock']
                        seam=any(max(abs(a[k]-v/INCH),abs(b[k]-v/INCH))<=rules.report_length_epsilon_in for k,key in [(0,'eastBoundsM'),(1,'northBoundsM')] for v in stock[key]);perimeter=line.difference(ctx.perimeter.buffer(rules.report_length_epsilon_in)).length<=rules.report_length_epsilon_in
                        row={'edge':rid+f'/e{ei}','kind':'sheet_seam' if seam else 'octagonal_perimeter' if perimeter else 'stand_notch','start_east_north_in':a.tolist(),'end_east_north_in':b.tolist(),'length_in':float(length),'unsupported_ranges_in':ranges,'unsupported_length_in':float(uncovered.length),'unbacked_3_8in_band_area_in2':float(missing_band.area),'bearing_band_area_in2':float(band.area),'receiver_ids':[pid for pid,g in masks.items() if line.intersection(g.buffer(rules.plan_coincidence_in)).length>rules.plan_coincidence_in],'screw_stations':[{'screw':s['screw'],'station_on_segment_in':s['station_in']-station} for s in associated if station-rules.plan_coincidence_in<=s['station_in']<=station+length+rules.plan_coincidence_in]}
                        if uncovered.length>rules.report_length_epsilon_in or missing_band.area>rules.report_area_epsilon_in2:bearing_failures.append(row)
                        segments.append(row);station+=length
                    profile_rows.append({'ring':rid,'perimeter_in':float(ring.length),'screw_associations':associated,'maximum_interval_in':float(maximum),'intervals_over_6in':bad,'segments':segments})
            detail['profiles'][label]=profile_rows
        fieldshape=profiles['upper'].intersection(profiles['lower']);e0,e1=np.asarray(ctx.parts[sheet]['sheet_stock']['eastBoundsM'])/INCH
        for jid,e in ctx.joists.items():
            if jid in excluded or not e0+.4375<e<e1-.4375:continue
            for component,line in enumerate(lines(fieldshape.intersection(LineString([(e,-10000),(e,10000)])))):
                if line.length<=rules.plan_coincidence_in:continue
                n0,n1=sorted([line.coords[0][1],line.coords[-1][1]]);positions=[{'screw':fid,'station_in':s['east_north_in'][1]-n0} for fid,s in owned.items() if jid in s['actual_ray_receivers_in'] and n0-rules.plan_coincidence_in<=s['east_north_in'][1]<=n1+rules.plan_coincidence_in];gaps=station_gaps([p['station_in'] for p in positions],n1-n0,False);maximum=max(g['length_in'] for g in gaps);field_max=max(field_max,maximum);bad=[g for g in gaps if g['length_in']>rules.field_interval_in+rules.interval_roundoff_in];row={'sheet':sheet,'joist':jid,'component':component,'east_in':float(e),'north_interval_in':[float(n0),float(n1)],'screws':positions,'maximum_interval_in':float(maximum),'intervals_over_12in':bad};detail['field_lines'].append(row)
                if bad:field_failures.append(row)
        sheets.append(detail)
    failures=bool(ctx.geometry_failures or screw_failures or bearing_failures or edge_failures or field_failures)
    return {'status':'FAIL' if failures else 'PASS','capacity_verified':False,'scope':'Actual occupied sheet/receiver geometry, mapped bores, gross edge contact and chosen6in edge/12in intermediate support screw pattern. No capacity or raw-triangle certificate.','source':ctx.provenance,'rules':vars(rules),'counts':{'physical_parts':len(ctx.parts),'sheets':len(ctx.sheet_ids),'support_members':len(ctx.support_ids),'contact_members':len(masks),'new_backers':len(ctx.backer_ids),'installed_deck_screws':len(screw_records),'valid_deck_screws':len(valid)},'maximum_edge_interval_in':edge_max,'maximum_field_interval_in':field_max,'minimum_panel_setback_in':min((r['setback_in'] for r in valid.values()),default=None),'minimum_receiving_penetration_in':min((r['maximum_receiving_length_in'] for r in valid.values()),default=None),'geometry_failures':ctx.geometry_failures,'screw_failures':screw_failures,'bearing_failures':bearing_failures,'edge_spacing_failures':edge_failures,'field_spacing_failures':field_failures,'stock_checks':ctx.stock_checks,'wood_bore_reconstruction':ctx.reconstruction,'support_contact_heights':ctx.contact_heights,'screws':list(screw_records.values()),'sheets':sheets,'mutations':{'excluded_support_ids':sorted(excluded),'omitted_screw_ids':sorted(omitted_screw_ids),'screw_translations_in':screw_translations_in or {}}}

def meaningful_adversaries(ctx,baseline):
    if baseline['status']!='PASS':raise ValueError('Adversaries require an independently passing baseline')
    tests=[]
    for bid in ctx.backer_ids:
        mutated=audit_floor(ctx,excluded_support_ids={bid})
        if mutated['bearing_failures']:
            tests.append({'name':'remove_required_backer','removed_part':bid,'expected_failure':'bearing_failures','status':'PASS','detected_status':mutated['status'],'evidence':mutated['bearing_failures'][:4]});break
    if not tests:raise AssertionError('No actually necessary backer was found for adversary')
    edge_candidate=None
    for sheet in baseline['sheets']:
        for ring in sheet['profiles']['upper']:
            for fid in dict.fromkeys(p['screw'] for p in ring['screw_associations']):
                gaps=station_gaps([p['station_in'] for p in ring['screw_associations'] if p['screw']!=fid],ring['perimeter_in'],True)
                if max(g['length_in'] for g in gaps)>ctx.rules.edge_interval_in+ctx.rules.interval_roundoff_in:edge_candidate=fid;break
            if edge_candidate:break
        if edge_candidate:break
    mutated=audit_floor(ctx,omitted_screw_ids={edge_candidate});assert mutated['edge_spacing_failures']
    tests.append({'name':'remove_required_edge_screw','removed_screw':edge_candidate,'expected_failure':'edge_spacing_failures','status':'PASS','detected_status':mutated['status'],'evidence':mutated['edge_spacing_failures'][:2]})
    field_candidate=None
    for sheet in baseline['sheets']:
        for field in sheet['field_lines']:
            length=field['north_interval_in'][1]-field['north_interval_in'][0]
            for fid in dict.fromkeys(p['screw'] for p in field['screws']):
                gaps=station_gaps([p['station_in'] for p in field['screws'] if p['screw']!=fid],length,False)
                if max(g['length_in'] for g in gaps)>ctx.rules.field_interval_in+ctx.rules.interval_roundoff_in:field_candidate=fid;break
            if field_candidate:break
        if field_candidate:break
    mutated=audit_floor(ctx,omitted_screw_ids={field_candidate});assert mutated['field_spacing_failures']
    tests.append({'name':'remove_required_field_screw','removed_screw':field_candidate,'expected_failure':'field_spacing_failures','status':'PASS','detected_status':mutated['status'],'evidence':mutated['field_spacing_failures'][:1]})
    moved=None
    for source in baseline['screws']:
        if source['setback_in']<2:continue
        fid=source['screw'];sheet=source['sheet'];q=np.asarray(source['east_north_in'])
        for de,dn in [(4,0),(-4,0),(6,0),(-6,0),(8,0),(-8,0),(4,4),(-4,4)]:
            target=q+[de,dn]
            if any(not p.covers(Point(target)) or p.boundary.distance(Point(target))<.5 for p in ctx.profiles[sheet].values()):continue
            records,failures=validate_screws(ctx,screw_translations_in={fid:[de,dn,0]})
            rec=records[fid]
            if rec['maximum_receiving_length_in']<ctx.rules.interval_roundoff_in and 'INSUFFICIENT_ACTUAL_RECEIVING_WOOD' in rec['issues'] and not rec['steel_conflicts']:
                moved={'name':'move_screw_outside_actual_receivers','moved_screw':fid,'translation_floor_in':[de,dn,0],'declared_receiver_ids_unchanged':source['declared_receiver_ids'],'expected_failure':'INSUFFICIENT_ACTUAL_RECEIVING_WOOD','status':'PASS','detected_status':'FAIL','evidence':rec};break
        if moved:break
    if moved is None:raise AssertionError('Could not construct isolated receiver adversary')
    tests.append(moved)
    return {'status':'PASS','basis':'Each case changes installed physical support/hardware while retaining the same measured source wood and its existing drilled holes; no source files are written. Required screws are selected by a real failing interval after removal, not by rejected candidate lists.','tests':tests}

def audit_source(path,run_adversaries=False,rules=Rules()):
    data,provenance=read_source(path);ctx=FloorContext(data,provenance,rules);result=audit_floor(ctx)
    if run_adversaries:result['adversaries']=meaningful_adversaries(ctx,result) if result['status']=='PASS' else {'status':'SKIPPED','reason':'Baseline has actual reported failures; adversaries cannot certify a failing floor.'}
    if sha256(path)!=provenance['metadata_sha256']:raise ValueError('Source metadata changed during audit')
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path);parser.add_argument('--output-prefix',type=Path,default=Path('final-floor-bearing'));parser.add_argument('--adversaries',action='store_true');args=parser.parse_args()
    report=audit_source(args.source,args.adversaries);path=Path(str(args.output_prefix)+'-report.json');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(report,indent=2)+'\n')
    if report.get('adversaries'):Path(str(args.output_prefix)+'-adversaries.json').write_text(json.dumps(report['adversaries'],indent=2)+'\n')
    summary={k:report[k] for k in ['status','source','counts','maximum_edge_interval_in','maximum_field_interval_in','minimum_panel_setback_in','minimum_receiving_penetration_in','capacity_verified']};summary['failure_counts']={k:len(report[k]) for k in ['geometry_failures','screw_failures','bearing_failures','edge_spacing_failures','field_spacing_failures']};summary['adversaries']=report.get('adversaries',{}).get('status');print(json.dumps(summary,indent=2))
    if report['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()

# TIMESTAMP END 2026-11-05T12:32:16+00:00 | REVISION R000040
