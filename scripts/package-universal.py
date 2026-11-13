#!/usr/bin/env python3
"""Build and verify the portable distribution locally. No TV/SSH/deployment operations."""
from pathlib import Path
import datetime,hashlib,io,json,os,re,shutil,subprocess,sys,tempfile,zipfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
A='{http://schemas.android.com/apk/res/android}'
SERVER=['portable_server.py','api_relay.py','us_api_worker.py','weather_gateway.py','tmdb_proxy.py','device_auth.py','movie_contract.py','chat_contract.py','transcription.py','dream_media.py','speed_probe.py']
SCRIPTS=['package-universal.py','build-proskurnin-preview.py','build-proskurnin-remote.py','launcher_profiles.py','provision-universal.py','provision-xiaomi-preview-api.py','prepare-remote-tls.py','prepare-dream-catalog.py']
TESTS=['test_device_auth.py','test_launcher_profiles.py','test_movie_contract.py','test_preview_provision.py','test_transcription.py','test_universal.py','ApiEndpointTest.java','HomeRoutePolicyTest.java','MiPressGestureTest.java','DeviceTelemetryTest.java','BannerShineStateTest.java','CurrencyConfigTest.java','BackgroundConfigTest.java']

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    log=[]
    def run(command):
        result=subprocess.run([str(x) for x in command],cwd=ROOT,capture_output=True,text=True)
        log.append('$ '+' '.join(str(x) for x in command)+'\n'+result.stdout+result.stderr)
        if result.returncode:print(log[-1]);raise RuntimeError('Verification failed')
        return result.stdout
    run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_*.py'])
    sdk=Path(os.environ.get('ANDROID_SDK_ROOT',str(Path.home()/'Library/Android/sdk')));bt=sdk/'build-tools/35.0.0'
    java=Path(os.environ['JAVA_HOME'])/'bin' if os.environ.get('JAVA_HOME') else Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin' if Path('/usr/libexec/java_home').exists() else Path(shutil.which('javac')).resolve().parent
    with tempfile.TemporaryDirectory() as tmp:
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/ApiEndpoint.java',ROOT/'tests/ApiEndpointTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.ApiEndpointTest'])
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/HomeRoutePolicy.java',ROOT/'tests/HomeRoutePolicyTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.HomeRoutePolicyTest'])
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/MiPressGesture.java',ROOT/'tests/MiPressGestureTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.MiPressGestureTest'])
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/CpuSample.java',ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/WifiName.java',ROOT/'tests/DeviceTelemetryTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.DeviceTelemetryTest'])
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/BannerShineState.java',ROOT/'tests/BannerShineStateTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.BannerShineStateTest'])
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/CurrencyConfig.java',ROOT/'tests/CurrencyConfigTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.CurrencyConfigTest'])
        run([java/'javac','-d',tmp,ROOT/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview/BackgroundConfig.java',ROOT/'tests/BackgroundConfigTest.java'])
        run([java/'java','-cp',tmp,'local.proskurnin.preview.BackgroundConfigTest'])
    run(['node','--check',ROOT/'builds/proskurnin-remote-v1/app/assets/app.js'])
    run([sys.executable,'scripts/build-proskurnin-preview.py','--profile','universal'])
    run([sys.executable,'scripts/build-proskurnin-remote.py'])
    for command in [[sys.executable,'--version'],[java/'javac','-version'],[bt/'aapt2','version'],['node','--version']]:run(command)
    launcher=ROOT/'builds/proskurnin-preview-v1/ProskurninUniversal.apk';remote=ROOT/'builds/proskurnin-remote-v1/ProskurninRemote.apk'
    certificates=[]
    for apk in [launcher,remote]:
        result=run([bt/'apksigner','verify','--print-certs',apk]);certificates.append(re.search(r'certificate SHA-256 digest: ([0-9a-f]+)',result).group(1))
        run([bt/'aapt2','dump','badging',apk])
    if certificates[0]!=certificates[1]:raise RuntimeError('Signer mismatch')
    xml=run([bt/'aapt2','dump','xmltree',launcher,'--file','AndroidManifest.xml'])
    if 'BootHomeReceiver' in xml or 'PowerMenuActivity' in xml or 'proskurnin.universal' not in xml:raise RuntimeError('Wrong APK profile')
    version=ET.parse(ROOT/'builds/proskurnin-preview-v1/app/AndroidManifest.xml').getroot().get(A+'versionName')
    remote_version=ET.parse(ROOT/'builds/proskurnin-remote-v1/app/AndroidManifest.xml').getroot().get(A+'versionName')
    name='Proskurnin-TV-Universal-'+version
    entries={}
    def add(path,target=None):
        if path.is_symlink():raise RuntimeError('Source symlink refused')
        entries[target or 'source/'+str(path.relative_to(ROOT))]=path.read_bytes()
    for folder in ['builds/proskurnin-preview-v1/app','builds/proskurnin-remote-v1/app','builds/proskurnin-remote-v1/bridge/src']:
        for f in sorted((ROOT/folder).rglob('*')):
            if f.is_file() and f.name!='.DS_Store':add(f)
    for item in SCRIPTS:add(ROOT/'scripts'/item)
    for item in SERVER:add(ROOT/'integrations/server'/item)
    for item in TESTS:add(ROOT/'tests'/item)
    for item in ['README.md','AGENTS.md','CHANGELOG.md','ROADMAP.md','.gitignore']:add(ROOT/item)
    for f in sorted((ROOT/'docs').glob('*.md')):add(f)
    for f in sorted((ROOT/'docs').glob('UNIVERSAL*.md')):add(f,'docs/'+f.name)
    entries['README.md']=b'# Proskurnin TV Universal\n\n'+('Начните с [руководства установки](docs/UNIVERSAL.md). Версии: лаунчер '+version+', пульт '+remote_version+'.\n\nВ комплекте собственные APK, необязательный shell-помощник, исходники/API-сервер и документация. Сторонние приложения — [каталог источников](docs/UNIVERSAL_APPS.md). Root не обязателен. Это не прошивка.\n\nНа ТВ этот выпуск автоматически не устанавливался; аппаратная приёмка ещё впереди. Проверьте SHA256SUMS до установки.\n').encode()
    add(launcher,'apks/ProskurninUniversal.apk');add(remote,'apks/ProskurninRemote.apk');add(ROOT/'builds/proskurnin-remote-v1/input-bridge.jar','optional/input-bridge.jar')
    log_text='\n'.join(log).replace(str(ROOT),'<PROJECT>').replace(str(Path.home()),'<HOME>')
    entries['BUILD-INFO.txt']=('UTC: '+datetime.datetime.now(datetime.timezone.utc).isoformat()+'\nProfile: universal\nHardware tests: NOT RUN\nNetwork provider calls: NOT RUN by package builder\nSigner SHA256: '+certificates[0]+'\n\n'+log_text).encode()
    # Read known secrets locally, never emit their values. Allowlist excludes all private dirs.
    known=set()
    def visit(value,key=''):
        if isinstance(value,dict):
            for k,v in value.items():visit(v,k)
        elif isinstance(value,list):
            for v in value:visit(v,key)
        elif isinstance(value,str) and re.search('token|secret|password|api_key|credential',key,re.I) and len(value)>=24 and not value.startswith(('https:','http:','/')):
            known.add(value.encode())
    for folder in [ROOT/'integrations/server/private',ROOT/'integrations/remote/private']:
        if not folder.exists():continue
        for f in folder.iterdir():
            if f.is_symlink() or not f.is_file() or f.stat().st_size>1048576:continue
            if f.suffix=='.json':
                try:visit(json.loads(f.read_text()))
                except (ValueError,UnicodeError):pass
            if f.suffix=='.env':
                for line in f.read_text().splitlines():
                    if not line.startswith('#') and '=' in line:
                        k,v=line.split('=',1);visit(v.strip().strip('\"\''),k)
    def scan(data):
        if any(secret in data for secret in known):raise RuntimeError('Known private value found; output withheld')
        if re.search(rb'-----BEGIN (?:RSA )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{32,}-----END',data):raise RuntimeError('Private key found')
    for path,data in entries.items():
        if '/private/' in path or path.endswith(('.keystore','.p12','.pem','.key')):raise RuntimeError('Private path found')
        scan(data)
        if path.endswith(('.apk','.jar')):
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if any(n.startswith('lib/') for n in archive.namelist()):raise RuntimeError('Unexpected native dependency')
                for n in archive.namelist():scan(archive.read(n))
    manifest={'launcher_version':version,'remote_version':remote_version,'profile':'universal','min_api':28,'signer_sha256':certificates[0],'hardware_verified':False,'files':[{'path':p,'bytes':len(d),'sha256':sha(d)} for p,d in sorted(entries.items())]}
    entries['MANIFEST.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    entries['SHA256SUMS']=''.join(sha(d)+'  '+p+'\n' for p,d in sorted(entries.items())).encode()
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    target=dist/(name+'.zip');temp=dist/(name+'.zip.tmp')
    with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path,data in sorted(entries.items()):archive.writestr(name+'/'+path,data)
    with zipfile.ZipFile(temp) as archive:
        if archive.testzip() is not None:raise RuntimeError('Archive corruption')
        for row in manifest['files']:
            if sha(archive.read(name+'/'+row['path']))!=row['sha256']:raise RuntimeError('Archive checksum mismatch')
    temp.replace(target)
    (dist/(name+'.zip.sha256')).write_text(sha(target.read_bytes())+'  '+target.name+'\n')
    # Expanded directory is convenient for Finder, refuse overwriting an older tree.
    expanded=dist/name
    if expanded.exists():expanded=Path(tempfile.mkdtemp(prefix=name+'-',dir=dist))
    for path,data in entries.items():
        destination=expanded/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    print('FOLDER',expanded)
    print('READY',target,'bytes='+str(target.stat().st_size),'files='+str(len(entries)))
    print('SHA256',sha(target.read_bytes()));print('Signer SHA256',certificates[0]);print('Hardware tests remain pending. No device/server modified.')
if __name__=='__main__':main()
