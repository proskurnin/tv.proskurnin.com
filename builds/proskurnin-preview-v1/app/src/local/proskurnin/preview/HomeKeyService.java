package local.proskurnin.preview;
import android.accessibilityservice.AccessibilityService;import android.view.accessibility.AccessibilityEvent;import android.view.KeyEvent;import android.content.*;import android.os.*;import android.widget.Toast;
public class HomeKeyService extends AccessibilityService {
 final Handler handler=new Handler(); boolean pressed,longFired;
 final MiPressGesture miGesture=new MiPressGesture();int miDevice=-1;long miDownTime;
 boolean pendingMiShort;
 final Runnable miSingle=()->{pendingMiShort=false;launchAi(false,"short");};
 String stockPackage,stockActivity;long lastRedirect=-1000;
 final Runnable hold=()->{if(pressed&&!longFired){longFired=true;launch(true);}};
 void launch(boolean google){if(google&&UniversalProfile.enabled(this)){UniversalProfile.otherHome(this);return;}try{Intent intent=google?new Intent(Intent.ACTION_MAIN).setComponent(new ComponentName("com.google.android.tvlauncher","com.google.android.tvlauncher.MainActivity")):new Intent(this,MainActivity.class).setAction(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME);intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);startActivity(intent);android.util.Log.i("ProskurninHomeKeys",google?"long HOME -> Google":"short HOME -> Proskurnin");}catch(Exception e){Toast.makeText(this,"Не удалось открыть главный экран",Toast.LENGTH_SHORT).show();}}
 @Override protected boolean onKeyEvent(KeyEvent e){if(e.getKeyCode()==KeyEvent.KEYCODE_POWER){if(e.getRepeatCount()==0||e.isLongPress())android.util.Log.i("ProskurninHomeKeys","POWER pass-through action="+e.getAction()+" repeat="+e.getRepeatCount());return false;}if(isMiButton(e))return miButton(e);if(e.getKeyCode()!=KeyEvent.KEYCODE_HOME)return false;if(e.getAction()==KeyEvent.ACTION_DOWN){if(!pressed){pressed=true;longFired=false;handler.postDelayed(hold,650);}if(e.isLongPress()&&!longFired){handler.removeCallbacks(hold);hold.run();}}else if(e.getAction()==KeyEvent.ACTION_UP){handler.removeCallbacks(hold);boolean shortPress=pressed&&!longFired&&!e.isCanceled();pressed=false;if(shortPress)launch(false);}return true;}
 boolean isMiButton(KeyEvent e){android.view.InputDevice d=e.getDevice();return UniversalProfile.enabled(this)&&"nino".equals(android.os.Build.DEVICE)&&"MiTV-MSSP1".equals(android.os.Build.MODEL)&&d!=null&&d.getVendorId()==0x2717&&d.getProductId()==0x32b9&&e.getKeyCode()==KeyEvent.KEYCODE_BUTTON_4&&e.getScanCode()==400;}
 boolean miButton(KeyEvent e){int id=e.getDeviceId();long time=e.getDownTime();if(e.getAction()==KeyEvent.ACTION_DOWN){if(miGesture.down(id,time,e.getRepeatCount())){miDevice=id;miDownTime=time;}return true;}if(e.getAction()==KeyEvent.ACTION_UP){long duration=e.getEventTime()-miDownTime;int action=miGesture.up(id,time,e.isCanceled());if(duration<700&&action==MiPressGesture.SHORT){if(pendingMiShort){handler.removeCallbacks(miSingle);pendingMiShort=false;launchAi(true,"double");}else{pendingMiShort=true;handler.postDelayed(miSingle,420);}}miDevice=-1;miDownTime=0;}return true;}
 void launchAi(boolean dialog,String trigger){try{startActivity(new Intent(this,dialog?AssistantActivity.class:MovieActivity.class).putExtra("auto_voice",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP));android.util.Log.i("ProskurninHomeKeys","Mi "+trigger+" -> "+(dialog?"AI dialog":"AI movies"));}catch(Exception e){android.util.Log.w("ProskurninHomeKeys","Mi AI launch failed");}}
 @Override protected void onServiceConnected(){
  super.onServiceConnected();reset();
  if(!UniversalProfile.enabled(this))return;
  android.content.pm.ResolveInfo home=UniversalProfile.alternativeHome(this);
  if(home!=null){stockPackage=home.activityInfo.packageName;stockActivity=home.activityInfo.name;
   android.accessibilityservice.AccessibilityServiceInfo info=getServiceInfo();
   if(info!=null){info.packageNames=new String[]{stockPackage};setServiceInfo(info);}
  }
  SharedPreferences prefs=getSharedPreferences("preview",0);
  int boot=android.provider.Settings.Global.getInt(getContentResolver(),"boot_count",-1);
  boolean start=HomeRoutePolicy.startOnConnection(prefs.getBoolean("home_route_initialized",false),prefs.getInt("home_route_boot",-1),boot);
  prefs.edit().putBoolean("home_route_initialized",true).putInt("home_route_boot",boot).apply();
  // One start on explicit activation or a new boot; service reconnection must not interrupt a film.
  if(start){prefs.edit().putBoolean("stock_home_session",false).apply();launch(false);}
 }
 @Override public void onAccessibilityEvent(AccessibilityEvent event){
  if(!UniversalProfile.enabled(this)||event.getEventType()!=AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED)return;
  if(HomeRoutePolicy.redirect(getSharedPreferences("preview",0).getBoolean("stock_home_session",false),stockPackage,stockActivity,event.getPackageName(),event.getClassName())){
   long now=SystemClock.elapsedRealtime();if(now-lastRedirect>=1000){lastRedirect=now;launch(false);}
  }
 }
 @Override public void onInterrupt(){reset();}
 void reset(){handler.removeCallbacks(hold);handler.removeCallbacks(miSingle);miGesture.reset();miDevice=-1;miDownTime=0;pendingMiShort=false;pressed=false;longFired=false;}
 @Override public void onDestroy(){reset();super.onDestroy();}
}
