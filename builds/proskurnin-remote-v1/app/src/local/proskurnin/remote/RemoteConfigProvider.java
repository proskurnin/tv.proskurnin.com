package local.proskurnin.remote;
import android.content.*;import android.database.Cursor;import android.net.Uri;import android.os.*;import android.util.*;import java.io.*;import java.net.URI;import java.security.*;import org.json.*;
/** Root-free setup via an already authorized shell. Fixed private filenames only. */
public final class RemoteConfigProvider extends ContentProvider {
 public boolean onCreate(){return true;}
 public synchronized Bundle call(String method,String arg,Bundle extras){
  if(Binder.getCallingUid()!=2000)throw new SecurityException("Authorized shell required");
  if(!"configure".equals(method))throw new IllegalArgumentException("Unsupported operation");
  try{
   String payload=extras.getString("payload");if(payload==null||payload.length()>65536)throw new Exception();
   JSONObject bundle=new JSONObject(payload),files=bundle.getJSONObject("files");if(bundle.length()!=2||bundle.getInt("version")!=1||files.length()<1||files.length()>5)throw new Exception();
   java.util.Iterator<String> names=files.keys();while(names.hasNext()){String name=names.next();if(!java.util.Arrays.asList("api-client.json","remote.p12","tls-password","ca.cer","remote-ca.mobileconfig").contains(name)||Base64.decode(files.getString(name),Base64.DEFAULT).length>16384)throw new Exception();}
   if(files.has("api-client.json")){JSONObject api=new JSONObject(new String(Base64.decode(files.getString("api-client.json"),Base64.DEFAULT),"UTF-8"));validBase(api.getString("base_url"));if(!api.getString("token").matches("[A-Za-z0-9_-]{32,128}"))throw new Exception();}
   if(files.has("remote.p12")){String password=new String(Base64.decode(files.getString("tls-password"),Base64.DEFAULT),"UTF-8").trim();KeyStore store=KeyStore.getInstance("PKCS12");store.load(new ByteArrayInputStream(Base64.decode(files.getString("remote.p12"),Base64.DEFAULT)),password.toCharArray());boolean found=false;java.util.Enumeration<String> aliases=store.aliases();while(aliases.hasMoreElements())if(store.isKeyEntry(aliases.nextElement()))found=true;if(!found)throw new Exception();}
   File target=new File(getContext().getFilesDir(),"portable-config.json");AtomicFile atomic=new AtomicFile(target);
   if(target.exists()){JSONObject old=new JSONObject(new String(RemoteTls.readRaw(target,65536),"UTF-8")).getJSONObject("files");names=old.keys();while(names.hasNext()){String key=names.next();if(!files.has(key))files.put(key,old.get(key));}}
   byte[] data=bundle.toString().getBytes("UTF-8");if(data.length>65536)throw new Exception();FileOutputStream out=null;try{out=atomic.startWrite();out.write(data);atomic.finishWrite(out);}catch(Exception e){if(out!=null)atomic.failWrite(out);throw e;}
   Bundle result=new Bundle();result.putBoolean("configured",true);return result;
  }catch(Exception e){throw new IllegalArgumentException("Invalid device configuration");}
 }
 static String validBase(String base)throws Exception{URI u=new URI(base);if(!"https".equals(u.getScheme())||u.getHost()==null||u.getUserInfo()!=null||u.getRawQuery()!=null||u.getRawFragment()!=null||!"/tv-api/v1/".equals(u.getRawPath())||(u.getPort()!=-1&&(u.getPort()<1||u.getPort()>65535)))throw new Exception();return base;}
 public Cursor query(Uri u,String[] p,String s,String[] a,String o){throw new SecurityException();}public String getType(Uri u){return null;}public Uri insert(Uri u,ContentValues v){throw new SecurityException();}public int update(Uri u,ContentValues v,String s,String[] a){throw new SecurityException();}public int delete(Uri u,String s,String[] a){throw new SecurityException();}
}
