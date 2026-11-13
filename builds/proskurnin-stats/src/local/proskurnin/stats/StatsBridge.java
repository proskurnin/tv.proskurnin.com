package local.proskurnin.stats;
import android.app.usage.*;import android.content.*;import android.content.pm.*;import android.net.*;import android.os.*;import android.os.storage.StorageManager;import java.io.*;import java.security.*;import java.util.*;import org.json.*;

/** Optional shell process: aggregate CPU only, no arbitrary commands, TCP or root. */
public final class StatsBridge {
 static final String PKG="local.proskurnin.preview",CERT="CERTIFICATE_PLACEHOLDER",SOCKET="proskurnin.stats.v1";
 static final File STOP_FILE=new File("/data/local/tmp/proskurnin-stats.stop");
 static Context context;static PackageManager pm;
 static boolean allowed(int uid){try{if(pm.getPackageUid(PKG,0)!=uid)return false;PackageInfo info=pm.getPackageInfo(PKG,PackageManager.GET_SIGNATURES);if(info.signatures==null||info.signatures.length!=1)return false;byte[] bytes=MessageDigest.getInstance("SHA-256").digest(info.signatures[0].toByteArray());StringBuilder hash=new StringBuilder();for(byte b:bytes)hash.append(String.format(Locale.US,"%02x",b&255));return CERT.equals(hash.toString());}catch(Exception e){return false;}}
 static void initialize()throws Exception{if(android.os.Process.myUid()!=2000)throw new SecurityException("Shell UID required");if(Looper.getMainLooper()==null)Looper.prepareMainLooper();Class<?> at=Class.forName("android.app.ActivityThread");Object thread=at.getMethod("systemMain").invoke(null);Context system=(Context)at.getMethod("getSystemContext").invoke(thread);context=system.createPackageContext("com.android.shell",0);pm=context.getPackageManager();}
 static void streamCpu()throws Exception{
  File dir=new File(Environment.getExternalStorageDirectory(),"Android/data/"+PKG+"/files");
  if(!dir.isDirectory()&&!dir.mkdirs())throw new IOException("Cannot access launcher private external-files directory");
  File target=new File(dir,"cpu.stat"),temp=new File(dir,"cpu.stat.tmp");
  STOP_FILE.delete();
  while(true){
   if(STOP_FILE.isFile()){STOP_FILE.delete();return;}
   String line="";
   try(BufferedReader r=new BufferedReader(new FileReader("/proc/stat"))){String value=r.readLine();if(value!=null&&value.startsWith("cpu ")&&value.length()<512)line=value;}catch(IOException ignored){}
   if(!line.isEmpty()){
    try(FileOutputStream out=new FileOutputStream(temp)){out.write((line+"\n").getBytes("US-ASCII"));out.getFD().sync();}catch(IOException ignored){}
    if(temp.isFile()&&!temp.renameTo(target)){try(FileOutputStream out=new FileOutputStream(target)){out.write((line+"\n").getBytes("US-ASCII"));}catch(IOException ignored){}}
   }
   Thread.sleep(1000);
  }
 }
 static void storage()throws Exception{
  StorageStatsManager manager=(StorageStatsManager)context.getSystemService(Context.STORAGE_STATS_SERVICE);JSONArray apps=new JSONArray();
  for(ApplicationInfo app:pm.getInstalledApplications(0)){
   StorageStats stats=manager.queryStatsForPackage(StorageManager.UUID_DEFAULT,app.packageName,android.os.Process.myUserHandle());
   apps.put(new JSONObject().put("package",app.packageName).put("label",app.loadLabel(pm).toString()).put("system",(app.flags&ApplicationInfo.FLAG_SYSTEM)!=0).put("updated_system",(app.flags&ApplicationInfo.FLAG_UPDATED_SYSTEM_APP)!=0).put("app_bytes",stats.getAppBytes()).put("data_bytes_including_cache",stats.getDataBytes()).put("cache_bytes",stats.getCacheBytes()));
  }
  StatFs fs=new StatFs(Environment.getDataDirectory().getPath());System.out.println(new JSONObject().put("apps",apps).put("measured_at_ms",System.currentTimeMillis()).put("data_total",fs.getTotalBytes()).put("data_free",fs.getFreeBytes()).put("data_available",fs.getAvailableBytes()));
 }
 public static void main(String[] args)throws Exception{
  initialize();
  if(args.length==1&&args[0].equals("--storage")){storage();return;}
  if(args.length==1&&args[0].equals("--stop")){try{new FileOutputStream(STOP_FILE).close();System.out.println("STOP REQUESTED");}catch(IOException e){System.out.println("STOP REQUEST FAILED");}return;}
  if(args.length==1&&args[0].equals("--ping")){File cpu=new File(Environment.getExternalStorageDirectory(),"Android/data/"+PKG+"/files/cpu.stat");System.out.println(cpu.isFile()&&System.currentTimeMillis()-cpu.lastModified()<=8000?"READY":"NO DATA");return;}
  System.out.println("CPU helper: writing aggregate counters only to Proskurnin app private external files");
  streamCpu();
 }
}
