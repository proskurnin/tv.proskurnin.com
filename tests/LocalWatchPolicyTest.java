package local.proskurnin.preview;
import java.time.*;
public class LocalWatchPolicyTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){long t=Instant.parse("2026-11-21T22:30:00Z").toEpochMilli(),now=t+3600000;ZoneId zone=ZoneId.of("Europe/Moscow");
  check(LocalWatchPolicy.day("reported_playback",t,now,zone).equals("2026-11-22"));
  for(String c:new String[]{"undated_history","continue_card","local_record_unverified","watchlist"})check(LocalWatchPolicy.day(c,t,now,zone).isEmpty());
  check(LocalWatchPolicy.day("reported_playback",0,now,zone).isEmpty());check(LocalWatchPolicy.day("reported_playback",now+86400000,now,zone).isEmpty());
  String a=LocalWatchPolicy.mergeKey("p","k","2026-11-22");check(a.equals(LocalWatchPolicy.mergeKey("p","k","2026-11-22")));check(!a.equals(LocalWatchPolicy.mergeKey("q","k","2026-11-22")));check(!a.equals(LocalWatchPolicy.mergeKey("p","k","")));check(!a.equals(LocalWatchPolicy.mergeKey("p","k","2026-11-23")));
  System.out.println("LocalWatchPolicy: dates, unknown evidence, repeated days, independent sources passed");
 }
}
