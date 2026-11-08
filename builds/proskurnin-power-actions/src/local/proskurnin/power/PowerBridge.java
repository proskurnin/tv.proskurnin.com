package local.proskurnin.power;
import android.net.*;import android.os.*;import android.content.*;import android.content.pm.*;import java.io.*;import java.security.*;import java.util.*;import java.util.concurrent.*;
/** Local-only, certificate-gated power service. No caller-supplied shell/arguments. */
public final class PowerBridge {
 static final String PKG="local.proskurnin.preview",CERT="d3733a24d525bbbe59f46f3707fb6b5b1c8341ecaadd619fd4bd62ee74c40f21";static PackageManager pm;static volatile boolean pending;static long lastAction=-60000;
 static boolean allowed(int uid){try{if(pm.getPackageUid(PKG,0)!=uid)return false;PackageInfo p=pm.getPackageInfo(PKG,PackageManager.GET_SIGNATURES);if(p.signatures.length!=1)return false;byte[] hash=MessageDigest.getInstance("SHA-256").digest(p.signatures[0].toByteArray());StringBuilder h=new StringBuilder();for(byte v:hash)h.append(String.format(Locale.US,"%02x",v&255));return CERT.equals(h.toString());}catch(Exception e){return false;}}
 static int run(String... args)throws Exception{java.lang.Process p=new ProcessBuilder(args).redirectErrorStream(true).redirectOutput(new File("/dev/null")).start();if(!p.waitFor(15,TimeUnit.SECONDS)){p.destroy();return -1;}return p.exitValue();}
 static void perform(String command){try{Thread.sleep(400);android.util.Log.i("ProskurninPower", "Requested "+command);
  if(command.equals("OFF")){
   // Notify apps before init stops services, syncs and unmounts. Never use a forced reboot syscall.
   run("/system/bin/am","broadcast","-a","android.intent.action.ACTION_SHUTDOWN","--receiver-foreground");
   run("/system/bin/sync");
   if(run("/system/bin/reboot","-p","userrequested")!=0)throw new IOException("init shutdown rejected");
  }else if(command.equals("REBOOT")){
   // Normal Android shutdown sequence, but explicit reason rather than menu's userrequested.
   if(run("/system/bin/svc","power","reboot","adb")!=0)throw new IOException("reboot rejected or timed out");
  }
 }catch(Exception e){android.util.Log.e("ProskurninPower","Power action failed; no automatic retry");}finally{pending=false;}}
 public static void main(String[] args)throws Exception{
  if(android.os.Process.myUid()!=0)throw new SecurityException("root service required");Looper.prepareMainLooper();Class<?> at=Class.forName("android.app.ActivityThread");Object thread=at.getMethod("systemMain").invoke(null);Context c=(Context)at.getMethod("getSystemContext").invoke(thread);pm=c.getPackageManager();
  LocalServerSocket server=new LocalServerSocket("proskurnin.power.v1");android.util.Log.i("ProskurninPower","Ready; only signed launcher accepted");
  while(true){try(LocalSocket client=server.accept()){client.setSoTimeout(1000);if(!allowed(client.getPeerCredentials().getUid())){client.getOutputStream().write("DENIED\n".getBytes("US-ASCII"));continue;}
   StringBuilder b=new StringBuilder();boolean complete=false;int ch;while(b.length()<8&&(ch=client.getInputStream().read())!=-1){if(ch=='\n'){complete=true;break;}if(ch<'A'||ch>'Z')break;b.append((char)ch);}String command=complete?b.toString():"";String result="DENIED";
   if(command.equals("PING"))result="READY";else if((command.equals("OFF")||command.equals("REBOOT"))&&!pending&&SystemClock.elapsedRealtime()-lastAction>=60000){pending=true;lastAction=SystemClock.elapsedRealtime();result="QUEUED";new Thread(()->perform(command),"power-action").start();}
   client.getOutputStream().write((result+"\n").getBytes("US-ASCII"));
  }catch(Exception e){android.util.Log.w("ProskurninPower","Rejected or disconnected request");}}
 }
}
