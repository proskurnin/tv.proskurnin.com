package local.proskurnin.remote;
import android.content.*;
public class RemoteBoot extends BroadcastReceiver {
 public void onReceive(Context c,Intent i){if(Intent.ACTION_BOOT_COMPLETED.equals(i.getAction())&&c.getSharedPreferences("remote",0).getBoolean("enabled",false))c.startForegroundService(new Intent(c,RemoteService.class));}
}
