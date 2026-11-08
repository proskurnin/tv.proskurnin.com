package local.proskurnin.remote;
import android.net.*;import java.io.*;
final class BridgeClient {
 static synchronized boolean send(String command){try(LocalSocket socket=new LocalSocket()){socket.connect(new LocalSocketAddress("proskurnin.remote.keys.v1",LocalSocketAddress.Namespace.ABSTRACT));socket.setSoTimeout(1500);socket.getOutputStream().write((command+"\n").getBytes("US-ASCII"));socket.getOutputStream().flush();byte[] result=new byte[8];int n=socket.getInputStream().read(result);return n>=2&&result[0]=='O'&&result[1]=='K';}catch(Exception e){return false;}}
}
