package local.proskurnin.preview;

import android.content.*;
import android.content.pm.PackageManager;
import android.media.tv.*;
import java.util.*;
import org.json.JSONArray;

/** Isolated ordinary Activity: no Home, boot receiver, accessibility or dream components. */
final class PreviewProfile {
 static boolean enabled(Context c){try{return c.getPackageManager().getApplicationInfo(c.getPackageName(),PackageManager.GET_META_DATA).metaData.getBoolean("proskurnin.preview_only",false);}catch(Exception ignored){return false;}}
 static boolean configured(Context c){try{ApiClient.privateJson(c,PreviewApiConfigProvider.FILE).getJSONObject("api").getString("token");return true;}catch(Exception ignored){return false;}}
 static void initialize(MainActivity a){
  if(!enabled(a))return;
  SharedPreferences.Editor e=a.prefs.edit();
  for(String key:new String[]{"boot_home","voice_key_enabled","power_menu","vpn_button"})e.putBoolean(key,false);
  if(!a.prefs.getBoolean("preview_api_ui",false))e.putBoolean("ai_enabled",true).putBoolean("youtube_enabled",true).putBoolean("preview_api_ui",true);
  if(!configured(a))e.putBoolean("weather_server",false);
  if(!a.prefs.getBoolean("preview_initialized",false)){
   String[][] choices={{"ru.more.play","tv.okko.androidtv"},{"ru.kinopoisk.tv"},{"ru.ivi.client"},{"org.smarttube.stable","com.liskovsoft.smarttubetv.beta","com.google.android.youtube.tv"},{"mobi.zona"},{"com.lazycatsoftware.lmd"}};
   JSONArray favorites=new JSONArray();
   for(String[] slot:choices)for(String pkg:slot)if(a.getPackageManager().getLeanbackLaunchIntentForPackage(pkg)!=null||a.getPackageManager().getLaunchIntentForPackage(pkg)!=null){favorites.put(pkg);break;}
   e.putString("favorites",favorites.toString()).putBoolean("preview_initialized",true);
  }
  e.apply();
 }
 static void settings(MainActivity a){
  new LauncherDialogs.Builder(a).setCustomTitle(a.versionTitle("Предпросмотр Xiaomi")).setItems(new String[]{"Фон лаунчера","Приложения главного экрана","Погода · Москва","Часы: "+(a.prefs.getBoolean("clock24",true)?"24 часа":"12 часов"),"Графики валют: "+(a.prefs.getBoolean("rates_chart",true)?"вкл":"выкл"),"Цветные подложки: "+(a.prefs.getBoolean("app_tints",true)?"вкл":"выкл"),"Открыть штатный главный экран","О предпросмотре","Счётчик YouTube","Что посмотрим?","Давайте поговорим","Значок AI: "+(a.prefs.getBoolean("ai_enabled",true)?"вкл":"выкл")},(d,n)->{
   if(n==0)a.backgroundSettings();
   else if(n==1)a.chooseFavoriteSlot();
   else if(n==2)a.weatherSettings();
   else if(n>=3&&n<=5){String key=n==3?"clock24":n==4?"rates_chart":"app_tints";a.prefs.edit().putBoolean(key,!a.prefs.getBoolean(key,true)).apply();a.updateTime();if(n==4){a.ratesAttempt=0;a.fetchRates();}a.screen.invalidate();}
   else if(n==6){a.openIntent(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));a.finish();}
   else if(n==8)a.youtubeSettings();
   else if(n==9)a.startActivity(new Intent(a,MovieActivity.class));
   else if(n==10)a.startActivity(new Intent(a,AssistantActivity.class));
   else if(n==11){a.prefs.edit().putBoolean("ai_enabled",!a.prefs.getBoolean("ai_enabled",true)).apply();a.topIndex=Math.min(a.topIndex,a.quickCount()-1);a.screen.invalidate();}
   else new LauncherDialogs.Builder(a).setTitle("Proskurnin TV · Preview").setMessage("Отдельное приложение Full HD. Home, питание, Bluetooth и системная заставка остаются у телевизора.\n\nВсе приложения — стрелка вниз. Долгий OK — вспомогательное меню.\n\nAPI: "+(configured(a)?"настройки подключения сохранены":"подключение ещё не настроено")+". Для YouTube и AI нужен доступ к нашему серверу; ключи сервисов остаются на сервере.\n\nAI-подбор — значок ✦; диалог — долгий OK на ✦ или пункт настроек. Кнопка «Голос» внутри AI использует разрешение микрофона; аппаратный помощник не переназначен.\n\nВыход: Home или Back. Удаление: настройки приложений → Proskurnin TV · Preview.").setPositiveButton("Закрыть",null).show();
  }).setNegativeButton("Закрыть",null).show();
 }
 static void sources(MainActivity a){
  ArrayList<String> labels=new ArrayList<>();ArrayList<Intent> intents=new ArrayList<>();
  try{TvInputManager manager=(TvInputManager)a.getSystemService(Context.TV_INPUT_SERVICE);for(TvInputInfo input:manager.getTvInputList()){
   if(!input.isPassthroughInput()||input.isHidden(a))continue;
   Intent intent=new Intent(Intent.ACTION_VIEW,TvContract.buildChannelUriForPassthroughInput(input.getId()));
   if(intent.resolveActivity(a.getPackageManager())!=null){CharSequence label=input.loadCustomLabel(a);if(label==null)label=input.loadLabel(a);labels.add(label==null?"Внешний источник":label.toString());intents.add(intent);}
  }}catch(RuntimeException ignored){}
  Intent live=new Intent(Intent.ACTION_VIEW,TvContract.Channels.CONTENT_URI);
  if(live.resolveActivity(a.getPackageManager())==null)live=a.getPackageManager().getLeanbackLaunchIntentForPackage("com.mediatek.wwtv.tvcenter");
  if(live!=null){labels.add("Live TV / телеканалы");intents.add(live);}
  if(labels.isEmpty()){new LauncherDialogs.Builder(a).setTitle("Источники").setMessage("Используйте штатную кнопку источников на пульте. Доступный экран источников не найден.").setPositiveButton("Закрыть",null).show();return;}
  new LauncherDialogs.Builder(a).setTitle("Источники телевизора").setItems(labels.toArray(new String[0]),(d,n)->a.openIntent(intents.get(n))).setNegativeButton("Закрыть",null).show();
 }
}
