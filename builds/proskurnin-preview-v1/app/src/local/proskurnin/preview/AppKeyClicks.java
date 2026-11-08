package local.proskurnin.preview;
/** Pure timing state machine. Results: 0=wait, 1=single, 2=double. */
final class AppKeyClicks {
 static final long WINDOW=450,HOLD=650;
 long deadline=-1,started;boolean down,second;
 int press(long now){if(down)return 0;int prior=deadline>=0&&now>deadline?1:0;second=deadline>=0&&now<=deadline;deadline=-1;down=true;started=now;return prior;}
 int release(long now,boolean canceled,boolean doubleEnabled){if(!down)return 0;down=false;if(canceled){clear();return 0;}if(second){int result=now-started<HOLD?2:1;clear();return result;}if(!doubleEnabled||now-started>=HOLD){clear();return 1;}deadline=now+WINDOW;return 0;}
 int expire(long now){if(!down&&deadline>=0&&now>=deadline){clear();return 1;}return 0;}
 void clear(){deadline=-1;started=0;down=false;second=false;}
}
