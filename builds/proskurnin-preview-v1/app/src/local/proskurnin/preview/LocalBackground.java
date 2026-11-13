package local.proskurnin.preview;
import android.content.Context;
import java.io.*;
/** User-owned photos stay outside APK and public distribution. */
final class LocalBackground {
 static File directory(Context c){return directory(c,c.getSharedPreferences("preview",0).getString("background_series","big-sur"));}
 static File directory(Context c,String series){File base=c.getExternalFilesDir(null);if(base==null)return null;File root=new File(base,"background-two-hour");String id=BackgroundConfig.series(series);File specific=new File(root,id);return specific.isDirectory()?specific:root;}
 static boolean available(Context c){return available(c,"big-sur")||available(c,"golden-gate")||available(c,"tahoe-2026");}
 static boolean available(Context c,String series){File dir=directory(c,series);if(dir==null)return false;long total=0;for(int h=0;h<24;h+=2){File f=new File(dir,BackgroundConfig.twoHourFrame(h));long n=f.length();if(!f.isFile()||n<100||n>8*1024*1024)return false;total+=n;}return total<=40*1024*1024;}
 static InputStream open(Context c,String path)throws IOException{
  if(!path.startsWith("local-twohour/"))return c.getAssets().open(path);
  String name=path.substring("local-twohour/".length());String series="big-sur";int slash=name.indexOf('/');if(slash>=0){series=BackgroundConfig.series(name.substring(0,slash));name=name.substring(slash+1);}
  if(!name.matches("(00|02|04|06|08|10|12|14|16|18|20|22)\\.jpg"))throw new IOException("frame");
  File dir=directory(c,series);if(dir==null)throw new IOException("storage");
  File f=new File(dir,name);if(f.length()>8*1024*1024)throw new IOException("size");
  return new FileInputStream(f);
 }
 static String credits(Context c){File dir=directory(c);if(dir==null)return "";File f=new File(dir,"CREDITS.txt");if(!f.isFile()||f.length()>16384)return "";
  try(BufferedReader r=new BufferedReader(new InputStreamReader(new FileInputStream(f),"UTF-8"))){StringBuilder b=new StringBuilder();String line;while((line=r.readLine())!=null)b.append(line).append("\n");return b.toString();}catch(IOException e){return "";}
 }
}
