package local.proskurnin.preview;
import android.content.Context;import android.graphics.*;import java.io.*;import java.net.*;import java.util.*;import org.json.*;
final class MovieClient {
 interface Alive{boolean get();}
 static String encode(String s)throws Exception{return URLEncoder.encode(s,"UTF-8");}
 static JSONObject tmdb(Context context,String path,String query)throws Exception{
  if(!path.matches("/(search/movie|discover/movie|movie/[0-9]+)"))throw new IOException("API");
  try{return ApiClient.request(context,"tmdb"+path+"?language=ru-RU"+(query.isEmpty()?"":"&"+query),null);}
  catch(Exception e){throw new IOException("TMDB");}
 }
 static String ids(JSONArray a)throws Exception{StringBuilder b=new StringBuilder();for(int i=0;i<a.length();i++){if(i>0)b.append(',');b.append(a.getInt(i));}return b.toString();}
 static boolean fits(JSONObject detail,JSONObject filters)throws Exception{
  if(detail.optBoolean("adult",false))return false;
  int runtime=detail.optInt("runtime",0);if(!filters.isNull("max_runtime_minutes")&&(runtime<=0||runtime>filters.getInt("max_runtime_minutes")))return false;
  HashSet<Integer> genres=new HashSet<>();JSONArray g=detail.getJSONArray("genres");for(int i=0;i<g.length();i++)genres.add(g.getJSONObject(i).getInt("id"));
  JSONArray excluded=filters.getJSONArray("excluded_genre_ids"),required=filters.getJSONArray("required_genre_ids"),languages=filters.getJSONArray("original_languages");
  for(int i=0;i<excluded.length();i++)if(genres.contains(excluded.getInt(i)))return false;
  for(int i=0;i<required.length();i++)if(!genres.contains(required.getInt(i)))return false;
  if(languages.length()>0){boolean found=false;for(int i=0;i<languages.length();i++)if(languages.getString(i).equals(detail.optString("original_language")))found=true;if(!found)return false;}
  return true;
 }
 static JSONObject compact(JSONObject detail,String reason)throws Exception{
  return new JSONObject().put("id",detail.getInt("id")).put("title",detail.getString("title")).put("year",detail.optString("release_date","").split("-")[0]).put("runtime",detail.optInt("runtime",0)).put("rating",detail.optDouble("vote_average",0)).put("poster_path",detail.optString("poster_path","")).put("reason",reason);
 }
 static JSONArray enrich(Context context,JSONObject proposal,String query,Alive alive)throws Exception{
  JSONArray candidates=new JSONArray();HashMap<Integer,JSONObject> details=new HashMap<>();HashSet<Integer> seen=new HashSet<>();long deadline=android.os.SystemClock.elapsedRealtime()+60000;
  JSONArray picks=proposal.getJSONArray("picks");
  for(int i=0;i<Math.min(picks.length(),6)&&alive.get()&&android.os.SystemClock.elapsedRealtime()<deadline;i++){
   JSONObject pick=picks.getJSONObject(i);String title=pick.getString("title"),original=pick.optString("original_title",title);
   try{JSONArray matches=tmdb(context,"/search/movie","include_adult=false&query="+encode(original.isEmpty()?title:original)+"&year="+pick.getInt("year")).getJSONArray("results");
    for(int j=0;j<Math.min(5,matches.length());j++){
     JSONObject match=matches.getJSONObject(j);int id=match.getInt("id");
     if(!MovieIdentity.matches(title,original,match.optString("title"),match.optString("original_title"))||!seen.add(id))continue;
     JSONObject detail=tmdb(context,"/movie/"+id,"append_to_response=keywords");
     if(!detail.optString("release_date").startsWith(String.valueOf(pick.getInt("year")))||!fits(detail,proposal))continue;
     if(!MovieIdentity.matches(title,original,detail.optString("title"),detail.optString("original_title")))continue;
     JSONArray keywords=new JSONArray(),genres=new JSONArray();JSONObject kw=detail.optJSONObject("keywords");JSONArray list=kw==null?null:kw.optJSONArray("keywords");
     if(list!=null)for(int k=0;k<Math.min(40,list.length());k++)keywords.put(shortText(list.getJSONObject(k).optString("name"),100));
     list=detail.getJSONArray("genres");for(int k=0;k<Math.min(40,list.length());k++)genres.put(shortText(list.getJSONObject(k).optString("name"),100));
     candidates.put(new JSONObject().put("id",id).put("title",shortText(detail.optString("title"),160)).put("original_title",shortText(detail.optString("original_title"),160)).put("year",detail.optString("release_date","").split("-")[0]).put("runtime",detail.optInt("runtime",0)).put("original_language",detail.optString("original_language","")).put("overview",shortText(detail.optString("overview"),2500)).put("keywords",keywords).put("genres",genres));details.put(id,detail);break;
    }
   }catch(IOException e){if(candidates.length()==0&&android.os.SystemClock.elapsedRealtime()+5000>=deadline)throw e;}
  }
  if(!alive.get())throw new InterruptedException();JSONArray result=new JSONArray();if(candidates.length()==0)return result;
  // No genre-only discover fallback. A separate pass checks the original query against TMDB evidence.
  JSONObject verified=ApiClient.request(context,"ai/movies",new JSONObject().put("query",query).put("candidates",candidates));
  if(verified.optInt("verification_version")!=2)throw new IOException("VERIFY");
  JSONArray accepted=verified.getJSONArray("matches");seen.clear();
  for(int i=0;i<Math.min(3,accepted.length());i++){JSONObject item=accepted.getJSONObject(i);int id=item.getInt("id");if(details.containsKey(id)&&seen.add(id))result.put(compact(details.get(id),item.getString("reason")));}
  if(!alive.get())throw new InterruptedException();return result;
 }
 static String shortText(String s,int limit){return s.length()<=limit?s:s.substring(0,limit);}
 static Bitmap poster(Context context,String path)throws Exception{
  if(!path.matches("/[A-Za-z0-9_-]+\\.jpg"))return null;
  HttpURLConnection c=(HttpURLConnection)new URL("https://ru01.firstvds.proskurn.in/tv-api/v1/tmdb/poster"+path).openConnection();
  try{c.setRequestProperty("Authorization","Bearer "+ApiClient.privateJson(context,"api-client.json").getString("token"));c.setConnectTimeout(4000);c.setReadTimeout(16000);c.setInstanceFollowRedirects(false);if(c.getResponseCode()!=200)return null;
   ByteArrayOutputStream out=new ByteArrayOutputStream();try(InputStream in=c.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>1048576)return null;out.write(b,0,n);}}
   BitmapFactory.Options options=new BitmapFactory.Options();options.inSampleSize=2;options.inPreferredConfig=Bitmap.Config.RGB_565;byte[] bytes=out.toByteArray();return BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);
  }finally{c.disconnect();}
 }
}
