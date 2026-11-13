package local.proskurnin.preview;
public class MiPressGestureTest {
 static void check(boolean ok,String name){if(!ok)throw new AssertionError(name);}
 public static void main(String[] args){
  MiPressGesture g=new MiPressGesture();
  check(g.up(1,10,false)==0,"orphan release");
  check(!g.down(1,10,1),"orphan repeat");check(g.hold()==0,"repeat does not arm");
  check(g.down(1,20,0),"short starts");check(!g.down(1,20,0),"duplicate down");
  check(g.up(2,20,false)==0,"different device cannot release");
  check(g.up(1,20,false)==1,"short once");check(g.up(1,20,false)==0,"duplicate release");
  g.down(1,30,0);check(g.hold()==2,"hold fires");check(g.hold()==0,"hold once");
  check(g.up(1,30,false)==0,"long has no short on release");
  g.down(1,40,0);check(g.up(1,40,true)==0,"cancelled press");check(g.hold()==0,"cancel removes hold");
  g.down(1,50,0);g.reset();check(g.hold()==0,"service reset cancels");
  g.down(1,60,0);check(g.down(1,70,0),"recover from missing release");
  check(g.up(1,60,false)==0,"stale release ignored");check(g.up(1,70,false)==1,"new press preserved");
  System.out.println("MiPressGesture: passed");
 }
}
