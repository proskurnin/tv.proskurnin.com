package local.proskurnin.preview;
/** One listening window after a completed answer; never retries silence or errors. */
final class ConversationTurn {
 boolean enabled; private int epoch; private boolean waiting;
 void enable(){enabled=true;cancel();}
 void stop(){enabled=false;cancel();}
 void cancel(){epoch++;waiting=false;}
 int arm(){cancel();if(!enabled)return -1;waiting=true;return epoch;}
 boolean consume(int ticket){if(!enabled||!waiting||ticket!=epoch)return false;waiting=false;return true;}
 boolean waiting(){return waiting;}
}
