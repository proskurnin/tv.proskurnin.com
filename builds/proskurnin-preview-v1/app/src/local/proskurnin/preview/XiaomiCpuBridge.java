package local.proskurnin.preview;

import android.os.Build;
import android.os.Environment;
import android.os.SystemClock;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.util.Locale;

/** Reads the aggregate CPU snapshot the authorized shell helper writes to this app's private external files. */
final class XiaomiCpuBridge {
 private static final String PACKAGE="local.proskurnin.preview";
 private XiaomiCpuBridge(){}

 static boolean supported(){return "nino".equals(Build.DEVICE)&&Build.MODEL.toUpperCase(Locale.US).contains("MSSP1");}

 static CpuSample read(){
  if(!supported())return null;
  try{
   File file=new File(Environment.getExternalStorageDirectory(),"Android/data/"+PACKAGE+"/files/cpu.stat");
   long age=System.currentTimeMillis()-file.lastModified();
   if(!file.isFile()||age<0||age>8000)return null;
   try(BufferedReader reader=new BufferedReader(new FileReader(file))){
    String line=reader.readLine();if(line==null||line.length()>512||!line.startsWith("cpu "))return null;
    return CpuSample.parse(line);
   }
  }catch(Exception ignored){return null;}
 }
}
