package local.proskurnin.preview;
public final class AppKeyClicksTest {
 static void eq(int want,int got){if(want!=got)throw new AssertionError(want+" != "+got);}
 public static void main(String[] args){
  AppKeyClicks c=new AppKeyClicks();
  eq(0,c.press(0));eq(1,c.release(50,false,false));eq(0,c.expire(1000));
  eq(0,c.press(1000));eq(0,c.release(1050,false,true));eq(0,c.expire(1499));eq(1,c.expire(1500));eq(0,c.expire(1501));
  c.press(2000);c.release(2050,false,true);eq(0,c.press(2300));eq(2,c.release(2350,false,true));eq(0,c.expire(4000));
  c.press(5000);eq(0,c.press(5100));eq(1,c.release(5700,false,true));eq(0,c.release(5800,false,true));
  c.press(6000);eq(0,c.release(6050,true,true));eq(0,c.expire(7000));
  c.press(8000);c.release(8050,false,true);eq(1,c.press(8600));eq(0,c.release(8650,false,true));eq(1,c.expire(9100));
  c.press(10000);c.release(10050,false,true);c.press(10300);eq(1,c.release(11000,false,true));eq(0,c.expire(12000));
  c.press(13000);c.release(13050,false,true);c.clear();eq(0,c.expire(14000));
  c.press(15000);c.clear();eq(0,c.release(26000,false,true));
  System.out.println("AppKeyClicks: single, double, hold, repeats, cancellation, expiry and reset passed");
 }
}
