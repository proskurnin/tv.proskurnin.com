#!/usr/bin/env python3
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];java=Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin';src=root/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview'
code='''package local.proskurnin.preview;class Check {static void check(boolean x){if(!x)throw new AssertionError();}public static void main(String[] a){AutoListenWindow w=new AutoListenWindow();check(!w.open(1));w.start(1000);check(w.open(1000));check(w.open(60999));check(!w.open(61000));check(!w.open(999));w.start(70000);w.cancel();check(!w.open(70000));System.out.println("Auto-listen timing/cancel: OK");}}'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'Check.java';p.write_text(code);subprocess.run([str(java/'javac'),'-d',d,str(src/'AutoListenWindow.java'),str(p)],check=True);subprocess.run([str(java/'java'),'-cp',d,'local.proskurnin.preview.Check'],check=True)
