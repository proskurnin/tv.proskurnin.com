package local.proskurnin.preview;
public class CinemaMatchTest {
 public static void main(String[] args){
  if(!CinemaMatch.title("Назад в будущее","Back to the Future","НАЗАД В БУДУЩЕЕ"))throw new AssertionError();
  if(CinemaMatch.title("Назад в будущее","Back to the Future","Назад в будущее 2"))throw new AssertionError();
  if(!CinemaMatch.year("1985 · Фантастика").equals("1985"))throw new AssertionError();
  for(String s:new String[]{"", "1985–1989","123198567","★ 8.5"})if(!CinemaMatch.year(s).isEmpty())throw new AssertionError(s);
  if(!CinemaMatch.title("Назад в будущее","Back to the Future","Назад в будущее / Back to the Future (1985)"))throw new AssertionError("bilingual");
  if(!CinemaMatch.lazyPayload("1,YQ==,Yg==,Yw==,ZA==,bm9uZQ==,"))throw new AssertionError("lazy card");
  if(!CinemaMatch.lazyPayload("1,YQ==\n,Yg==\n,Yw==\n,ZA==\n,bm9uZQ==\n,"))throw new AssertionError("Android Base64.DEFAULT line breaks");
  for(String s:new String[]{"javascript:evil","intent://x","1,http://evil,abc,,,","1,a,b,c,d,e,extra"})if(CinemaMatch.lazyPayload(s))throw new AssertionError(s);
  if(!CinemaMatch.zonaLink("https://mobi.zona/home_screen/movie/476").equals("https://mobi.zona/movie/476"))throw new AssertionError("Zona TV card");
  String other="https://evil.test/home_screen/movie/476";if(!CinemaMatch.zonaLink(other).equals(other))throw new AssertionError("Zona host");
  System.out.println("CinemaMatch: title, sequel, missing and ambiguous years passed");
 }
}
