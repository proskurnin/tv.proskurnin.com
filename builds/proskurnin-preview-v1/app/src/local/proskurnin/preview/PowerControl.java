package local.proskurnin.preview;
import android.net.*;import java.io.*;
final class PowerControl {
 static String request(String command){if(!command.equals("PING")&&!command.equals("OFF")&&!command.equals("REBOOT"))return "DENIED";try(LocalSocket s=new LocalSocket()){s.connect(new LocalSocketAddress("proskurnin.power.v1",LocalSocketAddress.Namespace.ABSTRACT));s.setSoTimeout(1000);s.getOutputStream().write((command+"\n").getBytes("US-ASCII"));StringBuilder b=new StringBuilder();for(int i=0;i<16;i++){int ch=s.getInputStream().read();if(ch<0||ch=='\n')break;b.append((char)ch);}return b.toString();}catch(Exception e){return "UNAVAILABLE";}}
}
