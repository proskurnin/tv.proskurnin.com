package local.proskurnin.preview;
import java.util.*;import java.text.*;
final class RatesTrend {
 static String yesterday(long now){Calendar c=Calendar.getInstance(TimeZone.getTimeZone("UTC"));c.setTimeInMillis(now);c.add(Calendar.DAY_OF_MONTH,-1);SimpleDateFormat f=new SimpleDateFormat("yyyy-MM-dd",Locale.US);f.setTimeZone(TimeZone.getTimeZone("UTC"));return f.format(c.getTime());}
 static double absolute(double current,double previous){if(!Double.isFinite(current)||!Double.isFinite(previous)||current<=0||previous<=0)return Double.NaN;return current-previous;}
 static String label(double delta,String currency){if(!Double.isFinite(delta))return "— нет сравнения";if(Math.abs(delta)<0.005)return "—";return (delta>0?"▲ +":"▼ −")+String.format(new Locale("ru"),"%.2f",Math.abs(delta))+" "+currency;}
}
