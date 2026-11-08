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
 static JSONArray enrich(Context context,JSONObject proposal,Alive alive)throws Exception{
  JSONArray result=new JSONArray();HashSet<Integer> seen=new HashSet<>();long deadline=System.currentTimeMillis()+45000;
  JSONArray picks=proposal.getJSONArray("picks");
  // Verify model suggestions against TMDB; reject mismatched year, genre or duration.
  for(int i=0;i<Math.min(picks.length(),6)&&result.length()<3&&alive.get()&&System.currentTimeMillis()<deadline;i++){
   JSONObject pick=picks.getJSONObject(i);
   try{JSONArray matches=tmdb(context,"/search/movie","include_adult=false&query="+encode(pick.getString("title"))+"&year="+pick.getInt("year")).getJSONArray("results");
    if(matches.length()==0)continue;JSONObject match=matches.getJSONObject(0);int id=match.getInt("id");if(!seen.add(id))continue;
    JSONObject detail=tmdb(context,"/movie/"+id,"");if(!detail.optString("release_date").startsWith(String.valueOf(pick.getInt("year"))))continue;
    if(fits(detail,proposal))result.put(compact(detail,pick.getString("reason")));
   }catch(IOException e){if(result.length()==0&&System.currentTimeMillis()+5000>=deadline)throw e;}
  }
  // Model suggestions can be wrong. Fill using verified discover filters, never fabricated cards.
  if(result.length()<3&&alive.get()&&System.currentTimeMillis()<deadline){
   String q="include_adult=false&sort_by=popularity.desc&vote_count.gte=100&with_genres="+ids(proposal.getJSONArray("required_genre_ids"))+"&without_genres="+ids(proposal.getJSONArray("excluded_genre_ids"));
   if(!proposal.isNull("max_runtime_minutes"))q+="&with_runtime.lte="+proposal.getInt("max_runtime_minutes");
   JSONArray languages=proposal.getJSONArray("original_languages");if(languages.length()==1)q+="&with_original_language="+encode(languages.getString(0));
   JSONArray matches=tmdb(context,"/discover/movie",q).getJSONArray("results");
   for(int i=0;i<Math.min(12,matches.length())&&result.length()<3&&alive.get()&&System.currentTimeMillis()<deadline;i++){
    int id=matches.getJSONObject(i).getInt("id");if(!seen.add(id))continue;
    JSONObject detail=tmdb(context,"/movie/"+id,"");if(fits(detail,proposal)){
     JSONArray genres=detail.getJSONArray("genres");ArrayList<String> labels=new ArrayList<>();for(int j=0;j<Math.min(2,genres.length());j++)labels.add(genres.getJSONObject(j).getString("name"));
     result.put(compact(detail,android.text.TextUtils.join(", ",labels)+" · "+detail.optInt("runtime",0)+" мин. Соответствует проверенным ограничениям запроса."));
    }
   }
  }
  if(!alive.get())throw new InterruptedException();return result;
 }
 static Bitmap poster(Context context,String path)throws Exception{
  if(!path.matches("/[A-Za-z0-9_-]+\\.jpg"))return null;
  HttpURLConnection c=(HttpURLConnection)new URL("https://ru01.firstvds.proskurn.in/tv-api/v1/tmdb/poster"+path).openConnection();
  try{c.setRequestProperty("Authorization","Bearer "+ApiClient.privateJson(context,"api-client.json").getString("token"));c.setConnectTimeout(4000);c.setReadTimeout(16000);c.setInstanceFollowRedirects(false);if(c.getResponseCode()!=200)return null;
   ByteArrayOutputStream out=new ByteArrayOutputStream();try(InputStream in=c.getInputStream()){byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1){if(out.size()+n>1048576)return null;out.write(b,0,n);}}
   BitmapFactory.Options options=new BitmapFactory.Options();options.inSampleSize=2;options.inPreferredConfig=Bitmap.Config.RGB_565;byte[] bytes=out.toByteArray();return BitmapFactory.decodeByteArray(bytes,0,bytes.length,options);
  }finally{c.disconnect();}
 }
}
