package local.proskurnin.preview;
public class CurrencyConfigTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  check(CurrencyConfig.parse(null).size()==4);check(CurrencyConfig.parse("").isEmpty());
  check(CurrencyConfig.parse("USD:RUB,USD:RUB,RUB:RUB,INVALID:USD,ETH:EUR").toString().equals("[USD:RUB, ETH:EUR]"));
  check(CurrencyConfig.parse("BTC:USD,EUR:RUB,CNY:USD,ETH:EUR,SOL:USD").size()==4);
  check(!CurrencyConfig.key("BTC:RUB","Coinbase").equals(CurrencyConfig.key("BTC:USD","Coinbase")));
  check(!CurrencyConfig.key("USD:RUB","CBR").equals(CurrencyConfig.key("USD:RUB","Coinbase")));
  check(CurrencyConfig.delta(.0001,.5,"₽").equals("▲ +0,0001 ₽"));check(CurrencyConfig.delta(0,.5,"₽").equals("—"));
  check(CurrencyConfig.symbol("RUB").equals("₽"));System.out.println("CurrencyConfigTest passed");
 }
}
