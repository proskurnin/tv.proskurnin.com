package local.proskurnin.preview;
import java.text.*;import java.util.*;
final class WeatherTimestamp {
 static String format(long at){return at>0?new SimpleDateFormat("dd.MM.yyyy HH:mm",new Locale("ru")).format(new Date(at)):"неизвестно";}
 static String label(long observed,long received,boolean cached){return observed>0?"Актуальность "+format(observed):"Актуальность неизвестна";}
 static long wttr(String value){try{SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd hh:mm a",Locale.US);f.setTimeZone(TimeZone.getTimeZone("Europe/Moscow"));f.setLenient(false);return f.parse(value).getTime();}catch(Exception e){return 0;}}
}
