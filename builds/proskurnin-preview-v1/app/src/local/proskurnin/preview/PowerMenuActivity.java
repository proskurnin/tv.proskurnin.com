package local.proskurnin.preview;
import android.app.*;import android.os.*;import android.content.*;import android.widget.*;
/** Explicit power action only after OK; opening/dismissing this screen never powers off. */
public class PowerMenuActivity extends Activity {
 boolean chosen;AlertDialog dialog;
 public void onCreate(Bundle b){super.onCreate(b);getWindow().getDecorView().setSystemUiVisibility(5894);dialog=new LauncherDialogs.Builder(this).setTitle("Телевизор").setItems(new String[]{"Выключить","Перезагрузить","Сделать скриншот"},(d,n)->{chosen=true;if(n==2){finish();new Handler().postDelayed(()->{if(!VoiceKeyService.takeScreenshot())Toast.makeText(this,"Системный скриншот недоступен",0).show();},400);}else new Thread(()->{String result=PowerControl.request(n==0?"OFF":"REBOOT");runOnUiThread(()->{if(!"QUEUED".equals(result))Toast.makeText(this,"Служба питания недоступна. Команда не выполнена.",1).show();finish();});},"power-request").start();}).setNegativeButton("Отмена",null).create();dialog.setOnDismissListener(d->{if(!chosen)finish();});dialog.show();}
 protected void onDestroy(){if(dialog!=null){dialog.setOnDismissListener(null);dialog.dismiss();}super.onDestroy();}
}
