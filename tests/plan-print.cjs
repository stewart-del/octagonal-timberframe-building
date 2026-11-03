'use strict';
const assert=require('node:assert'),fs=require('node:fs');
const html=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8');
const print=html.slice(html.indexOf('@media print{'),html.indexOf('\n.step-lap-modal'));
assert(print.includes('body.plans-print>:not(#plansModal){display:none!important}'),'Other fixed/viewport UI cannot produce print pages');
assert(print.includes('.plans-note{display:none!important}'),'Modal intro/status are screen-only; sheet review/provenance remains in SVG');
// TIMESTAMP START 2026-11-03T07:21:14-05:00 | REVISION R004918
assert(print.includes('height:390mm!important')&&print.includes('size:A3 portrait'),'Dimensioned sheets retain readable A3 portrait proportions');
// TIMESTAMP END 2026-11-03T07:21:14-05:00 | REVISION R004918
assert(print.includes('.plans-sheet+.plans-sheet{break-before:page'),'Only later sheets force a page break');
assert(!print.includes('break-after:page'),'No trailing forced blank page');
assert(print.includes('display:block!important;height:auto!important'),'No viewport flex container fragmentation');
assert(print.includes('svg{display:block;width:100%!important;height:100%!important'),'SVG scales as one intact viewBox including footer');
// TIMESTAMP START 2026-11-02T22:10:21-05:00 | REVISION R004884
// TIMESTAMP START 2026-11-03T07:17:50-05:00 | REVISION R004916
const plans=fs.readFileSync(__dirname+'/../src/architectural-plans.js','utf8');assert(plans.includes('modelHash')&&plans.includes('1000 ${sheetHeight}'),'Source hash and complete dimensioned-sheet viewBox remain intact');
// TIMESTAMP END 2026-11-03T07:17:50-05:00 | REVISION R004916
// TIMESTAMP END 2026-11-02T22:10:21-05:00 | REVISION R004884
// TIMESTAMP START 2026-11-03T07:21:14-05:00 | REVISION R004918
assert(390<=420-20);
console.log('PASS: readable A3 portrait sheets, intact SVG provenance, no intro-only or trailing forced pages');
// TIMESTAMP END 2026-11-03T07:21:14-05:00 | REVISION R004918
