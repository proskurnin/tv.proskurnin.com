#!/usr/bin/env python3
"""Render approved boot artwork from native text; build five stock Android ZIPs. No ADB."""
from pathlib import Path
import argparse, base64, hashlib, json, math, zipfile
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
COLORS = {'ruby':'710d2d','copper':'78300b','emerald':'06513b','sapphire':'123c88','amethyst':'4d187b'}
FPS, FRAMES = 12, 24
TRIM = (480, 320, 960, 448)

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=ROOT/'builds/proskurnin-boot-v4')
    parser.add_argument('--font',type=Path,default=Path.home()/'Library/Fonts/Roboto-Bold.ttf')
    parser.add_argument('--chrome',default=str(Path.home()/'Library/Caches/ms-playwright/chromium-1217/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing'))
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    font=base64.b64encode(args.font.read_bytes()).decode()
    html='''<!doctype html><meta charset="utf-8"><style>
@font-face{font-family:BootRoboto;src:url(data:font/ttf;base64,FONTDATA) format('truetype');font-weight:700;font-display:block}
*{box-sizing:border-box}html,body{margin:0;width:1920px;height:1080px;overflow:hidden}
.stage{width:1920px;height:1080px;position:relative;background:#710d2d;color:white;font-family:Arial,Helvetica,sans-serif}
.brand{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:28.8px}
.wordmark{font-family:BootRoboto;font-size:149.76px;font-weight:700;font-synthesis:none;line-height:1.08;letter-spacing:-.04em}
.system{font-size:47.04px;font-weight:400;line-height:1.3;letter-spacing:.24em;margin-top:44.16px;padding-left:.24em}
.tiles{display:flex;align-items:center;gap:19.2px;margin-top:69.12px;height:26.88px}
.tile{width:19.2px;height:19.2px;background:white;opacity:.45}
</style><div class="stage"><div class="brand"><div class="wordmark">PROSKURNIN</div><div class="system">TV SYSTEM</div><div class="tiles"><span class="tile"></span><span class="tile"></span><span class="tile"></span></div></div></div>'''.replace('FONTDATA',font)
    template=args.out/'render-source.html';template.write_text(html)
    manifest={'version':4,'resolution':[1920,1080],'fps':FPS,'loop_frames':FRAMES,'trim':list(TRIM),'font_sha256':digest(args.font),'font_weight':700,'wordmark':'PROSKURNIN','subtitle':'TV SYSTEM','random_early_logo':False,'installed':False,'runtime_verified':False,'colors':{}}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=args.chrome)
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        page.goto(template.as_uri());page.evaluate('()=>document.fonts.ready')
        assert page.evaluate('()=>document.fonts.check("700 150px BootRoboto")')
        for name,color in COLORS.items():
            dest=args.out/name;dest.mkdir(exist_ok=True)
            page.locator('.stage').evaluate('(e,c)=>e.style.background="#"+c',color)
            page.locator('.tiles').evaluate('(e)=>Array.from(e.children).forEach(t=>{t.style.opacity=".45";t.style.transform="none"})')
            page.screenshot(path=str(dest/'preview.png'))
            for quality in range(90,19,-5):
                page.screenshot(path=str(dest/'bootlogo.jpg'),type='jpeg',quality=quality)
                if (dest/'bootlogo.jpg').stat().st_size<=49420: break
            else: raise RuntimeError('JPEG exceeds device-specific logo slot')
            clip=dict(zip(('x','y','width','height'),TRIM));frames=[]
            for i in range(FRAMES):
                time=i/FPS;states=[]
                for delay in (0,.3,.6):
                    phase=time-delay
                    pulse=math.sin(math.pi*phase/.7)**2 if 0<phase<.7 else 0
                    states.append([round(.45+.55*pulse,5),round(-13.44*pulse,3)])
                page.locator('.tiles').evaluate('(e,states)=>Array.from(e.children).forEach((t,i)=>{t.style.opacity=states[i][0];t.style.transform="translateY("+states[i][1]+"px)"})',states)
                frames.append(page.screenshot(clip=clip))
            trim=f'{TRIM[2]}x{TRIM[3]}+{TRIM[0]}+{TRIM[1]}\n'
            # p parts are interruptible: never hold up Android after boot completion.
            desc=f'1920 1080 {FPS}\np 1 5 intro #{color}\np 0 0 loop #{color}\n'
            with zipfile.ZipFile(dest/'bootanimation.zip','w',compression=zipfile.ZIP_STORED) as z:
                z.writestr('desc.txt',desc)
                z.writestr('intro/000.png',frames[0]);z.writestr('intro/trim.txt',trim)
                for i,frame in enumerate(frames):z.writestr(f'loop/{i:03}.png',frame)
                z.writestr('loop/trim.txt',trim*FRAMES)
            manifest['colors'][name]={'background':'#'+color,'jpeg_quality':quality,'jpeg_bytes':(dest/'bootlogo.jpg').stat().st_size,'decoded_rgba_mib':round((FRAMES+1)*TRIM[2]*TRIM[3]*4/1048576,2),'files':{f:digest(dest/f) for f in ('bootlogo.jpg','bootanimation.zip','preview.png')}}
            print(name,manifest['colors'][name]['jpeg_bytes'],'bytes JPEG; trimmed animation',flush=True)
        browser.close()
    (args.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')

if __name__=='__main__':main()
