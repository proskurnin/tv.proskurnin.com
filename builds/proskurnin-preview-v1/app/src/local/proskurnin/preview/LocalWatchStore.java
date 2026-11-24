package local.proskurnin.preview;
import android.content.*;import android.net.*;import android.os.*;import org.json.*;import java.io.*;import java.util.*;
/** Local only. Imported evidence is separate from the user's manual watched marks. */
final class LocalWatchStore {
 static final String KEY="local_watch_v1";static final Object LOCK=new Object(),WRITE_LOCK=new Object();
 static boolean supported(){return "SaluteTV".equals(Build.MODEL)&&"m7332_eu".equals(Build.DEVICE);}
 static boolean enabled(Context c){return supported()&&c.getSharedPreferences("preview",0).getBoolean("local_watch_enabled",true);}
 static JSONObject saved(Context c){try{return new JSONObject(c.getSharedPreferences("preview",0).getString(KEY,"{}"));}catch(Exception e){return new JSONObject();}}
 static String name(String pkg){String[] ids={"ru.kinopoisk.tv","ru.ivi.client","tv.okko.androidtv","gpm.tnt_premier","ru.mts.mtstv","ru.rt.video.app.tv","mobi.zona","com.lazycatsoftware.lmd"};String[] names={"Кинопоиск","Иви","Okko","PREMIER","KION","Wink","Zona","LazyMedia"};for(int i=0;i<ids.length;i++)if(ids[i].equals(pkg))return names[i];return "Неизвестный источник";}
 static String date(JSONObject row){return LocalWatchPolicy.day(row.optString("certainty"),row.optLong("reported_at"),System.currentTimeMillis(),java.time.ZoneId.systemDefault());}
 static String state(String value){switch(value){case "available":return "доступен";case "available_undated":return "история без дат";case "available_unverified_dates":return "локальные записи, дата не подтверждена";case "empty":return "источник пуст";case "no_local_source":return "локальный источник пока не найден";default:return "чтение недоступно";}}
 static String evidence(JSONObject r){String certainty=r.optString("certainty");if(certainty.equals("reported_playback")){long p=r.optLong("position"),d=r.optLong("duration");return "Просмотр по данным приложения · "+date(r)+" · "+(p/60000)+" мин"+(d>0?" из "+(d/60000):"")+" · завершение не подтверждено";}if(certainty.equals("continue_card"))return "Карточка «Продолжить» · факт и дата просмотра не подтверждены";if(certainty.equals("undated_history"))return "История приложения · дата неизвестна";return "Локальная запись приложения · факт и дата просмотра не подтверждены";}
 static final class Job {
  volatile boolean cancelled;volatile LocalSocket socket;
  void cancel(){cancelled=true;LocalSocket s=socket;if(s!=null)try{s.close();}catch(Exception ignored){}}
 }
 static Job refresh(Context context,Runnable done){Context c=context.getApplicationContext();Job job=new Job();new Thread(()->{
  try{if(!enabled(c)||job.cancelled)return;
   synchronized(LOCK){if(job.cancelled)return;try(LocalSocket socket=new LocalSocket()){job.socket=socket;socket.connect(new LocalSocketAddress("proskurnin.history.v1"));if(socket.getPeerCredentials().getUid()!=0)throw new SecurityException();socket.setSoTimeout(6000);socket.getOutputStream().write("SNAPSHOT\n".getBytes("US-ASCII"));DataInputStream in=new DataInputStream(socket.getInputStream());int length=in.readInt();if(length<2||length>524288)throw new IOException();byte[] bytes=new byte[length];in.readFully(bytes);JSONObject snapshot=new JSONObject(new String(bytes,"UTF-8"));if(snapshot.optInt("schema")!=1)throw new IOException();
    JSONArray fresh=snapshot.getJSONArray("items");if(fresh.length()>1600)throw new IOException();JSONObject old=saved(c);JSONArray rows=old.optJSONArray("items");LinkedHashMap<String,JSONObject> merged=new LinkedHashMap<>();if(rows!=null)for(int i=0;i<rows.length();i++)add(merged,rows.getJSONObject(i));for(int i=0;i<fresh.length();i++){JSONObject row=fresh.getJSONObject(i);row.put("observed_at",snapshot.optLong("observed_at"));add(merged,row);}while(merged.size()>2000)merged.remove(merged.keySet().iterator().next());JSONArray all=new JSONArray();for(JSONObject row:merged.values())all.put(row);snapshot.put("items",all);
    synchronized(WRITE_LOCK){if(!job.cancelled&&enabled(c))c.getSharedPreferences("preview",0).edit().putString(KEY,snapshot.toString()).putString("local_watch_error","").apply();}
   }}
  }catch(Exception e){if(!job.cancelled)c.getSharedPreferences("preview",0).edit().putString("local_watch_error","Помощник чтения недоступен. Показаны ранее сохранённые записи.").apply();}
  finally{job.socket=null;if(done!=null&&!job.cancelled)new Handler(Looper.getMainLooper()).post(()->{if(!job.cancelled)done.run();});}
 },"local-watch-reader").start();return job;}
 static void add(LinkedHashMap<String,JSONObject> rows,JSONObject row){String pkg=row.optString("package"),key=row.optString("key");if(name(pkg).equals("Неизвестный источник")||key.isEmpty()||key.length()>240||row.optString("title").length()>240)return;String day=date(row),prefix=pkg+"|"+key+"|";if(!day.isEmpty())rows.remove(prefix);else for(String existing:rows.keySet())if(existing.startsWith(prefix)&&existing.length()>prefix.length())return;String id=LocalWatchPolicy.mergeKey(pkg,key,day);rows.remove(id);rows.put(id,row);}
}
