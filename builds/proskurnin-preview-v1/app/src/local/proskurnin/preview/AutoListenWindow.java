package local.proskurnin.preview;
/** Bounded waiting period after natural TTS completion, using monotonic time. */
final class AutoListenWindow {
 private long until;
 void start(long now){until=now+60000;}
 void cancel(){until=0;}
 boolean open(long now){return until>0&&now>=until-60000&&now<until;}
}
