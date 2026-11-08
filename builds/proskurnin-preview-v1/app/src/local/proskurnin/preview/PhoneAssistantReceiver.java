package local.proskurnin.preview;
import android.content.*;
public class PhoneAssistantReceiver extends BroadcastReceiver {
 public void onReceive(Context c,Intent i){String query=i.getStringExtra("query"),mode=i.getStringExtra("mode");if(!c.getSharedPreferences("preview",0).getBoolean("ai_enabled",true)||query==null||query.trim().length()<2||query.length()>512||!("chat".equals(mode)||"movie".equals(mode)))return;c.startActivity(new Intent(c,"chat".equals(mode)?AssistantActivity.class:MovieActivity.class).putExtra("phone_query",query).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_SINGLE_TOP));}
}
