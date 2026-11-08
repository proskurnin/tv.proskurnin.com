package local.proskurnin.preview;
public class RatesSparklineTest { public static void main(String[] args){
 if(RatesSparkline.normalize(new double[]{1,2,3,4,5,6,7})[6]!=0)throw new AssertionError("up");
 if(RatesSparkline.normalize(new double[]{7,6,5,4,3,2,1})[6]!=1)throw new AssertionError("down");
 if(RatesSparkline.normalize(new double[]{2,2,2,2,2,2,2})[3]!=.5f)throw new AssertionError("flat");
 if(RatesSparkline.normalize(new double[]{2,2,2,Double.NaN,2,2,2})!=null)throw new AssertionError("gap");
 if(RatesSparkline.normalize(new double[]{2,2,2,0,2,2,2})!=null)throw new AssertionError("invalid");
 System.out.println("Sparkline normalization PASS");}}
