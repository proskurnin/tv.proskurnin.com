package local.proskurnin.preview;
import java.time.*;
/** Observation time must never be used as a viewing date. */
final class LocalWatchPolicy {
 static String day(String certainty,long reported,long now,ZoneId zone){
  if(!"reported_playback".equals(certainty)||reported<946684800000L||reported>now+300000L)return "";
  try{return Instant.ofEpochMilli(reported).atZone(zone).toLocalDate().toString();}catch(Exception e){return "";}
 }
 static String mergeKey(String pkg,String key,String day){return pkg+"|"+key+"|"+day;}
}
