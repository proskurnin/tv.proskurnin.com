package local.proskurnin.preview;
import java.util.*;
public class Home137Test {
 static void ok(boolean v){if(!v)throw new AssertionError();}
 public static void main(String[] args){
 TimeZone.setDefault(TimeZone.getTimeZone("Europe/Moscow"));long t=WeatherTimestamp.wttr("2026-11-09 12:30 AM");ok(WeatherTimestamp.format(t).equals("09.11.2026 00:30"));ok(WeatherTimestamp.wttr("invalid")==0);ok(WeatherTimestamp.label(t,t+7200000,true).contains("00:30"));ok(!WeatherTimestamp.label(t,t+7200000,true).contains("02:30"));
 ok(MovieRecall.requested("Фильм про путешествия во времени, который я смотрел на прошлой неделе"));ok(MovieRecall.requested("Забыл название фильма про море"));ok(MovieRecall.requested("Хочу пересмотреть старый фильм"));ok(!MovieRecall.requested("Фильмы которые я не смотрел"));ok(!MovieRecall.requested("Фильмы про черепах"));
 ok(ClockEstimate.due(100,200,300000));System.out.println("Weather dates, recall vs unseen, clock rollback retry: PASS");
 }
}
