'use strict';
const assert=require('node:assert'),fs=require('node:fs');
const html=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8');
const right=html.slice(html.indexOf('<aside class="right"'),html.indexOf('</aside>',html.indexOf('<aside class="right"')));
assert(right.indexOf('id="selection"')<right.indexOf('load-review-controls'),'Selected piece precedes load review');
assert(right.indexOf('id="openStepLap"')<right.indexOf('hollow-controls'),'Joint comparison precedes diagnostics');
assert(/<details class="section hollow-controls">/.test(right),'Diagnostics collapsed by default');
assert(!/id="assemblyControls" open/.test(right),'Advanced assembly details collapsed');
for(const id of ['modelViewport','roomLayers','browsePieces','inspector'])assert(html.includes('href="#'+id+'"'),'Keyboard/mobile direct navigation: '+id);
assert(html.includes('.layout>.viewport{order:-1}'),'Narrow layout presents model first');
assert(html.includes('select:focus-visible,a:focus-visible,canvas:focus-visible'),'Keyboard focus visible on all principal controls');
assert(html.includes('.plans-sheet{min-width:0}'),'Fit-sheet works on narrow screens');
console.log('PASS: primary inspection and comparison order, collapsed diagnostics, model-first narrow layout, focus and direct navigation');

// TIMESTAMP START 2026-11-03T08:08:16-05:00 | REVISION R004938
const stageStart=html.indexOf('<div class="viewport-stage">'),toolbarStart=html.indexOf('<div class="viewport-toolbar">');
for(const id of ['scene','labels','loadReviewOverlay','pieceCenter']){const at=html.indexOf('id="'+id+'"');assert(at>stageStart&&at<toolbarStart,id+' stays inside the dedicated drawing stage');}
assert(html.includes('height:70svh;min-height:440px'),'Narrow-screen drawing area retains its own useful height');
assert(html.includes('position:relative;inset:auto;margin:10px;order:-1;flex:none'),'Toolbar occupies its own flow space');
assert(html.includes('Site west: porch / door')&&!html.includes('site north not assigned'));

// TIMESTAMP END 2026-11-03T08:08:16-05:00 | REVISION R004938
