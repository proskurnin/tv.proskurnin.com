package local.proskurnin.remote;
import android.net.*;import android.os.*;import android.content.*;import android.content.pm.*;import android.view.*;import java.lang.reflect.*;import java.security.*;import java.io.*;import java.util.*;
/** Shell-only input helper. No TCP, shell execution, text entry, coordinates or arbitrary keycodes. */
public final class InputBridge {
 static final String PKG="local.proskurnin.remote",CERT="d3733a24d525bbbe59f46f3707fb6b5b1c8341ecaadd619fd4bd62ee74c40f21";
 static PackageManager pm;static Object input;static Method inject;
 static boolean allowed(int uid){try{if(pm.getPackageUid(PKG,0)!=uid)return false;PackageInfo info=pm.getPackageInfo(PKG,PackageManager.GET_SIGNATURES);if(info.signatures.length!=1)return false;byte[] digest=MessageDigest.getInstance("SHA-256").digest(info.signatures[0].toByteArray());StringBuilder h=new StringBuilder();for(byte b:digest)h.append(String.format(Locale.US,"%02x",b&255));return CERT.equals(h.toString());}catch(Exception e){return false;}}
 static boolean press(int key)throws Exception{long start=SystemClock.uptimeMillis();KeyEvent down=new KeyEvent(start,start,KeyEvent.ACTION_DOWN,key,0,0,KeyCharacterMap.VIRTUAL_KEYBOARD,0,0,InputDevice.SOURCE_DPAD);boolean first=(Boolean)inject.invoke(input,down,2);KeyEvent up=new KeyEvent(start,SystemClock.uptimeMillis(),KeyEvent.ACTION_UP,key,0,0,KeyCharacterMap.VIRTUAL_KEYBOARD,0,0,InputDevice.SOURCE_DPAD);boolean second=(Boolean)inject.invoke(input,up,2);return first&&second;}
 public static void main(String[] args)throws Exception{
  if(android.os.Process.myUid()!=2000)throw new SecurityException("Must run as shell");if(Looper.getMainLooper()==null)Looper.prepareMainLooper();Class<?> activityThread=Class.forName("android.app.ActivityThread");Object thread=activityThread.getMethod("systemMain").invoke(null);Context context=(Context)activityThread.getMethod("getSystemContext").invoke(thread);pm=context.getPackageManager();Class<?> manager=Class.forName("android.hardware.input.InputManager");input=manager.getMethod("getInstance").invoke(null);inject=manager.getMethod("injectInputEvent",InputEvent.class,int.class);
  Map<String,Integer> keys=new HashMap<>();keys.put("UP",19);keys.put("DOWN",20);keys.put("LEFT",21);keys.put("RIGHT",22);keys.put("OK",23);keys.put("BACK",4);keys.put("MENU",82);keys.put("PLAY",85);keys.put("VOLUP",24);keys.put("VOLDOWN",25);keys.put("MUTE",164);
  LocalServerSocket server=new LocalServerSocket("proskurnin.remote.keys.v1");android.util.Log.i("ProskurninRemoteBridge","Ready as shell; app certificate required");long window=0;int count=0;
  while(true){try(LocalSocket client=server.accept()){client.setSoTimeout(1000);if(!allowed(client.getPeerCredentials().getUid())){client.getOutputStream().write("DENIED\n".getBytes("US-ASCII"));continue;}StringBuilder command=new StringBuilder();int ch;boolean complete=false;InputStream in=client.getInputStream();while(command.length()<16&&(ch=in.read())!=-1){if(ch=='\n'){complete=true;break;}if(ch<'A'||ch>'Z')break;command.append((char)ch);}String name=complete?command.toString():"";boolean ok=false;
    if(name.equals("PING"))ok=true;else if(keys.containsKey(name)){long now=SystemClock.elapsedRealtime();if(now-window>=1000){window=now;count=0;}if(++count<=15)ok=press(keys.get(name));}
    client.getOutputStream().write((ok?"OK\n":"DENIED\n").getBytes("US-ASCII"));
   }catch(Exception e){android.util.Log.w("ProskurninRemoteBridge","Rejected or interrupted command");}}
 }
}
