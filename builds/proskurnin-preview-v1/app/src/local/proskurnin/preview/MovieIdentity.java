package local.proskurnin.preview;
import java.text.Normalizer;import java.util.Locale;
final class MovieIdentity {
 static String normalize(String s){return Normalizer.normalize(s,Normalizer.Form.NFD).replaceAll("\\p{M}+","").toLowerCase(Locale.ROOT).replace('ё','е').replaceAll("[^\\p{L}\\p{N}]","");}
 static boolean matches(String proposed,String original,String title,String originalTitle){String a=normalize(proposed),b=normalize(original),c=normalize(title),d=normalize(originalTitle);return !a.isEmpty()&&(a.equals(c)||a.equals(d))||!b.isEmpty()&&(b.equals(c)||b.equals(d));}
}
