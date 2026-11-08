package local.proskurnin.homerouter;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

/** A permission-free system HOME entry. No window, background service or key filtering. */
public class HomeActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        try {
            if (Intent.ACTION_ALL_APPS.equals(getIntent().getAction())) {
                open("com.google.android.tvlauncher", "com.google.android.tvlauncher.MainActivity");
            } else {
                open("local.proskurnin.preview", "local.proskurnin.preview.MainActivity");
            }
        } catch (RuntimeException unavailable) {
            Log.w("ProskurninHomeRouter", "Custom Home unavailable; opening Google", unavailable);
            try {
                open("com.google.android.tvlauncher", "com.google.android.tvlauncher.MainActivity");
            } catch (RuntimeException fallbackUnavailable) {
                Log.e("ProskurninHomeRouter", "Fallback unavailable", fallbackUnavailable);
            }
        } finally {
            finish();
        }
    }

    private void open(String pkg, String activity) {
        startActivity(new Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME)
                .setComponent(new ComponentName(pkg, activity))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED));
        Log.i("ProskurninHomeRouter", "HOME -> " + pkg);
    }
}
