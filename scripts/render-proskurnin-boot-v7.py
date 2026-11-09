#!/usr/bin/env python3
"""White boot artwork, precisely centered Arial Black and opacity-only rainbow indicator. No ADB."""
from pathlib import Path
import argparse, base64, hashlib, json, zipfile
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
FPS, FADE, SETTLE, LOOP=12,19,6,24
INTRO=FADE+SETTLE
NAVY='#11264b'
RAINBOW=['#FF1744','#FF7900','#FFD600','#00BF55','#00A9F4','#304FFE','#AA00FF']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def decode(uri):return base64.b64decode(uri.split(',',1)[1])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'builds/proskurnin-boot-v7')
    parser.add_argument('--font',type=Path,default=Path('/System/Library/Fonts/Supplemental/Arial Black.ttf'))
    parser.add_argument('--thin-font',type=Path,default=Path.home()/'Library/Fonts/Roboto-Thin.ttf')
    parser.add_argument('--chrome',default=str(Path.home()/'Library/Caches/ms-playwright/chromium-1217/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'))
    args=parser.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
    font=base64.b64encode(args.font.read_bytes()).decode();thin=base64.b64encode(args.thin_font.read_bytes()).decode()
    html='''<!doctype html><meta charset="utf-8"><title>PROSKURNIN · Arial Black</title>
<style>*{box-sizing:border-box}html,body{margin:0;background:#fff}canvas{display:block;width:100%;height:auto}</style>
<canvas id="screen" width="1920" height="1080"></canvas>
<script>
window.ready=(async()=>{
 const bold=new FontFace('BootArialBlack','url(data:font/ttf;base64,FONTDATA)',{weight:'900'});
 const thin=new FontFace('BootThin','url(data:font/ttf;base64,THINDATA)',{weight:'100'});
 await Promise.all([bold.load(),thin.load()]);document.fonts.add(bold);document.fonts.add(thin);
 const canvas=document.getElementById('screen'),ctx=canvas.getContext('2d');
 ctx.fillStyle='#fff';ctx.fillRect(0,0,1920,1080);ctx.fillStyle='#11264b';ctx.font='900 144px BootArialBlack';ctx.textBaseline='alphabetic';
 const text='PROSKURNIN',m=ctx.measureText(text),width=m.actualBoundingBoxLeft+m.actualBoundingBoxRight;
 const left=960-width/2,top=540-(m.actualBoundingBoxAscent+m.actualBoundingBoxDescent)/2;
 const baseline=540+(m.actualBoundingBoxAscent-m.actualBoundingBoxDescent)/2;
 ctx.fillText(text,left+m.actualBoundingBoxLeft,baseline);
 const bottom=baseline+m.actualBoundingBoxDescent;
 ctx.font='100 42px BootThin';
 const letters=Array.from('TV·SYSTEM'),metrics=letters.map(c=>ctx.measureText(c));
 const subtitleTop=bottom+34,subtitleBaseline=subtitleTop+Math.max(...metrics.map(v=>v.actualBoundingBoxAscent));
 const widths=metrics.map(v=>v.actualBoundingBoxLeft+v.actualBoundingBoxRight);
 const spacing=(width-widths.reduce((a,b)=>a+b,0))/(letters.length-1);
 let x=left;letters.forEach((c,i)=>{ctx.fillText(c,x+metrics[i].actualBoundingBoxLeft,subtitleBaseline);x+=widths[i]+spacing;});
 const subtitleBottom=subtitleBaseline+Math.max(...metrics.map(v=>v.actualBoundingBoxDescent));
 const squareY=Math.ceil(subtitleBottom+52),squareSize=54,gap=54,rowWidth=7*squareSize+6*gap;
 const crop={x:Math.floor(left-18),y:Math.floor(top-18),width:Math.ceil(width+36),height:0};crop.height=squareY+squareSize+18-crop.y;
 window.geometry={wordmark:{left,top,width,height:bottom-top,center:[960,540]},subtitle:{left,top:subtitleTop,width},squares:{x:(1920-rowWidth)/2,y:squareY,size:squareSize,gap},crop};
 const saved=new Image();
 // Decode the exact JPEG used by the early boot stage as the immutable animation base.
 window.useJpeg=async uri=>{saved.src=uri;await saved.decode();ctx.clearRect(0,0,1920,1080);ctx.drawImage(saved,0,0);};
 window.frame=(fade,time,flat=0)=>{
  ctx.globalAlpha=1;ctx.drawImage(saved,0,0);
  const colors=RAINBOW;
  colors.forEach((color,i)=>{const pulse=Math.pow(Math.max(0,Math.cos(2*Math.PI*(time/2-i*.12))),4);ctx.globalAlpha=fade*(flat+(1-flat)*(1-.65*pulse));ctx.fillStyle=color;ctx.fillRect((1920-rowWidth)/2+i*(squareSize+gap),squareY,squareSize,squareSize);});
  ctx.globalAlpha=1;
  const cropped=document.createElement('canvas');cropped.width=crop.width;cropped.height=crop.height;
  cropped.getContext('2d').drawImage(canvas,crop.x,crop.y,crop.width,crop.height,0,0,crop.width,crop.height);
  return cropped.toDataURL('image/png');
 };
 return true;
})();
</script>'''.replace('FONTDATA',font).replace('THINDATA',thin).replace('RAINBOW',json.dumps(RAINBOW))
    source=out/'render-source.html';source.write_text(html)
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=args.chrome)
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        page.goto(source.as_uri());page.evaluate('()=>window.ready')
        assert page.evaluate('()=>document.fonts.check("900 144px BootArialBlack") && document.fonts.check("100 42px BootThin")')
        geometry=page.evaluate('()=>window.geometry')
        for quality in range(95,19,-5):
            uri=page.evaluate('(q)=>document.getElementById("screen").toDataURL("image/jpeg",q/100)',quality)
            jpg=decode(uri)
            if len(jpg)<=49420:break
        else:raise RuntimeError('JPEG exceeds the device slot')
        (out/'bootlogo.jpg').write_bytes(jpg);page.evaluate('(uri)=>window.useJpeg(uri)',uri)
        (out/'preview-static.png').write_bytes(decode(page.evaluate('()=>document.getElementById("screen").toDataURL("image/png")')))
        intro=[];loop=[]
        for i in range(FADE):
            f=i/(FADE-1);fade=f*f*(3-2*f)
            intro.append(decode(page.evaluate('([fade,t,flat])=>window.frame(fade,t,flat)',[fade,0,1])))
        for i in range(1,SETTLE+1):
            f=i/SETTLE;flat=1-f*f*(3-2*f)
            intro.append(decode(page.evaluate('([fade,t,flat])=>window.frame(fade,t,flat)',[1,0,flat])))
        for i in range(LOOP):loop.append(decode(page.evaluate('([fade,t])=>window.frame(fade,t)',[1,i/FPS])))
        page.evaluate('()=>window.frame(1,0,1)')
        (out/'preview-animation.png').write_bytes(decode(page.evaluate('()=>document.getElementById("screen").toDataURL("image/png")')))
        browser.close()
    crop=geometry['crop'];trim=f"{crop['width']}x{crop['height']}+{crop['x']}+{crop['y']}\n"
    desc=f'1920 1080 {FPS}\np 1 0 intro #FFFFFF\np 0 0 loop #FFFFFF\n'
    with zipfile.ZipFile(out/'bootanimation.zip','w',compression=zipfile.ZIP_STORED) as z:
        z.writestr('desc.txt',desc)
        for name,frames in [('intro',intro),('loop',loop)]:
            for i,frame in enumerate(frames):z.writestr(f'{name}/{i:03}.png',frame)
            z.writestr(name+'/trim.txt',trim*len(frames))
    manifest={'version':7,'resolution':[1920,1080],'background':'#FFFFFF','foreground':NAVY,'font':'Arial Black','font_sha256':sha(args.font),'subtitle_font':'Roboto Thin','subtitle_font_sha256':sha(args.thin_font),'wordmark':'PROSKURNIN','subtitle':'TV · SYSTEM','fps':FPS,'intro_frames':INTRO,'loop_frames':LOOP,'jpeg_quality':quality,'jpeg_bytes':len(jpg),'geometry':geometry,'indicator_colors':RAINBOW,'indicator_translation':False,'static_indicator_visible':False,'decoded_rgba_mib':round((INTRO+LOOP)*crop['width']*crop['height']*4/1048576,2),'files':{name:sha(out/name) for name in ['bootlogo.jpg','bootanimation.zip','preview-static.png','preview-animation.png']},'installed':False,'runtime_verified':False}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:manifest[k] for k in ['jpeg_bytes','fps','decoded_rgba_mib','geometry']},indent=2))

if __name__=='__main__':main()
