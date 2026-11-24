package local.proskurnin.power;
public final class SberRebootPolicyTest {
 public static void main(String[] args) {
  String fp="MediaTek/m7332_eu/m7332_eu:9/PPR2.180905.006.A1/yankeqi12211211:userdebug/release-keys";
  if(!"poweron".equals(SberRebootPolicy.reason("SaluteTV","m7332_eu",fp)))throw new AssertionError();
  for(String[] profile:new String[][]{{"MiTV-MSSP1","nino",fp},{"SaluteTV","m7332_eu","changed-firmware"},{"SaluteTV","other",fp}}){
   try{SberRebootPolicy.reason(profile[0],profile[1],profile[2]);throw new AssertionError("Unsupported TV accepted");}catch(SecurityException expected){}
  }
  System.out.println("SberRebootPolicy: supported firmware only; hardware reboot NOT tested");
 }
}
