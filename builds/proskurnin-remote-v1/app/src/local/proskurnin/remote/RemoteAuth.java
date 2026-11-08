package local.proskurnin.remote;
import android.content.*;import java.security.*;import java.util.*;import org.json.*;
/** Pairing secrets exist only in memory; stored sessions contain SHA256, never bearer tokens. */
final class RemoteAuth {
 final SharedPreferences prefs;final SecureRandom random=new SecureRandom();String code="";long codeUntil;int attempts;Pending pending;JSONArray sessions;final HashMap<String,long[]> limits=new HashMap<>();
 static final long LIFETIME=30L*24*60*60*1000;
 static class Pending {String id,ip,name,token;long until;boolean approved,rejected;}
 RemoteAuth(Context c){prefs=c.getSharedPreferences("remote_auth",0);try{sessions=new JSONArray(prefs.getString("sessions","[]"));}catch(Exception e){sessions=new JSONArray();}prune();}
 String secret(){byte[] b=new byte[32];random.nextBytes(b);return android.util.Base64.encodeToString(b,android.util.Base64.URL_SAFE|android.util.Base64.NO_WRAP|android.util.Base64.NO_PADDING);}
 static String hash(String s){try{byte[] b=MessageDigest.getInstance("SHA-256").digest(s.getBytes("UTF-8"));StringBuilder h=new StringBuilder();for(byte v:b)h.append(String.format(Locale.US,"%02x",v&255));return h.toString();}catch(Exception e){throw new IllegalStateException(e);}}
 synchronized void prune(){JSONArray keep=new JSONArray();long now=System.currentTimeMillis();for(int i=0;i<sessions.length();i++){JSONObject x=sessions.optJSONObject(i);if(x!=null&&x.optLong("expires")>now)keep.put(x);}if(keep.length()!=sessions.length()){sessions=keep;save();}}
 void save(){prefs.edit().putString("sessions",sessions.toString()).apply();}
 synchronized void open(){code=String.format(Locale.US,"%06d",random.nextInt(1000000));codeUntil=System.currentTimeMillis()+120000;attempts=0;pending=null;}
 synchronized void closePairing(){code="";codeUntil=0;pending=null;}
 synchronized String visibleCode(){if(System.currentTimeMillis()>codeUntil||attempts>=5)return "";return code;}
 synchronized int seconds(){return Math.max(0,(int)((codeUntil-System.currentTimeMillis())/1000));}
 synchronized JSONObject pair(String value,String name,String ip)throws Exception{
  if(visibleCode().isEmpty())throw new SecurityException("pair_closed");
  attempts++;if(!MessageDigest.isEqual(value.getBytes("UTF-8"),code.getBytes("UTF-8")))throw new SecurityException("wrong_code");
  code="";pending=new Pending();pending.id=secret();pending.ip=ip;pending.name=name.replaceAll("[^\\p{L}\\p{N} ._-]","").trim();if(pending.name.isEmpty())pending.name="Телефон";if(pending.name.length()>32)pending.name=pending.name.substring(0,32);pending.until=System.currentTimeMillis()+60000;
  return new JSONObject().put("pending",pending.id);
 }
 synchronized Pending request(){if(pending!=null&&System.currentTimeMillis()>pending.until)pending=null;return pending;}
 synchronized void approve(String id,boolean allow){Pending p=request();if(p==null||!p.id.equals(id)||p.approved||p.rejected)return;if(!allow){p.rejected=true;return;}p.approved=true;p.token=secret();prune();JSONArray keep=new JSONArray();for(int i=Math.max(0,sessions.length()-4);i<sessions.length();i++)keep.put(sessions.opt(i));sessions=keep;try{sessions.put(new JSONObject().put("hash",hash(p.token)).put("name",p.name).put("expires",System.currentTimeMillis()+LIFETIME));save();}catch(Exception ignored){}}
 synchronized String poll(String id,String ip){Pending p=request();if(p==null||!p.id.equals(id)||!p.ip.equals(ip))throw new SecurityException("pair_expired");if(p.rejected)throw new SecurityException("pair_rejected");if(!p.approved)return null;String token=p.token;pending=null;return token;}
 synchronized String authenticate(String token){if(token==null||!token.matches("[A-Za-z0-9_-]{43}"))return null;String digest=hash(token);long now=System.currentTimeMillis();for(int i=0;i<sessions.length();i++){JSONObject x=sessions.optJSONObject(i);if(x!=null&&x.optLong("expires")>now&&MessageDigest.isEqual(digest.getBytes(),x.optString("hash").getBytes()))return digest;}return null;}
 synchronized boolean permit(String digest){long now=android.os.SystemClock.elapsedRealtime();long[] state=limits.get(digest);if(state==null||now-state[0]>=1000){limits.put(digest,new long[]{now,1});return true;}return ++state[1]<=12;}
 synchronized void revoke(String digest){JSONArray keep=new JSONArray();for(int i=0;i<sessions.length();i++){JSONObject x=sessions.optJSONObject(i);if(x!=null&&!x.optString("hash").equals(digest))keep.put(x);}sessions=keep;save();limits.remove(digest);}
 synchronized void clear(){sessions=new JSONArray();save();limits.clear();closePairing();}
 synchronized String names(){prune();StringBuilder b=new StringBuilder();for(int i=0;i<sessions.length();i++){if(i>0)b.append(", ");b.append(sessions.optJSONObject(i).optString("name","Телефон"));}return b.length()==0?"Нет сопряжённых телефонов":b.toString();}
}
