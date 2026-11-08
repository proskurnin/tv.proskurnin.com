package local.proskurnin.preview;
import android.accessibilityservice.AccessibilityService;import android.view.accessibility.AccessibilityEvent;import android.view.KeyEvent;import android.content.*;import android.os.*;
/** Filters only the assistant key. Never reads screen contents or handles Home/Power. */
public class VoiceKeyService extends AccessibilityService {
 final Handler h=new Handler();boolean down,longPress;int activeKey=-1;long started;boolean pendingShort;
 final Runnable single=()->{pendingShort=false;open(false);};
 final Runnable hold=()->{if(down)longPress=true;};
 final Runnable watchdog=()->reset();
 protected boolean onKeyEvent(KeyEvent e){int key=e.getKeyCode();android.view.InputDevice device=e.getDevice();boolean remoteF9=key==KeyEvent.KEYCODE_F9&&device!=null&&device.getVendorId()==0x7545&&device.getProductId()==0x0198;if(!remoteF9&&key!=KeyEvent.KEYCODE_ASSIST&&key!=KeyEvent.KEYCODE_VOICE_ASSIST)return false;if(!getSharedPreferences("preview",0).getBoolean("voice_key_enabled",true))return false;
  android.util.Log.i("ProskurninVoiceKey","action="+e.getAction()+" key="+key+" repeat="+e.getRepeatCount());
  if(e.getAction()==KeyEvent.ACTION_DOWN){if(!down){down=true;activeKey=key;started=e.getEventTime();longPress=false;h.postDelayed(hold,700);h.postDelayed(watchdog,10000);}if(e.isLongPress()||e.getEventTime()-started>=700)longPress=true;}
  else if(e.getAction()==KeyEvent.ACTION_UP){boolean launch=down&&activeKey==key&&!e.isCanceled(),dialog=longPress||e.getEventTime()-started>=700;reset();if(launch){if(dialog||pendingShort){h.removeCallbacks(single);pendingShort=false;open(true);}else{pendingShort=true;h.postDelayed(single,420);}}}return true;
 }
 void open(boolean dialog){if(!getSharedPreferences("preview",0).getBoolean("ai_enabled",true)||!getSharedPreferences("preview",0).getBoolean("voice_key_enabled",true))return;try{Intent intent=new Intent(this,dialog?AssistantActivity.class:MovieActivity.class).putExtra("auto_voice",true).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);startActivity(intent);android.util.Log.i("ProskurninVoiceKey",dialog?"launch=dialog":"launch=movies");}catch(Exception e){android.util.Log.w("ProskurninVoiceKey","launch failed");}}
 void reset(){h.removeCallbacks(hold);h.removeCallbacks(watchdog);down=false;longPress=false;activeKey=-1;}
 public void onAccessibilityEvent(AccessibilityEvent e){}public void onInterrupt(){reset();h.removeCallbacks(single);pendingShort=false;}public void onDestroy(){onInterrupt();super.onDestroy();}
}
