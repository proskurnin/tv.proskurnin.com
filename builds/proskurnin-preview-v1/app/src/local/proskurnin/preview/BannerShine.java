package local.proskurnin.preview;
import android.graphics.*;
/** Original vector rendering inspired by the locally saved PatchWall focus reference. */
final class BannerShine {
 private final Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
 private final Path clip=new Path();private final RectF bounds=new RectF();
 BannerShine(){paint.setShader(new LinearGradient(-110,0,110,0,new int[]{0x00ffffff,0x18ffffff,0x78ffffff,0x35ffffff,0x00ffffff},new float[]{0,.16f,.45f,.7f,1},Shader.TileMode.CLAMP));paint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.ADD));}
 void draw(Canvas canvas,float x,float y,float w,float h,float progress){
  if(progress<=0||progress>=1)return;
  int save=canvas.save();bounds.set(x,y,x+w,y+h);clip.reset();clip.addRoundRect(bounds,22,22,Path.Direction.CW);canvas.clipPath(clip);
  canvas.translate(x-160+(w+320)*progress,y-160+(h+320)*progress);canvas.rotate(45);canvas.drawRect(-110,-h*3,110,h*3,paint);canvas.restoreToCount(save);
 }
}
