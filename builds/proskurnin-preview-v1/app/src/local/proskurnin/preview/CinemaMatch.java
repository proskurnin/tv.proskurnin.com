package local.proskurnin.preview;
/** Conservative movie identity for public search suggestions. Missing year is never an exact match. */
final class CinemaMatch {
 static boolean title(String title,String original,String candidate){String clean=candidate.replaceFirst("\\s*[\\(\\[]((?:18|19|20|21)[0-9]{2})[\\)\\]]\\s*$","");for(String part:clean.split(" / ")){String key=MovieIdentity.normalize(part);if(!key.isEmpty()&&(key.equals(MovieIdentity.normalize(title))||(!original.isEmpty()&&key.equals(MovieIdentity.normalize(original)))))return true;}return false;}
 static String zonaLink(String data){return data.matches("https://mobi[.]zona/home_screen/movie/[0-9]+")?data.replace("/home_screen/movie/","/movie/"):data;}
 static boolean lazyPayload(String data){return data.length()<=8192&&data.matches("[0-9]{1,3},(?:[A-Za-z0-9+~=\\r\\n]*,){5}");}
 static String year(String text){java.util.regex.Matcher m=java.util.regex.Pattern.compile("(?<![0-9])(?:18|19|20|21)[0-9]{2}(?![0-9])").matcher(text);if(!m.find())return "";String year=m.group();return m.find()?"":year;}
}
