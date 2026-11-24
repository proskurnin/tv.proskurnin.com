package local.proskurnin.preview;
import android.content.SharedPreferences;import org.json.*;import java.util.*;
/** Explicit local marks only. Launching a cinema never marks a film as watched. */
final class MovieHistory {
 final SharedPreferences prefs;JSONObject data;
 MovieHistory(SharedPreferences p){prefs=p;try{data=new JSONObject(p.getString("movie_watched_v1","{}"));}catch(Exception e){data=new JSONObject();}}
 synchronized boolean seen(int id){return data.has(String.valueOf(id));}
 synchronized boolean mark(JSONObject movie,boolean watched){try{String key=String.valueOf(movie.getInt("id"));if(watched){if(!data.has(key)&&data.length()>=1000)return false;if(!data.has(key))data.put(key,new JSONObject(movie.toString()));}else data.remove(key);prefs.edit().putString("movie_watched_v1",data.toString()).apply();return true;}catch(Exception e){return false;}}
 synchronized JSONArray entries(){ArrayList<JSONObject> list=new ArrayList<>();Iterator<String> keys=data.keys();while(keys.hasNext()){JSONObject entry=data.optJSONObject(keys.next());if(entry!=null)list.add(entry);}list.sort((a,b)->a.optString("title").compareToIgnoreCase(b.optString("title")));JSONArray out=new JSONArray();for(JSONObject v:list)out.put(v);return out;}
 synchronized boolean remember(JSONObject movie,String date,String service){try{
  java.time.LocalDate day=java.time.LocalDate.parse(date);if(day.isAfter(java.time.LocalDate.now())||day.getYear()<1900)return false;
  String key=String.valueOf(movie.getInt("id"));if(!data.has(key)&&data.length()>=1000)return false;
  JSONObject old=data.optJSONObject(key);JSONArray views=old==null?null:old.optJSONArray("views");if(views==null)views=new JSONArray();
  for(int i=0;i<views.length();i++){JSONObject v=views.optJSONObject(i);if(v!=null&&date.equals(v.optString("date"))&&service.equals(v.optString("service")))return true;}
  if(views.length()>=50)return false;
  views.put(new JSONObject().put("date",date).put("timezone",java.util.TimeZone.getDefault().getID()).put("service",service).put("source","manual"));
  JSONObject entry=new JSONObject(movie.toString());entry.put("views",views);data.put(key,entry);prefs.edit().putString("movie_watched_v1",data.toString()).apply();return true;
 }catch(Exception e){return false;}}
 synchronized JSONArray during(WatchPeriod period){JSONArray out=new JSONArray();Iterator<String> keys=data.keys();while(keys.hasNext()){JSONObject entry=data.optJSONObject(keys.next());if(entry==null)continue;JSONArray views=entry.optJSONArray("views");if(views==null)continue;for(int i=0;i<views.length();i++){JSONObject v=views.optJSONObject(i);if(v!=null&&period.contains(v.optString("date"))){try{JSONObject m=new JSONObject(entry.toString());m.put("reason","Записано вами: "+v.optString("date")+" · "+v.optString("service"));out.put(m);}catch(Exception ignored){}break;}}}return out;}
 synchronized JSONArray visible(JSONArray all,boolean hide){JSONArray out=new JSONArray();for(int i=0;i<all.length();i++){JSONObject m=all.optJSONObject(i);if(m!=null&&(!hide||!seen(m.optInt("id"))))out.put(m);}return out;}
 synchronized void clear(){data=new JSONObject();prefs.edit().remove("movie_watched_v1").apply();}
}
