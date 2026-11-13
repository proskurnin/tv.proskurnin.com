package local.proskurnin.preview;

/** One short or held action per physical press; no Android or device assumptions. */
final class MiPressGesture {
 static final int NONE=0, SHORT=1, LONG=2;
 private boolean pressed,held;
 private int device;
 private long downTime;
 boolean down(int id,long time,int repeat){
  if(repeat!=0||pressed&&device==id&&downTime==time)return false;
  pressed=true;held=false;device=id;downTime=time;return true;
 }
 int hold(){if(!pressed||held)return NONE;held=true;return LONG;}
 int up(int id,long time,boolean canceled){
  if(!pressed||device!=id||downTime!=time)return NONE;
  int action=!canceled&&!held?SHORT:NONE;reset();return action;
 }
 void reset(){pressed=false;held=false;}
}
