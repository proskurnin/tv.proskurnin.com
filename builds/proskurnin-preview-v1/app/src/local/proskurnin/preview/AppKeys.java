package local.proskurnin.preview;
import android.content.*;import android.content.pm.*;import android.view.*;import android.widget.Toast;import java.util.*;import java.security.*;
final class AppKeys {
 static final String[] NAMES={"ОККО","Кинопоиск","Wink","RUTUBE"};
 static final String[] DEFAULTS={"tv.okko.androidtv","ru.kinopoisk.tv","ru.rt.video.app.tv","ru.rutube.app"};
 static SharedPreferences prefs(Context c){return c.getSharedPreferences("preview",0);}
 static String key(int slot,String kind){return "appkey_"+slot+"_"+kind;}
 static boolean enabled(Context c){return prefs(c).getBoolean("appkeys_enabled",true);}
 static String action(Context c,int slot,boolean twice){return prefs(c).getString(key(slot,twice?"double":"single"),twice?"none":"app:"+DEFAULTS[slot]);}
 static boolean eligible(int key){return key>=KeyEvent.KEYCODE_F1&&key<=KeyEvent.KEYCODE_F12&&key!=KeyEvent.KEYCODE_F9||key>=KeyEvent.KEYCODE_PROG_RED&&key<=KeyEvent.KEYCODE_PROG_BLUE;}
 static String identity(KeyEvent e){InputDevice d=e.getDevice();if(d==null||d.isVirtual()||!eligible(e.getKeyCode()))return "";try{byte[] hash=MessageDigest.getInstance("SHA-256").digest(d.getDescriptor().getBytes("UTF-8"));StringBuilder b=new StringBuilder();for(byte v:hash)b.append(String.format(Locale.US,"%02x",v&255));return b+":"+e.getScanCode()+":"+e.getKeyCode();}catch(Exception ex){return "";}}
 static int slot(Context c,String id){if(id.isEmpty())return -1;for(int i=0;i<4;i++)if(id.equals(prefs(c).getString(key(i,"binding"),"")))return i;return -1;}
 static String label(Context c,String value){switch(value){case "none":return "Ничего";case "home":return "Главный экран";case "movies":return "Подбор фильма · голос";case "chat":return "Диалог AI · голос";case "sources":return "Источники";case "settings":return "Настройки ТВ";default:if(value.startsWith("app:")){String pkg=value.substring(4);try{return c.getPackageManager().getApplicationLabel(c.getPackageManager().getApplicationInfo(pkg,0)).toString();}catch(Exception e){for(int i=0;i<4;i++)if(pkg.equals(DEFAULTS[i]))return NAMES[i]+" · не установлено";return "Приложение не установлено";}}return "Недоступно";}}
 static void run(Context c,String value){if(value.equals("none"))return;Intent intent=null;try{
  switch(value){case "home":intent=new Intent(c,MainActivity.class).setAction(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME);break;
   case "movies":case "chat":if(!prefs(c).getBoolean("ai_enabled",true)){Toast.makeText(c,"AI выключен в настройках лаунчера",0).show();return;}intent=new Intent(c,value.equals("chat")?AssistantActivity.class:MovieActivity.class).putExtra("auto_voice",true).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);break;
   case "sources":intent=new Intent("com.android.tv.action.VIEW_INPUTS");break;
   case "settings":intent=new Intent("android.settings.SETTINGS");break;
   default:if(value.startsWith("app:")){String pkg=value.substring(4);intent=c.getPackageManager().getLeanbackLaunchIntentForPackage(pkg);if(intent==null)intent=c.getPackageManager().getLaunchIntentForPackage(pkg);}}
  if(intent==null||intent.resolveActivity(c.getPackageManager())==null){Toast.makeText(c,"Приложение или действие недоступно. Измените назначение кнопки.",0).show();return;}c.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
 }catch(Exception e){Toast.makeText(c,"Не удалось выполнить действие кнопки",0).show();}}
 static LinkedHashMap<String,String> apps(Context c){Map<String,String> found=new HashMap<>();for(String category:new String[]{Intent.CATEGORY_LEANBACK_LAUNCHER,Intent.CATEGORY_LAUNCHER})for(ResolveInfo r:c.getPackageManager().queryIntentActivities(new Intent(Intent.ACTION_MAIN).addCategory(category),0))found.put(r.activityInfo.packageName,r.loadLabel(c.getPackageManager()).toString());List<String> packages=new ArrayList<>(found.keySet());java.text.Collator collator=java.text.Collator.getInstance(new Locale("ru"));Collections.sort(packages,(a,b)->{int n=collator.compare(found.get(a),found.get(b));return n==0?a.compareTo(b):n;});LinkedHashMap<String,String> result=new LinkedHashMap<>();for(String pkg:packages)result.put(pkg,found.get(pkg));return result;}
}
