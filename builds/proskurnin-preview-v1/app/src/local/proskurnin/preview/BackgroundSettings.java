package local.proskurnin.preview;

import android.app.Activity;
import android.content.SharedPreferences;
import java.io.*;
import java.util.*;

/** Local static-image packs. No network, system settings or DreamService changes. */
final class BackgroundSettings {
 static final String[] PACKS={"classic","mountains","sea","twohour"};
 static final String[] PACK_NAMES={"Прежние пейзажи","Горы и озёра","Море","Один пейзаж · каждые 2 часа"};
 static final String[] PERIOD_NAMES={"Утро","День","Вечер","Ночь"};
 final Activity owner;final SharedPreferences prefs;final Runnable changed;
 BackgroundSettings(Activity a,SharedPreferences p,Runnable c){owner=a;prefs=p;changed=c;}
 static int[] hours(SharedPreferences p){int[] h=new int[4];for(int i=0;i<4;i++)h[i]=p.getInt("background_hour_"+i,BackgroundConfig.DEFAULT_HOURS[i]);return BackgroundConfig.validHours(h)?h:BackgroundConfig.DEFAULT_HOURS.clone();}
 static String packName(SharedPreferences p){String id=BackgroundConfig.pack(p.getString("background_pack","classic"));for(int i=0;i<PACKS.length;i++)if(PACKS[i].equals(id))return PACK_NAMES[i];return PACK_NAMES[0];}
 boolean alive(){return !owner.isFinishing()&&!owner.isDestroyed();}
 void save(){changed.run();show();}
 void show(){if(!alive())return;String mode=BackgroundConfig.mode(prefs.getString("background_mode","auto"));String modeName="twohour".equals(prefs.getString("background_pack",""))?"Каждые 2 часа · 00:00–22:00":"По времени суток";for(int i=0;i<4;i++)if(BackgroundConfig.PERIODS[i].equals(mode))modeName="Всегда · "+PERIOD_NAMES[i];
  new LauncherDialogs.Builder(owner).setTitle("Фон лаунчера").setItems(new String[]{
   "Изображение: "+(prefs.getBoolean("background",true)?"включено":"выключено · однотонный фон"),
   "Набор: "+packName(prefs),"Режим: "+modeName,"Расписание переключения…",
   "Затемнение: "+BackgroundConfig.dim(prefs.getInt("background_dim",69))+"%",
   "Плавная смена: "+(prefs.getBoolean("background_fade",true)?"вкл · 30 FPS":"выкл"),
   "Авторы фотографий и лицензии","Вернуть прежний фон и настройки"},(d,n)->{
    if(n==0){prefs.edit().putBoolean("background",!prefs.getBoolean("background",true)).apply();save();}
    else if(n==1)choosePack();else if(n==2)chooseMode();else if(n==3){if("twohour".equals(prefs.getString("background_pack","")))new LauncherDialogs.Builder(owner).setTitle("Каждые два часа").setMessage("Смена в 00:00, 02:00, 04:00 … 22:00 по местному времени ТВ. После включения сразу выбирается текущий кадр. Интернет не нужен.").setPositiveButton("Назад",(dd,nn)->show()).show();else schedule();}else if(n==4)dim();
    else if(n==5){prefs.edit().putBoolean("background_fade",!prefs.getBoolean("background_fade",true)).apply();save();}
    else if(n==6)credits();else reset();
   }).setNegativeButton("Закрыть",null).show();
 }
 void choosePack(){String current=BackgroundConfig.pack(prefs.getString("background_pack","classic"));String[] labels=new String[PACKS.length];for(int i=0;i<PACKS.length;i++)labels[i]=(PACKS[i].equals(current)?"✓ ":"")+PACK_NAMES[i]+(i==3&&!LocalBackground.available(owner)?" · набор не загружен":" · на ТВ");
  new LauncherDialogs.Builder(owner).setTitle("Набор фонов · работают без сети").setItems(labels,(d,n)->{if(n==3){chooseSeries();return;}SharedPreferences.Editor e=prefs.edit().putString("background_pack",PACKS[n]).putBoolean("background",true);e.apply();save();}).setOnCancelListener(d->show()).setNegativeButton("Назад",(d,n)->show()).show();
 }
 void chooseSeries(){String[] ids={"big-sur","golden-gate","tahoe-2026"},names={"Big Sur","Golden Gate","Tahoe 2026"};String current=BackgroundConfig.series(prefs.getString("background_series","big-sur"));String[] labels=new String[ids.length];for(int i=0;i<ids.length;i++)labels[i]=(ids[i].equals(current)?"✓ ":"")+names[i]+(LocalBackground.available(owner,ids[i])?"":" · не загружен");
  new LauncherDialogs.Builder(owner).setTitle("Серия · смена каждые 2 часа").setItems(labels,(d,n)->{if(!LocalBackground.available(owner,ids[n])){new LauncherDialogs.Builder(owner).setTitle("Серия не загружена").setMessage("Для выбора нужны все 12 кадров этой серии. Текущий фон останется без изменений.").setPositiveButton("Назад",(dd,nn)->chooseSeries()).show();return;}prefs.edit().putString("background_series",ids[n]).putString("background_pack","twohour").putString("background_mode","auto").putBoolean("background",true).apply();save();}).setOnCancelListener(d->choosePack()).setNegativeButton("Назад",(d,n)->choosePack()).show();
 }
 void chooseMode(){String[] modes={"auto","morning","day","evening","night"};String[] names={"twohour".equals(prefs.getString("background_pack",""))?"Каждые 2 часа":"По времени суток","Всегда утро","Всегда день","Всегда вечер","Всегда ночь"};String current=BackgroundConfig.mode(prefs.getString("background_mode","auto"));for(int i=0;i<5;i++)if(modes[i].equals(current))names[i]="✓ "+names[i];
  new LauncherDialogs.Builder(owner).setTitle("Режим фона").setItems(names,(d,n)->{prefs.edit().putString("background_mode",modes[n]).apply();save();}).setOnCancelListener(d->show()).setNegativeButton("Назад",(d,n)->show()).show();
 }
 void schedule(){int[] h=hours(prefs);String[] labels=new String[4];for(int i=0;i<4;i++)labels[i]=PERIOD_NAMES[i]+" начинается в "+String.format(Locale.ROOT,"%02d:00",h[i]);
  new LauncherDialogs.Builder(owner).setTitle("Расписание · системное время ТВ").setItems(labels,(d,n)->chooseHour(n)).setOnCancelListener(d->show()).setNegativeButton("Назад",(d,n)->show()).show();
 }
 void chooseHour(int index){int[] current=hours(prefs);int min=index==0?0:current[index-1]+1,max=index==3?23:current[index+1]-1;String[] names=new String[max-min+1];for(int i=min;i<=max;i++)names[i-min]=(current[index]==i?"✓ ":"")+String.format(Locale.ROOT,"%02d:00",i);final int start=min;
  new LauncherDialogs.Builder(owner).setTitle(PERIOD_NAMES[index]+" · начало").setItems(names,(d,n)->{prefs.edit().putInt("background_hour_"+index,start+n).apply();changed.run();schedule();}).setOnCancelListener(d->schedule()).setNegativeButton("Назад",(d,n)->schedule()).show();
 }
 void dim(){int[] values={0,20,35,50,60,69,75,85};String[] labels=new String[values.length];int current=BackgroundConfig.dim(prefs.getInt("background_dim",69));for(int i=0;i<values.length;i++)labels[i]=(current==values[i]?"✓ ":"")+values[i]+"%"+(values[i]==69?" · как сейчас по умолчанию":"");
  new LauncherDialogs.Builder(owner).setTitle("Затемнение фона").setItems(labels,(d,n)->{prefs.edit().putInt("background_dim",values[n]).apply();save();}).setOnCancelListener(d->show()).setNegativeButton("Назад",(d,n)->show()).show();
 }
 void credits(){String text="Фотографии загружены заранее и доступны без интернета. Новые наборы: Wikimedia Commons; лицензии и авторы ниже. При отображении применяется кадрирование 16:9 и затемнение.\n\n";
  try(BufferedReader r=new BufferedReader(new InputStreamReader(owner.getAssets().open("backgrounds/CREDITS.txt"),"UTF-8"))){String line;while((line=r.readLine())!=null)text+=line+"\n";}catch(IOException e){text+="Не удалось прочитать сведения об авторах.";}
  text+="\n"+LocalBackground.credits(owner);
  new LauncherDialogs.Builder(owner).setTitle("Авторы фотографий").setMessage(text).setOnCancelListener(d->show()).setPositiveButton("Назад",(d,n)->show()).show();
 }
 void reset(){new LauncherDialogs.Builder(owner).setTitle("Вернуть прежние фоны?").setMessage("Прежние пейзажи, автоматическая смена в 06:00 / 11:00 / 17:00 / 22:00, затемнение 69%, плавный переход. Остальные настройки лаунчера сохранятся.").setPositiveButton("Вернуть",(d,n)->{SharedPreferences.Editor e=prefs.edit().putBoolean("background",true).remove("background_pack").remove("background_mode").remove("background_dim").remove("background_fade");for(int i=0;i<4;i++)e.remove("background_hour_"+i);e.apply();save();}).setOnCancelListener(d->show()).setNegativeButton("Отмена",(d,n)->show()).show();}
}
