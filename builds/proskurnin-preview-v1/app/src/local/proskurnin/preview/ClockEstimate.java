package local.proskurnin.preview;
/** Display-only estimate. Never changes Android/RTC and never invents elapsed powered-off time. */
final class ClockEstimate {
 static long estimate(long wall,long elapsed,int boot,long saved,long savedElapsed,int savedBoot){
  if(saved<=0)return wall;
  if(boot==savedBoot&&elapsed>=savedElapsed)return saved+elapsed-savedElapsed;
  // A plausible running RTC is preferable to the last saved time after a long power-off.
  if(wall>=saved-120000&&wall-saved<=7L*86400000)return wall;
  return saved+elapsed;
 }
 static boolean due(long now,long previous,long interval){return previous<0||now<previous||now-previous>=interval;}
}
