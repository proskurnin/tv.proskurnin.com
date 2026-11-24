package local.proskurnin.preview;
import java.time.LocalDate;
public class WatchPeriodTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){LocalDate now=LocalDate.of(2026,11,22);WatchPeriod p=WatchPeriod.parse("Что я смотрела на прошлой неделе",now);check(p.contains("2026-11-09")&&p.contains("2026-11-15"));check(!p.contains("2026-11-16")&&!p.contains("")&&!p.contains("2026-02-30"));p=WatchPeriod.parse("смотрел в прошлом месяце",LocalDate.of(2026,1,2));check(p.contains("2025-12-31")&&!p.contains("2026-01-01"));check(WatchPeriod.parse("фильмы про прошлую неделю",now)==null);check(WatchPeriod.parse("не смотрел вчера",now)==null);System.out.println("WatchPeriod: passed calendar boundaries and undated marks");}
}
