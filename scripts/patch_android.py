"""Донастройка Android-проекта после `npx cap add android`.
Запускается в GitHub Actions: альбомная ориентация, полный экран без панелей, экран не гаснет, номер версии."""
import re, sys, pathlib
run = int(sys.argv[1]) if len(sys.argv) > 1 else 1
root = pathlib.Path('android/app')

man = root / 'src/main/AndroidManifest.xml'
t = man.read_text(encoding='utf-8')
if 'screenOrientation' not in t:
    t = re.sub(r'(<activity\b[^>]*?android:name="\.MainActivity")', r'\1 android:screenOrientation="sensorLandscape"', t, count=1)
man.write_text(t, encoding='utf-8')

gr = root / 'build.gradle'
g = gr.read_text(encoding='utf-8')
g = re.sub(r'versionCode \d+', f'versionCode {run}', g)
g = re.sub(r'versionName "[^"]*"', f'versionName "1.{run}"', g)
gr.write_text(g, encoding='utf-8')

act = next((root / 'src/main/java').rglob('MainActivity.java'))
pkg = re.search(r'package ([\w.]+);', act.read_text(encoding='utf-8')).group(1)
act.write_text(f'''package {pkg};

import android.os.Bundle;
import android.view.WindowManager;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {{
    @Override
    public void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        hideBars();
    }}

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {{
        super.onWindowFocusChanged(hasFocus);
        if (hasFocus) hideBars();
    }}

    private void hideBars() {{
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        WindowInsetsControllerCompat c = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        c.hide(WindowInsetsCompat.Type.systemBars());
        c.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
    }}
}}
''', encoding='utf-8')
print('android patched: version', run, 'package', pkg)
