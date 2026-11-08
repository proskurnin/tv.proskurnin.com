package local.proskurnin.preview;
public final class SystemDialogKeysTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  check(SystemDialogKeys.suspended(false,"com.android.systemui","android.app.Dialog"));
  check(SystemDialogKeys.suspended(false,"com.android.systemui","com.android.systemui.globalactions.GlobalActionsDialog$ActionsDialog"));
  check(!SystemDialogKeys.suspended(false,"local.proskurnin.preview","android.app.Dialog"));
  check(!SystemDialogKeys.suspended(true,"local.proskurnin.preview","local.proskurnin.preview.MainActivity"));
  check(SystemDialogKeys.suspended(true,"com.android.systemui","android.widget.FrameLayout"));
  check(SystemDialogKeys.suspended(true,null,null));
  check(!SystemDialogKeys.suspended(false,"com.android.systemui","android.widget.FrameLayout"));
  System.out.println("SystemDialogKeys: suspend, restore, unrelated and incomplete events passed");
 }
}
