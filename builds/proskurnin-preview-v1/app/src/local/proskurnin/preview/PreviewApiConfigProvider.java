package local.proskurnin.preview;

import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import android.util.AtomicFile;
import java.io.*;
import org.json.*;

/** Explicit import into our own sandbox, only from an already authorized ADB shell. */
public final class PreviewApiConfigProvider extends ContentProvider {
 static final String FILE="preview-api-bundle.json";
 static final String BASE="https://ru01.firstvds.proskurn.in/tv-api/v1/";
 public boolean onCreate(){return true;}
 static String token(JSONObject value,String key)throws Exception{
  Object raw=value.get(key);if(!(raw instanceof String)||!((String)raw).matches("[A-Za-z0-9_-]{32,128}"))throw new IllegalArgumentException();return (String)raw;
 }
 @Override public synchronized Bundle call(String method,String arg,Bundle extras){
  if(Binder.getCallingUid()!=2000||!(PreviewProfile.enabled(getContext())||UniversalProfile.enabled(getContext())))throw new SecurityException("Authorized shell required");
  Bundle result=new Bundle();
  if("status".equals(method)){result.putBoolean("configured",new File(getContext().getFilesDir(),FILE).isFile());return result;}
  if(!"configure".equals(method))throw new IllegalArgumentException("Unsupported operation");
  try{
   configure(getContext(),extras==null?null:extras.getString("payload"));
   result.putBoolean("configured",true);return result;
  }catch(Exception ignored){throw new IllegalArgumentException("Invalid or unwritable device configuration");}
 }
 static synchronized void configure(Context context,String payload)throws Exception{
   if(payload==null||payload.length()>1024)throw new IllegalArgumentException();
   JSONObject value=new JSONObject(payload);if(value.length()!=(UniversalProfile.enabled(context)?4:3)||value.getInt("version")!=1)throw new IllegalArgumentException();
   String apiToken=token(value,"api_token"),weatherToken=token(value,"weather_token");
   if(apiToken.equals(weatherToken))throw new IllegalArgumentException();
   String base=UniversalProfile.enabled(context)?ApiEndpoint.validate(value.getString("base_url")):BASE;
   JSONObject api=new JSONObject().put("base_url",base).put("token",apiToken);
   JSONObject weather=new JSONObject().put("base_url",base+"weather/").put("token",weatherToken)
    .put("providers",new JSONArray().put("open_meteo").put("wttr"))
    .put("routes",new JSONObject().put("open_meteo","ru").put("wttr","ru"))
    .put("fallback_routes",new JSONObject().put("open_meteo","direct").put("wttr","direct"));
   byte[] bytes=new JSONObject().put("version",1).put("api",api).put("weather",weather).toString().getBytes("UTF-8");
   AtomicFile file=new AtomicFile(new File(context.getFilesDir(),FILE));FileOutputStream out=null;
   try{out=file.startWrite();out.write(bytes);file.finishWrite(out);}catch(IOException e){if(out!=null)file.failWrite(out);throw e;}
   context.getSharedPreferences("preview",0).edit().putBoolean("weather_server",true).putBoolean("ai_enabled",true).putBoolean("youtube_enabled",true).remove("youtube_attempt").apply();
 }
 public Cursor query(Uri u,String[] p,String s,String[] a,String o){throw new SecurityException("Not supported");}
 public String getType(Uri u){return null;}
 public Uri insert(Uri u,ContentValues v){throw new SecurityException("Not supported");}
 public int update(Uri u,ContentValues v,String s,String[] a){throw new SecurityException("Not supported");}
 public int delete(Uri u,String s,String[] a){throw new SecurityException("Not supported");}
}
