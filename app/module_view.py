"""Smooth fire animation for the module page (ADR-052): the flame front is drawn on a canvas by bilinear interpolation
of the computed arrival times (fif.physics.module_fire), with glow and flicker. Display only: every time shown comes
from the arrival-time grids; colours, glow and flicker are illustrative."""

from __future__ import annotations

import json
import math

import numpy as np
import streamlit.components.v1 as components

_HTML = r"""<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#0d1322;font-family:Inter,system-ui,sans-serif;color:#e8ecf4}
#panels{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.p{position:relative;border-radius:12px;overflow:hidden;background:#0a0f1c}
.p.big{grid-column:1 / span 2}
@media (max-width:600px){#panels{grid-template-columns:1fr}.p.big{grid-column:auto}}
.p canvas{display:block;width:100%;height:auto}
.t{position:absolute;left:12px;top:8px;font-size:13px;font-weight:600;text-shadow:0 1px 3px #000}
.h{position:absolute;right:12px;top:8px;font-size:12px;padding:2px 8px;border-radius:9px;background:#2fd27a;color:#06210f;font-weight:700}
.h.no{background:#5c6678;color:#e8ecf4}
.bar{display:flex;align-items:center;gap:10px;margin-top:4px;font-size:13px}
button{background:#f0843f;border:0;color:#0d1322;font-weight:700;border-radius:8px;padding:6px 12px;cursor:pointer}
button.s{background:#151d33;color:#e8ecf4;border:1px solid #26304a;font-weight:500}button.s.on{border-color:#f0843f;color:#f0843f}
input[type=range]{flex:1;accent-color:#f0843f}
#clock{min-width:150px;color:#ffb627;font-weight:600}
</style></head><body><div id="panels"></div>
<div class="bar"><button id="play">__PAUSE__</button><span id="clock"></span><input id="seek" type="range" min="0" max="1000" value="0">
<button class="s" data-s="0.5">0.5x</button><button class="s on" data-s="1">1x</button><button class="s" data-s="2">2x</button></div>
<script>
const D=__DATA__, L=__LABELS__;
const MAT={0:[26,34,53],1:[92,102,120],2:[201,166,107],3:[95,179,217],4:[47,210,122]};
const W=D.w, H=D.h, SC=7; // canvas pixels per cell
const panels=[];
D.envs.forEach((e,i)=>{
  const div=document.createElement('div'); div.className='p'+(i===0?' big':'');
  const cv=document.createElement('canvas'); cv.width=W*SC; cv.height=H*SC; div.appendChild(cv);
  const tl=document.createElement('div'); tl.className='t'; tl.textContent=e.label; div.appendChild(tl);
  const hb=document.createElement('div'); hb.className='h'; div.appendChild(hb);
  document.getElementById('panels').appendChild(div);
  const glow=document.createElement('canvas'); glow.width=cv.width; glow.height=cv.height;
  panels.push({e,cv,ctx:cv.getContext('2d'),glow,gctx:glow.getContext('2d'),hb,img:null});
});
function at(arr,x,y){ // bilinear interpolation over the burning neighbours only (cells the flame never reaches are skipped)
  const cx=Math.min(Math.floor(x),W-1), cy=Math.min(Math.floor(y),H-1), own=arr[cy*W+cx];
  if(own>=D.never) return own;
  const fx=Math.min(Math.max(x-0.5,0),W-1), fy=Math.min(Math.max(y-0.5,0),H-1);
  const x0=Math.floor(fx), y0=Math.floor(fy), x1=Math.min(x0+1,W-1), y1=Math.min(y0+1,H-1), tx=fx-x0, ty=fy-y0;
  const v=[arr[y0*W+x0],arr[y0*W+x1],arr[y1*W+x0],arr[y1*W+x1]], wt=[(1-tx)*(1-ty),tx*(1-ty),(1-tx)*ty,tx*ty];
  let s=0,ws=0; for(let i=0;i<4;i++){ if(v[i]<D.never){ s+=v[i]*wt[i]; ws+=wt[i]; } }
  return ws>0? s/ws : own;
}
function base(m,x,y){ // soft edges between materials: blend the four neighbouring cell colours
  const fx=Math.min(Math.max(x-0.5,0),W-1), fy=Math.min(Math.max(y-0.5,0),H-1);
  const x0=Math.floor(fx), y0=Math.floor(fy), x1=Math.min(x0+1,W-1), y1=Math.min(y0+1,H-1);
  let tx=fx-x0, ty=fy-y0; tx=tx*tx*(3-2*tx); ty=ty*ty*(3-2*ty);
  const q=(i)=>MAT[m[i]], A=q(y0*W+x0),B=q(y0*W+x1),C=q(y1*W+x0),E=q(y1*W+x1);
  return [0,1,2].map(k=>(A[k]*(1-tx)+B[k]*tx)*(1-ty)+(C[k]*(1-tx)+E[k]*tx)*ty);
}
const STOPS=[[0,[255,250,220]],[0.15,[255,214,90]],[0.45,[255,140,30]],[0.8,[235,70,25]],[1.3,[150,32,18]],[2.0,[40,24,20]]];
function fire(age,win){ const a=age/win; if(a>=2) return [[24,16,14],0];
  for(let i=1;i<STOPS.length;i++){ if(a<=STOPS[i][0]){ const [a0,c0]=STOPS[i-1],[a1,c1]=STOPS[i], f=(a-a0)/(a1-a0);
    return [c0.map((v,k)=>v+(c1[k]-v)*f), Math.max(0,1-a/1.3)]; } }
  return [[24,16,14],0];
}
function noise(x,y,t){ return 0.5+0.5*Math.sin(x*0.9+t*7.3)*Math.sin(y*1.3-t*5.1); }
let T=0, speed=1, playing=true, last=null; const TEND=D.t_end*1.05, DUR=20; // seconds of animation at 1x
function draw(){
  panels.forEach(p=>{
    const {ctx,gctx,cv,e}=p, w=cv.width, h=cv.height;
    if(!p.img) p.img=ctx.createImageData(w,h);
    const im=p.img.data, g=gctx.createImageData(w,h), gd=g.data, win=D.win;
    const step=2; // compute every 2 px, fill a 2x2 block
    for(let py=0;py<h;py+=step){ for(let px=0;px<w;px+=step){
      const x=px/SC, y=py/SC; let c=base(D.mat,x,y), glowA=0;
      const ta=at(e.t,x,y);
      if(ta<=T){ const [fc,ga]=fire(T-ta,win); const n=noise(x,y,T/win);
        const burnAmt=Math.min(1,(T-ta)/(win*0.12)+0.0);
        c=c.map((v,k)=>v*(1-burnAmt)+fc[k]*burnAmt*(0.85+0.3*n*ga)); glowA=ga*(0.6+0.4*n); }
      for(let dy=0;dy<step;dy++) for(let dx=0;dx<step;dx++){ const i=((py+dy)*w+(px+dx))*4; if(px+dx>=w||py+dy>=h) continue;
        im[i]=c[0];im[i+1]=c[1];im[i+2]=c[2];im[i+3]=255;
        gd[i]=255;gd[i+1]=120;gd[i+2]=30;gd[i+3]=Math.round(255*glowA); }
    }}
    ctx.putImageData(p.img,0,0);
    gctx.putImageData(g,0,0);
    ctx.save(); ctx.globalCompositeOperation='lighter'; ctx.filter='blur(10px)'; ctx.globalAlpha=0.9; ctx.drawImage(p.glow,0,0);
    ctx.filter='blur(3px)'; ctx.globalAlpha=0.5; ctx.drawImage(p.glow,0,0); ctx.restore();
    const reached=e.hatch!==null && T>=e.hatch;
    p.hb.textContent = e.hatch===null ? L.never : (reached ? L.reached : L.hatch.replace('{m}', (e.hatch/60).toFixed(e.hatch>=600?0:1)));
    p.hb.className = 'h' + (e.hatch===null ? ' no' : '');
    if(reached){ p.hb.style.background='#ff5a1f'; p.hb.style.color='#fff'; } else { p.hb.style.background=''; p.hb.style.color=''; }
  });
  document.getElementById('clock').textContent=L.clock.replace('{m}',(T/60).toFixed(1));
  document.getElementById('seek').value=Math.round(1000*T/TEND);
}
function loop(ts){ if(last===null) last=ts; const dt=(ts-last)/1000; last=ts;
  if(playing){ T+=dt*speed*TEND/DUR; if(T>TEND){ T=TEND; playing=false; document.getElementById('play').textContent=L.replay; } draw(); }
  requestAnimationFrame(loop); }
document.getElementById('play').onclick=()=>{ if(T>=TEND){T=0;} playing=!playing; document.getElementById('play').textContent=playing?L.pause:L.play; };
document.getElementById('seek').oninput=(ev)=>{ T=TEND*ev.target.value/1000; playing=false; document.getElementById('play').textContent=L.play; draw(); };
document.querySelectorAll('button.s').forEach(b=>b.onclick=()=>{ speed=+b.dataset.s; document.querySelectorAll('button.s').forEach(q=>q.classList.toggle('on',q===b)); });
draw(); requestAnimationFrame(loop);
</script></body></html>"""

CODE = {".": 0, "M": 1, "F": 2, "A": 3, "H": 4}


def render(layout: np.ndarray, envs: list[dict], labels: dict, height: int) -> None:
    """``envs``: [{"label": str, "t": arrival-time grid (s, inf = never), "hatch": seconds or inf}]."""
    h, w = layout.shape
    finite = [float(e["t"][np.isfinite(e["t"])].max()) for e in envs if np.isfinite(e["t"]).any()]
    t_end = max(finite) if finite else 1.0
    big = t_end * 10 + 1e6  # "never": interpolates to a time that is never reached
    data = {
        "w": w,
        "h": h,
        "t_end": t_end,
        "win": max(45.0, t_end / 14),
        "never": big / 2,  # display only: how long a spot glows before it turns to embers and char
        "mat": [CODE[c] for c in layout.ravel()],
        "envs": [
            {
                "label": e["label"],
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
