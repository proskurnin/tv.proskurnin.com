package local.proskurnin.preview;
import java.time.*;import java.util.Locale;
/** Calendar periods use the TV's local date; old undated marks never acquire a date. */
final class WatchPeriod {
 final LocalDate from,to;
 WatchPeriod(LocalDate f,LocalDate t){from=f;to=t;}
 boolean contains(String date){try{LocalDate d=LocalDate.parse(date);return !d.isBefore(from)&&!d.isAfter(to);}catch(Exception e){return false;}}
 static WatchPeriod parse(String query,LocalDate today){
  String q=query.toLowerCase(new Locale("ru"));if(!MovieRecall.requested(q))return null;
  if(q.contains("позавчера"))return new WatchPeriod(today.minusDays(2),today.minusDays(2));
  if(q.contains("вчера"))return new WatchPeriod(today.minusDays(1),today.minusDays(1));
  if(q.contains("сегодня"))return new WatchPeriod(today,today);
  LocalDate monday=today.minusDays(today.getDayOfWeek().getValue()-1);
  if(q.contains("прошлой неделе")||q.contains("прошлую неделю"))return new WatchPeriod(monday.minusWeeks(1),monday.minusDays(1));
  if(q.contains("этой неделе")||q.contains("эту неделю"))return new WatchPeriod(monday,today);
  if(q.contains("последнюю неделю")||q.contains("последние 7 дней"))return new WatchPeriod(today.minusDays(6),today);
  if(q.contains("прошлом месяце")||q.contains("прошлый месяц")){LocalDate first=today.withDayOfMonth(1);return new WatchPeriod(first.minusMonths(1),first.minusDays(1));}
  return null;
 }
}
