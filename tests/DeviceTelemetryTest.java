package local.proskurnin.preview;
public class DeviceTelemetryTest {
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  CpuSample a=CpuSample.parse("cpu 100 0 50 800 50 0 0 0 100 0");
  CpuSample b=CpuSample.parse("cpu 140 0 60 840 60 0 0 0 200 0");
  check(CpuSample.usage(a,b)==50,"system busy excludes idle+iowait and guest double counting");
  check(CpuSample.usage(null,b)==-1,"first sample needs interval");check(CpuSample.usage(b,a)==-1,"restarted counter");check(CpuSample.usage(a,a)==-1,"duplicate counter");
  try{CpuSample.parse("cpu0 1 2 3 4");throw new AssertionError("per-core must not substitute total");}catch(IllegalArgumentException expected){}
  check(WifiName.clean(null).isEmpty(),"null");check(WifiName.clean("\"<unknown ssid>\"").isEmpty(),"unknown");check(WifiName.clean("0x").isEmpty(),"empty hex");
  check(WifiName.clean("\"Дом 5G\"").equals("Дом 5G"),"quotes and Unicode");check(WifiName.clean(" A\nB\u202e ").equals("AB"),"remove controls and bidi");
  System.out.println("DeviceTelemetryTest passed");
 }
}
