package local.proskurnin.preview;
import android.content.*;
import android.content.pm.*;
import android.widget.*;
import android.text.InputType;
import org.json.*;
import java.util.*;

/** Portable application profile. Firmware adapters are never selected automatically. */
final class UniversalProfile {
 static boolean enabled(Context c){try{return c.getPackageManager().getApplicationInfo(c.getPackageName(),PackageManager.GET_META_DATA).metaData.getBoolean("proskurnin.universal",false);}catch(Exception e){return false;}}
 static void initialize(MainActivity a){if(!enabled(a))return;
  SharedPreferences.Editor e=a.prefs.edit().putBoolean("boot_home",false).putBoolean("power_menu",false);
  if(!a.prefs.getBoolean("universal_initialized",false))e.putBoolean("voice_key_enabled",false).putBoolean("universal_initialized",true);
  if(!PreviewProfile.configured(a))e.putBoolean("weather_server",false);
  if(!a.prefs.contains("app_arrangement_v1")&&!a.prefs.contains("favorites")){
   JSONArray selected=new JSONArray();String[][] choices={{"ru.more.play","tv.okko.androidtv"},{"ru.kinopoisk.tv"},{"ru.ivi.client"},{"org.smarttube.stable","com.liskovsoft.smarttubetv.beta","com.google.android.youtube.tv"},{"mobi.zona"},{"com.lazycatsoftware.lmd"}};
   for(String[] slot:choices)for(String pkg:slot)if(a.getPackageManager().getLeanbackLaunchIntentForPackage(pkg)!=null||a.getPackageManager().getLaunchIntentForPackage(pkg)!=null){selected.put(pkg);break;}
   e.putString("favorites",selected.toString());
  }
  e.apply();
 }
 static ResolveInfo alternativeHome(Context c){ResolveInfo chosen=null;
  for(ResolveInfo r:c.getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME),0))
   if(r.activityInfo.enabled&&r.activityInfo.applicationInfo.enabled&&HomeRoutePolicy.alternative(c.getPackageName(),r.activityInfo.packageName,r.activityInfo.name,r.priority)&&(chosen==null||r.priority>chosen.priority))chosen=r;
  return chosen;
 }
 static void resumedHome(Context c){if(enabled(c))c.getSharedPreferences("preview",0).edit().putBoolean("stock_home_session",false).apply();}
 static void otherHome(Context c){ResolveInfo r=alternativeHome(c);
  if(r!=null){try{c.getSharedPreferences("preview",0).edit().putBoolean("stock_home_session",true).apply();c.startActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).setComponent(new ComponentName(r.activityInfo.packageName,r.activityInfo.name)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));return;}catch(Exception ignored){c.getSharedPreferences("preview",0).edit().putBoolean("stock_home_session",false).apply();}}
  try{c.startActivity(new Intent("android.settings.HOME_SETTINGS").addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));}catch(Exception e){Toast.makeText(c,"Откройте выбор главного экрана в настройках ТВ",1).show();}
 }
 static void settings(MainActivity a){String[] names={"Настройки телевизора","Оформление экрана","Фон лаунчера","Приложения главного экрана","Погода · Москва","Счётчик YouTube","Что посмотрим?","Давайте поговорим","Заставка и кэш видео","Пульт с телефона","Подключение API","Возможности телевизора","Выбор главного экрана Android","Открыть другой Home","Кнопки приложений","Службы кнопок (по желанию)","Кнопка AI: "+(a.prefs.getBoolean("voice_key_enabled",false)?"вкл":"выкл"),"Графики валют: "+(a.prefs.getBoolean("rates_chart",true)?"вкл":"выкл"),"Цветные подложки: "+(a.prefs.getBoolean("app_tints",true)?"вкл":"выкл"),"Часы: "+(a.prefs.getBoolean("clock24",true)?"24":"12"),"Значок VPN: "+(a.prefs.getBoolean("vpn_button",true)?"вкл":"выкл"),"Оформление: "+(a.prefs.getBoolean("design",true)?"вкл":"выкл"),"Значок AI: "+(a.prefs.getBoolean("ai_enabled",true)?"вкл":"выкл"),"Блик на баннерах: "+(a.prefs.getBoolean("banner_shine",true)?"вкл":"выкл")};
  new LauncherDialogs.Builder(a).setCustomTitle(a.versionTitle("Proskurnin TV · Universal")).setItems(names,(d,n)->{switch(n){
   case 1:appearance(a);break;
   case 0:a.openIntent(new Intent("android.settings.SETTINGS"));break;
   case 2:a.backgroundSettings();break;case 3:a.chooseFavoriteSlot();break;case 4:a.weatherSettings();break;case 5:a.youtubeSettings();break;
   case 6:a.startActivity(new Intent(a,MovieActivity.class));break;case 7:a.startActivity(new Intent(a,AssistantActivity.class));break;
   case 8:a.dreamMenu();break;case 9:a.openIntent(new Intent().setClassName("local.proskurnin.remote","local.proskurnin.remote.RemoteActivity"));break;
   case 10:configure(a);break;case 11:capabilities(a);break;case 12:a.openIntent(new Intent("android.settings.HOME_SETTINGS"));break;case 13:otherHome(a);break;
   case 14:a.startActivity(new Intent(a,AppKeySettingsActivity.class));break;case 15:a.openIntent(new Intent("android.settings.ACCESSIBILITY_SETTINGS"));break;
   default:String key=new String[]{"voice_key_enabled","rates_chart","app_tints","clock24","vpn_button","design","ai_enabled","banner_shine"}[n-16];a.prefs.edit().putBoolean(key,!a.prefs.getBoolean(key,!key.equals("voice_key_enabled"))).apply();a.topIndex=Math.min(a.topIndex,a.quickCount()-1);a.updateTime();a.screen.stopShine();a.screen.invalidate();
  }}).setNegativeButton("Закрыть",null).show();
 }
 static void appearance(MainActivity a){new LauncherDialogs.Builder(a).setTitle("Оформление экрана").setItems(new String[]{"Виджет валют","Фон лаунчера","Оформление: "+(a.prefs.getBoolean("design",true)?"вкл":"выкл"),"Часы: "+(a.prefs.getBoolean("clock24",true)?"24":"12"),"Графики валют: "+(a.prefs.getBoolean("rates_chart",true)?"вкл":"выкл"),"Цветные подложки: "+(a.prefs.getBoolean("app_tints",true)?"вкл":"выкл"),"Блик на баннерах: "+(a.prefs.getBoolean("banner_shine",true)?"вкл":"выкл")},(d,n)->{if(n==0){CurrencyWidget.menu(a);return;}if(n==1){a.backgroundSettings();return;}String key=new String[]{"","","design","clock24","rates_chart","app_tints","banner_shine"}[n];a.prefs.edit().putBoolean(key,!a.prefs.getBoolean(key,true)).apply();a.updateTime();a.screen.stopShine();a.screen.invalidate();}).setNegativeButton("Назад",null).show();}
 static void capabilities(MainActivity a){StringBuilder s=new StringBuilder("Android "+android.os.Build.VERSION.RELEASE+" · API "+android.os.Build.VERSION.SDK_INT+"\nRoot для лаунчера не требуется.\n");
  s.append("CPU: ").append(android.os.Build.HARDWARE).append(" · доступно ядер: ").append(Runtime.getRuntime().availableProcessors()).append("\nABI: ").append(android.text.TextUtils.join(", ",android.os.Build.SUPPORTED_ABIS)).append("\n");
  s.append(a.stats.cpuPercent>=0?"Общая загрузка CPU: "+a.stats.cpuPercent+"%":"Прошивка не предоставляет общую загрузку CPU приложению.").append("\n");
  s.append("Распознавание речи: ").append(android.speech.SpeechRecognizer.isRecognitionAvailable(a)?"служба найдена (микрофон проверяется отдельно)":"нет доступной службы").append("\n");
  try{s.append("TV Input: ").append(((android.media.tv.TvInputManager)a.getSystemService(Context.TV_INPUT_SERVICE)).getTvInputList().size()).append("\n");}catch(Exception e){s.append("TV Input недоступен\n");}
  s.append("Системная заставка: ").append(new Intent("android.settings.DREAM_SETTINGS").resolveActivity(a.getPackageManager())!=null?"настройки доступны":"используйте настройки производителя").append("\n");
  s.append("API: ").append(PreviewProfile.configured(a)?"настроен; сеть проверяется запросом":"не настроен").append("\n\nАппаратный Home/голос, сон и 4K зависят от прошивки. Службы доступности включаются вручную. Питание остаётся системным. VPN: открытие приложения и фактический индикатор, без универсальной команды переключения.");
  new LauncherDialogs.Builder(a).setTitle("Возможности").setMessage(s.toString()).setPositiveButton("Закрыть",null).show();
 }
 static void configure(MainActivity a){LinearLayout box=new LinearLayout(a);box.setOrientation(1);box.setPadding(24,12,24,12);EditText url=new EditText(a),api=new EditText(a),weather=new EditText(a);url.setHint("https://ваш-сервер/tv-api/v1/");url.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);api.setHint("Токен устройства · API");weather.setHint("Токен устройства · погода");for(EditText v:new EditText[]{url,api,weather}){v.setSingleLine(true);box.addView(v);}api.setInputType(129);weather.setInputType(129);
  try{url.setText(ApiClient.privateJson(a,"api-client.json").getString("base_url"));}catch(Exception ignored){}
  new android.app.AlertDialog.Builder(a).setTitle("Подключение сервисов").setMessage("Здесь только адрес и отдельные токены ТВ. Ключи OpenAI / YouTube / TMDB остаются на сервере. Можно также импортировать через авторизованный ADB без root.").setView(box).setPositiveButton("Сохранить",(d,n)->{try{PreviewApiConfigProvider.configure(a,new JSONObject().put("version",1).put("base_url",url.getText().toString().trim()).put("api_token",api.getText().toString()).put("weather_token",weather.getText().toString()).toString());a.weatherGeneration++;a.weatherAt=-1;Toast.makeText(a,"Подключение сохранено",0).show();}catch(Exception e){Toast.makeText(a,"Нужны HTTPS-адрес /tv-api/v1/ и два токена устройства",1).show();}}).setNegativeButton("Отмена",null).show();
 }
}
