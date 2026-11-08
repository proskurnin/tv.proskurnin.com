package local.proskurnin.preview;
import android.content.*;
public class BootHomeReceiver extends BroadcastReceiver {
 public void onReceive(Context c,Intent event){if(!Intent.ACTION_BOOT_COMPLETED.equals(event.getAction())||!c.getSharedPreferences("preview",0).getBoolean("boot_home",true))return;android.content.pm.ResolveInfo home=c.getPackageManager().resolveActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME),0);if(home!=null&&"local.proskurnin.homerouter".equals(home.activityInfo.packageName))return;try{c.startActivity(new Intent(c,MainActivity.class).setAction(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));}catch(RuntimeException e){android.util.Log.w("ProskurninHomeKeys","Startup launch unavailable");}}
}
