package local.proskurnin.preview;

/** Decisions shared by the optional Home service; no Android or screen-content access. */
final class HomeRoutePolicy {
 static boolean alternative(String ownPackage,String pkg,String activity,int priority){
  return pkg!=null&&activity!=null&&!pkg.equals(ownPackage)&&priority>=0&&!activity.endsWith(".FallbackHome");
 }
 static boolean startOnConnection(boolean initialized,int previousBoot,int currentBoot){
  return !initialized||(currentBoot>=0&&currentBoot!=previousBoot);
 }
 static boolean redirect(boolean stockSession,String stockPackage,String stockActivity,CharSequence eventPackage,CharSequence eventActivity){
  return !stockSession&&stockPackage!=null&&stockActivity!=null&&eventPackage!=null&&eventActivity!=null
   &&stockPackage.contentEquals(eventPackage)&&stockActivity.contentEquals(eventActivity);
 }
}
