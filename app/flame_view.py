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
 <button id="play"></button><button id="replay"></button>
 <span style="margin-left:6px" id="speedlab"></span><button data-s="1" class="on" id="rt"></button><button data-s="2">2×</button><button data-s="4">4×</button>
</div>
<script>
const P = __DATA__;
const L = __LABELS__;
const STATUS = {"in range":"#15803D","extrapolation":"#B45309","unreliable":"#B91C1C"};
const row = document.getElementById('row');
const V = P.map((p,i)=>{
  const el = document.createElement('div'); el.className='panel';
  const g = !p.gravity ? L.microgravity : (Math.abs(p.gravity-1)<1e-9 ? '1 g' : (Math.abs(p.gravity-1/6)<1e-9 ? '1/6 g' : p.gravity.toFixed(2)+' g'));
  el.innerHTML = `<div class="head"><span class="t">${p.label}</span><span class="chip" style="background:${!p.gravity?'#1E3A8A':(p.gravity<1?'#4B5563':'#7C2D12')};color:#fff">${g}</span></div>
   <canvas></canvas><div class="bar"><div></div></div>
   <div class="foot"><span class="hud"></span><br>
   K <b>${p.K_mm2_s.toFixed(2)} ${L.mm2s}</b> · ${p.extinguishes ? (p.sustained ? L.flame_out_at : L.no_sustained) : L.burns_out_in} <b>${p.sustained ? p.t_end_s.toFixed(1)+' '+L.s : ''}</b>
   · T<sub>f</sub> <b>${Math.round(p.T_f_K)} K</b><br>
   O<sub>2</sub> ${(p.x_o2*100).toFixed(0)} % · ${p.p_psi.toFixed(1)} psi · <span class="chip" style="background:${STATUS[p.status]||'#6B7280'};color:#fff">${L[p.status]||p.status}</span></div>`;
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
  let need=0; P.forEach(p=>{const R=p.series.flame_d_mm[0]/2; const S=shp(p); need=Math.max(need, p.gravity? Math.max(R*(S.up+S.dn)*1.05, R*2.5) : R*2.5);});
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
const rgba=(c,a)=>`rgba(${c[0]|0},${c[1]|0},${c[2]|0},${Math.max(0,Math.min(1,a))})`;
const BLUE=[90,140,255], DEEP=[60,80,235], VIOLET=[150,115,255];
const mix=(a,b,f)=>a.map((q,i)=>q+(b[i]-q)*Math.max(0,Math.min(1,f)));
function noise(a,t){return Math.sin(3*a+1.7*t)*0.5+Math.sin(5*a-2.3*t+1)*0.3+Math.sin(9*a+3.1*t+2)*0.2;}
// smooth value noise + fractal sum: illustrative turbulence only (all physics comes from Python)
const _P=(()=>{const r=rnd(99);return Array.from({length:512},()=>r());})();
function vn(x,y){const xi=Math.floor(x),yi=Math.floor(y),xf=x-xi,yf=y-yi;
  const h=(i,j)=>_P[(((i*57+j*131)%512)+512)%512], sm=f=>f*f*(3-2*f), u=sm(xf), w=sm(yf);
  const a0=h(xi,yi)+(h(xi+1,yi)-h(xi,yi))*u, a1=h(xi,yi+1)+(h(xi+1,yi+1)-h(xi,yi+1))*u; return a0+(a1-a0)*w;}
function fbm(x,y){return 0.55*vn(x,y)+0.3*vn(2.1*x+5.2,2.1*y+1.3)+0.15*vn(4.3*x+9.1,4.3*y+7.7);}

function background(c,v){
  const g=c.createRadialGradient(v.W/2,v.H*0.48,0,v.W/2,v.H*0.48,Math.max(v.W,v.H)*0.78);
  g.addColorStop(0,'#0C1426'); g.addColorStop(0.6,'#060A15'); g.addColorStop(1,'#010207'); c.fillStyle=g; c.fillRect(0,0,v.W,v.H);
  c.fillStyle='rgba(255,255,255,0.5)';
  stars.forEach(s=>{c.globalAlpha=0.12+0.3*s[2]; c.fillRect(s[0]*v.W,s[1]*v.H,s[2]>0.8?1.5:1,s[2]>0.8?1.5:1);}); c.globalAlpha=1;
}
function droplet(c,x,y,r,p,glow,col){
  r=Math.max(r,2.2);
  const liq = p.fuel==='Heptane' ? [250,228,175] : [200,225,255];
  const g=c.createRadialGradient(x-r*0.35,y-r*0.4,r*0.08,x,y,r);
  g.addColorStop(0,rgba([255,255,255],0.95)); g.addColorStop(0.3,rgba(liq,0.85)); g.addColorStop(1,rgba(liq.map(q=>q*0.35),0.95));
  c.beginPath(); c.arc(x,y,r,0,6.283); c.fillStyle=g; c.fill();
  if(glow>0){ // rim light from the surrounding flame
    c.save(); c.globalCompositeOperation='lighter';
    const rg=c.createRadialGradient(x,y,r*0.55,x,y,r*1.08);
    rg.addColorStop(0,rgba(col,0)); rg.addColorStop(0.85,rgba(col,0.55*Math.min(1,glow))); rg.addColorStop(1,rgba(col,0));
    c.fillStyle=rg; c.beginPath(); c.arc(x,y,r*1.08,0,6.283); c.fill(); c.restore();
  }
}
function ring(c,x,y,R,w,col,a,t,wob){ // soft annulus (flame sheet) with a slight wobble
  c.beginPath();
  for(let i=0;i<=120;i++){const an=i/120*6.283; const rr=(R+w)*(1+wob*noise(an,t*1.3));
    const px=x+rr*Math.cos(an), py=y+rr*Math.sin(an); i?c.lineTo(px,py):c.moveTo(px,py);}
  const g=c.createRadialGradient(x,y,Math.max(0,R-w*1.6),x,y,R+w);
  g.addColorStop(0,rgba(col,0)); g.addColorStop(0.62,rgba(mix(col,[255,255,255],0.3),a)); g.addColorStop(1,rgba(col,0));
  c.fillStyle=g; c.fill();
}
// microgravity: spherical flame. Heptane: luminous soot shell inside a thin blue reaction sheet (as in FLEX images);
// methanol: nearly soot-free, a faint blue-violet sphere.
function sphereFlame(c,v,x,y,R,I,t){
  const p=v.p, soot=p.flame_rgb;
  c.globalCompositeOperation='lighter';
  const hc=p.sooty?soot:BLUE;
  let g=c.createRadialGradient(x,y,R*0.4,x,y,R*2.0);
  g.addColorStop(0,rgba(hc,0)); g.addColorStop(0.28,rgba(hc,0.11*I)); g.addColorStop(1,rgba(hc,0));
  c.fillStyle=g; c.beginPath(); c.arc(x,y,R*2.0,0,6.283); c.fill();
  ring(c,x,y,R,R*0.06,BLUE,(p.sooty?0.45:0.8)*I,t,0.012);
  if(!p.sooty){ ring(c,x,y,R*0.9,R*0.2,VIOLET,0.22*I,t+3,0.02); ring(c,x,y,R*1.02,R*0.03,[200,215,255],0.35*I,t+1,0.01); }
  else {
    const N=150, Rs=R*0.74;
    for(let i=0;i<N;i++){
      const a0=i/N*6.283, a1=(i+1.2)/N*6.283;
      const n=fbm(Math.cos(a0)*2.2+t*0.22, Math.sin(a0)*2.2-t*0.18);
      const r0=Rs*(0.92+0.08*n), th=R*(0.08+0.13*n);
      const col=mix(soot,[255,250,225],(n-0.45)*1.6);
      const gg=c.createRadialGradient(x,y,Math.max(0,r0-th),x,y,r0+th);
      gg.addColorStop(0,rgba(col,0)); gg.addColorStop(0.5,rgba(col,(0.3+0.8*n)*I)); gg.addColorStop(1,rgba(col,0));
      c.fillStyle=gg; c.beginPath(); c.arc(x,y,r0+th,a0,a1); c.arc(x,y,Math.max(0,r0-th),a1,a0,true); c.closePath(); c.fill();
    }
    v.sparks.forEach(s=>{const ph=(s.ph+t*s.sp*0.12)%1; const rr=R*(s.rr+0.3*ph); const an=s.a+t*0.04;
      c.fillStyle=rgba(mix(soot,[255,240,200],0.5),(1-ph)*0.9*I); c.beginPath(); c.arc(x+rr*Math.cos(an),y+rr*Math.sin(an),Math.max(0.7,R*0.013),0,6.283); c.fill();});
  }
}
// buoyant shape: e = f_B(g)/f_B(1 g) from Python (0 = sphere, 1 = Earth); shape itself is illustrative
function shp(p){const e=p.shape_e||0; return {e, up:1+(EARTH_UP-1)*e, dn:1-(1-EARTH_DN)*e, hw:1-(1-EARTH_HW)*e};}
// gravity: flame built from stacked soft layers - blue base, white-yellow luminous core (sooty fuel), orange tip,
// flicker and sway growing with gravity
function buoyantFlame(c,v,x,y,R,I,t){
  const p=v.p, S=shp(p), e=S.e, f=Math.sqrt(Math.max(e,0.01)), soot=p.flame_rgb;
  c.globalCompositeOperation='lighter';
  const Hh=R*(S.up+S.dn), base=y+R*S.dn;
  const tipJ=1+0.18*e*(fbm(t*2.4,1.3)-0.5)*2, N=48;
  const gc=p.sooty?soot:BLUE;
  let g=c.createRadialGradient(x,y-Hh*0.25,R*0.2,x,y-Hh*0.25,Hh*0.95);
  g.addColorStop(0,rgba(gc,0.15*I)); g.addColorStop(1,rgba(gc,0)); c.fillStyle=g; c.fillRect(x-Hh*1.2,y-Hh*1.5,Hh*2.4,Hh*2.6);
  for(let k=0;k<N;k++){
    const u=k/(N-1), yy=base-u*Hh*tipJ;
    const prof=Math.pow(Math.sin(Math.PI*Math.min(1,0.2+u*0.88)),0.75)*Math.pow(1-u,0.32);
    const w=R*S.hw*(0.3+0.9*prof)*(1-0.3*e*u);
    const sway=e*R*0.25*Math.pow(u,1.6)*(fbm(u*2.6-t*1.7*f,t*0.6)-0.5)*2;
    let col,a;
    if(p.sooty){
      if(u<0.15){col=mix(BLUE,[140,170,255],u/0.15);a=0.34;}
      else if(u<0.55){col=mix([255,240,205],soot,(u-0.15)/0.4);a=0.3;}
      else {col=mix(soot,[225,85,20],(u-0.55)/0.45);a=0.32*(1-Math.pow((u-0.55)/0.45,1.6));}
    } else {col=mix(BLUE,VIOLET,u*0.7);a=0.13*(1-Math.pow(u,1.8));}
    a*=I*(0.8+0.4*fbm(u*4.5-t*3*f,k*0.37))*(1-0.45*(1-e)*u);
    const rx=Math.max(1,w*0.58), ry=Hh/N*2.8, cx=x+sway;
    c.save(); c.translate(cx,yy); c.scale(1,ry/rx);
    const gg=c.createRadialGradient(0,0,0,0,0,rx);
    if(p.sooty){gg.addColorStop(0,rgba(col,a)); gg.addColorStop(0.65,rgba(col,a*0.55)); gg.addColorStop(1,rgba(col,0));}
    else {gg.addColorStop(0,rgba(col,a*0.12)); gg.addColorStop(0.78,rgba(col,a)); gg.addColorStop(1,rgba(col,0));}
    c.fillStyle=gg; c.beginPath(); c.arc(0,0,rx,0,6.283); c.fill(); c.restore();
  }
  if(p.sooty){ // fuel-rich dark zone around the droplet
    c.globalCompositeOperation='destination-out';
    const dg=c.createRadialGradient(x,y-R*0.12,0,x,y-R*0.12,R*0.58);
    dg.addColorStop(0,'rgba(0,0,0,0.8)'); dg.addColorStop(1,'rgba(0,0,0,0)'); c.fillStyle=dg; c.fillRect(x-R,y-R,2*R,2*R);
    c.globalCompositeOperation='lighter';
    if(e>0.05) v.sparks.forEach(s=>{const ph=(s.ph+t*s.sp*0.5*f)%1;
      const px=x+R*0.7*(fbm(s.a+ph*2,t*0.3)-0.5)*2*ph, py=base-Hh*(0.45+ph*0.95);
      c.fillStyle=rgba([255,195,95],(1-ph)*0.6*I); c.beginPath(); c.arc(px,py,Math.max(0.6,R*0.017),0,6.283); c.fill();});
  }
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
    const p=v.p, sc=scalePx(v), x=v.W/2, y=p.gravity? v.H*(0.5+0.2*shp(p).e) : v.H*0.5;
    const tend=p.t_end_s, tp=Math.min(clock,tend), s=interp(p,tp);
    let I=Math.pow(p.T_f_K/2300,2); I=Math.max(0.55,Math.min(1.6,I));
    I*=Math.min(1,clock/IGN);
    let R=s.fd/2*sc;
    if(!p.sustained){R=p.series.flame_d_mm[0]/2*sc*Math.min(1,clock/0.25)*0.7; I*=Math.max(0,1-clock/0.9);}
    else if(clock>tend){I*=Math.max(0,1-(clock-tend)/FADE);}
    const rd=s.d/2*sc, burnedOut=!p.extinguishes&&clock>=tend;
    if(I>0.003&&R>0.5){ // flame drawn on its own layer, then composited with bloom (soft glow passes + crisp pass)
      if(!v.fx||v.fx.width!==v.cv.width||v.fx.height!==v.cv.height){v.fx=document.createElement('canvas'); v.fx.width=v.cv.width; v.fx.height=v.cv.height;}
      const fc=v.fx.getContext('2d'); fc.setTransform(1,0,0,1,0,0); fc.clearRect(0,0,v.fx.width,v.fx.height); fc.setTransform(DPR,0,0,DPR,0,0);
      p.gravity? buoyantFlame(fc,v,x,y,R,I,wall) : sphereFlame(fc,v,x,y,R,I,wall);
      c.save(); c.setTransform(1,0,0,1,0,0); c.globalCompositeOperation='lighter';
      c.filter=`blur(${(Math.max(6,R*0.3)*DPR).toFixed(1)}px)`; c.globalAlpha=0.85; c.drawImage(v.fx,0,0);
      c.filter=`blur(${(Math.max(1.2,R*0.045)*DPR).toFixed(1)}px)`; c.globalAlpha=0.9; c.drawImage(v.fx,0,0);
      c.filter='none'; c.globalAlpha=0.5; c.drawImage(v.fx,0,0);
      c.restore();
    }
    if(!burnedOut) droplet(c,x,y,rd,p,I,p.sooty?mix(p.flame_rgb,[255,255,255],0.2):BLUE);
    if(p.extinguishes&&clock>tend+(p.sustained?0:0.9)){ smoke(c,x,y,Math.max(rd*3,12),clock-tend-0.2,p.gravity);
      label(c,v,p.sustained?`${L.FLAME_OUT} · ${(p.unburned_fraction*100).toFixed(0)} % ${L.fuel_left}`:L.NO_SUSTAINED,'#FCA5A5'); }
    else if(burnedOut) label(c,v,L.BURNED_OUT,'#FDE68A');
    v.bar.style.width=(tend>0?Math.min(1,clock/tend)*100:100)+'%';
    v.hud.innerHTML=`t <b>${tp.toFixed(1)} ${L.s}</b> · d <b>${s.d.toFixed(2)} ${L.mm}</b> · ${L.burned} <b>${(s.b*100).toFixed(0)} %</b>`;
  });
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
const pb=document.getElementById('play');
pb.textContent='❚❚ '+L.Pause; document.getElementById('replay').textContent='↺ '+L.Replay;
document.getElementById('speedlab').textContent=L.Speed; document.getElementById('rt').textContent='1× '+L.real_time;
pb.onclick=()=>{playing=!playing; pb.textContent=playing?'❚❚ '+L.Pause:'▶ '+L.Play;};
document.getElementById('replay').onclick=()=>{clock=0; playing=true; pb.textContent='❚❚ '+L.Pause;};
document.querySelectorAll('button[data-s]').forEach(b=>b.onclick=()=>{speed=+b.dataset.s; document.querySelectorAll('button[data-s]').forEach(q=>q.classList.toggle('on',q===b));});
</script></body></html>
"""


LABELS_EN = {  # texts drawn by the JavaScript; app/i18n.py supplies the Russian set
    "microgravity": "microgravity",
    "flame_out_at": "flame out at",
    "no_sustained": "no sustained flame",
    "burns_out_in": "burns out in",
    "s": "s",
    "mm": "mm",
    "mm2s": "mm²/s",
    "burned": "burned",
    "FLAME_OUT": "FLAME OUT",
    "fuel_left": "of fuel left",
    "NO_SUSTAINED": "NO SUSTAINED FLAME",
    "BURNED_OUT": "BURNED OUT",
    "Pause": "Pause",
    "Play": "Play",
    "Replay": "Replay",
    "Speed": "Speed",
    "real_time": "real time",
    "in range": "in range",
    "extrapolation": "extrapolation",
    "unreliable": "unreliable",
}


def html(sims: list[dict], labels: dict | None = None) -> str:
    keep = (
        "label",
        "fuel",
        "gravity",
        "shape_e",
        "x_o2",
        "p_psi",
        "K_mm2_s",
        "t_end_s",
        "extinguishes",
        "sustained",
        "unburned_fraction",
        "T_f_K",
        "status",
        "sooty",
        "flame_rgb",
        "series",
    )
    data = json.dumps([{k: s[k] for k in keep} for s in sims]).replace("</", "<\\/")
    lab = json.dumps({**LABELS_EN, **(labels or {})}).replace("</", "<\\/")
    return _HTML.replace("__DATA__", data).replace("__LABELS__", lab)


def render(sims: list[dict], labels: dict, height: int = 500) -> None:
    components.html(html(sims, labels), height=height, scrolling=False)
