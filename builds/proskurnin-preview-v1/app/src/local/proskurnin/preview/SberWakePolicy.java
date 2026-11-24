package local.proskurnin.preview;

/** Bounded, one-shot recovery of the Sber Google boot/resume sequence. No window contents. */
final class SberWakePolicy {
 static final String GOOGLE="com.google.android.tvlauncher";
 static final String HELPER=GOOGLE+".BootHelperEmptyActivity", MAIN=GOOGLE+".MainActivity";
 static final long WINDOW_MS=15000;
 boolean sleeping, helper, googlePending;
 long deadline=-1;
 static boolean supported(boolean universal,String model,String device){return !universal&&"SaluteTV".equals(model)&&"m7332_eu".equals(device);}
 void screenOff(){cancel();sleeping=true;}
 boolean screenOn(long now){
  if(sleeping||helper)deadline=now+WINDOW_MS;
  sleeping=false;
  boolean pending=googlePending;googlePending=false;
  return pending&&consume(now);
 }
 boolean window(String pkg,String cls,boolean interactive,long now){
  if(!GOOGLE.equals(pkg)){
   // A real intervening app must never be replaced by a deferred callback.
   googlePending=false;return false;
  }
  if(HELPER.equals(cls)){
   helper=true;
   if(interactive&&!sleeping)deadline=now+WINDOW_MS;
   return false;
  }
  if(!MAIN.equals(cls))return false;
  if(!interactive||sleeping){googlePending=true;return false;}
  return consume(now);
 }
 boolean consume(long now){boolean allowed=deadline>=0&&now<=deadline;cancel();return allowed;}
 void cancel(){sleeping=false;helper=false;googlePending=false;deadline=-1;}
}
