package local.proskurnin.preview;
/** Window metadata only. No accessibility node or text access. */
final class SystemDialogKeys {
 static boolean suspended(boolean previous,String pkg,String cls){
  if(pkg==null||pkg.isEmpty()||cls==null||cls.isEmpty())return previous;
  if(!"com.android.systemui".equals(pkg))return false;
  return previous||cls.endsWith("ActionsDialog")||"android.app.Dialog".equals(cls)||"android.app.AlertDialog".equals(cls);
 }
}
