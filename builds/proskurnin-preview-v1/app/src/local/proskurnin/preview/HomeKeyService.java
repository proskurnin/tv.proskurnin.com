package local.proskurnin.preview;
import android.accessibilityservice.AccessibilityService;import android.view.accessibility.AccessibilityEvent;import android.view.KeyEvent;import android.content.*;import android.os.*;import android.widget.Toast;
public class HomeKeyService extends AccessibilityService {
 final Handler handler=new Handler(); boolean pressed,longFired;
 final Runnable hold=()->{if(pressed&&!longFired){longFired=true;launch(true);}};
 void launch(boolean google){try{Intent intent=google?new Intent(Intent.ACTION_MAIN).setComponent(new ComponentName("com.google.android.tvlauncher","com.google.android.tvlauncher.MainActivity")):new Intent(this,MainActivity.class).setAction(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME);intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);startActivity(intent);android.util.Log.i("ProskurninHomeKeys",google?"long HOME -> Google":"short HOME -> Proskurnin");}catch(Exception e){Toast.makeText(this,"Не удалось открыть главный экран",Toast.LENGTH_SHORT).show();}}
 @Override protected boolean onKeyEvent(KeyEvent e){if(e.getKeyCode()==KeyEvent.KEYCODE_POWER){if(e.getRepeatCount()==0||e.isLongPress())android.util.Log.i("ProskurninHomeKeys","POWER pass-through action="+e.getAction()+" repeat="+e.getRepeatCount());return false;}if(e.getKeyCode()!=KeyEvent.KEYCODE_HOME)return false;if(e.getAction()==KeyEvent.ACTION_DOWN){if(!pressed){pressed=true;longFired=false;handler.postDelayed(hold,650);}if(e.isLongPress()&&!longFired){handler.removeCallbacks(hold);hold.run();}}else if(e.getAction()==KeyEvent.ACTION_UP){handler.removeCallbacks(hold);boolean shortPress=pressed&&!longFired&&!e.isCanceled();pressed=false;if(shortPress)launch(false);}return true;}
 @Override public void onAccessibilityEvent(AccessibilityEvent event){}
 @Override public void onInterrupt(){reset();}
 void reset(){handler.removeCallbacks(hold);pressed=false;longFired=false;}
 @Override public void onDestroy(){reset();super.onDestroy();}
}
