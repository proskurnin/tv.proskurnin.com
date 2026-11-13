package local.proskurnin.preview;
public class StartupLoadPlanTest {
 static void check(boolean ok,String name){if(!ok)throw new AssertionError(name);}
 public static void main(String[] args){
  long[] early=StartupLoadPlan.delays(1000);
  check(early[0]==10000&&early[1]==25000&&early[2]==40000&&early[3]==55000,"startup tasks are staggered");
  long[] boundary=StartupLoadPlan.delays(179999);
  check(boundary[0]<boundary[1]&&boundary[1]<boundary[2]&&boundary[2]<boundary[3],"stagger remains before end of boot window");
  long[] normal=StartupLoadPlan.delays(180000);
  check(normal[0]==0&&normal[1]==0&&normal[2]==0&&normal[3]==0,"normal resume has no added delay");
  System.out.println("StartupLoadPlan: passed");
 }
}
