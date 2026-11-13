package local.proskurnin.preview;
public class BannerShineStateTest {
 static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
 public static void main(String[] args){
  BannerShineState s=new BannerShineState();
  check(s.update("home:a",1000,true)==0,"initial delay");float p=s.update("home:a",1400,true);check(p>0&&p<1,"sweep");
  check(s.update("home:a",2000,true)<0,"ends");check(s.update("home:a",20000,true)<0,"no idle loop");
  check(s.update("apps:a",20001,true)==0,"different screen retriggers");check(s.update("apps:b",20010,true)==0,"new tile resets");
  check(s.update(null,20020,true)<0,"top toolbar cancels");check(s.update("home:a",20030,false)<0,"disabled/background cancels");
  check(s.update("home:a",20040,true)==0,"resume starts fresh");s.reset();check(s.update("home:a",30000,true)==0,"window focus loss reset");
  System.out.println("BannerShineStateTest passed");
 }
}
