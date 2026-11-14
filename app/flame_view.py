"""Burning-droplet animation window (ADR-035). Draws two panels from numbers computed by fif.insights.flame_sim;
the JavaScript only interpolates the precomputed series and paints them (no physics here).

Visual elements and what they mean:
- droplet diameter d(t), flame diameter, burn time, extinction diameter, flame temperature: from the package;
- common scale in both panels (relative theoretical flame size, which NASA reports overestimates several-fold);
- 1 g flame shape, flicker, soot sparks, ignition ramp, smoke after flame-out: illustrative only.
"""
from __future__ import annotations

import json

import streamlit.components.v1 as components

_HTML = r"""
<!doctype html><html><head><meta charset="utf-8">
<style>
:root{--ink:#111827;--muted:#6B7280;}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink);background:transparent}
.row{display:flex;gap:12px}
.panel{flex:1 1 0;min-width:0;background:#060a14;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.18)}
.head{display:flex;justify-content:space-between;align-items:center;padding:8px 12px 4px;color:#E5E7EB;font-size:13px;font-weight:600;gap:6px}
.head span.t{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chip{font-size:11px;font-weight:700;padding:2px 8px;border-radius:9px;white-space:nowrap}
canvas{display:block;width:100%}
.bar{height:4px;background:#1F2937}.bar>div{height:100%;width:0;background:linear-gradient(90deg,#F59E0B,#EA580C)}
.foot{padding:7px 12px 10px;color:#CBD5E1;font-size:12px;line-height:1.45}
.foot b{color:#F8FAFC}
.ctl{display:flex;gap:6px;align-items:center;margin:10px 0 2px;flex-wrap:wrap;font-size:12px;color:var(--muted)}
button{font:inherit;font-size:13px;border:1px solid #CBD5E1;background:#fff;color:#111827;border-radius:8px;padding:4px 10px;cursor:pointer}
button.on{background:#1D4ED8;color:#fff;border-color:#1D4ED8}
@media (max-width:520px){.row{gap:6px}.head{font-size:11px;padding:6px 8px 3px}.foot{font-size:10.5px;padding:5px 8px 8px}.chip{font-size:9.5px;padding:1px 5px}}
</style></head><body>
<div class="row" id="row"></div>
<div class="ctl">
 <button id="play">❚❚ Pause</button><button id="replay">↺ Replay</button>
 <span style="margin-left:6px">Speed</span><button data-s="1" class="on">1× real time</button><button data-s="2">2×</button><button data-s="4">4×</button>
</div>
<script>
const P = __DATA__;
const STATUS = {"in range":"#15803D","extrapolation":"#B45309","unreliable":"#B91C1C"};
const row = document.getElementById('row');
const V = P.map((p,i)=>{
  const el = document.createElement('div'); el.className='panel';
  const g = p.gravity ? '1 g' : 'microgravity';
  el.innerHTML = `<div class="head"><span class="t">${p.label}</span><span class="chip" style="background:${p.gravity?'#7C2D12':'#1E3A8A'};color:#fff">${g}</span></div>
   <canvas></canvas><div class="bar"><div></div></div>
   <div class="foot"><span class="hud"></span><br>
   K <b>${p.K_mm2_s.toFixed(2)} mm²/s</b> · ${p.extinguishes ? (p.sustained ? 'flame out at' : 'no sustained flame') : 'burns out in'} <b>${p.sustained ? p.t_end_s.toFixed(1)+' s' : ''}</b>
   · T<sub>f</sub> <b>${Math.round(p.T_f_K)} K</b><br>
   O<sub>2</sub> ${(p.x_o2*100).toFixed(0)} % · ${p.p_psi.toFixed(1)} psi · <span class="chip" style="background:${STATUS[p.status]||'#6B7280'};color:#fff">${p.status}</span></div>`;
  row.appendChild(el);
  return {p, el, cv: el.querySelector('canvas'), bar: el.querySelector('.bar>div'), hud: el.querySelector('.hud')};
});
// star field (static, seeded)
function rnd(s){return ()=>{s=(s*16807)%2147483647;return s/2147483647;}}
const stars = Array.from({length:70},((r)=>()=>[r(),r(),r()])(rnd(7)));
// sparks for sooty flames (illustrative)
V.forEach((v,i)=>{const r=rnd(11+i);v.sparks=Array.from({length:46},()=>({a:r()*6.283,ph:r(),sp:0.25+r()*0.6,rr:0.55+r()*0.4}));});

let W=300,H=300,DPR=window.devicePixelRatio||1;
function layout(){
  // canvas fills the iframe height left after header, footer and controls (iframe height is fixed by Streamlit)
  const ctl=document.querySelector('.ctl'); let other=0;
  V.forEach(v=>{other=Math.max(other, v.el.offsetHeight-v.cv.offsetHeight);});
  const avail=Math.max(180, window.innerHeight-other-ctl.offsetHeight-16);
  V.forEach(v=>{const w=v.cv.clientWidth||300; W=w; H=Math.round(Math.min(avail, Math.max(180,w*1.1)));
    v.cv.width=Math.round(w*DPR); v.cv.height=Math.round(H*DPR); v.cv.style.height=H+'px'; v.H=H; v.W=w;});
}
layout(); window.addEventListener('resize',layout);

// common scale: largest flame extent of both panels fits the window (relative theoretical size)
const EARTH_UP=2.3, EARTH_DN=0.55, EARTH_HW=0.8;
function scalePx(v){
  let need=0; P.forEach(p=>{const R=p.series.flame_d_mm[0]/2; need=Math.max(need, p.gravity? R*(EARTH_UP+EARTH_DN)*1.05 : R*2.5);});
  return Math.min(v.H*0.86, v.W*0.95)/need;
}
function interp(p,t){
  const s=p.series, ts=s.t_s, n=ts.length;
  if(t<=0||n<2) return {d:s.d_mm[0],fd:s.flame_d_mm[0],b:s.burned_frac[0]};
  if(t>=ts[n-1]) return {d:s.d_mm[n-1],fd:s.flame_d_mm[n-1],b:s.burned_frac[n-1]};
  let lo=0,hi=n-1; while(hi-lo>1){const m=(lo+hi)>>1; if(ts[m]<=t) lo=m; else hi=m;}
  const f=(t-ts[lo])/(ts[hi]-ts[lo]); const L=(a)=>a[lo]+(a[hi]-a[lo])*f;
  return {d:L(s.d_mm),fd:L(s.flame_d_mm),b:L(s.burned_frac)};
}
const rgba=(c,a)=>`rgba(${c[0]},${c[1]},${c[2]},${Math.max(0,Math.min(1,a))})`;
const BLUE=[88,140,255], DEEP=[50,70,230];
function noise(a,t){return Math.sin(3*a+1.7*t)*0.5+Math.sin(5*a-2.3*t+1)*0.3+Math.sin(9*a+3.1*t+2)*0.2;}

function background(c,v){
  const g=c.createRadialGradient(v.W/2,v.H*0.5,0,v.W/2,v.H*0.5,Math.max(v.W,v.H)*0.75);
  g.addColorStop(0,'#0B1222'); g.addColorStop(1,'#020409'); c.fillStyle=g; c.fillRect(0,0,v.W,v.H);
  c.fillStyle='rgba(255,255,255,0.5)';
  stars.forEach(s=>{c.globalAlpha=0.15+0.35*s[2]; c.fillRect(s[0]*v.W,s[1]*v.H,s[2]>0.8?1.5:1,s[2]>0.8?1.5:1);}); c.globalAlpha=1;
}
function droplet(c,x,y,r,p,glow,col){
  r=Math.max(r,2.2);
  const liq = p.fuel==='Heptane' ? [255,236,190] : [205,228,255];
  const g=c.createRadialGradient(x-r*0.35,y-r*0.4,r*0.1,x,y,r);
  g.addColorStop(0,rgba([255,255,255],0.95)); g.addColorStop(0.35,rgba(liq,0.85)); g.addColorStop(1,rgba(liq.map(q=>q*0.45),0.9));
  c.beginPath(); c.arc(x,y,r,0,6.283); c.fillStyle=g; c.fill();
  if(glow>0){c.lineWidth=Math.max(1,r*0.12); c.strokeStyle=rgba(col,0.55*glow); c.stroke();}
}
function sphereFlame(c,v,x,y,R,I,t){
  const p=v.p, col=p.flame_rgb;
  c.save(); c.globalCompositeOperation='lighter';
  // halo
  let g=c.createRadialGradient(x,y,R*0.6,x,y,R*1.7);
  const hc = p.sooty?col:BLUE;
  g.addColorStop(0,rgba(hc,0)); g.addColorStop(0.35,rgba(hc,0.16*I)); g.addColorStop(1,rgba(hc,0)); c.fillStyle=g;
  c.beginPath(); c.arc(x,y,R*1.7,0,6.283); c.fill();
  // shells: sooty -> luminous soot shell inside a blue reaction zone; methanol -> faint blue shell only
  const shells = p.sooty ? [[0.80,col,0.95,0.22],[1.0,BLUE,0.55,0.09]] : [[1.0,BLUE,0.85,0.10],[0.96,DEEP,0.5,0.18],[0.7,[40,60,160],0.18,0.35]];
  shells.forEach(([k,cc,a,w])=>{
    const Rk=R*k; c.beginPath();
    for(let i=0;i<=96;i++){const an=i/96*6.283; const rr=Rk*(1+0.018*noise(an,t*1.3+k*4)); const px=x+rr*Math.cos(an), py=y+rr*Math.sin(an); i?c.lineTo(px,py):c.moveTo(px,py);}
    const gg=c.createRadialGradient(x,y,Rk*(1-w*2.2),x,y,Rk*(1+w));
    gg.addColorStop(0,rgba(cc,0)); gg.addColorStop(0.62,rgba(cc,a*0.35*I)); gg.addColorStop(0.83,rgba(cc.map(q=>Math.min(255,q+50)),a*I)); gg.addColorStop(1,rgba(cc,0));
    c.fillStyle=gg; c.fill();
  });
  if(p.sooty){ // drifting soot sparks in the soot shell (illustrative)
    v.sparks.forEach(s=>{const ph=(s.ph+t*s.sp*0.15)%1; const rr=R*(s.rr+0.25*ph); const an=s.a+t*0.05;
      c.fillStyle=rgba(col.map(q=>Math.min(255,q+40)),(1-ph)*0.8*I); c.beginPath(); c.arc(x+rr*Math.cos(an),y+rr*Math.sin(an),Math.max(0.6,R*0.012),0,6.283); c.fill();});
  }
  c.restore();
}
function earthPath(c,x,y,R,t,scale){
  c.beginPath();
  for(let i=0;i<=120;i++){const ph=i/120*6.283; const up=Math.pow((1+Math.cos(ph))/2,3.2);
    const fl=0.10*Math.sin(t*9.0+ph*2)+0.06*Math.sin(t*14.3+1.3);
    const rr=R*scale*(EARTH_DN+(EARTH_UP-EARTH_DN)*up*(1+fl)) ;
    const side=Math.sin(ph)*(EARTH_HW/0.76)*(1-0.55*Math.pow(up,0.6));
    const px=x+rr*side*0.76+R*0.10*up*Math.sin(t*6.1), py=y-rr*Math.cos(ph)*(Math.cos(ph)>0?1:1);
    i?c.lineTo(px,py):c.moveTo(px,py);}
  c.closePath();
}
function earthFlame(c,v,x,y,R,I,t){
  const p=v.p, col=p.sooty?p.flame_rgb:BLUE;
  c.save(); c.globalCompositeOperation='lighter';
  let g=c.createRadialGradient(x,y-R*0.9,R*0.2,x,y-R*0.9,R*2.6); g.addColorStop(0,rgba(col,0.18*I)); g.addColorStop(1,rgba(col,0));
  c.fillStyle=g; c.fillRect(x-R*3,y-R*3.6,R*6,R*5);
  earthPath(c,x,y,R,t,1.0);
  const lg=c.createLinearGradient(0,y+R*EARTH_DN,0,y-R*EARTH_UP);
  lg.addColorStop(0,rgba(BLUE,0.75*I)); lg.addColorStop(0.18,rgba(BLUE,0.45*I));
  if(p.sooty){lg.addColorStop(0.38,rgba(col.map(q=>Math.min(255,q+60)),0.95*I)); lg.addColorStop(0.75,rgba(col,0.8*I)); lg.addColorStop(1,rgba([200,60,10],0));}
  else {lg.addColorStop(0.6,rgba(BLUE,0.35*I)); lg.addColorStop(1,rgba(DEEP,0));}
  c.fillStyle=lg; c.fill();
  c.globalCompositeOperation='source-over'; earthPath(c,x,y+R*0.08,R,t+0.3,0.55);  // darker fuel-rich core
  c.fillStyle=rgba([8,10,25],0.35); c.fill();
  if(p.sooty){ c.globalCompositeOperation='lighter'; v.sparks.forEach(s=>{const ph=(s.ph+t*s.sp*0.6)%1; const px=x+R*0.5*Math.sin(s.a*3+t)*(1-ph), py=y-R*(0.6+ph*2.6);
      c.fillStyle=rgba(col,(1-ph)*0.7*I); c.beginPath(); c.arc(px,py,Math.max(0.6,R*0.02),0,6.283); c.fill();});}
  c.restore();
}
function smoke(c,x,y,R,age,gravity){
  if(age<0||age>4) return; const a=Math.max(0,0.22*(1-age/4));
  for(let k=0;k<3;k++){const rr=R*(0.6+0.35*k+age*0.25); c.beginPath();
    if(gravity) c.arc(x+Math.sin(age*2+k)*R*0.2,y-R*(0.4+age*0.9+k*0.4),rr*0.5,0,6.283); else c.arc(x,y,rr,0,6.283);
    c.fillStyle=`rgba(160,170,190,${a/(k+1)})`; c.fill();}
}
function label(c,v,txt,col){c.font=`600 ${v.W<240?11:14}px system-ui`; c.textAlign='center'; c.fillStyle=col; c.fillText(txt,v.W/2,v.H-12);}

let clock=0,last=null,speed=1,playing=true;
const FADE=0.7, IGN=0.35;
const T_total=Math.max(...P.map(p=>p.t_end_s+(p.sustained?0:0.9)))+3.0;
function frame(ts){
  if(last===null) last=ts; let dt=Math.min(0.1,(ts-last)/1000); last=ts;
  if(playing){clock+=dt*speed; if(clock>T_total+1.5) clock=0;}
  const wall=ts/1000;
  V.forEach(v=>{
    const c=v.cv.getContext('2d'); c.setTransform(DPR,0,0,DPR,0,0); background(c,v);
    const p=v.p, sc=scalePx(v), x=v.W/2, y=p.gravity? v.H*0.70 : v.H*0.5;
    const tend=p.t_end_s, tp=Math.min(clock,tend), s=interp(p,tp);
    let I=Math.pow(p.T_f_K/2300,2); I=Math.max(0.55,Math.min(1.6,I));
    I*=Math.min(1,clock/IGN);
    let R=s.fd/2*sc;
    if(!p.sustained){R=p.series.flame_d_mm[0]/2*sc*Math.min(1,clock/0.25)*0.7; I*=Math.max(0,1-clock/0.9);}
    else if(clock>tend){I*=Math.max(0,1-(clock-tend)/FADE);}
    const rd=s.d/2*sc, burnedOut=!p.extinguishes&&clock>=tend;
    if(I>0.003&&R>0.5){ p.gravity? earthFlame(c,v,x,y,R,I,wall) : sphereFlame(c,v,x,y,R,I,wall); }
    if(!burnedOut) droplet(c,x,y,rd,p,I,p.sooty?p.flame_rgb:BLUE);
    if(p.extinguishes&&clock>tend+(p.sustained?0:0.9)){ smoke(c,x,y,Math.max(rd*3,12),clock-tend-0.2,p.gravity);
      label(c,v,p.sustained?`FLAME OUT · ${(p.unburned_fraction*100).toFixed(0)} % of fuel left`:'NO SUSTAINED FLAME','#FCA5A5'); }
    else if(burnedOut) label(c,v,'BURNED OUT','#FDE68A');
    v.bar.style.width=(tend>0?Math.min(1,clock/tend)*100:100)+'%';
    v.hud.innerHTML=`t <b>${tp.toFixed(1)} s</b> · d <b>${s.d.toFixed(2)} mm</b> · burned <b>${(s.b*100).toFixed(0)} %</b>`;
  });
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
const pb=document.getElementById('play');
pb.onclick=()=>{playing=!playing; pb.textContent=playing?'❚❚ Pause':'▶ Play';};
document.getElementById('replay').onclick=()=>{clock=0; playing=true; pb.textContent='❚❚ Pause';};
document.querySelectorAll('button[data-s]').forEach(b=>b.onclick=()=>{speed=+b.dataset.s; document.querySelectorAll('button[data-s]').forEach(q=>q.classList.toggle('on',q===b));});
</script></body></html>
"""


def html(sims: list[dict]) -> str:
    keep = ("label", "fuel", "gravity", "x_o2", "p_psi", "K_mm2_s", "t_end_s", "extinguishes", "sustained", "unburned_fraction",
            "T_f_K", "status", "sooty", "flame_rgb", "series")
    data = json.dumps([{k: s[k] for k in keep} for s in sims]).replace("</", "<\\/")
    return _HTML.replace("__DATA__", data)


def render(sims: list[dict], height: int = 500) -> None:
    components.html(html(sims), height=height, scrolling=False)
