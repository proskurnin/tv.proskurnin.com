package local.proskurnin.preview;
public class CinemaEvidenceTest {
 public static void main(String[] args){
  if(!CinemaEvidence.status("no_matches","found",true).equals("Карточка найдена"))throw new AssertionError("public card");
  if(!CinemaEvidence.access("").equals("Просмотр не подтверждён"))throw new AssertionError("card is not playback");
  if(!CinemaEvidence.access("подписка").startsWith("По каталогу:"))throw new AssertionError("catalog attribution");
  if(!CinemaEvidence.status("timeout","no_matches",false).equals("Приложение не ответило"))throw new AssertionError("timeout is not absence");
  if(!CinemaEvidence.status("pending","no_matches",false).equals("Ищем карточку…"))throw new AssertionError("independent pending search");
  if(!CinemaEvidence.status("found","error",true).equals("Карточка найдена"))throw new AssertionError("native survives web failure");
  System.out.println("CinemaEvidence: independent card, catalog, timeout and pending states passed");
 }
}
