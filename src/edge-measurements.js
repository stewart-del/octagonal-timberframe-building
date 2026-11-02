/* Fitted-model feature-edge measurements. No source vertices or IDs are edited.
 * Lengths describe the displayed fitted prototype, not fabrication instructions.
 * planeAngleDeg = acute angle between planes, 0..90 degrees (winding independent).
 * normalAngleDeg = angle between the two mesh normals, 0..180 degrees.
 * interiorAngleDeg = material-side dihedral, 0..360 degrees, only for a closed,
 * consistently wound single shell with nonzero signed volume. This assumes an
 * embedded solid boundary; self-intersections are not tested. Never a saw setting.
 */
(function (root) {
  'use strict';
  const add = (a,b) => a.map((x,i)=>x+b[i]);
  const sub = (a,b) => a.map((x,i)=>x-b[i]);
  const scale = (a,s) => a.map(x=>x*s);
  const dot = (a,b) => a.reduce((s,x,i)=>s+x*b[i],0);
  const cross = (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
  const norm = a => Math.hypot(...a);
  const unit = a => scale(a,1/norm(a));
  const clamp = v => Math.max(-1,Math.min(1,v));
  const degrees = v => v*180/Math.PI;
  const cache = new WeakMap();

  function analyse(vertices, triangles, options={}) {
    const weldToleranceM = options.weldToleranceM ?? 1e-6;
    const angleToleranceDeg = options.angleToleranceDeg ?? .1;
    if (!(weldToleranceM>0) || !(angleToleranceDeg>0 && angleToleranceDeg<10)) throw Error('Invalid edge tolerances');
    const cosThreshold = Math.cos(angleToleranceDeg*Math.PI/180);
    const lineDistanceToleranceM = 2*weldToleranceM;
    const lineAngularTolerance = 1e-5;
    const directionBin = 1e-3;
    const vertexCells = new Map(), welded=[], vertexMap=[];
    // Neighbour-cell search avoids missing coincident vertices across rounding
    // cell boundaries. Retain an original coordinate rather than moving the mesh.
    for (const point of vertices) {
      if (!Array.isArray(point) || point.length!==3 || !point.every(Number.isFinite)) throw Error('Invalid fitted vertex');
      const cell = point.map(x=>Math.floor(x/weldToleranceM));
      let best=-1, distance=weldToleranceM;
      for(let x=-1;x<=1;x++) for(let y=-1;y<=1;y++) for(let z=-1;z<=1;z++) {
        const entries=vertexCells.get([cell[0]+x,cell[1]+y,cell[2]+z].join(',')) || [];
        for(const index of entries) {
          const d=norm(sub(point,welded[index]));
          if(d<=distance) { best=index;distance=d; }
        }
      }
      if(best<0) {
        best=welded.length;welded.push(point.slice());
        const key=cell.join(',');if(!vertexCells.has(key))vertexCells.set(key,[]);vertexCells.get(key).push(best);
      }
      vertexMap.push(best);
    }
    const buckets=[], directionCells=new Map(), validTriangles=[];
    let skippedTriangles=0, signedVolumeM3=0;
    const volumeOrigin=welded[0] || [0,0,0];
    function directionKey(u) { return u.map(x=>Math.floor(x/directionBin)); }
    function candidatesFor(u) {
      const found=new Set();
      for(const sign of [1,-1]) {
        const cell=directionKey(scale(u,sign));
        for(let x=-1;x<=1;x++) for(let y=-1;y<=1;y++) for(let z=-1;z<=1;z++) {
          const list=directionCells.get([cell[0]+x,cell[1]+y,cell[2]+z].join(',')) || [];
          for(const index of list)found.add(index);
        }
      }
      return found;
    }
    function bucketFor(a,b) {
      let u=unit(sub(b,a));
      const major=u.reduce((best,x,i)=>Math.abs(x)>Math.abs(u[best])?i:best,0);
      if(u[major]<0)u=scale(u,-1);
      for(const index of candidatesFor(u)) {
        const bucket=buckets[index];
        if(norm(cross(u,bucket.u))>lineAngularTolerance)continue;
        if(norm(cross(sub(a,bucket.origin),bucket.u))>lineDistanceToleranceM)continue;
        if(norm(cross(sub(b,bucket.origin),bucket.u))>lineDistanceToleranceM)continue;
        return bucket;
      }
      const bucket={origin:a.slice(),u,segments:[],planes:[]};
      const index=buckets.length;buckets.push(bucket);
      const key=directionKey(u).join(',');if(!directionCells.has(key))directionCells.set(key,[]);directionCells.get(key).push(index);
      return bucket;
    }
    for(let triangleIndex=0;triangleIndex<triangles.length;triangleIndex++) {
      const indices=triangles[triangleIndex];
      if(!Array.isArray(indices)||indices.length!==3||indices.some(i=>!Number.isInteger(i)||i<0||i>=vertices.length)) {skippedTriangles++;continue;}
      const points=indices.map(i=>welded[vertexMap[i]]);
      const normalRaw=cross(sub(points[1],points[0]),sub(points[2],points[0]));
      if(norm(normalRaw)<=1e-18) {skippedTriangles++;continue;}
      const normal=unit(normalRaw);
      validTriangles.push(triangleIndex);
      signedVolumeM3+=dot(sub(points[0],volumeOrigin),cross(sub(points[1],volumeOrigin),sub(points[2],volumeOrigin)))/6;
      for(let k=0;k<3;k++) {
        const a=points[k],b=points[(k+1)%3];
        if(norm(sub(a,b))<weldToleranceM*.5) {skippedTriangles++;continue;}
        const bucket=bucketFor(a,b);
        let lo=dot(sub(a,bucket.origin),bucket.u),hi=dot(sub(b,bucket.origin),bucket.u);
        const direction=hi>=lo?1:-1;
        if(lo>hi)[lo,hi]=[hi,lo];
        // Plane grouping is winding independent; inconsistent winding remains
        // visible in the topology check and prevents interior-angle claims.
        let plane=bucket.planes.findIndex(n=>Math.abs(dot(n,normal))>=cosThreshold);
        if(plane<0) {plane=bucket.planes.length;bucket.planes.push(normal);}
        bucket.segments.push({lo,hi,normal,direction,triangleIndex,plane});
      }
    }
    const parent=new Map(validTriangles.map(i=>[i,i]));
    function find(i) {let r=i;while(parent.get(r)!==r)r=parent.get(r);while(i!==r){const n=parent.get(i);parent.set(i,r);i=n;}return r;}
    function union(a,b) {const x=find(a),y=find(b);if(x!==y)parent.set(y,x);}
    let boundaryIntervals=0,nonManifoldIntervals=0,inconsistentIntervals=0;
    const atoms=[];
    for(const bucket of buckets) {
      const stops=bucket.segments.flatMap(s=>[s.lo,s.hi]).sort((a,b)=>a-b), breaks=[];
      // Cluster endpoint parameters, including long-edge/short-edge T-junctions.
      for(let i=0;i<stops.length;) {
        let j=i+1;while(j<stops.length && stops[j]-stops[i]<=weldToleranceM)j++;
        breaks.push(stops[Math.floor((i+j-1)/2)]);i=j;
      }
      const runs=[];
      for(let k=0;k<breaks.length-1;k++) {
        const lo=breaks[k],hi=breaks[k+1];if(hi-lo<weldToleranceM*.5)continue;
        const mid=(lo+hi)/2;
        // Interior midpoint test, with a small relative epsilon only. Expanding
        // ranges by the weld tolerance could count disjoint tiny segments twice.
        const epsilon=1e-12;
        const cover=bucket.segments.filter(s=>s.lo<=mid+epsilon && s.hi>=mid-epsilon);
        if(!cover.length)continue;
        if(cover.length===1)boundaryIntervals++;
        else if(cover.length!==2)nonManifoldIntervals++;
        if(cover.length===2) {
          union(cover[0].triangleIndex,cover[1].triangleIndex);
          if(cover[0].direction===cover[1].direction)inconsistentIntervals++;
        }
        const planeIds=[...new Set(cover.map(s=>s.plane))].sort((a,b)=>a-b);
        if(planeIds.length===1 && cover.length!==1)continue; // no triangle diagonals
        const key=planeIds.join(':')+'|'+(cover.length===1?'boundary':cover.length===2?'two':'many');
        const previous=runs[runs.length-1];
        if(previous && previous.key===key && Math.abs(previous.hi-lo)<=weldToleranceM) {
          previous.hi=hi;previous.atoms.push({cover,planeIds});
        } else runs.push({lo,hi,key,atoms:[{cover,planeIds}]});
      }
      for(const run of runs) atoms.push({bucket,...run});
    }
    const connectedComponents=new Set(validTriangles.map(find)).size;
    const closedConsistent=validTriangles.length>0 && skippedTriangles===0 && boundaryIntervals===0 &&
      nonManifoldIntervals===0 && inconsistentIntervals===0 && connectedComponents===1 && Math.abs(signedVolumeM3)>1e-15;
    const orientationSign=signedVolumeM3>=0?1:-1;
    const topology={closedConsistent,connectedComponents,boundaryIntervals,nonManifoldIntervals,
      inconsistentIntervals,skippedTriangles,signedVolumeM3,
      status:closedConsistent?'closed_consistently_wound_single_shell':'interior_angle_unverified',
      interiorAngleAssumption:'Closed consistently wound single shell is an embedded solid boundary; self-intersections are not tested.'};
    const edges=atoms.map(run=>{
      const {bucket}=run;
      const a=add(bucket.origin,scale(bucket.u,run.lo)),b=add(bucket.origin,scale(bucket.u,run.hi));
      // A collinear line can contain separated patches whose outward normals
      // oppose each other. Take local incident normals, never the first normal
      // encountered elsewhere on the infinite line.
      const first=run.atoms[0],planes=first.planeIds.map(i=>first.cover.find(s=>s.plane===i).normal);
      let planeAngleDeg=null,normalAngleDeg=null,interiorAngleDeg=null;
      const planeAnglesDeg=[];
      for(let i=0;i<planes.length;i++)for(let j=i+1;j<planes.length;j++)planeAnglesDeg.push(degrees(Math.acos(clamp(Math.abs(dot(planes[i],planes[j]))))));
      if(planes.length===2) {
        planeAngleDeg=planeAnglesDeg[0];
        if(first.cover.length===2)normalAngleDeg=degrees(Math.acos(clamp(dot(planes[0],planes[1]))));
      }
      if(closedConsistent && planes.length===2 && run.atoms.every(atom=>atom.cover.length===2)) {
        const values=run.atoms.map(atom=>{
          const [s,t]=atom.cover;
          const turn=degrees(Math.atan2(s.direction*orientationSign*dot(bucket.u,cross(s.normal,t.normal)),clamp(dot(s.normal,t.normal))));
          return 180-turn;
        });
        if(Math.max(...values)-Math.min(...values)<=angleToleranceDeg)interiorAngleDeg=values.reduce((s,x)=>s+x,0)/values.length;
      }
      const status=planes.length<2?'open_boundary':planes.length>2?'multiple_planes_no_unique_dihedral':
        interiorAngleDeg==null?'plane_angle_only_interior_unverified':'interior_angle_from_oriented_closed_mesh';
      return {a,b,endpoints:[a,b],midpoint:scale(add(a,b),.5),length_m:norm(sub(b,a)),length_in:norm(sub(b,a))/.0254,
        planeAngleDeg,normalAngleDeg,interiorAngleDeg,planeAnglesDeg,planeCount:planes.length,status,
        angleDefinition:interiorAngleDeg==null?'Acute angle between geometric planes (0–90°); not a saw setting.':
          'Material-side interior/reflex dihedral (0–360°), assuming an embedded solid boundary; not a saw setting.',
        adjacentTriangleIndices:[...new Set(run.atoms.flatMap(atom=>atom.cover.map(s=>s.triangleIndex)))],
        numericalLengthToleranceM:4*weldToleranceM};
    });
    edges.sort((a,b)=>{for(const key of ['a','b'])for(let i=0;i<3;i++){const d=a[key][i]-b[key][i];if(Math.abs(d)>1e-12)return d;}return 0;});
    return {edges,topology,weldToleranceM,angleToleranceDeg,
      scope:'Fitted prototype measurements only. No machining allowance, structural capacity, or construction approval.'};
  }

  function cached(vertices,triangles) {
    const previous=cache.get(vertices);
    if(previous && previous.triangles===triangles)return previous.result;
    const result=analyse(vertices,triangles);cache.set(vertices,{triangles,result});return result;
  }
  function edgeMeasurementData(part) {
    const result=cached(part.vertices||[],part.triangles||[]);
    return result.edges.map((edge,i)=>({...edge,id:'E'+String(i+1).padStart(3,'0'),number:i+1,
      globalId:String(part.id)+'-E'+String(i+1).padStart(3,'0'),timber_id:part.id}));
  }
  function edgeMeasurementReport(part) {
    return {...cached(part.vertices||[],part.triangles||[]),edges:edgeMeasurementData(part)};
  }
  function featureEdges(vertices,triangles) {
    const raw=[];
    for(const edge of cached(vertices,triangles).edges)raw.push(...edge.a,0,1,0,...edge.b,0,1,0);
    return raw;
  }
  function edgeMeasurementText(edge) {
    const angle=value=>Number(value).toFixed(1).replace(/\.0$/,'');
    const value=edge.interiorAngleDeg!=null?angle(edge.interiorAngleDeg)+'° inside':
      edge.planeAngleDeg!=null?'planes '+angle(edge.planeAngleDeg)+'°':
      edge.status==='open_boundary'?'open boundary':'angle unverified';
    return edge.id+' · '+edge.length_in.toFixed(2)+'″ · '+value;
  }
  function edgeMeasurementDescription(edge) {
    const definition=edge.interiorAngleDeg!=null?
      'Inside is the material-side dihedral; reflex values above 180° mark a concave edge. It assumes the checked, closed, consistently wound single shell is an embedded solid boundary; self-intersections are not tested.':
      edge.planeAngleDeg!=null?
      'Planes is the smaller, acute angle between the two geometric planes (0–90°), independent of normal direction. The material-side interior/reflex angle is unverified.':
      edge.status==='open_boundary'?'Only one adjacent surface is present, so no angle between planes is defined.':
      'More than two adjacent planes or uncertain topology prevents a unique dihedral measurement.';
    return String(edge.timber_id)+' '+edge.id+': fitted-model edge '+edge.length_in.toFixed(4)+' inches. '+definition+
      ' Collinear segments use a 1 micrometre weld tolerance; coplanar triangle seams within 0.1° are omitted. These are prototype geometry measurements, not saw settings, machining allowances, or construction approval.';
  }
  const api={analyse,edgeMeasurementData,edgeMeasurementReport,edgeMeasurementText,edgeMeasurementDescription,featureEdges};
  if(typeof module!=='undefined' && module.exports)module.exports=api;
  root.TimberEdgeMeasurements=api;
  root.edgeMeasurementData=edgeMeasurementData;
  root.edgeMeasurementReport=edgeMeasurementReport;
  root.edgeMeasurementText=edgeMeasurementText;
  root.edgeMeasurementDescription=edgeMeasurementDescription;
})(typeof globalThis!=='undefined'?globalThis:this);
