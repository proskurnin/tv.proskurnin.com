package local.proskurnin.preview;
import android.graphics.*;
/** Original, uniform outline symbols in a 40 x 40 coordinate space. */
final class WeatherIcon {
 static void inline(Canvas c,int kind,boolean night,float x,float baseline,float size,int color,Paint text,String word){
  Rect bounds=new Rect();text.getTextBounds(word,0,word.length(),bounds);
  // The plain cloud occupies y≈5..25, unlike rain/snow symbols using the whole box.
  float center=kind==WeatherState.CLOUD?15:kind==WeatherState.PARTLY?17:20;
  draw(c,kind,night,x,baseline+(bounds.top+bounds.bottom)/2f-center*size/40f,size,color);
 }
 static void draw(Canvas c,int kind,boolean night,float x,float y,float size,int color){
  Paint p=new Paint(Paint.ANTI_ALIAS_FLAG);p.setColor(color);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(2);p.setStrokeCap(Paint.Cap.ROUND);p.setStrokeJoin(Paint.Join.ROUND);c.save();c.translate(x,y);c.scale(size/40,size/40);
  if(kind==WeatherState.CLEAR){sunMoon(c,p,night,20,20,8);}
  else if(kind==WeatherState.WIND){wind(c,p);}
  else if(kind==WeatherState.UNKNOWN){c.drawCircle(20,20,13,p);p.setStyle(Paint.Style.FILL);c.drawCircle(20,20,2,p);}
  else{
   if(kind==WeatherState.PARTLY){sunMoon(c,p,night,13,12,5);c.save();c.translate(4,7);c.scale(.83f,.83f);cloud(c,p);c.restore();}
   else{cloud(c,p);}
   if(kind==WeatherState.FOG){c.drawLine(6,29,33,29,p);c.drawLine(10,34,29,34,p);}
   if(kind==WeatherState.RAIN||kind==WeatherState.ICE){for(int i=0;i<3;i++)c.drawLine(11+i*9,28,8+i*9,34,p);}
   if(kind==WeatherState.DRIZZLE){p.setStyle(Paint.Style.FILL);for(int i=0;i<3;i++)c.drawCircle(10+i*10,31,1.5f,p);p.setStyle(Paint.Style.STROKE);}
   if(kind==WeatherState.SNOW||kind==WeatherState.ICE){for(int i=0;i<(kind==WeatherState.ICE?1:3);i++){float sx=kind==WeatherState.ICE?31:10+i*10,sy=33;c.drawLine(sx-2,sy,sx+2,sy,p);c.drawLine(sx,sy-2,sx,sy+2,p);c.drawLine(sx-1.5f,sy-1.5f,sx+1.5f,sy+1.5f,p);}}
   if(kind==WeatherState.STORM||kind==WeatherState.STORM_HAIL){Path bolt=new Path();bolt.moveTo(21,25);bolt.lineTo(16,31);bolt.lineTo(22,31);bolt.lineTo(18,38);c.drawPath(bolt,p);if(kind==WeatherState.STORM_HAIL){c.drawCircle(9,32,2,p);c.drawCircle(30,32,2,p);}}
   if(kind==WeatherState.HAIL){for(int i=0;i<3;i++)c.drawCircle(10+i*10,32,2,p);}
  }
  c.restore();
 }
 static void cloud(Canvas c,Paint p){Path a=new Path();a.moveTo(10,24);a.cubicTo(1,24,1,13,10,13);a.cubicTo(11,2,28,1,30,14);a.cubicTo(39,13,40,24,31,24);a.close();c.drawPath(a,p);}
 static void sunMoon(Canvas c,Paint p,boolean night,float x,float y,float r){if(night){Path m=new Path();m.moveTo(x+r*.3f,y-r);m.cubicTo(x-r*1.5f,y-r,x-r*1.5f,y+r,x+r*.4f,y+r);m.cubicTo(x-r*.4f,y+r*.2f,x-r*.4f,y-r*.2f,x+r*.3f,y-r);c.drawPath(m,p);}else{c.drawCircle(x,y,r,p);for(int i=0;i<8;i++){double a=i*Math.PI/4;c.drawLine(x+(float)Math.cos(a)*(r+4),y+(float)Math.sin(a)*(r+4),x+(float)Math.cos(a)*(r+7),y+(float)Math.sin(a)*(r+7),p);}}}
 static void wind(Canvas c,Paint p){Path a=new Path();a.moveTo(5,14);a.lineTo(25,14);a.cubicTo(34,14,34,3,26,5);c.drawPath(a,p);a.reset();a.moveTo(3,21);a.lineTo(30,21);a.cubicTo(40,21,38,32,30,30);c.drawPath(a,p);c.drawLine(7,28,20,28,p);}
}
