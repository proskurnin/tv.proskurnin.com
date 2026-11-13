package local.proskurnin.preview;

/** Staggers only the launcher's noncritical startup work on a freshly booted TV. */
final class StartupLoadPlan {
 static final long COLD_BOOT_WINDOW_MS=180_000L;
 private StartupLoadPlan(){}

 /** Delays correspond to app discovery, weather, currency and YouTube refresh. */
 static long[] delays(long uptimeMs){
  if(uptimeMs>=COLD_BOOT_WINDOW_MS)return new long[]{0,0,0,0};
  return new long[]{10_000L,25_000L,40_000L,55_000L};
 }
}
