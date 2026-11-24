package local.proskurnin.preview;
public class ConversationTurnTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){ConversationTurn t=new ConversationTurn();check(t.arm()==-1);t.enable();int a=t.arm();check(t.consume(a));check(!t.consume(a));a=t.arm();t.cancel();check(!t.consume(a));a=t.arm();t.stop();check(!t.consume(a));t.enable();int b=t.arm();check(!t.consume(a));check(t.consume(b));System.out.println("ConversationTurn: passed cancellation, single window, opt-in");}
}
