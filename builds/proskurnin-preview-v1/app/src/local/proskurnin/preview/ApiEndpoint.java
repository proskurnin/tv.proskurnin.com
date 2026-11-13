package local.proskurnin.preview;
import java.net.URI;
import java.io.IOException;
/** Explicitly configured HTTPS origin only; never credentials in a URL or redirects. */
final class ApiEndpoint {
 static String validate(String value)throws IOException{return check(value,"/tv-api/v1/");}
 static String validateWeather(String value)throws IOException{return check(value,"/tv-api/v1/weather/");}
 static String check(String value,String path)throws IOException{
  try{URI u=new URI(value);if(!"https".equals(u.getScheme())||u.getHost()==null||u.getUserInfo()!=null||u.getRawQuery()!=null||u.getRawFragment()!=null||!path.equals(u.getRawPath())||(u.getPort()!=-1&&(u.getPort()<1||u.getPort()>65535)))throw new Exception();return value;}catch(Exception e){throw new IOException("CONFIG");}
 }
}
