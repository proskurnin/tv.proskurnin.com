package local.proskurnin.preview;
import java.util.*;
final class CurrencyConfig {
 static final String DEFAULT="USD:RUB,EUR:RUB,CNY:RUB,BTC:USD";
 static final String[] BASES={"USD","EUR","CNY","GBP","CHF","JPY","AED","RUB","BTC","ETH","SOL"};
 static final String[] QUOTES={"RUB","USD","EUR"};
 static ArrayList<String> parse(String raw){ArrayList<String> out=new ArrayList<>();if(raw==null)raw=DEFAULT;for(String p:raw.split(",")){String[] v=p.split(":");if(v.length==2&&Arrays.asList(BASES).contains(v[0])&&Arrays.asList(QUOTES).contains(v[1])&&!v[0].equals(v[1])&&!out.contains(p)&&out.size()<4)out.add(p);}return out;}
 static String symbol(String c){switch(c){case "USD":return "$";case "EUR":return "€";case "CNY":case "JPY":return "¥";case "RUB":return "₽";case "GBP":return "£";case "BTC":return "₿";case "ETH":return "Ξ";case "SOL":return "◎";default:return c;}}
 static int precision(double value){return value<1?4:2;}
 static boolean neutral(double delta,double value){return !Double.isFinite(delta)||Math.abs(delta)<.5*Math.pow(10,-precision(value));}
 static String delta(double delta,double value,String quote){if(!Double.isFinite(delta))return "— нет сравнения";if(neutral(delta,value))return "—";return (delta>0?"▲ +":"▼ −")+String.format(new Locale("ru"),"%."+precision(value)+"f",Math.abs(delta))+" "+quote;}
 static String key(String pair,String source){return "cw_"+pair.replace(':','_')+"_"+source;}
}
