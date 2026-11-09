package local.proskurnin.preview;

import android.content.Context;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.graphics.drawable.BitmapDrawable;
import android.graphics.drawable.Drawable;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/** Local APK artwork. Loading and rasterization run on launcher-apps, never in onDraw. */
final class AppArtwork {
    static final float TILE_WIDTH = 260f, TILE_HEIGHT = TILE_WIDTH * 9f / 16f;
    static final int NEUTRAL = 0xff262b34;
    final Bitmap bitmap;
    final boolean banner;
    final int tint;
    final String revision;

    private AppArtwork(Bitmap bitmap, boolean banner, int tint, String revision) {
        this.bitmap = bitmap; this.banner = banner; this.tint = tint; this.revision = revision;
    }

    static final class Loader {
        private final ConcurrentHashMap<String, AppArtwork> cache = new ConcurrentHashMap<>();

        AppArtwork peek(String pkg) { return cache.get(pkg); }

        AppArtwork load(Context context, ActivityInfo activity) {
            PackageManager pm = context.getPackageManager();
            String pkg = activity.packageName;
            try {
                PackageInfo info = pm.getPackageInfo(pkg, 0);
                String revision = info.lastUpdateTime + ":" + activity.name + ":"
                        + context.getResources().getConfiguration().toString();
                AppArtwork existing = cache.get(pkg);
                if (existing != null && revision.equals(existing.revision)) return existing;
                AppArtwork result = null;
                // A TV activity can override the application's default banner.
                if (activity.banner != 0) {
                    try { result = render(pm.getDrawable(pkg, activity.banner, activity.applicationInfo), true, revision); }
                    catch (RuntimeException ignored) { }
                }
                if (result == null) {
                    try { result = render(pm.getApplicationBanner(pkg), true, revision); }
                    catch (PackageManager.NameNotFoundException | RuntimeException ignored) { }
                }
                if (result == null) {
                    try { result = render(activity.loadIcon(pm), false, revision); }
                    catch (RuntimeException ignored) { }
                }
                if (result == null) {
                    try { result = render(pm.getApplicationIcon(pkg), false, revision); }
                    catch (PackageManager.NameNotFoundException | RuntimeException ignored) { }
                }
                if (result != null) cache.put(pkg, result);
                else cache.remove(pkg);
                return result;
            } catch (PackageManager.NameNotFoundException | RuntimeException ignored) {
                cache.remove(pkg);
                return null;
            }
        }

        void retain(Set<String> installed) {
            // Do not recycle: the previous UI snapshot may still refer to these bitmaps.
            for (String pkg : cache.keySet()) if (!installed.contains(pkg)) cache.remove(pkg);
        }
    }

    private static AppArtwork render(Drawable drawable, boolean banner, String revision) {
        if (drawable == null) return null;
        int width = banner ? 320 : 144, height = banner ? 180 : 144;
        Bitmap raw = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        try {
            Canvas canvas = new Canvas(raw);
            if (banner) canvas.drawColor(NEUTRAL);
            int iw = drawable.getIntrinsicWidth(), ih = drawable.getIntrinsicHeight();
            if (iw <= 0 || ih <= 0) { iw = width; ih = height; }
            float scale = Math.min(width / (float) iw, height / (float) ih);
            int dw = Math.max(1, Math.round(iw * scale)), dh = Math.max(1, Math.round(ih * scale));
            if (drawable instanceof BitmapDrawable) ((BitmapDrawable) drawable).setFilterBitmap(true);
            drawable.setBounds((width - dw) / 2, (height - dh) / 2,
                    (width + dw) / 2, (height + dh) / 2);
            drawable.draw(canvas);
            int tint = banner ? NEUTRAL : tint(raw);
            Bitmap rounded = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
            Paint mask = new Paint(Paint.ANTI_ALIAS_FLAG | Paint.FILTER_BITMAP_FLAG);
            mask.setShader(new BitmapShader(raw, Shader.TileMode.CLAMP, Shader.TileMode.CLAMP));
            float radius = banner ? 22f * width / TILE_WIDTH : 24f;
            new Canvas(rounded).drawRoundRect(new RectF(0, 0, width, height), radius, radius, mask);
            return new AppArtwork(rounded, banner, tint, revision);
        } finally { raw.recycle(); }
    }

    private static int tint(Bitmap icon) {
        float[] hsv = new float[3], weights = new float[12];
        long[] red = new long[12], green = new long[12], blue = new long[12];
        int[] counts = new int[12];
        for (int y = 3; y < icon.getHeight(); y += 6) for (int x = 3; x < icon.getWidth(); x += 6) {
            int color = icon.getPixel(x, y);
            if (Color.alpha(color) < 180) continue;
            Color.colorToHSV(color, hsv);
            if (hsv[1] < .22f || hsv[2] < .18f) continue;
            int bin = Math.min(11, (int) (hsv[0] / 30));
            weights[bin] += hsv[1]; red[bin] += Color.red(color);
            green[bin] += Color.green(color); blue[bin] += Color.blue(color); counts[bin]++;
        }
        int best = 0;
        for (int i = 1; i < 12; i++) if (weights[i] > weights[best]) best = i;
        if (counts[best] < 4) return NEUTRAL;
        int n = counts[best];
        return Color.rgb((int) (29 * .8 + red[best] / n * .2),
                (int) (38 * .8 + green[best] / n * .2), (int) (50 * .8 + blue[best] / n * .2));
    }
}
