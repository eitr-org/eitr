// Both the wolf and the palette boundary share the same downward-only progress.
export const CHASE_DURATION=2500;
export function chaseDepth(progress:number) {
  return progress<=.7 ? -.14+1.3*progress/.7 : 1.16+1.24*(progress-.7)/.3;
}
export function chaseRevealFrames():Keyframe[] {
  return Array.from({length:61},(_,index)=>{
    const progress=index/60,depth=Math.max(0,chaseDepth(progress));
    const spread=depth*40;
    return {offset:progress,clipPath:`polygon(${50-spread}% 0%,${50+spread}% 0%,50% ${depth*100}%)`};
  });
}
const wolves=new Map<boolean,{image:HTMLImageElement;ready:boolean}>();
function loadWolf(night:boolean) {
  const cached=wolves.get(night);
  if(cached) return cached;
  const image=new Image();
  const wolf={image,ready:false};
  wolves.set(night,wolf);
  image.src=night?'/art/skoll-bite.webp':'/art/hati-bite.webp';
  void image.decode().then(()=>{wolf.ready=true;}).catch(()=>{});
  return wolf;
}
export function preloadChaseWolves() {
  const preload=()=>{loadWolf(false);loadWolf(true);};
  if('requestIdleCallback' in window) window.requestIdleCallback(preload,{timeout:1000});
  else setTimeout(preload,200);
}
const moonCraters=[[-.3,-.2,.2],[.3,.25,.25],[-.15,.45,.12]];
export function celestialChase(canvas:HTMLCanvasElement,night:boolean,done:()=>void) {
  const context=canvas.getContext('2d');
  if(!context) {done();return ()=>{};}
  const sprite=loadWolf(night),wolf=sprite.image;
  const color=night?'#ec7735':'#59aaff',core=night?'#fff1c4':'#d4efff';
  // Cache the soft celestial halo instead of blurring it on every frame.
  const halo=document.createElement('canvas');
  halo.width=halo.height=128;
  const haloContext=halo.getContext('2d')!;
  const gradient=haloContext.createRadialGradient(64,64,12,64,64,64);
  gradient.addColorStop(0,night?'#ec773580':'#59aaff80');
  gradient.addColorStop(1,night?'#ec773500':'#59aaff00');
  haloContext.fillStyle=gradient;haloContext.fillRect(0,0,128,128);
  let frame=0,start=0,stopped=false;
  let width=0,height=0;
  const resize=()=>{
    width=innerWidth;height=innerHeight;
    canvas.width=width;canvas.height=height;
  };
  resize();addEventListener('resize',resize);
  const stop=()=>{
    stopped=true;cancelAnimationFrame(frame);removeEventListener('resize',resize);
    context.clearRect(0,0,width,height);
  };
  const paint=(now:number)=>{
    if(stopped) return;
    start ||= now;
    const progress=Math.min(1,(now-start)/CHASE_DURATION);
    const depth=chaseDepth(progress),headX=width*.5,headY=depth*height;
    canvas.dataset.wolfY=String(headY);
    context.clearRect(0,0,width,height);
    const size=Math.min(90,width*.15);
    // The sprite extends .88 sizes behind its origin; leave a gap after its tail.
    const wolfY=headY+size*.88+20;
    {
      // Keep the celestial body just ahead of the downward-facing mouth.
      const r=Math.min(25,width*.045),x=headX,y=wolfY+size*.12+r+12;
      context.save();
      const haloRadius=r+34;
      context.drawImage(halo,x-haloRadius,y-haloRadius,haloRadius*2,haloRadius*2);
      context.fillStyle=night?'#ffd082':'#e6eef8';
      context.beginPath();context.arc(x,y,r,0,Math.PI*2);context.fill();
      if(!night) {
        context.fillStyle='#a8b7c555';
        for(let craterIndex=0;craterIndex<moonCraters.length;craterIndex++) {
          const crater=moonCraters[craterIndex];
          context.beginPath();context.arc(x+crater[0]*r,y+crater[1]*r,r*crater[2],0,Math.PI*2);context.fill();
        }
      }
      context.restore();
    }
    context.save();context.globalCompositeOperation='lighter';
    // The V is the trail behind the wolf, not the wolf's route.
    for(let side=-1;side<=1;side+=2) {
      const topX=headX+side*Math.max(0,depth)*width*.4;
      for(let strand=0;strand<7;strand++) {
        context.beginPath();
        for(let i=0;i<=64;i++) {
          const u=i/64;
          const sway=(1-u)*((strand-3)*3+Math.sin(u*23+strand+now*.002)*5);
          const x=topX+(headX-topX)*u+sway;
          const y=headY*u;
          if(i===0) context.moveTo(x,y);else context.lineTo(x,y);
        }
        context.strokeStyle=color;
        context.lineWidth=strand===3?22:9;
        context.globalAlpha=strand===3?.06:.025;
        context.stroke();
        context.lineWidth=strand===3?10:4;
        context.globalAlpha=strand===3?.12:.05;
        context.stroke();
        context.strokeStyle=strand===3?core:color;
        context.lineWidth=strand===3?2.5:1.3;
        context.globalAlpha=strand===3?.85:.25;
        context.stroke();
      }
    }
    context.restore();
    // Paint the wolf last with normal compositing so its ink covers the trails.
    context.save();
    context.translate(headX,wolfY);context.rotate(Math.PI/2);
    context.globalCompositeOperation='source-over';
    context.globalAlpha=1;
    if(sprite.ready && wolf.naturalWidth>0) {
      const sourceWidth=wolf.naturalWidth/2;
      const sourceX=Math.floor(now/150)%2*sourceWidth;
      context.filter='none';
      context.drawImage(wolf,sourceX,0,sourceWidth,wolf.naturalHeight,-size*.88,-size*.34,size,size*wolf.naturalHeight/sourceWidth);
    }
    context.restore();
    if(progress<1) frame=requestAnimationFrame(paint);
    else {stop();done();}
  };
  frame=requestAnimationFrame(paint);
  return stop;
}
