package local.proskurnin.preview;
import android.content.Context;import java.io.*;import java.net.*;import org.json.*;
final class ApiClient {
 static JSONObject privateJson(Context context,String name)throws Exception{
  if((PreviewProfile.enabled(context)||UniversalProfile.enabled(context))&&"api-client.json".equals(name))return privateJson(context,PreviewApiConfigProvider.FILE).getJSONObject("api");
  File file=new File(context.getFilesDir(),name);if(file.length()>16384)throw new IOException("CONFIG");
  ByteArrayOutputStream b=new ByteArrayOutputStream();try(InputStream in=PreviewApiConfigProvider.FILE.equals(name)?new android.util.AtomicFile(file).openRead():new FileInputStream(file)){byte[] buf=new byte[1024];int n;while((n=in.read(buf))!=-1){if(b.size()+n>16384)throw new IOException("CONFIG");b.write(buf,0,n);}}
  return new JSONObject(b.toString("UTF-8"));
 }
 static JSONObject request(Context context,String endpoint,JSONObject body)throws Exception{return request(context,endpoint,body,null);}
 static JSONObject request(Context context,String endpoint,JSONObject body,android.os.CancellationSignal cancel)throws Exception{
  if(!endpoint.startsWith("youtube/channel?interval=")&&!endpoint.equals("ai/movies")&&!endpoint.equals("ai/chat")&&!endpoint.equals("ai/speech")&&!endpoint.startsWith("tmdb/")&&!endpoint.equals("dream/catalog"))throw new IOException("API");
  JSONObject config=privateJson(context,"api-client.json");String base=config.getString("base_url");
  ApiEndpoint.validate(base);
  HttpURLConnection c=(HttpURLConnection)new URL(base+endpoint).openConnection();
  try{if(cancel!=null){cancel.throwIfCanceled();cancel.setOnCancelListener(()->c.disconnect());}c.setConnectTimeout(5000);c.setReadTimeout(body==null?18000:45000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Authorization","Bearer "+config.getString("token"));
   if(body!=null){c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");try(OutputStream out=c.getOutputStream()){out.write(body.toString().getBytes("UTF-8"));}}
   int status=c.getResponseCode();InputStream source=status==200?c.getInputStream():c.getErrorStream();ByteArrayOutputStream b=new ByteArrayOutputStream();
   if(source!=null)try(InputStream in=source){byte[] bytes=new byte[4096];int n;while((n=in.read(bytes))!=-1){if(b.size()+n>(endpoint.equals("ai/speech")?1500000:262144))throw new IOException("LIMIT");b.write(bytes,0,n);}}
   JSONObject result=b.size()>0?new JSONObject(b.toString("UTF-8")):new JSONObject();
   if(status!=200)throw new IOException(status==401?"AUTH":status==429?"RATE":safeError(result.optString("error","NETWORK")));
   return result;
  }finally{if(cancel!=null)cancel.setOnCancelListener(null);c.disconnect();}
 }
 static String safeError(String value){for(String known:new String[]{"daily_limit","rate_limit","quota_or_rate_limit","provider_auth","provider_unavailable","us_worker_unavailable","tmdb_unavailable","speech_unavailable","speech_expired","web_search_unavailable"})if(known.equals(value))return known;return "NETWORK";}
 static String message(Exception e){String m=e.getMessage();if("CONFIG".equals(m)||e instanceof FileNotFoundException)return "Подключение API ещё не настроено для этого телевизора";if("web_search_unavailable".equals(m))return "Веб-поиск недоступен. Повторите запрос позже";if("TMDB".equals(m)||"tmdb_unavailable".equals(m))return "Не удалось загрузить данные фильмов TMDB. Повторите позже";if("AUTH".equals(m))return "Нет доступа к API — требуется настройка подключения";if("daily_limit".equals(m))return "Достигнут дневной лимит AI-запросов";if("RATE".equals(m)||"rate_limit".equals(m))return "Подождите немного перед следующим запросом";if("quota_or_rate_limit".equals(m)||"provider_auth".equals(m))return "Проверьте ключ и лимиты API";return "Сервис недоступен. Проверьте сеть и повторите позже";}
}
