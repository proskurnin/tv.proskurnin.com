package local.proskurnin.preview;
import android.content.*;import android.os.*;import android.provider.Settings;import java.net.*;
final class LauncherClock {
 final SharedPreferences prefs;final int boot;final Handler handler=new Handler();boolean busy;long attempt=-1;long saved,at;int savedBoot;
 LauncherClock(Context c){prefs=c.getSharedPreferences("launcher_clock",0);boot=Settings.Global.getInt(c.getContentResolver(),"boot_count",-1);saved=prefs.getLong("epoch",0);at=prefs.getLong("elapsed",0);savedBoot=prefs.getInt("boot",-2);}
 long now(){long elapsed=SystemClock.elapsedRealtime(),value=ClockEstimate.estimate(System.currentTimeMillis(),elapsed,boot,saved,at,savedBoot);if(!approximate()&&elapsed-at>=60000){saved=value;at=elapsed;prefs.edit().putLong("epoch",saved).putLong("elapsed",at).apply();}return value;}
 boolean approximate(){return saved<=0||boot<0||boot!=savedBoot;}
 void sync(Runnable changed){long elapsed=SystemClock.elapsedRealtime();if(busy||!ClockEstimate.due(elapsed,attempt,approximate()?60000:3600000))return;attempt=elapsed;busy=true;
  new Thread(()->{long epoch=0;HttpURLConnection c=null;try{c=(HttpURLConnection)new URL("https://ru01.firstvds.proskurn.in/").openConnection();c.setRequestMethod("HEAD");c.setConnectTimeout(4000);c.setReadTimeout(4000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);c.getResponseCode();long date=c.getDate();if(date>=1577836800000L&&date<4102444800000L)epoch=date;}catch(Exception ignored){}finally{if(c!=null)c.disconnect();}final long verified=epoch;final long received=SystemClock.elapsedRealtime();handler.post(()->{busy=false;if(verified>0){saved=verified;at=received;savedBoot=boot;prefs.edit().putLong("epoch",saved).putLong("elapsed",at).putInt("boot",boot).apply();changed.run();}});},"launcher-clock").start();
 }
}
