package local.proskurnin.preview;
import android.view.KeyEvent;
/** In-process, foreground-only calibration. Never records ordinary keyboard input. */
final class AppKeyLearning {
 interface Listener{void captured(String identity);}
 static Listener listener;static String held="";
 static void begin(Listener value){listener=value;held="";}
 static void cancel(){listener=null;held="";}
 static boolean active(){return listener!=null;}
 static boolean event(KeyEvent e){if(listener==null)return false;String id=AppKeys.identity(e);if(id.isEmpty())return false;if(e.getAction()==KeyEvent.ACTION_DOWN){if(e.getRepeatCount()==0&&held.isEmpty())held=id;return id.equals(held);}if(e.getAction()==KeyEvent.ACTION_UP){if(!id.equals(held))return false;boolean valid=!e.isCanceled();Listener callback=listener;held="";if(valid){listener=null;callback.captured(id);}return true;}return false;}
}
