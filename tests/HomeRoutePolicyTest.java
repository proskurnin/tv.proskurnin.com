package local.proskurnin.preview;
public class HomeRoutePolicyTest {
 static void check(boolean value,String name){if(!value)throw new AssertionError(name);}
 public static void main(String[] args){
  check(HomeRoutePolicy.alternative("our.home","google.home","google.home.MainActivity",2),"stock home accepted");
  check(!HomeRoutePolicy.alternative("our.home","our.home","our.home.MainActivity",0),"no self loop");
  check(!HomeRoutePolicy.alternative("our.home","settings","settings.FallbackHome",0),"fallback excluded even at zero priority");
  check(!HomeRoutePolicy.alternative("our.home","settings","settings.OtherHome",-1000),"negative fallback excluded");
  check(HomeRoutePolicy.startOnConnection(false,-1,12),"explicit first activation");
  check(HomeRoutePolicy.startOnConnection(true,12,13),"new boot");
  check(!HomeRoutePolicy.startOnConnection(true,12,12),"rebind must not interrupt playback");
  check(!HomeRoutePolicy.startOnConnection(true,12,-1),"unavailable boot count must not repeatedly launch");
  check(HomeRoutePolicy.redirect(false,"google.home","google.home.Main","google.home","google.home.Main"),"ordinary stock Home redirected");
  check(!HomeRoutePolicy.redirect(true,"google.home","google.home.Main","google.home","google.home.Main"),"long Home keeps stock session");
  check(!HomeRoutePolicy.redirect(false,"google.home","google.home.Main","movie.app","movie.app.Main"),"other applications untouched");
  check(!HomeRoutePolicy.redirect(false,"google.home","google.home.Main","google.home","google.home.Settings"),"stock settings untouched");
  check(!HomeRoutePolicy.redirect(false,null,null,"google.home","google.home.Main"),"missing stock Home safe");
  System.out.println("HomeRoutePolicy: passed");
 }
}
