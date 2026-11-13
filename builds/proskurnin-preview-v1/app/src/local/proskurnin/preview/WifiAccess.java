package local.proskurnin.preview;
import android.Manifest;import android.content.*;import android.content.pm.PackageManager;import android.location.LocationManager;import android.provider.Settings;
/** Android 9 requires location access for SSID. Never changes the global setting itself. */
final class WifiAccess {
 static final int REQUEST=771;
 static boolean allowed(MainActivity a){return a.checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED;}
 static boolean locationEnabled(MainActivity a){try{return ((LocationManager)a.getSystemService(Context.LOCATION_SERVICE)).isLocationEnabled();}catch(Exception e){return false;}}
 static void open(MainActivity a){
  if(a.networkTransport!=2||!a.wifiSsid.isEmpty()){a.openIntent(new Intent(Settings.ACTION_WIFI_SETTINGS));return;}
  new LauncherDialogs.Builder(a).setTitle("Имя сети Wi-Fi").setMessage("Android относит имя Wi-Fi к данным местоположения. Нужны разрешение лаунчеру и включённое местоположение в настройках ТВ. Лаунчер не запрашивает координаты и не передаёт имя сети на сервер.")
   .setPositiveButton("Разрешить имя сети",(d,n)->{if(!allowed(a))a.requestPermissions(new String[]{Manifest.permission.ACCESS_COARSE_LOCATION},REQUEST);else if(!locationEnabled(a))a.openIntent(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS));else a.openIntent(new Intent(Settings.ACTION_WIFI_SETTINGS));})
   .setNeutralButton("Настройки Wi-Fi",(d,n)->a.openIntent(new Intent(Settings.ACTION_WIFI_SETTINGS))).setNegativeButton("Отмена",null).show();
 }
 static void result(MainActivity a){a.refreshWifiSignal();a.screen.invalidate();if(allowed(a)&&!locationEnabled(a))new LauncherDialogs.Builder(a).setTitle("Местоположение выключено").setMessage("Чтобы Android показал имя Wi-Fi, включите местоположение в системных настройках ТВ. Это общая настройка Android; автоматически она не меняется.").setPositiveButton("Открыть настройки",(d,n)->a.openIntent(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS))).setNegativeButton("Позже",null).show();}
}
