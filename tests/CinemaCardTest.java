package local.proskurnin.preview;
public class CinemaCardTest {
 public static void main(String[] args){
  if(!CinemaCard.allowed("ivi","https://www.ivi.tv/watch/90324"))throw new AssertionError("Ivi card");
  if(!CinemaCard.allowed("zona","https://www.kinopoisk.ru/film/476/"))throw new AssertionError("Zona card");
  for(String u:new String[]{"http://ivi.ru/watch/1","https://ivi.ru.evil.test/watch/1","https://user@ivi.ru/watch/1","https://ivi.ru/watch/1?next=evil","https://ivi.ru/auth","https://ivi.ru/watch/%2e%2e","https://ivi.ru:bad/watch/1"})if(CinemaCard.allowed("ivi",u))throw new AssertionError(u);
  if(!CinemaCard.provider(7).equals("wink")||!CinemaCard.provider(5).isEmpty())throw new AssertionError("mapping");
  System.out.println("CinemaCard: public URL and provider checks passed");
 }
}
