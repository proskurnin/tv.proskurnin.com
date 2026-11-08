package local.proskurnin.preview;
import android.content.*;import android.os.*;import android.view.KeyEvent;
/** Reuses the existing assistant key filter; no competing accessibility service. */
final class AppKeyController implements SharedPreferences.OnSharedPreferenceChangeListener {
 final java.util.HashSet<String> consumed=new java.util.HashSet<>();
 final Context context;final Handler handler=new Handler();final AppKeyClicks[] clicks=new AppKeyClicks[4];final Runnable[] timers=new Runnable[4],watchdogs=new Runnable[4];
 AppKeyController(Context c){context=c;for(int i=0;i<4;i++){final int slot=i;clicks[i]=new AppKeyClicks();timers[i]=()->fire(slot,clicks[slot].expire(SystemClock.uptimeMillis()));watchdogs[i]=()->clear(slot);}AppKeys.prefs(c).registerOnSharedPreferenceChangeListener(this);}
 void fire(int slot,int result){if(result!=0&&AppKeys.enabled(context))AppKeys.run(context,AppKeys.action(context,slot,result==2));}
 void clear(int slot){handler.removeCallbacks(timers[slot]);handler.removeCallbacks(watchdogs[slot]);clicks[slot].clear();}
 void clear(){for(int i=0;i<4;i++)clear(i);}
 boolean event(KeyEvent e){String id=AppKeys.identity(e);boolean wasConsumed=e.getAction()==KeyEvent.ACTION_UP&&consumed.remove(id);
  if(AppKeyLearning.active()){clear();boolean captured=AppKeyLearning.event(e);if(captured&&e.getAction()==KeyEvent.ACTION_DOWN)consumed.add(id);return captured||wasConsumed;}
  if(!AppKeys.enabled(context)){clear();return wasConsumed;}int slot=AppKeys.slot(context,id);if(slot<0){int key=e.getKeyCode();if(key==KeyEvent.KEYCODE_HOME||key==KeyEvent.KEYCODE_BACK||key==KeyEvent.KEYCODE_POWER||key==KeyEvent.KEYCODE_F9||key==KeyEvent.KEYCODE_ASSIST||key==KeyEvent.KEYCODE_VOICE_ASSIST)clear();return wasConsumed;}
  AppKeyClicks state=clicks[slot];if(e.getAction()==KeyEvent.ACTION_DOWN){if(e.getRepeatCount()==0&&!state.down){consumed.add(id);handler.removeCallbacks(timers[slot]);fire(slot,state.press(e.getEventTime()));handler.postDelayed(watchdogs[slot],10000);}return consumed.contains(id);}
  if(e.getAction()==KeyEvent.ACTION_UP){if(!wasConsumed)return false;handler.removeCallbacks(watchdogs[slot]);int result=state.release(e.getEventTime(),e.isCanceled(),!AppKeys.action(context,slot,true).equals("none"));fire(slot,result);if(state.deadline>=0)handler.postDelayed(timers[slot],Math.max(0,state.deadline-SystemClock.uptimeMillis()));return true;}return false;
 }

 public void onSharedPreferenceChanged(SharedPreferences p,String key){if(key!=null&&(key.startsWith("appkey_")||key.equals("appkeys_enabled")))clear();}
 void close(){clear();AppKeys.prefs(context).unregisterOnSharedPreferenceChangeListener(this);}
}
