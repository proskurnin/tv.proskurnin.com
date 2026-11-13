package local.proskurnin.remote;
import android.content.*;import java.io.*;import java.net.*;import org.json.*;
final class PhoneVoice {
 static long last;static final java.util.concurrent.atomic.AtomicBoolean busy=new java.util.concurrent.atomic.AtomicBoolean();
 static JSONObject transcribe(Context c,JSONObject body)throws Exception{
  if(!busy.compareAndSet(false,true))throw new IOException("rate_limit");
  try{long now=android.os.SystemClock.elapsedRealtime();if(now-last<3000)throw new IOException("rate_limit");last=now;
   String mime=body.getString("mime"),audio=body.getString("audio");if(!(mime.equals("audio/webm")||mime.equals("audio/mp4"))||audio.length()>1000000)throw new IOException("invalid_audio");
   JSONObject config=new JSONObject(new String(RemoteTls.read(new File(c.getFilesDir(),"api-client.json"),16384),"UTF-8"));String base=config.getString("base_url");RemoteConfigProvider.validBase(base);HttpURLConnection conn=(HttpURLConnection)new URL(base+"ai/transcribe").openConnection();
   try{conn.setRequestMethod("POST");conn.setDoOutput(true);conn.setConnectTimeout(5000);conn.setReadTimeout(45000);conn.setInstanceFollowRedirects(false);conn.setRequestProperty("Content-Type","application/json");conn.setRequestProperty("Authorization","Bearer "+config.getString("token"));byte[] data=new JSONObject().put("mime",mime).put("audio",audio).toString().getBytes("UTF-8");conn.setFixedLengthStreamingMode(data.length);try(OutputStream out=conn.getOutputStream()){out.write(data);}if(conn.getResponseCode()!=200)throw new IOException("transcription_unavailable");try(InputStream in=conn.getInputStream();ByteArrayOutputStream out=new ByteArrayOutputStream()){byte[] b=new byte[2048];int n;while((n=in.read(b))!=-1){if(out.size()+n>8192)throw new IOException();out.write(b,0,n);}JSONObject result=new JSONObject(out.toString("UTF-8"));String text=result.getString("text");if(text.isEmpty()||text.length()>512)throw new IOException();return new JSONObject().put("text",text);}}
   finally{conn.disconnect();}
  }finally{busy.set(false);}
 }
 static boolean send(Context c,JSONObject body)throws Exception{String mode=body.getString("mode"),text=body.getString("text");if(!(mode.equals("chat")||mode.equals("movie"))||text.trim().length()<2||text.length()>(mode.equals("movie")?400:512))return false;c.sendBroadcast(new Intent().setClassName("local.proskurnin.preview","local.proskurnin.preview.PhoneAssistantReceiver").putExtra("query",text).putExtra("mode",mode));return true;}
}
