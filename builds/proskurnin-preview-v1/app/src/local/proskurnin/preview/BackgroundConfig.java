package local.proskurnin.preview;

/** Android-independent validation and local-time schedule for static backgrounds. */
final class BackgroundConfig {
 static final String[] PERIODS={"morning","day","evening","night"};
 static final int[] DEFAULT_HOURS={6,11,17,22};
 static boolean validHours(int[] h){return h!=null&&h.length==4&&h[0]>=0&&h[3]<24&&h[0]<h[1]&&h[1]<h[2]&&h[2]<h[3];}
 static String pack(String value){return "mountains".equals(value)||"sea".equals(value)?value:"classic";}
 static String mode(String value){for(String p:PERIODS)if(p.equals(value))return p;return "auto";}
 static String period(int hour,String mode,int[] starts){
  String fixed=mode(mode);if(!"auto".equals(fixed))return fixed;
  int[] h=validHours(starts)?starts:DEFAULT_HOURS;int t=Math.floorMod(hour,24);
  if(t<h[0]||t>=h[3])return "night";
  return t<h[1]?"morning":t<h[2]?"day":"evening";
 }
 static int dim(int value){return Math.max(0,Math.min(85,value));}
 static String asset(String pack,String period){String p=pack(pack),m=mode(period);if("auto".equals(m))m="day";return "classic".equals(p)?"backgrounds/"+m+".jpg":"backgrounds/"+p+"/"+m+".jpg";}
}
