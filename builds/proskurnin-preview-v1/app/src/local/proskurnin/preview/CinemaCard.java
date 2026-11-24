package local.proskurnin.preview;
import java.net.URI;
/** Only public movie-card URLs; never auth, playback, payment or arbitrary intents. */
final class CinemaCard {
 static String provider(int index){String[] ids={"kinopoisk","ivi","okko","premier","zona","","kion","wink"};return index>=0&&index<ids.length?ids[index]:"";}
 static boolean allowed(String provider,String url){try{URI u=new URI(url);if(url.length()>1000||!"https".equals(u.getScheme())||u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null||(u.getPort()!=-1&&u.getPort()!=443))return false;String host=u.getHost(),path=u.getRawPath();if(host==null||path==null)return false;
  if(provider.equals("kinopoisk"))return host.equals("hd.kinopoisk.ru")&&path.matches("/film/[A-Za-z0-9-]+/?");
  if(provider.equals("ivi"))return (host.equals("ivi.ru")||host.equals("www.ivi.ru")||host.equals("ivi.tv")||host.equals("www.ivi.tv"))&&path.matches("/watch/[A-Za-z0-9_-]+/?");
  if(provider.equals("okko"))return host.equals("okko.tv")&&path.matches("/movie/[A-Za-z0-9_-]+/?");
  if(provider.equals("premier"))return host.equals("premier.one")&&path.matches("/show/[A-Za-z0-9_-]+/?");
  if(provider.equals("kion"))return host.equals("kion.ru")&&path.matches("/(video|film|movie)/[A-Za-z0-9_/-]+/?");
  if(provider.equals("wink"))return host.equals("wink.ru")&&path.matches("/movies/[A-Za-z0-9_-]+/?");
  return provider.equals("zona")&&host.equals("www.kinopoisk.ru")&&path.matches("/film/[0-9]+/?");
 }catch(Exception e){return false;}}
}
