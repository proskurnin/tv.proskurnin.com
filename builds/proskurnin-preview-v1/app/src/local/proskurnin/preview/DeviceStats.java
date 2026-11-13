package local.proskurnin.preview;
import android.app.ActivityManager;import android.content.Context;import android.os.*;import java.io.*;import java.util.Locale;
final class DeviceStats {
 final Context context;CpuSample previous;
 DeviceStats(Context c){context=c.getApplicationContext();}
 static final class Snapshot {String cpu="CPU · замер…",ram="RAM —",disk="Диск —";int cpuPercent=-1,ramPercent=-1,diskPercent=-1;}
 Snapshot read(){Snapshot s=new Snapshot();
  CpuSample current=null;
  if(XiaomiCpuBridge.supported())current=XiaomiCpuBridge.read();
  else try(BufferedReader r=new BufferedReader(new FileReader("/proc/stat"))){current=CpuSample.parse(r.readLine());}catch(Exception ignored){}
  if(current==null){previous=null;s.cpu="CPU —";}
  else{s.cpuPercent=CpuSample.usage(previous,current);previous=current;}
  if(s.cpuPercent>=0)s.cpu="CPU "+s.cpuPercent+"%";
  try{ActivityManager.MemoryInfo m=new ActivityManager.MemoryInfo();((ActivityManager)context.getSystemService(Context.ACTIVITY_SERVICE)).getMemoryInfo(m);if(m.totalMem>0){s.ramPercent=(int)Math.round(100.0*(m.totalMem-m.availMem)/m.totalMem);s.ram="RAM "+s.ramPercent+"%";}}catch(Exception ignored){}
  try{StatFs f=new StatFs(Environment.getDataDirectory().getPath());long total=f.getTotalBytes(),free=f.getAvailableBytes();if(total>0){s.diskPercent=(int)Math.round(100.0*(total-free)/total);s.disk=String.format(new Locale("ru"),"Диск %d%% · %.1f ГиБ св.",s.diskPercent,free/1073741824.0);}}catch(Exception ignored){}
  return s;
 }
}
