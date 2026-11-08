package local.proskurnin.preview;
import android.content.*;import android.os.*;import java.net.*;import java.io.*;import java.util.Locale;import org.json.JSONObject;
/** Bounded downstream throughput to our authenticated RU node, only while focused. */
final class NetworkSpeedProbe {
 static final long LIMIT=16L*1024*1024,INTERVAL=30L*60*1000;
 final Context context;final android.content.SharedPreferences prefs;final Handler h=new Handler();final Runnable changed;
 String key="",suffix="";boolean focused,busy;int generation;CancellationSignal cancel;
 final Runnable begin=()->start();
 NetworkSpeedProbe(Context c,Runnable changed){context=c.getApplicationContext();prefs=c.getSharedPreferences("preview",0);this.changed=changed;}
 void networkChanged(String next){if(key.equals(next))return;stop();key=next;suffix="";}
 String label(){long age=System.currentTimeMillis()-prefs.getLong("speed_at",0);if(!busy&&age>=0&&age<INTERVAL&&key.equals(prefs.getString("speed_network",""))){double mbps=Double.longBitsToDouble(prefs.getLong("speed_value",0));if(Double.isFinite(mbps)&&mbps>0)return String.format(new Locale("ru")," · ↓ %.1f Мбит/с · до RU",mbps);}return suffix;}
 void focus(boolean value){if(value==focused)return;focused=value;if(value){suffix=" · замер скорости…";h.postDelayed(begin,900);}else stop();}
 void stop(){focused=false;h.removeCallbacks(begin);generation++;if(cancel!=null)cancel.cancel();cancel=null;busy=false;suffix="";}
 void start(){if(!focused)return;long now=System.currentTimeMillis(),age=now-prefs.getLong("speed_attempt",0);if(age>=0&&age<INTERVAL){suffix=" · замер позже";changed.run();return;}prefs.edit().putLong("speed_attempt",now).apply();busy=true;suffix=" · измеряю…";changed.run();final int token=++generation;final String connectionKey=key;final CancellationSignal signal=new CancellationSignal();cancel=signal;
  new Thread(()->{double value=Double.NaN;long bytes=0,elapsed=0;HttpURLConnection c=null;Runnable timeout=()->signal.cancel();h.postDelayed(timeout,9000);
   try{JSONObject config=ApiClient.privateJson(context,"api-client.json");String base=config.getString("base_url");if(!base.equals("https://ru01.firstvds.proskurn.in/tv-api/v1/"))throw new IOException("CONFIG");
    c=(HttpURLConnection)new URL(base+"network/speed").openConnection();final HttpURLConnection connection=c;signal.setOnCancelListener(()->connection.disconnect());signal.throwIfCanceled();c.setConnectTimeout(4000);c.setReadTimeout(2000);c.setInstanceFollowRedirects(false);c.setUseCaches(false);c.setRequestProperty("Authorization","Bearer "+config.getString("token"));c.setRequestProperty("Accept-Encoding","identity");c.setRequestProperty("Cache-Control","no-cache");
    if(c.getResponseCode()!=200||c.getContentLengthLong()!=LIMIT||c.getHeaderField("Content-Encoding")!=null)throw new IOException("RESPONSE");
    long start=SystemClock.elapsedRealtime();try(InputStream in=c.getInputStream()){byte[] buffer=new byte[32768];int n;while(bytes<LIMIT&&(n=in.read(buffer,0,(int)Math.min(buffer.length,LIMIT-bytes)))!=-1){signal.throwIfCanceled();bytes+=n;elapsed=SystemClock.elapsedRealtime()-start;if(elapsed>=5000)break;}}
    signal.throwIfCanceled();if(bytes>=131072&&elapsed>=100)value=bytes*8.0/(elapsed*1000.0);
   }catch(Exception ignored){}finally{h.removeCallbacks(timeout);signal.setOnCancelListener(null);if(c!=null)c.disconnect();}
   final double measured=value;final long readBytes=bytes,readMs=elapsed;h.post(()->{if(token!=generation||!focused)return;busy=false;cancel=null;if(Double.isFinite(measured)){prefs.edit().putLong("speed_at",System.currentTimeMillis()).putLong("speed_value",Double.doubleToLongBits(measured)).putString("speed_network",connectionKey).apply();suffix="";android.util.Log.i("ProskurninSpeed","node=RU bytes="+readBytes+" ms="+readMs+" mbps="+measured);}else suffix=" · замер недоступен";changed.run();});
  },"network-speed").start();
 }
}
