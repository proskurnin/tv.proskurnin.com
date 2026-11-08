#!/usr/bin/env python3
"""Exercise provider code groups and CPU delta arithmetic without Android/network."""
import subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];src=root/'builds/proskurnin-preview-v1/app/src/local/proskurnin/preview'
java=Path(subprocess.check_output(['/usr/libexec/java_home'],text=True).strip())/'bin'
code='''package local.proskurnin.preview;
class Checks {
 static void eq(int a,int b){if(a!=b)throw new AssertionError(a+" != "+b);}
 public static void main(String[] args){
 int[][] groups={{0,1},{2},{3},{45,48},{51,53,55},{61,63,65,80,81,82},{71,73,75,77,85,86},{56,57,66,67},{95},{96,99}};
 for(int k=0;k<groups.length;k++)for(int c:groups[k]){eq(WeatherState.wmo(c),k==9?12:k+1);if(WeatherState.description(c).equals("Состояние неизвестно"))throw new AssertionError();}
 eq(WeatherState.wmo(-1),0);eq(WeatherState.wmo(42),0);eq(WeatherState.wttr(113),1);eq(WeatherState.wttr(248),4);eq(WeatherState.wttr(311),8);eq(WeatherState.wttr(389),9);eq(WeatherState.wttr(338),7);eq(WeatherState.wttr(999),0);
 eq(WeatherState.legacy("Облачно"),3);eq(WeatherState.legacy("Гроза с градом"),12);
 CpuSample first=CpuSample.parse("cpu 100 0 50 850 0 0 0 0 20 0"),second=CpuSample.parse("cpu 200 0 100 1650 50 0 0 0 40 0");
 eq(CpuSample.usage(first,second),15);eq(CpuSample.usage(null,second),-1);eq(CpuSample.usage(second,first),-1);eq(CpuSample.usage(first,first),-1);
 eq(CpuSample.usage(new CpuSample(100,100),new CpuSample(200,200)),0);eq(CpuSample.usage(new CpuSample(100,100),new CpuSample(200,100)),100);
 try{CpuSample.parse("cpu -1 0 0 0");throw new AssertionError();}catch(IllegalArgumentException expected){}
 System.out.println("Weather codes, unknown values, legacy fallback and CPU arithmetic: OK");
 }
}'''
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'Checks.java';p.write_text(code)
 subprocess.run([str(java/'javac'),'-d',d,str(src/'WeatherState.java'),str(src/'CpuSample.java'),str(p)],check=True)
 subprocess.run([str(java/'java'),'-cp',d,'local.proskurnin.preview.Checks'],check=True)
