package local.proskurnin.preview;
import android.content.SharedPreferences;import org.json.*;import java.util.*;
/** Explicit local marks only. Launching a cinema never marks a film as watched. */
final class MovieHistory {
 final SharedPreferences prefs;JSONObject data;
 MovieHistory(SharedPreferences p){prefs=p;try{data=new JSONObject(p.getString("movie_watched_v1","{}"));}catch(Exception e){data=new JSONObject();}}
 synchronized boolean seen(int id){return data.has(String.valueOf(id));}
 synchronized boolean mark(JSONObject movie,boolean watched){try{String key=String.valueOf(movie.getInt("id"));if(watched){if(!data.has(key)&&data.length()>=1000)return false;data.put(key,new JSONObject().put("id",movie.getInt("id")).put("title",movie.getString("title")).put("year",movie.optString("year")));}else data.remove(key);prefs.edit().putString("movie_watched_v1",data.toString()).apply();return true;}catch(Exception e){return false;}}
 synchronized JSONArray entries(){ArrayList<JSONObject> list=new ArrayList<>();Iterator<String> keys=data.keys();while(keys.hasNext()){JSONObject entry=data.optJSONObject(keys.next());if(entry!=null)list.add(entry);}list.sort((a,b)->a.optString("title").compareToIgnoreCase(b.optString("title")));JSONArray out=new JSONArray();for(JSONObject v:list)out.put(v);return out;}
 synchronized JSONArray visible(JSONArray all,boolean hide){JSONArray out=new JSONArray();for(int i=0;i<all.length();i++){JSONObject m=all.optJSONObject(i);if(m!=null&&(!hide||!seen(m.optInt("id"))))out.put(m);}return out;}
 synchronized void clear(){data=new JSONObject();prefs.edit().remove("movie_watched_v1").apply();}
}
