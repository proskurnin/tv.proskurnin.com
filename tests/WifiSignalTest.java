package local.proskurnin.preview;
public class WifiSignalTest {
 public static void main(String[] args){
  if(WifiSignal.level(-127)!=-1||WifiSignal.level(0)!=-1)throw new AssertionError("Unknown readings must not show full signal");
  if(WifiSignal.level(-39)!=4||WifiSignal.level(-77)!=2||WifiSignal.level(-110)!=0)throw new AssertionError("Strong, medium, weak");
  int lit=0;for(int arc=1;arc<=4;arc++)if(WifiSignal.lit(WifiSignal.level(-77),arc))lit++;
  if(lit!=2)throw new AssertionError("Exactly two of four arcs for medium signal");
  System.out.println("WifiSignalTest passed");
 }
}
