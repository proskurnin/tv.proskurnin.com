package local.proskurnin.remote;
import android.content.*;
import java.util.concurrent.*;
/** Signed, foreground-only launcher navigation. No global key injection. */
final class LauncherNavigation {
 static boolean send(Context context,String command){
  CountDownLatch done=new CountDownLatch(1);boolean[] ok={false};
  context.sendOrderedBroadcast(new Intent("local.proskurnin.REMOTE_NAV").setPackage("local.proskurnin.preview").putExtra("command",command),"local.proskurnin.permission.REMOTE_AI",new BroadcastReceiver(){public void onReceive(Context c,Intent i){ok[0]=getResultCode()==android.app.Activity.RESULT_OK;done.countDown();}},new android.os.Handler(android.os.Looper.getMainLooper()),0,null,null);
  try{return done.await(1200,TimeUnit.MILLISECONDS)&&ok[0];}catch(InterruptedException e){Thread.currentThread().interrupt();return false;}
 }
}
