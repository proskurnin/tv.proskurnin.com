package local.proskurnin.preview;
/** One sweep per focus change. Time is monotonic, no timer repeats on an idle tile. */
final class BannerShineState {
 static final long DELAY_MS=70, DURATION_MS=919, FRAME_MS=34;
 private String target;private long start;
 float update(String key,long now,boolean enabled){
  if(!enabled||key==null){reset();return -1;}
  if(!key.equals(target)){target=key;start=now;}
  long elapsed=now-start-DELAY_MS;
  if(elapsed<0)return 0;if(elapsed>=DURATION_MS)return -1;
  float t=(float)elapsed/DURATION_MS;
  return (1f-(float)Math.cos(Math.PI*t))/2f;
 }
 void reset(){target=null;start=0;}
}
