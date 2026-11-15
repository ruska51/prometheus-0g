"""Smooth fire animation for the module page (ADR-052): the flame front is drawn on a canvas by bilinear interpolation
of the computed arrival times (fif.physics.module_fire), with glow and flicker. Display only: every time shown comes
from the arrival-time grids; colours, glow and flicker are illustrative."""

from __future__ import annotations

import json
import math

import numpy as np
import streamlit.components.v1 as components
from blueprint import data_uri

_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:transparent;font-family:Inter,system-ui,sans-serif;color:#e8ecf4}
#panels{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.p{position:relative;border-radius:14px;overflow:hidden;background:#0a0f1c;justify-self:center;width:max-content;border:1px solid rgba(140,170,255,.18);transition:box-shadow .4s,border-color .4s}.p.hot{border-color:rgba(255,122,26,.65);box-shadow:0 0 28px rgba(255,90,31,.45),inset 0 0 30px rgba(255,90,31,.15)}.p.lost{border-color:#ff3b30;box-shadow:0 0 34px rgba(255,59,48,.7)}
.p.big{grid-column:1 / span 2}
@media (max-width:600px){#panels{grid-template-columns:1fr}.p.big{grid-column:auto}}
.p canvas{display:block;margin:0 auto}
.t{position:absolute;left:12px;top:8px;font-size:13px;font-weight:600;text-shadow:0 1px 3px #000}
.h{position:absolute;right:12px;top:8px;font-size:12px;padding:2px 8px;border-radius:9px;background:#2fd27a;color:#06210f;font-weight:700}
.h.no{background:#5c6678;color:#e8ecf4}
.bar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-top:4px;font-size:13px}
button{background:linear-gradient(135deg,#ffb627,#ff5a1f);border:0;color:#140a04;font-weight:800;border-radius:10px;padding:7px 14px;cursor:pointer;box-shadow:0 0 18px rgba(255,90,31,.45)}
button.s{background:#151d33;color:#e8ecf4;border:1px solid #26304a;font-weight:500}button.s.on{border-color:#f0843f;color:#f0843f}
input[type=range]{flex:1;accent-color:#f0843f}
#clock{min-width:150px;color:#ffb627;font-weight:600}
</style></head><body><div id="panels"></div>
<div class="bar"><button id="play">__PAUSE__</button><span id="clock"></span><input id="seek" type="range" min="0" max="1000" value="0">
<button class="s" data-s="0.5">0.5x</button><button class="s on" data-s="1">1x</button><button class="s" data-s="2">2x</button></div>
<script>
const D=__DATA__, L=__LABELS__;
const MAT={0:[26,34,53],1:[92,102,120],2:[201,166,107],3:[95,179,217],4:[47,210,122]};
const W=D.w, H=D.h, SC=12; // canvas pixels per cell (= blueprint.PX)
let BGD=null; const bgi=new Image(); bgi.onload=()=>{ const c=document.createElement('canvas'); c.width=W*SC; c.height=H*SC;
  const x=c.getContext('2d'); x.drawImage(bgi,0,0); BGD=x.getImageData(0,0,c.width,c.height).data; }; bgi.src=D.bg;
const panels=[];
D.envs.forEach((e,i)=>{
  const div=document.createElement('div'); div.className='p'+(i===0?' big':'');
  const cv=document.createElement('canvas'); cv.width=W*SC; cv.height=H*SC; div.appendChild(cv);
  const tl=document.createElement('div'); tl.className='t'; tl.textContent=e.label; div.appendChild(tl);
  const hb=document.createElement('div'); hb.className='h'; div.appendChild(hb);
  document.getElementById('panels').appendChild(div);
  const glow=document.createElement('canvas'); glow.width=cv.width; glow.height=cv.height;
  const idx=[...e.t.keys()].filter(k=>e.t[k]<D.never).sort((a,b)=>e.t[a]-e.t[b]);
  panels.push({e,cv,div,ctx:cv.getContext('2d'),glow,gctx:glow.getContext('2d'),hb,img:null,idx,ts:idx.map(k=>e.t[k]),parts:[],smoke:[]});
});
// ---- flame tongues, sparks and smoke (illustrative): buoyant rise scales with gravity - NASA: a flame with ~100 cm/s
// buoyant flow on Earth has ~40 cm/s on the Moon (NTRS 20210020516); in microgravity only the 20 cm/s ventilation moves it
const FLOW={earth:[0,-1.0],moon:[0,-0.4],iss:[0.2*(D.vent||1),0]};
function sprite(r,g,b){ const c=document.createElement('canvas'); c.width=c.height=64; const x=c.getContext('2d');
  const gr=x.createRadialGradient(32,32,0,32,32,32); gr.addColorStop(0,`rgba(${r},${g},${b},1)`); gr.addColorStop(0.35,`rgba(${r},${g},${b},.55)`);
  gr.addColorStop(1,`rgba(${r},${g},${b},0)`); x.fillStyle=gr; x.fillRect(0,0,64,64); return c; }
const SPR=[sprite(255,248,215),sprite(255,190,70),sprite(255,110,30),sprite(220,50,20)], SMK=sprite(60,58,62), SPK=sprite(255,230,160);
function lowerBound(a,v){ let lo=0,hi=a.length; while(lo<hi){ const m=(lo+hi)>>1; if(a[m]<v) lo=m+1; else hi=m; } return lo; }
function emit(p,dt){
  const {idx,ts,e}=p, win=D.win, i0=lowerBound(ts,T-win*0.55), i1=lowerBound(ts,T+1e-6), n=i1-i0;
  p.div.classList.toggle('hot', n>0);
  if(n<=0) return 0;
  const [fx,fy]=FLOW[e.kind]||[0,-0.4], rate=Math.min(260, 30+n*0.9)*dt*60/60;
  for(let k=0;k<rate;k++){ const c=idx[i0+Math.floor(Math.random()*n)], cx=(c%W+Math.random())*SC, cy=(Math.floor(c/W)+Math.random())*SC;
    const age=(T-e.t[c])/win, hot=Math.max(0,1-age*1.6);
    p.parts.push({x:cx,y:cy,vx:fx*120+(Math.random()-0.5)*(e.kind==='iss'?46:26),vy:fy*120+(Math.random()-0.5)*(e.kind==='iss'?46:18),
      life:0,max:0.35+Math.random()*0.55*(e.kind==='earth'?1.3:1),s:(0.9+Math.random()*1.4)*SC*(0.7+hot),hot});
    if(Math.random()<0.06) p.parts.push({x:cx,y:cy,vx:fx*200+(Math.random()-0.5)*90,vy:fy*200-(Math.random())*60,life:0,max:0.6+Math.random()*0.9,s:3,spark:1});
    if(Math.random()<0.05 && e.kind!=='iss') p.smoke.push({x:cx,y:cy,vx:fx*30+(Math.random()-0.5)*14,vy:fy*55,life:0,max:2.5+Math.random()*2,s:SC*2.2});
    if(Math.random()<0.03 && e.kind==='iss') p.smoke.push({x:cx,y:cy,vx:fx*40+(Math.random()-0.5)*22,vy:(Math.random()-0.5)*22,life:0,max:3+Math.random()*2,s:SC*2.4});
  }
  if(p.parts.length>900) p.parts.splice(0,p.parts.length-900);
  if(p.smoke.length>160) p.smoke.splice(0,p.smoke.length-160);
  return n;
}
function particles(p,dt){
  const ctx=p.ctx;
  ctx.save(); ctx.globalCompositeOperation='source-over';
  p.smoke=p.smoke.filter(q=>(q.life+=dt)<q.max);
  for(const q of p.smoke){ q.x+=q.vx*dt; q.y+=q.vy*dt; q.vx*=0.995; const a=q.life/q.max, sz=q.s*(1+a*2.2);
    ctx.globalAlpha=0.22*Math.sin(Math.PI*a); ctx.drawImage(SMK,q.x-sz/2,q.y-sz/2,sz,sz); }
  ctx.globalCompositeOperation='lighter';
  p.parts=p.parts.filter(q=>(q.life+=dt)<q.max);
  for(const q of p.parts){ q.x+=q.vx*dt; q.y+=q.vy*dt; const a=q.life/q.max;
    if(q.spark){ ctx.globalAlpha=1-a; ctx.drawImage(SPK,q.x-3,q.y-3,6,6); continue; }
    q.vx*=0.98; const sz=q.s*(1-a*0.65), sp=SPR[Math.min(3,Math.floor(a*3.2+(1-q.hot)*0.8))];
    ctx.globalAlpha=(1-a)*0.75; ctx.drawImage(sp,q.x-sz/2,q.y-sz/2,sz,sz); }
  ctx.restore();
}
function at(arr,x,y){ // bilinear interpolation over the burning neighbours only (cells the flame never reaches are skipped)
  const cx=Math.min(Math.floor(x),W-1), cy=Math.min(Math.floor(y),H-1), own=arr[cy*W+cx];
  if(own>=D.never) return own;
  const fx=Math.min(Math.max(x-0.5,0),W-1), fy=Math.min(Math.max(y-0.5,0),H-1);
  const x0=Math.floor(fx), y0=Math.floor(fy), x1=Math.min(x0+1,W-1), y1=Math.min(y0+1,H-1), tx=fx-x0, ty=fy-y0;
  const v=[arr[y0*W+x0],arr[y0*W+x1],arr[y1*W+x0],arr[y1*W+x1]], wt=[(1-tx)*(1-ty),tx*(1-ty),(1-tx)*ty,tx*ty];
  let s=0,ws=0; for(let i=0;i<4;i++){ if(v[i]<D.never){ s+=v[i]*wt[i]; ws+=wt[i]; } }
  return ws>0? s/ws : own;
}
function base(m,x,y){ // crisp materials with a light texture: fabric weave, brushed metal, glossy acrylic
  const cx=Math.min(Math.floor(x),W-1), cy=Math.min(Math.floor(y),H-1), code=m[cy*W+cx], c=MAT[code];
  let f=1;
  if(code===2) f=0.93+0.07*((Math.floor(x*SC/3)+Math.floor(y*SC/3))%2);            // weave
  else if(code===1) f=0.92+0.08*Math.sin(y*SC*0.9);                                 // brushed metal
  else if(code===3) f=1.0+0.12*Math.max(0,1-Math.abs(((x+y)%3)-1.5));              // gloss streak
  else if(code===0) f=1.0;
  return c.map(v=>Math.min(255,v*f));
}
const STOPS=[[0,[255,250,220]],[0.15,[255,214,90]],[0.45,[255,140,30]],[0.8,[235,70,25]],[1.3,[150,32,18]],[2.0,[40,24,20]]];
function fire(age,win){ const a=age/win; if(a>=2) return [[24,16,14],0];
  for(let i=1;i<STOPS.length;i++){ if(a<=STOPS[i][0]){ const [a0,c0]=STOPS[i-1],[a1,c1]=STOPS[i], f=(a-a0)/(a1-a0);
    return [c0.map((v,k)=>v+(c1[k]-v)*f), Math.max(0,1-a/1.3)]; } }
  return [[24,16,14],0];
}
function noise(x,y,t){ return 0.5+0.5*Math.sin(x*0.9+t*7.3)*Math.sin(y*1.3-t*5.1); }
let T=0, speed=1, playing=false, last=null; const TEND=D.t_end*1.05, DUR=20; // seconds of animation at 1x
function draw(){
  panels.forEach(p=>{
    const {ctx,gctx,cv,e}=p, w=cv.width, h=cv.height;
    if(!p.img) p.img=ctx.createImageData(w,h);
    const im=p.img.data, g=gctx.createImageData(w,h), gd=g.data, win=D.win;
    const step=1;
    for(let py=0;py<h;py+=step){ for(let px=0;px<w;px+=step){
      const x=px/SC, y=py/SC, bi=(py*w+px)*4; let c=BGD? [BGD[bi],BGD[bi+1],BGD[bi+2]] : base(D.mat,x,y), glowA=0;
      const ta=at(e.t,x,y);
      if(ta<=T){ const [fc,ga]=fire(T-ta,win); const n=noise(x,y,T/win);
        const burnAmt=Math.min(0.86,(T-ta)/(win*0.12));  // the drawing stays faintly visible under the char
        c=c.map((v,k)=>v*(1-burnAmt)+fc[k]*burnAmt*(0.85+0.3*n*ga)); glowA=ga*(0.6+0.4*n); }
      for(let dy=0;dy<step;dy++) for(let dx=0;dx<step;dx++){ const i=((py+dy)*w+(px+dx))*4; if(px+dx>=w||py+dy>=h) continue;
        im[i]=c[0];im[i+1]=c[1];im[i+2]=c[2];im[i+3]=255;
        gd[i]=255;gd[i+1]=120;gd[i+2]=30;gd[i+3]=Math.round(255*glowA); }
    }}
    ctx.putImageData(p.img,0,0);
    gctx.putImageData(g,0,0);
    ctx.save(); ctx.globalCompositeOperation='lighter'; ctx.filter='blur(5px)'; ctx.globalAlpha=0.6; ctx.drawImage(p.glow,0,0);
    ctx.filter='blur(22px)'; ctx.globalAlpha=0.55; ctx.drawImage(p.glow,0,0); ctx.restore();
    particles(p,FRAME_DT);
    const reached=e.hatch!==null && T>=e.hatch;
    p.hb.textContent = e.hatch===null ? L.never : (reached ? L.reached : L.hatch.replace('{m}', (e.hatch/60).toFixed(e.hatch>=600?0:1)));
    p.hb.className = 'h' + (e.hatch===null ? ' no' : '');
    if(reached){ p.hb.style.background='#ff5a1f'; p.hb.style.color='#fff'; } else { p.hb.style.background=''; p.hb.style.color=''; }
    p.div.classList.toggle('lost', reached);
  });
  document.getElementById('clock').textContent=L.clock.replace('{m}',(T/60).toFixed(1));
  document.getElementById('seek').value=Math.round(1000*T/TEND);
}
let FRAME_DT=0;
function loop(ts){ if(last===null) last=ts; const dt=Math.min(0.05,(ts-last)/1000); last=ts; FRAME_DT=dt;
  if(playing){ T+=dt*speed*TEND/DUR; if(T>TEND){ T=TEND; playing=false; document.getElementById('play').textContent=L.replay; } }
  panels.forEach(p=>emit(p,dt));
  draw();
  requestAnimationFrame(loop); }
document.getElementById('play').onclick=()=>{ if(T>=TEND){T=0;} playing=!playing; document.getElementById('play').textContent=playing?L.pause:L.play; };
document.getElementById('seek').oninput=(ev)=>{ T=TEND*ev.target.value/1000; playing=false; document.getElementById('play').textContent=L.play; draw(); };
document.querySelectorAll('button.s').forEach(b=>b.onclick=()=>{ speed=+b.dataset.s; document.querySelectorAll('button.s').forEach(q=>q.classList.toggle('on',q===b)); });
// size the panels from the frame height so everything (three panels + controls) is always visible
function fit(){
  const bar=document.querySelector('.bar'), avail=window.innerHeight-bar.offsetHeight-22;
  const one=window.innerWidth<=600, bigH=one? Math.floor((avail-20)/3) : Math.floor((avail-10)*0.58), smallH=one? bigH : avail-10-bigH;
  const full=document.getElementById('panels').clientWidth, half=one? full : (full-10)/2;
  panels.forEach((p,i)=>{ const hh=i===0?bigH:smallH, cw=(i===0||one)? full : half;
    const ww=Math.min(cw, hh*W/H), h2=Math.round(ww*H/W); p.cv.style.width=ww+'px'; p.cv.style.height=h2+'px'; });
}
window.addEventListener('resize', fit); fit();
draw(); requestAnimationFrame(loop);
// start when the animation scrolls into view (it would otherwise be over before anyone sees it)
document.getElementById('play').textContent=L.play;
try{ new IntersectionObserver((es)=>{ es.forEach(en=>{ if(en.isIntersecting && T===0 && !playing){ playing=true; document.getElementById('play').textContent=L.pause; } }); }, {threshold:0.4}).observe(document.getElementById('panels')); }
catch(err){ playing=true; }
</script></body></html>"""

CODE = {".": 0, "M": 1, "F": 2, "A": 3, "H": 4}


def render(layout: np.ndarray, envs: list[dict], labels: dict, height: int, vent: int = 1) -> None:
    """``envs``: [{"label": str, "kind": "moon" | "iss" | "earth", "t": arrival-time grid (s, inf = never),
    "hatch": seconds or inf}]; ``vent``: +1 ventilation towards the hatch (right), -1 away (microgravity panel only)."""
    h, w = layout.shape
    finite = [float(e["t"][np.isfinite(e["t"])].max()) for e in envs if np.isfinite(e["t"]).any()]
    t_end = max(finite) if finite else 1.0
    big = t_end * 10 + 1e6  # "never": interpolates to a time that is never reached
    data = {
        "w": w,
        "bg": data_uri(layout),
        "vent": vent,
        "h": h,
        "t_end": t_end,
        "win": max(45.0, t_end / 14),
        "never": big / 2,  # display only: how long a spot glows before it turns to embers and char
        "mat": [CODE[c] for c in layout.ravel()],
        "envs": [
            {
                "label": e["label"],
                "kind": e.get("kind", "moon"),
                "t": [round(float(v), 1) if math.isfinite(v) else big for v in e["t"].ravel()],
                "hatch": round(float(e["hatch"]), 1) if math.isfinite(e["hatch"]) else None,
            }
            for e in envs
        ],
    }
    html = (
        _HTML.replace("__DATA__", json.dumps(data))
        .replace("__LABELS__", json.dumps(labels))
        .replace("__PAUSE__", labels["pause"])
    )
    components.html(html, height=height, scrolling=False)
