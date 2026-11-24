package local.proskurnin.power;
import android.net.*;import android.database.*;import android.database.sqlite.*;import android.os.*;import android.util.Xml;import org.xmlpull.v1.XmlPullParser;import org.json.*;import java.io.*;import java.util.*;
/** Separate read-only socket. Fixed sources only; no network, caller paths, SQL or credentials. */
public final class HistoryBridge {
 static final String[] PACKAGES={"ru.kinopoisk.tv","ru.ivi.client","tv.okko.androidtv","gpm.tnt_premier","ru.mts.mtstv","ru.rt.video.app.tv","mobi.zona","com.lazycatsoftware.lmd"};
 // Initialize Android 9 SQLite process defaults before ActivityThread.systemMain.
 // A standalone app_process is not a registered app and cannot query Settings via that context.
 static void prepare(){try(SQLiteDatabase memory=SQLiteDatabase.create(null)){}catch(Exception e){android.util.Log.w("ProskurninHistory","SQLite init unavailable");}}
 static final int LIMIT=200;static long cachedAt;static byte[] cache;
 static SQLiteDatabase db(String path){File f=new File(path);try{if(!f.getCanonicalPath().equals(path))throw new SecurityException();}catch(IOException e){throw new SecurityException();}return SQLiteDatabase.openDatabase(path,null,SQLiteDatabase.OPEN_READONLY|SQLiteDatabase.NO_LOCALIZED_COLLATORS);}
 static String text(Cursor c,String name){int i=c.getColumnIndex(name);return i<0||c.isNull(i)?"":c.getString(i);}
 static long number(Cursor c,String name){try{return Long.parseLong(text(c,name));}catch(Exception e){return 0;}}
 static String shortText(String s){return s==null?"":s.substring(0,Math.min(240,s.length()));}
 static JSONObject item(String pkg,String key,String title,String source,long pos,long duration,long reported,String certainty)throws Exception{
  long now=System.currentTimeMillis();if(reported<946684800000L||reported>now+300000)reported=0;
  return new JSONObject().put("package",pkg).put("key",shortText(key)).put("title",shortText(title)).put("source",source).put("position",Math.max(0,pos)).put("duration",Math.max(0,duration)).put("reported_at",reported).put("certainty",certainty);
 }
 static JSONObject collect()throws Exception{
  JSONArray items=new JSONArray(),states=new JSONArray();HashMap<String,String> status=new HashMap<>();for(String p:PACKAGES)status.put(p,"no_local_source");
  try(SQLiteDatabase database=db("/data/data/com.android.providers.tv/databases/tv.db")){
   for(String pkg:PACKAGES){try(Cursor c=database.query("watch_next_programs",new String[]{"_id","title","watch_next_type","last_engagement_time_utc_millis","last_playback_position_millis","duration_millis"},"package_name=?",new String[]{pkg},null,null,"last_engagement_time_utc_millis DESC","200")){
    int count=0;while(c.moveToNext()){if(number(c,"watch_next_type")!=0)continue;String title=text(c,"title");if(title.isEmpty())continue;long pos=number(c,"last_playback_position_millis");items.put(item(pkg,"watchnext:"+text(c,"_id"),title,"watch_next",pos,number(c,"duration_millis"),pos>0?number(c,"last_engagement_time_utc_millis"):0,pos>0?"reported_playback":"continue_card"));count++;}if(count>0)status.put(pkg,"available");
   }}
  }catch(Exception e){android.util.Log.w("ProskurninHistory","watch_next "+e.getClass().getSimpleName());for(String p:PACKAGES)status.put(p,"watch_next_unavailable");}
  try{int before=items.length();zona(items);status.put("mobi.zona",items.length()>before?"available_undated":"empty");}catch(Exception e){android.util.Log.w("ProskurninHistory","zona "+e.getClass().getSimpleName());status.put("mobi.zona","format_unavailable");}
  try{int before=items.length();lazy(items);status.put("com.lazycatsoftware.lmd",items.length()>before?"available_unverified_dates":"empty");}catch(Exception e){android.util.Log.w("ProskurninHistory","lazy "+e.getClass().getSimpleName());status.put("com.lazycatsoftware.lmd","format_unavailable");}
  for(String p:PACKAGES){int count=0;for(int i=0;i<items.length();i++)if(p.equals(items.getJSONObject(i).optString("package")))count++;states.put(new JSONObject().put("package",p).put("status",status.get(p)).put("count",count));}
  return new JSONObject().put("schema",1).put("helper","1.0").put("observed_at",System.currentTimeMillis()).put("sources",states).put("items",items);
 }
 static Map<String,String> preferences(String path)throws Exception{
  File f=new File(path);if(!f.getCanonicalPath().equals(path)||f.length()>262144)throw new IOException();Map<String,String> values=new HashMap<>();
  try(InputStream in=new FileInputStream(f)){XmlPullParser p=Xml.newPullParser();p.setInput(in,"UTF-8");for(int event=p.next();event!=XmlPullParser.END_DOCUMENT;event=p.next())if(event==XmlPullParser.START_TAG){String tag=p.getName(),name=p.getAttributeValue(null,"name");if(name!=null){if("string".equals(tag))values.put(name,p.nextText());else if("long".equals(tag)||"int".equals(tag))values.put(name,p.getAttributeValue(null,"value"));}}}return values;
 }
 static long integer(String s){try{return Long.parseLong(s);}catch(Exception e){return 0;}}
 static void zona(JSONArray items)throws Exception{
  String pkg="mobi.zona";Map<String,String> h=preferences("/data/data/mobi.zona/shared_prefs/history.xml");JSONArray ids=new JSONArray(h.getOrDefault("entity_id_history","[]"));
  // Position keys/units are not yet verified; do not join or infer dates from file mtime.
  try(SQLiteDatabase database=db("/data/data/mobi.zona/databases/zonadb")){
   for(int i=0;i<Math.min(LIMIT,ids.length());i++){String id=ids.optString(i);if(id.isEmpty()||id.length()>120)continue;String title="Запись Zona";
    try(Cursor c=database.query("movie_cache",new String[]{"json"},"id=?",new String[]{id},null,null,null,"1")){if(c.moveToFirst()){String raw=c.getString(0);if(raw!=null&&raw.length()<131072){JSONObject m=new JSONObject(raw);for(String key:new String[]{"name","name_rus","title","rusName"})if(!m.optString(key).isEmpty()){title=m.optString(key);break;}}}}
    items.put(item(pkg,"zona:"+id,title,"zona_history",0,0,0,"undated_history"));
   }
  }
 }
 static void lazy(JSONArray items)throws Exception{
  try(SQLiteDatabase database=db("/data/data/com.lazycatsoftware.lmd/databases/data.db");Cursor c=database.query("articles",new String[]{"_id","profile_id","title"},"typearticle=?",new String[]{"V"},null,null,"time_added DESC","200")){
   while(c.moveToNext()){String title=text(c,"title");if(title.isEmpty())continue;items.put(item("com.lazycatsoftware.lmd","lazy:"+text(c,"profile_id")+":"+text(c,"_id"),title,"lazy_recent",0,0,0,"local_record_unverified"));}
  }
 }
 public static void start(){new Thread(()->{try{
  if(!"SaluteTV".equals(Build.MODEL)||!"m7332_eu".equals(Build.DEVICE))return;
  LocalServerSocket server=new LocalServerSocket("proskurnin.history.v1");android.util.Log.i("ProskurninHistory","Ready 1.0");
  while(true){try(LocalSocket client=server.accept()){client.setSoTimeout(1500);if(!PowerBridge.allowed(client.getPeerCredentials().getUid()))continue;
   InputStream in=client.getInputStream();byte[] expected="SNAPSHOT\n".getBytes("US-ASCII");boolean valid=true;for(byte b:expected)if(in.read()!=(b&255)){valid=false;break;}if(!valid)continue;
   if(cache==null||SystemClock.elapsedRealtime()-cachedAt>30000){byte[] next=collect().toString().getBytes("UTF-8");if(next.length>524288)throw new IOException();cache=next;cachedAt=SystemClock.elapsedRealtime();}
   DataOutputStream out=new DataOutputStream(client.getOutputStream());out.writeInt(cache.length);out.write(cache);out.flush();
  }catch(Exception e){android.util.Log.w("ProskurninHistory","Read unavailable");}}
 }catch(Exception e){android.util.Log.w("ProskurninHistory","Adapter unavailable");}},"local-history").start();}
}
