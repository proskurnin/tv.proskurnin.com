package local.proskurnin.remote;
import android.accessibilityservice.*;import android.view.accessibility.*;import android.os.*;import org.json.*;import java.util.concurrent.*;
/** Only focused editable nodes; never traverse or publish the screen or password fields. */
public class TextInputService extends AccessibilityService {
 static volatile TextInputService instance;final Handler handler=new Handler();AccessibilityNodeInfo tracked;String id="";long sequence;int revision;String lastText="";
 protected void onServiceConnected(){instance=this;}
 boolean enabled(){RemoteService r=RemoteService.instance;return r!=null&&r.server!=null&&r.awake&&getSharedPreferences("remote",0).getBoolean("text_input",true)&&getSharedPreferences("remote",0).getBoolean("enabled",false);}
 static boolean safe(AccessibilityNodeInfo n){if(n==null||!n.isEditable()||!n.isEnabled()||!n.isVisibleToUser()||!n.isFocused()||n.isPassword())return false;int type=n.getInputType(),cls=type&15,variation=type&4080;if(cls==1&&(variation==128||variation==144||variation==224)||cls==2&&variation==16)return false;return n.getActionList().contains(AccessibilityNodeInfo.AccessibilityAction.ACTION_SET_TEXT);}
 void clear(){if(tracked!=null)tracked.recycle();tracked=null;id="";lastText="";revision=0;}
 void inspect(){if(!enabled()){clear();return;}AccessibilityNodeInfo root=getRootInActiveWindow(),node=null;try{if(root!=null)node=root.findFocus(AccessibilityNodeInfo.FOCUS_INPUT);if(!safe(node)){clear();return;}if(tracked==null||!tracked.equals(node)){clear();tracked=AccessibilityNodeInfo.obtain(node);id=java.util.UUID.randomUUID().toString();sequence++;}String value=node.getText()==null?"":node.getText().toString();if(value.length()>512){clear();return;}if(!lastText.equals(value)){lastText=value;revision++;}}finally{if(node!=null)node.recycle();if(root!=null)root.recycle();}}
 public void onAccessibilityEvent(AccessibilityEvent e){inspect();}
 public void onInterrupt(){clear();}
 public void onDestroy(){clear();instance=null;super.onDestroy();}
 JSONObject snapshot()throws Exception{inspect();JSONObject result=new JSONObject().put("available",true).put("active",tracked!=null);if(tracked!=null)result.put("id",id).put("revision",revision).put("text",lastText).put("package",String.valueOf(tracked.getPackageName()));return result;}
 boolean write(String field,int expected,String text){inspect();if(tracked==null||!id.equals(field)||revision!=expected||text.length()>512)return false;Bundle args=new Bundle();args.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,text);boolean ok=tracked.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,args);if(ok){lastText=text;revision++;}return ok;}
 interface Operation<T>{T run()throws Exception;}
 static <T>T main(Operation<T> op,T fallback){TextInputService s=instance;if(s==null)return fallback;FutureTask<T> task=new FutureTask<>(()->op.run());s.handler.post(task);try{return task.get(1500,TimeUnit.MILLISECONDS);}catch(Exception e){task.cancel(false);return fallback;}}
 static void reset(){TextInputService s=instance;if(s!=null)s.handler.post(()->s.clear());}
 static JSONObject state(){TextInputService s=instance;return main(()->s.snapshot(),new JSONObject());}
 static boolean set(String id,int revision,String value){TextInputService s=instance;return main(()->s.write(id,revision,value),false);}
}
