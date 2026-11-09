package local.proskurnin.preview;
import android.accessibilityservice.AccessibilityService;import android.view.accessibility.AccessibilityEvent;import android.view.KeyEvent;import android.content.*;import android.os.*;
/** Assistant and explicitly learned app buttons. No screen reading; Home/Power pass through. */
public class VoiceKeyService extends AccessibilityService {
 AppKeyController appKeys;boolean systemDialog;static VoiceKeyService current;boolean powerPending;long lastPowerMenu;
 static boolean takeScreenshot(){return current!=null&&current.performGlobalAction(GLOBAL_ACTION_TAKE_SCREENSHOT);}
 final BroadcastReceiver windowReturn=new BroadcastReceiver(){public void onReceive(Context c,Intent i){if(systemDialog&&i.getBooleanExtra("application_focused",false))updateKeyFilter(false);}};
 @Override public void onCreate(){super.onCreate();appKeys=new AppKeyController(this);registerReceiver(windowReturn,new IntentFilter("local.proskurnin.preview.APP_WINDOW_FOCUSED"),"local.proskurnin.permission.REMOTE_AI",null);}
 final Handler h=new Handler();boolean down,longPress;int activeKey=-1;long started;boolean pendingShort;
 final Runnable single=()->{pendingShort=false;open(false);};
 final Runnable hold=()->{if(down)longPress=true;};
 final Runnable watchdog=()->reset();
 protected boolean onKeyEvent(KeyEvent e){if(appKeys!=null&&appKeys.event(e))return true;int key=e.getKeyCode();android.view.InputDevice device=e.getDevice();boolean remoteF9=key==KeyEvent.KEYCODE_F9&&device!=null&&device.getVendorId()==0x7545&&device.getProductId()==0x0198;if(!remoteF9&&key!=KeyEvent.KEYCODE_ASSIST&&key!=KeyEvent.KEYCODE_VOICE_ASSIST)return false;if(!getSharedPreferences("preview",0).getBoolean("voice_key_enabled",true))return false;
  android.util.Log.i("ProskurninVoiceKey","action="+e.getAction()+" key="+key+" repeat="+e.getRepeatCount());
  if(e.getAction()==KeyEvent.ACTION_DOWN){if(!down){down=true;activeKey=key;started=e.getEventTime();longPress=false;h.postDelayed(hold,700);h.postDelayed(watchdog,10000);}if(e.isLongPress()||e.getEventTime()-started>=700)longPress=true;}
  else if(e.getAction()==KeyEvent.ACTION_UP){boolean launch=down&&activeKey==key&&!e.isCanceled(),dialog=longPress||e.getEventTime()-started>=700;reset();if(launch){if(dialog||pendingShort){h.removeCallbacks(single);pendingShort=false;open(true);}else{pendingShort=true;h.postDelayed(single,420);}}}return true;
 }
 void open(boolean dialog){if(!getSharedPreferences("preview",0).getBoolean("ai_enabled",true)||!getSharedPreferences("preview",0).getBoolean("voice_key_enabled",true))return;try{Intent intent=new Intent(this,dialog?AssistantActivity.class:MovieActivity.class).putExtra("auto_voice",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);startActivity(intent);android.util.Log.i("ProskurninVoiceKey",dialog?"launch=dialog":"launch=movies");}catch(Exception e){android.util.Log.w("ProskurninVoiceKey","launch failed");}}
 void reset(){h.removeCallbacks(hold);h.removeCallbacks(watchdog);down=false;longPress=false;activeKey=-1;}
 @Override protected void onServiceConnected(){super.onServiceConnected();current=this;updateKeyFilter(false);}
 void updateKeyFilter(boolean suspend){
  android.accessibilityservice.AccessibilityServiceInfo info=getServiceInfo();if(info==null)return;
  int flag=android.accessibilityservice.AccessibilityServiceInfo.FLAG_REQUEST_FILTER_KEY_EVENTS;
  int flags=suspend?info.flags&~flag:info.flags|flag;
  if(flags!=info.flags){onInterrupt();info.flags=flags;setServiceInfo(info);android.util.Log.i("ProskurninVoiceKey",suspend?"System dialog: key filter suspended":"App window: key filter restored");}
  systemDialog=suspend;
 }
 public void onAccessibilityEvent(AccessibilityEvent e){if(e.getEventType()!=AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED)return;String pkg=e.getPackageName()==null?null:e.getPackageName().toString(),cls=e.getClassName()==null?null:e.getClassName().toString();if("com.android.systemui".equals(pkg))android.util.Log.i("ProskurninVoiceKey","System window class="+cls);updateKeyFilter(SystemDialogKeys.suspended(systemDialog,pkg,cls));
 if("com.android.systemui".equals(pkg)&&"com.android.systemui.globalactions.GlobalActionsDialog$ActionsDialog".equals(cls)&&getSharedPreferences("preview",0).getBoolean("power_menu",false)&&(PowerMenuActivity.visible||SystemClock.elapsedRealtime()-lastPowerMenu<=1500)){sendBroadcast(new Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS));return;}
 if("com.android.systemui".equals(pkg)&&"com.android.systemui.globalactions.GlobalActionsDialog$ActionsDialog".equals(cls)&&getSharedPreferences("preview",0).getBoolean("power_menu",false)&&!powerPending&&SystemClock.elapsedRealtime()-lastPowerMenu>1500){powerPending=true;new Thread(()->{boolean ready="READY".equals(PowerControl.request("PING"));h.post(()->{powerPending=false;if(!ready||!systemDialog)return;lastPowerMenu=SystemClock.elapsedRealtime();sendBroadcast(new Intent(Intent.ACTION_CLOSE_SYSTEM_DIALOGS));startActivity(new Intent(this,PowerMenuActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP));});},"power-check").start();}
 }
 public void onInterrupt(){if(appKeys!=null)appKeys.clear();reset();h.removeCallbacks(single);pendingShort=false;}public void onDestroy(){if(current==this)current=null;unregisterReceiver(windowReturn);onInterrupt();if(appKeys!=null)appKeys.close();super.onDestroy();}
}
