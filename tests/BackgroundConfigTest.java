package local.proskurnin.preview;
public final class BackgroundConfigTest {
 static void eq(Object a,Object b){if(!a.equals(b))throw new AssertionError(a+" != "+b);}
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  int[] normal={6,11,17,22};
  for(int h=0;h<24;h++)eq(BackgroundConfig.period(h,"auto",normal),h<6||h>=22?"night":h<11?"morning":h<17?"day":"evening");
  int[] custom={0,8,16,23};eq(BackgroundConfig.period(0,"auto",custom),"morning");eq(BackgroundConfig.period(7,"auto",custom),"morning");eq(BackgroundConfig.period(8,"auto",custom),"day");eq(BackgroundConfig.period(16,"auto",custom),"evening");eq(BackgroundConfig.period(23,"auto",custom),"night");
  for(String p:BackgroundConfig.PERIODS)for(int h=0;h<24;h++)eq(BackgroundConfig.period(h,p,normal),p);
  for(int[] bad:new int[][]{null,{}, {6,6,17,22},{6,17,11,22},{-1,11,17,22},{6,11,17,24}}){check(!BackgroundConfig.validHours(bad));eq(BackgroundConfig.period(12,"auto",bad),"day");}
  eq(BackgroundConfig.period(-1,"auto",normal),"night");eq(BackgroundConfig.period(24,"auto",normal),"night");
  eq(BackgroundConfig.asset("sea","night"),"backgrounds/sea/night.jpg");eq(BackgroundConfig.asset("mountains","day"),"backgrounds/mountains/day.jpg");
  eq(BackgroundConfig.asset("../../private","../../private"),"backgrounds/day.jpg");eq(BackgroundConfig.asset(null,null),"backgrounds/day.jpg");
  eq(BackgroundConfig.dim(-5),0);eq(BackgroundConfig.dim(120),85);eq(BackgroundConfig.dim(69),69);
  System.out.println("Background schedule: boundaries, fixed modes, invalid preferences, safe asset paths OK");
 }
}
