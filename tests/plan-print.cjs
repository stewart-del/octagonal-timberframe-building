'use strict';
const assert=require('node:assert'),fs=require('node:fs');
const html=fs.readFileSync(__dirname+'/../src/viewer.template.html','utf8');
const print=html.slice(html.indexOf('@media print{'),html.indexOf('\n.step-lap-modal'));
assert(print.includes('body.plans-print>:not(#plansModal){display:none!important}'),'Other fixed/viewport UI cannot produce print pages');
assert(print.includes('.plans-note{display:none!important}'),'Modal intro/status are screen-only; sheet review/provenance remains in SVG');
assert(print.includes('height:180mm!important'),'Whole sheet constrained to landscape printable height');
assert(print.includes('.plans-sheet+.plans-sheet{break-before:page'),'Only later sheets force a page break');
assert(!print.includes('break-after:page'),'No trailing forced blank page');
assert(print.includes('display:block!important;height:auto!important'),'No viewport flex container fragmentation');
assert(print.includes('svg{display:block;width:100%!important;height:100%!important'),'SVG scales as one intact viewBox including footer');
const plans=fs.readFileSync(__dirname+'/../src/architectural-plans.js','utf8');assert(plans.includes('modelHash')&&plans.includes('1000 790'),'Source hash and complete sheet viewBox remain intact');
// Smallest standard landscape printable height: A4 210mm minus 20mm margins.
assert(180<=210-20);assert(180<=215.9-20);
console.log('PASS: landscape sheet sizing, intact SVG provenance, no intro-only or trailing forced pages');
