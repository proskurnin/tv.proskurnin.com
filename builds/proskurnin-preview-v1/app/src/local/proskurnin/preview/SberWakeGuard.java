package local.proskurnin.preview;

import android.content.*;
import android.content.pm.ResolveInfo;
import android.os.*;
import android.view.KeyEvent;

/** Sber-only adapter, hosted by the already enabled service; no polling or extra permissions. */
final class SberWakeGuard {
 final Context context;
 final SberWakePolicy policy=new SberWakePolicy();
 final PowerManager power;
 final boolean enabled;
 final BroadcastReceiver receiver=new BroadcastReceiver(){public void onReceive(Context c,Intent i){
  if(Intent.ACTION_SCREEN_OFF.equals(i.getAction()))policy.screenOff();
  else if(Intent.ACTION_SCREEN_ON.equals(i.getAction())&&policy.screenOn(SystemClock.elapsedRealtime()))restore();
 }};
 SberWakeGuard(Context c){
  context=c;power=(PowerManager)c.getSystemService(Context.POWER_SERVICE);
  enabled=SberWakePolicy.supported(UniversalProfile.enabled(c),Build.MODEL,Build.DEVICE);
  if(enabled){IntentFilter f=new IntentFilter(Intent.ACTION_SCREEN_OFF);f.addAction(Intent.ACTION_SCREEN_ON);c.registerReceiver(receiver,f);}
 }
 void key(KeyEvent e){
  // A deliberate navigation after wake, including long Home, wins over automatic recovery.
  if(enabled&&e.getAction()==KeyEvent.ACTION_DOWN&&e.getKeyCode()!=KeyEvent.KEYCODE_POWER&&e.getKeyCode()!=KeyEvent.KEYCODE_WAKEUP&&e.getKeyCode()!=KeyEvent.KEYCODE_SLEEP)policy.cancel();
 }
 void window(String pkg,String cls){
  if(enabled&&policy.window(pkg,cls,power!=null&&power.isInteractive(),SystemClock.elapsedRealtime()))restore();
 }
 void restore(){
  if(power==null||!power.isInteractive())return;
  ResolveInfo home=context.getPackageManager().resolveActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME),0);
  if(home==null||home.activityInfo==null||!("local.proskurnin.homerouter".equals(home.activityInfo.packageName)||context.getPackageName().equals(home.activityInfo.packageName)))return;
  try{
   context.startActivity(new Intent(context,MainActivity.class).setAction(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED));
   android.util.Log.i("ProskurninWakeGuard","Sber automatic Google resume -> Proskurnin");
  }catch(RuntimeException e){android.util.Log.w("ProskurninWakeGuard","Home recovery unavailable");}
 }
 void close(){if(enabled)context.unregisterReceiver(receiver);policy.cancel();}
}
