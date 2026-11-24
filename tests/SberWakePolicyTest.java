package local.proskurnin.preview;
public class SberWakePolicyTest {
 static void check(boolean b,String name){if(!b)throw new AssertionError(name);}
 static boolean main(SberWakePolicy p,long t){return p.window(SberWakePolicy.GOOGLE,SberWakePolicy.MAIN,true,t);}
 public static void main(String[] args){
  check(SberWakePolicy.supported(false,"SaluteTV","m7332_eu"),"exact Sber");
  check(!SberWakePolicy.supported(true,"SaluteTV","m7332_eu"),"Universal excluded");
  check(!SberWakePolicy.supported(false,"MiTV-MSSP1","nino"),"Xiaomi excluded");
  check(!SberWakePolicy.supported(false,"SaluteTV","other"),"unknown hardware excluded");
  SberWakePolicy p=new SberWakePolicy();
  check(!main(p,1),"service connection/manual Google must not launch Home");
  p.screenOff();check(!p.screenOn(100),"screen on alone must not replace film");
  check(!p.window("movie.app","Player",true,101),"film preserved");
  check(main(p,102),"automatic Google immediately after wake recovered");
  check(!main(p,103),"one shot, no redirect loop");
  p.screenOff();p.screenOn(200);p.cancel();check(!main(p,201),"user navigation/long Home wins");
  p.screenOff();p.screenOn(300);check(!main(p,15301),"expired window cannot steal Google");
  p.screenOff();check(!p.window(SberWakePolicy.GOOGLE,SberWakePolicy.MAIN,false,400),"never launch while asleep");
  check(p.screenOn(500),"Google event before screen-on handled");
  p.screenOff();p.window(SberWakePolicy.GOOGLE,SberWakePolicy.MAIN,false,600);p.window("movie.app","Player",false,601);check(!p.screenOn(700),"no stale pending callback over movie");
  p=new SberWakePolicy();p.window(SberWakePolicy.GOOGLE,SberWakePolicy.HELPER,true,800);check(main(p,801),"exact helper sequence after rebind");
  p=new SberWakePolicy();p.window(SberWakePolicy.GOOGLE,"Settings",true,900);check(!main(p,901),"Google settings not helper");
  p.screenOff();p.window(SberWakePolicy.GOOGLE,SberWakePolicy.HELPER,false,1000);check(!p.screenOn(100000),"long sleep doesn't itself launch");check(main(p,100001),"long sleep then Google handled");
  System.out.println("SberWakePolicy: passed");
 }
}
