package local.proskurnin.preview;
public class ClockAndMovieTest {
 static void ok(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args){long saved=1794182400000L;
 ok(ClockEstimate.estimate(0,60000,5,saved,30000,5)==saved+30000);
 ok(ClockEstimate.estimate(saved-86400000,60000,6,saved,30000,5)==saved+60000);
 ok(ClockEstimate.estimate(saved+315360000000L,60000,6,saved,30000,5)==saved+60000);
 ok(ClockEstimate.estimate(saved+3600000,60000,6,saved,30000,5)==saved+3600000);
 ok(ClockEstimate.due(1000,-1,300000));ok(!ClockEstimate.due(1000,500,300000));ok(ClockEstimate.due(301000,500,300000));
 ok(MovieIdentity.matches("В поисках Немо","Finding Nemo","В поисках Немо","Finding Nemo"));
 ok(!MovieIdentity.matches("Turtle","Turtle","Turtle Power","Turtle Power"));
 ok(MovieIdentity.matches("Le monde du silence","Le Monde du silence","Мир безмолвия","Le Monde du Silence"));
 System.out.println("Clock rollback/reboot/RTC and exact movie identity: PASS");}
}
