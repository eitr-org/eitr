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
export function celestialChase(canvas:HTMLCanvasElement,night:boolean,done:()=>void) {
  const context=canvas.getContext('2d');
  if(!context) {done();return ()=>{};}
  const wolf=new Image();
  wolf.src=night?'/art/skoll-bite.webp':'/art/hati-bite.webp';
  let frame=0,start=0,stopped=false;
  let width=0,height=0;
  const resize=()=>{
    width=innerWidth;height=innerHeight;
    const ratio=Math.min(devicePixelRatio||1,2);
    canvas.width=width*ratio;canvas.height=height*ratio;
    context.setTransform(ratio,0,0,ratio,0,0);
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
    const depth=chaseDepth(progress),head={x:width*.5,y:depth*height};
    canvas.dataset.wolfY=String(head.y);
    context.clearRect(0,0,width,height);
    const color=night?'#ec7735':'#59aaff',core=night?'#fff1c4':'#d4efff';
    const size=Math.min(90,width*.15);
    // The sprite extends .88 sizes behind its origin; leave a gap after its tail.
    const wolfY=head.y+size*.88+20;
    {
      // Keep the celestial body just ahead of the downward-facing mouth.
      const r=Math.min(25,width*.045),x=head.x,y=wolfY+size*.12+r+12;
      context.save();context.shadowColor=color;context.shadowBlur=34;
      context.fillStyle=night?'#ffd082':'#e6eef8';
      context.beginPath();context.arc(x,y,r,0,Math.PI*2);context.fill();
      if(!night) {
        context.shadowBlur=0;context.fillStyle='#a8b7c555';
        for(const [dx,dy,s] of [[-.3,-.2,.2],[.3,.25,.25],[-.15,.45,.12]]) {
          context.beginPath();context.arc(x+dx*r,y+dy*r,r*s,0,Math.PI*2);context.fill();
        }
      }
      context.restore();
    }
    context.save();context.globalCompositeOperation='lighter';
    // The V is the trail behind the wolf, not the wolf's route.
    for(const side of [-1,1]) {
      const topX=head.x+side*Math.max(0,depth)*width*.4;
      for(let strand=0;strand<7;strand++) {
        context.beginPath();
        for(let i=0;i<=64;i++) {
          const u=i/64;
          const sway=(1-u)*((strand-3)*3+Math.sin(u*23+strand+now*.002)*5);
          const x=topX+(head.x-topX)*u+sway;
          const y=head.y*u;
          if(i===0) context.moveTo(x,y);else context.lineTo(x,y);
        }
        context.strokeStyle=strand===3?core:color;
        context.lineWidth=strand===3?2.5:1.3;
        context.globalAlpha=strand===3?.85:.25;
        context.shadowColor=color;context.shadowBlur=strand===3?22:9;
        context.stroke();
      }
    }
    context.restore();
    // Paint the wolf last with normal compositing so its ink covers the trails.
    context.save();
    context.translate(head.x,wolfY);context.rotate(Math.PI/2);
    context.globalCompositeOperation='source-over';
    context.globalAlpha=1;context.shadowBlur=0;
    if(wolf.complete && wolf.naturalWidth>0) {
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
