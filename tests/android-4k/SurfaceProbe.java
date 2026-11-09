package local.proskurnin.displayprobe;

import android.app.Activity;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PixelFormat;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.widget.FrameLayout;

/** Manual device diagnostic only. No permissions, Home registration or persistent settings. */
public final class SurfaceProbe extends Activity implements SurfaceHolder.Callback {
    private final Handler handler = new Handler();
    private String mode;
    private boolean resumed;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        mode = getIntent().getStringExtra("mode");
        if (!"rgb565".equals(mode) && !"tiles".equals(mode)) mode = "rgba";
        getWindow().setBackgroundDrawable(new android.graphics.drawable.ColorDrawable(Color.BLACK));
        getWindow().getDecorView().setSystemUiVisibility(5894);
        FrameLayout root = new FrameLayout(this);
        setContentView(root);
        root.post(() -> {
            if (isFinishing()) return;
            int columns = "tiles".equals(mode) ? 2 : 1;
            for (int row = 0; row < columns; row++) for (int col = 0; col < columns; col++) {
                SurfaceView view = new SurfaceView(this);
                view.getHolder().setFormat("rgb565".equals(mode) ? PixelFormat.RGB_565 : PixelFormat.OPAQUE);
                view.getHolder().setFixedSize(3840 / columns, 2160 / columns);
                view.getHolder().addCallback(this);
                FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(root.getWidth() / columns, root.getHeight() / columns);
                lp.leftMargin = col * root.getWidth() / columns;
                lp.topMargin = row * root.getHeight() / columns;
                root.addView(view, lp);
            }
        });
        handler.postDelayed(this::finish, 120000);
    }

    @Override protected void onResume() { super.onResume(); resumed = true; }
    @Override protected void onPause() { resumed = false; handler.removeCallbacksAndMessages(null); super.onPause(); finish(); }
    @Override protected void onDestroy() { handler.removeCallbacksAndMessages(null); super.onDestroy(); }
    @Override public void surfaceCreated(SurfaceHolder holder) { }
    @Override public void surfaceDestroyed(SurfaceHolder holder) { }
    @Override public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
        handler.postDelayed(() -> render(holder), 100);
    }

    private void render(SurfaceHolder holder) {
        if (!resumed || isFinishing() || !holder.getSurface().isValid()) return;
        Canvas canvas = null;
        long begin = SystemClock.elapsedRealtime();
        try {
            canvas = "rgb565".equals(mode) ? holder.lockCanvas() : holder.lockHardwareCanvas();
            if (canvas == null) throw new IllegalStateException("No canvas");
            int width = canvas.getWidth(), height = canvas.getHeight();
            canvas.drawColor(0xff10141d);
            Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
            paint.setColor(Color.WHITE); paint.setTextSize(width / 48f);
            canvas.drawText("Proskurnin TV · surface diagnostic", width / 25f, height / 12f, paint);
            paint.setTextSize(width / 70f);
            canvas.drawText(mode + " · " + width + " × " + height + " · Back to return", width / 25f, height / 7f, paint);
            paint.setAntiAlias(false);
            for (int x = width / 20; x < width * 9 / 20; x++) {
                paint.setColor(x % 2 == 0 ? Color.WHITE : Color.BLACK);
                canvas.drawRect(x, height / 4, x + 1, height * 3 / 4, paint);
            }
            for (int y = height / 4; y < height * 3 / 4; y++) {
                paint.setColor(y % 2 == 0 ? Color.WHITE : Color.BLACK);
                canvas.drawRect(width * 11 / 20, y, width * 19 / 20, y + 1, paint);
            }
            paint.setColor(0xff8ddbaf); paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(4);
            canvas.drawRect(4, 4, width - 4, height - 4, paint);
            android.util.Log.i("Proskurnin4KProbe", "mode=" + mode + " canvas=" + width + "x" + height
                    + " hardware=" + canvas.isHardwareAccelerated());
        } catch (RuntimeException | OutOfMemoryError error) {
            android.util.Log.e("Proskurnin4KProbe", "Surface diagnostic failed", error);
            finish();
        } finally {
            if (canvas != null) try { holder.unlockCanvasAndPost(canvas); }
            catch (RuntimeException error) { finish(); }
        }
        android.util.Log.i("Proskurnin4KProbe", "submit_ms=" + (SystemClock.elapsedRealtime() - begin));
    }
}
