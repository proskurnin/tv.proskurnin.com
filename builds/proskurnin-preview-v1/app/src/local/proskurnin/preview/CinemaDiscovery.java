package local.proskurnin.preview;
import android.content.*;import android.net.Uri;import android.os.*;import java.util.*;import java.util.concurrent.*;import org.json.*;
/** Independent evidence for all cinemas. Catalog availability never substitutes for a card URL. */
final class CinemaDiscovery {
 interface Listener {void changed(int index,Row row);}
 static final class Row {final int index;final String pkg;volatile CinemaSearch.Result nativeResult;volatile String web="pending",url="",offer="",catalog="pending";Row(int i,String p){index=i;pkg=p;if(CinemaCard.provider(i).isEmpty())web="unsupported";}}
 static final Semaphore webSlot=new Semaphore(1);static long nextWeb;
 static final class Job {
  final Context context;final JSONObject movie;final Listener listener;final Handler main=new Handler(Looper.getMainLooper());final Row[] rows=new Row[8];final List<CancellationSignal> signals=new CopyOnWriteArrayList<>();final List<Thread> threads=new CopyOnWriteArrayList<>();volatile boolean cancelled;
  Job(Context c,JSONObject m,String[] installed,Listener l){context=c.getApplicationContext();movie=m;listener=l;for(int i=0;i<8;i++)rows[i]=new Row(i,installed[i]);}
  CancellationSignal signal(){CancellationSignal s=new CancellationSignal();signals.add(s);if(cancelled)s.cancel();return s;}
  void cancel(){cancelled=true;for(CancellationSignal s:signals)s.cancel();for(Thread t:threads)t.interrupt();}
  void emit(Row r){main.post(()->{if(!cancelled)listener.changed(r.index,r);});}
  void thread(Runnable r){Thread t=new Thread(r,"cinema-discovery");threads.add(t);t.start();}
  void start(){
   thread(()->{CancellationSignal s=signal();try{JSONArray offers=MovieAvailability.offers(ApiClient.request(context,"tmdb/movie/"+movie.getInt("id")+"/watch/providers",null,s));for(Row row:rows){row.catalog="checked";for(int j=0;j<offers.length();j++){JSONObject offer=offers.getJSONObject(j);if(MovieAvailability.cinema(offer.optString("name"))==row.index)row.offer=offer.optString("offer");}emit(row);}}catch(Exception e){for(Row row:rows){row.catalog="error";emit(row);}}finally{signals.remove(s);}});
   for(Row row:rows){emit(row);thread(()->{CancellationSignal s=signal();try{if(row.pkg!=null)row.nativeResult=CinemaSearch.inspect(context,row.pkg,movie,s);else{row.nativeResult=new CinemaSearch.Result();row.nativeResult.status="not_installed";}emit(row);}finally{signals.remove(s);}});}
   // One serial web queue, paced across all sessions, with bounded on-device public-metadata cache.
   thread(()->{for(int i:new int[]{1,0,4,2,3,6,7,5}){if(cancelled)return;Row row=rows[i];String provider=CinemaCard.provider(i);if(provider.isEmpty()){row.web="unsupported";emit(row);continue;}if(row.nativeResult!=null&&!row.nativeResult.matches.isEmpty()){row.web="not_needed";emit(row);continue;}lookup(row,provider);}});
  }
  void lookup(Row row,String provider){CancellationSignal s=signal();boolean acquired=false;try{
   String key="cinema_card_v1_"+movie.getInt("id")+"_"+provider;android.content.SharedPreferences prefs=context.getSharedPreferences("cinema_cards",0);JSONObject answer=null;
   try{JSONObject cached=new JSONObject(prefs.getString(key,"{}"));long age=System.currentTimeMillis()-cached.optLong("saved_at");long ttl=cached.optBoolean("found")?86400000:600000;if(age>=0&&age<ttl)answer=cached;}catch(Exception ignored){}
   if(answer==null){while(!webSlot.tryAcquire(200,TimeUnit.MILLISECONDS))s.throwIfCanceled();acquired=true;while(SystemClock.elapsedRealtime()<nextWeb){s.throwIfCanceled();Thread.sleep(200);}s.throwIfCanceled();nextWeb=SystemClock.elapsedRealtime()+12500;row.web="searching";emit(row);
    answer=ApiClient.request(context,"ai/cinema",new JSONObject().put("id",movie.getInt("id")).put("title",movie.getString("title")).put("original_title",movie.optString("original_title").trim().isEmpty()?movie.getString("title"):movie.optString("original_title")).put("year",movie.optString("year")).put("provider",provider),s);answer.put("saved_at",System.currentTimeMillis());
    synchronized(CinemaDiscovery.class){android.content.SharedPreferences.Editor edit=prefs.edit();Map<String,?> all=prefs.getAll();if(all.size()>=100)for(String old:all.keySet()){edit.remove(old);break;}edit.putString(key,answer.toString()).apply();}
   }
   String url=answer.optString("url");if(answer.optBoolean("found")&&CinemaCard.allowed(provider,url)){row.url=url;row.web="found";}else row.web="no_matches";
  }catch(Exception e){row.web=cancelled?"cancelled":"error";}finally{if(acquired)webSlot.release();signals.remove(s);emit(row);}}
 }
 static String nativeState(Row r){return r.nativeResult==null?"pending":r.nativeResult.status;}
 static String status(Row r){return CinemaEvidence.status(nativeState(r),r.web,(r.nativeResult!=null&&!r.nativeResult.matches.isEmpty())||!r.url.isEmpty());}
 static String access(Row r){return CinemaEvidence.access(r.offer);}
 static Job start(Context c,JSONObject m,String[] installed,Listener l){Job j=new Job(c,m,installed,l);j.start();return j;}
}
