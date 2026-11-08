package local.proskurnin.preview;
import java.net.*;import java.io.*;import java.util.*;import org.json.*;
final class WeatherClient {
 interface Alive { boolean get(); }
 interface Source { Result fetch() throws Exception; }
 static final class Result {final String text,source;final int kind;final boolean night;final double wind;
 Result(double temp,String description,String source)throws IOException{this(temp,description,source,WeatherState.legacy(description),false,Double.NaN);}
 Result(double temp,String description,String source,int kind,boolean night,double wind)throws IOException{if(Double.isNaN(temp)||Double.isInfinite(temp)||temp < -90||temp>65)throw new IOException("Invalid temperature");this.source=source;this.text="Москва · "+Math.round(temp)+"°\n"+description+"\n"+source;this.kind=kind;this.night=night;this.wind=Double.isFinite(wind)&&wind>=0&&wind<=150?wind:Double.NaN;}}

 static Result first(List<Source> sources,Alive alive)throws Exception{for(Source s:sources){if(!alive.get())throw new InterruptedException();try{return s.fetch();}catch(InterruptedException e){throw e;}catch(Exception e){android.util.Log.w("ProskurninWeather","Provider unavailable: "+e.getClass().getSimpleName());}}throw new IOException("All providers unavailable");}
 static Result fetch(File configFile,boolean serverEnabled,Alive alive)throws Exception{
  ArrayList<Source> sources=new ArrayList<>();
  if(!serverEnabled){sources.add(()->openMeteo());sources.add(()->wttr());return first(sources,alive);}
  if(configFile.length()>16384)throw new IOException("Routing file too large");
  ByteArrayOutputStream out=new ByteArrayOutputStream();try(InputStream in=new FileInputStream(configFile)){byte[] b=new byte[1024];int n;while((n=in.read(b))!=-1){if(out.size()+n>16384)throw new IOException("Routing file too large");out.write(b,0,n);}}
  final JSONObject config=new JSONObject(out.toString("UTF-8"));
  JSONArray providers=config.getJSONArray("providers");
  if(providers.length()<1||providers.length()>2)throw new IOException("Invalid providers");
  for(int i=0;i<providers.length();i++){
   final String provider=providers.getString(i);if(!provider.equals("open_meteo")&&!provider.equals("wttr"))throw new IOException("Unknown provider");
   final String route=config.getJSONObject("routes").getString(provider);
   sources.add(()->routed(provider,route,config));
   final String fallback=config.getJSONObject("fallback_routes").optString(provider,"");
   if(!fallback.isEmpty()&&!fallback.equals(route))sources.add(()->routed(provider,fallback,config));
  }
  return first(sources,alive);
 }
 static Result routed(String provider,String route,JSONObject config)throws Exception{
  Result result;
  if(route.equals("direct"))result=provider.equals("open_meteo")?openMeteo():wttr();
  else if(route.equals("ru")){
   String base=config.getString("base_url");
   if(!base.equals("https://ru01.firstvds.proskurn.in/tv-api/v1/weather/"))throw new IOException("Untrusted API endpoint");
   String token=config.getString("token");if(token.length()<32)throw new IOException("Missing device credential");
   JSONObject payload=json(base+provider,token);
   result=provider.equals("open_meteo")?parseOpenMeteo(payload):parseWttr(payload);
  }else throw new IOException("Unsupported API route");
  android.util.Log.i("ProskurninWeather","API "+provider+" route="+route+" OK");return result;
 }
 static JSONObject json(String url)throws Exception{return json(url,null);}
 static JSONObject json(String url,String bearer)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();try{c.setConnectTimeout(4500);c.setReadTimeout(bearer==null?4500:8000);c.setInstanceFollowRedirects(false);c.setRequestProperty("User-Agent","ProskurninTV/1.14");if(bearer!=null)c.setRequestProperty("Authorization","Bearer "+bearer);if(c.getResponseCode()!=200)throw new IOException("HTTP "+c.getResponseCode());ByteArrayOutputStream b=new ByteArrayOutputStream();long deadline=System.nanoTime()+8000000000L;try(InputStream in=c.getInputStream()){byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){if(b.size()+n>262144||System.nanoTime()>deadline)throw new IOException("Response limit");b.write(buf,0,n);}}return new JSONObject(b.toString("UTF-8"));}finally{c.disconnect();}}
 static void fresh(long seconds)throws IOException{long age=System.currentTimeMillis()-seconds*1000;if(age< -3600000||age>21600000)throw new IOException("Stale weather");}
 static String cacheSuffix(JSONObject root){JSONObject meta=root.optJSONObject("_proskurnin");return meta!=null&&meta.optBoolean("stale",false)?" · сохранённые данные":"";}
 static Result openMeteo()throws Exception{return parseOpenMeteo(json("https://api.open-meteo.com/v1/forecast?latitude=55.75&longitude=37.62&current=temperature_2m,weather_code,is_day,wind_speed_10m&wind_speed_unit=ms&timeformat=unixtime"));}
 static Result parseOpenMeteo(JSONObject root)throws Exception{JSONObject j=root.getJSONObject("current");fresh(j.getLong("time"));int c=j.getInt("weather_code");return new Result(j.getDouble("temperature_2m"),WeatherState.description(c)+cacheSuffix(root),"Open-Meteo",WeatherState.wmo(c),j.optInt("is_day",1)==0,j.optDouble("wind_speed_10m",Double.NaN));}
 static Result wttr()throws Exception{return parseWttr(json("https://wttr.in/55.75,37.62?format=j1&lang=ru"));}
 static Result parseWttr(JSONObject root)throws Exception{JSONObject j=root.getJSONArray("current_condition").getJSONObject(0);JSONArray d=j.optJSONArray("lang_ru");if(d==null)d=j.getJSONArray("weatherDesc");String description=d.getJSONObject(0).getString("value").trim();int code=WeatherState.wttr(j.optInt("weatherCode",-1));return new Result(j.getDouble("temp_C"),description+cacheSuffix(root),"wttr.in",code==WeatherState.UNKNOWN?WeatherState.legacy(description):code,false,j.optDouble("windspeedKmph",Double.NaN)/3.6);}
}
