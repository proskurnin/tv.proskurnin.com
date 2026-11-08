package local.proskurnin.preview;
import android.service.dreams.DreamService;import android.media.MediaPlayer;import android.graphics.Color;import android.os.*;import android.view.*;import android.widget.*;import java.io.File;import java.util.*;

public class CachedDreamService extends DreamService implements SurfaceHolder.Callback {
 final Handler handler=new Handler();DreamCache cache;SurfaceView surface;TextView fallback;MediaPlayer player;boolean live=false,surfaceReady=false;String previous="";final Random random=new Random();
 final Runnable refresh=new Runnable(){public void run(){if(!live)return;if(getSharedPreferences("preview",0).getBoolean("dream_cache_update",true)){long age=System.currentTimeMillis()-getSharedPreferences("preview",0).getLong("dream_cache_refreshed",0);if(cache.ready().length<5||age>=300000||age<0)cache.sync(cache.ready().length<5,text->{});}handler.postDelayed(this,300000);}};
 public void onAttachedToWindow(){super.onAttachedToWindow();setFullscreen(true);setInteractive(true);setScreenBright(true);cache=new DreamCache(this);FrameLayout root=new FrameLayout(this);root.setBackgroundColor(Color.BLACK);fallback=new TextView(this);fallback.setTextColor(0xffb9c6d8);fallback.setTextSize(24);fallback.setGravity(Gravity.CENTER);fallback.setText("Proskurnin TV\nЛокальная заставка");surface=new SurfaceView(this);root.addView(surface,new FrameLayout.LayoutParams(-1,-1));root.addView(fallback,new FrameLayout.LayoutParams(-1,-1));surface.getHolder().addCallback(this);setContentView(root);}
 public void onDreamingStarted(){super.onDreamingStarted();if(!getSharedPreferences("preview",0).getBoolean("dream_cache_enabled",true)){finish();return;}live=true;if(surfaceReady)playNext();handler.postDelayed(refresh,2000);}
 public void surfaceCreated(SurfaceHolder h){surfaceReady=true;if(live)playNext();}
 public void surfaceChanged(SurfaceHolder h,int format,int w,int height){}
 public void surfaceDestroyed(SurfaceHolder h){surfaceReady=false;release();}
 void release(){if(player!=null){try{player.release();}catch(Exception ignored){}player=null;}DreamCache.playing="";}
 void playNext(){if(!live||!surfaceReady)return;release();File file=cache.choose(previous,random);if(file==null){fallback.setText("Нет загруженных роликов\nШестерёнка → Заставка → Кэш видео");fallback.setVisibility(View.VISIBLE);handler.postDelayed(()->{if(live)playNext();},3000);return;}previous=file.getName();final long start=SystemClock.elapsedRealtime();
  try{MediaPlayer p=new MediaPlayer();player=p;p.setDisplay(surface.getHolder());p.setDataSource(file.getPath());p.setVolume(0,0);p.setVideoScalingMode(MediaPlayer.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING);p.setOnPreparedListener(mp->{if(live&&player==mp)mp.start();});p.setOnInfoListener((mp,what,extra)->{if(what==MediaPlayer.MEDIA_INFO_VIDEO_RENDERING_START){fallback.setVisibility(View.GONE);android.util.Log.i("ProskurninDream","first_frame_ms="+(SystemClock.elapsedRealtime()-start)+" cached="+cache.ready().length);}return false;});p.setOnCompletionListener(mp->{if(live&&player==mp)playNext();});p.setOnErrorListener((mp,what,extra)->{release();fallback.setVisibility(View.VISIBLE);handler.postDelayed(()->{if(live)playNext();},2000);return true;});p.prepareAsync();}
  catch(Exception e){release();handler.postDelayed(()->{if(live)playNext();},2000);}
 }
 public boolean dispatchKeyEvent(KeyEvent e){if(e.getAction()==KeyEvent.ACTION_DOWN)wakeUp();return true;}
 public boolean dispatchTouchEvent(android.view.MotionEvent e){wakeUp();return true;}
 void stopAll(){live=false;handler.removeCallbacksAndMessages(null);release();if(cache!=null)cache.stop();}
 public void onDreamingStopped(){stopAll();super.onDreamingStopped();}
 public void onDetachedFromWindow(){stopAll();super.onDetachedFromWindow();}
}
