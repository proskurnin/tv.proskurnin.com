package local.proskurnin.preview;
import android.content.Context;import android.media.MediaMetadataRetriever;import android.os.*;import java.io.*;import java.net.*;import java.security.*;import java.util.*;import java.util.concurrent.atomic.AtomicBoolean;import org.json.*;

final class DreamCache {
 static final long LIMIT=300000000L,MAX_CLIP=40000000L,RESERVE=268435456L;
 static final AtomicBoolean working=new AtomicBoolean();static volatile String playing="";
 final Context context;final File dir;final CancellationSignal cancel=new CancellationSignal();
 interface Progress{void update(String text);}
 DreamCache(Context c){context=c.getApplicationContext();dir=new File(context.getFilesDir(),"dream-cache");dir.mkdirs();}
 File[] ready(){File[] f=dir.listFiles(x->x.getName().matches("[a-z0-9]{1,40}-[a-f0-9]{64}\\.mp4")&&x.length()>0&&x.length()<=MAX_CLIP);return f==null?new File[0]:f;}
 long bytes(){long n=0;File[] fs=dir.listFiles();if(fs!=null)for(File f:fs)n+=f.length();return n;}
 String summary(){return ready().length+" из 5 роликов · "+(bytes()/1000000)+" / 300 МБ";}
 void stop(){cancel.cancel();}
 void clear(){synchronized(DreamCache.class){if(working.get())return;new File(dir,"download.part").delete();for(File f:ready())if(!f.getName().equals(playing))f.delete();}}
 File choose(String previous,Random random){synchronized(DreamCache.class){ArrayList<File> choices=new ArrayList<>(Arrays.asList(ready()));if(choices.size()>1)choices.removeIf(f->f.getName().equals(previous));if(choices.isEmpty())return null;File f=choices.get(random.nextInt(choices.size()));playing=f.getName();return f;}}
 void sync(boolean fill,Progress progress){
  if(!working.compareAndSet(false,true)){progress.update("Загрузка уже выполняется");return;}
  new Thread(()->{File part=new File(dir,"download.part");try{
   part.delete();trim();cancel.throwIfCanceled();
   JSONObject catalog=ApiClient.request(context,"dream/catalog",null,cancel);JSONArray list=catalog.getJSONArray("clips");
   if(list.length()>40)throw new IOException("CATALOG");ArrayList<JSONObject> candidates=new ArrayList<>();
   for(int i=0;i<list.length();i++){JSONObject x=list.getJSONObject(i);String id=x.getString("id"),hash=x.getString("sha256");long size=x.getLong("bytes");
    if(!id.matches("[a-z0-9]{1,40}")||!hash.matches("[a-f0-9]{64}")||size<=0||size>MAX_CLIP)throw new IOException("CATALOG");
    if(!new File(dir,id+"-"+hash+".mp4").exists())candidates.add(x);
   }
   Collections.shuffle(candidates);int downloaded=0;
   for(JSONObject x:candidates){cancel.throwIfCanceled();if(fill&&ready().length>=5)break;if(!fill&&downloaded>=1)break;
    long size=x.getLong("bytes");if(bytes()+size>LIMIT||new StatFs(dir.getPath()).getAvailableBytes()-size<RESERVE){progress.update("Недостаточно места; готовые ролики сохранены");return;}
    progress.update(summary()+" · загружаю новый ролик…");download(x,part,progress);
    cancel.throwIfCanceled();File dest=new File(dir,x.getString("id")+"-"+x.getString("sha256")+".mp4");
    if(!part.renameTo(dest))throw new IOException("COMMIT");trim();downloaded++;
    context.getSharedPreferences("preview",0).edit().putLong("dream_cache_refreshed",System.currentTimeMillis()).apply();progress.update(summary());
   }
   progress.update(summary()+" · готово");
  }catch(android.os.OperationCanceledException e){progress.update(summary());}catch(Exception e){progress.update(summary()+" · сеть недоступна, сохранённые видео работают");}
  finally{part.delete();working.set(false);}},"dream-cache-download").start();
 }
 void trim(){synchronized(DreamCache.class){ArrayList<File> fs=new ArrayList<>(Arrays.asList(ready()));fs.sort(Comparator.comparingLong(File::lastModified));while(fs.size()>5){File victim=null;for(File f:fs)if(!f.getName().equals(playing)){victim=f;break;}if(victim==null)break;if(!victim.delete())throw new IllegalStateException("CACHE_DELETE");fs.remove(victim);}}}
 void download(JSONObject item,File part,Progress progress)throws Exception{
  JSONObject config=ApiClient.privateJson(context,"api-client.json");String base=config.getString("base_url");ApiEndpoint.validate(base);
  HttpURLConnection c=(HttpURLConnection)new URL(base+"dream/clip/"+item.getString("id")+".mp4").openConnection();
  long expected=item.getLong("bytes"),count=0,started=SystemClock.elapsedRealtime(),lastProgress=0;MessageDigest digest=MessageDigest.getInstance("SHA-256");
  try{cancel.setOnCancelListener(()->c.disconnect());cancel.throwIfCanceled();c.setConnectTimeout(5000);c.setReadTimeout(12000);c.setInstanceFollowRedirects(false);c.setRequestProperty("Authorization","Bearer "+config.getString("token"));
   if(c.getResponseCode()!=200||c.getContentLengthLong()!=expected)throw new IOException("RESPONSE");
   try(InputStream in=c.getInputStream();FileOutputStream out=new FileOutputStream(part)){byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1){cancel.throwIfCanceled();if(SystemClock.elapsedRealtime()-started>180000||count+n>expected||bytes()+n>LIMIT)throw new IOException("LIMIT");out.write(b,0,n);digest.update(b,0,n);count+=n;if(SystemClock.elapsedRealtime()-lastProgress>1000){progress.update(summary()+" · загрузка "+(count*100/expected)+"%");lastProgress=SystemClock.elapsedRealtime();}}out.getFD().sync();}
   StringBuilder hex=new StringBuilder();for(byte b:digest.digest())hex.append(String.format(java.util.Locale.US,"%02x",b&255));if(count!=expected||!hex.toString().equals(item.getString("sha256")))throw new IOException("HASH");
   MediaMetadataRetriever metadata=new MediaMetadataRetriever();try{metadata.setDataSource(part.getPath());long duration=Long.parseLong(metadata.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION));if(duration<1000||duration>300000)throw new IOException("VIDEO");}finally{metadata.release();}
  }finally{cancel.setOnCancelListener(null);c.disconnect();}
 }
}
