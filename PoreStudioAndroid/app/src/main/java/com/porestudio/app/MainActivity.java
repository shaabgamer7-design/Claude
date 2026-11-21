package com.porestudio.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.media.MediaScannerConnection;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.SystemClock;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.view.ViewGroup;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
import android.webkit.PermissionRequest;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.ArrayList;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MainActivity extends Activity {
    private static final String TAG = "PoreStudio";
    private static final String START_URL = "file:///android_asset/index.html";
    private static final int MIN_WEBVIEW = 87;   // the studio uses CSS/JS that needs Chromium 87+
    private static final int REQ_FILE = 101;
    private static final int REQ_MIC = 102;
    private static final int REQ_STORAGE = 103;

    private FrameLayout root;
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private PermissionRequest pendingWebPermission;
    private long lastRendererCrash;
    private final Bridge bridge = new Bridge();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        installCrashLogger();
        super.onCreate(savedInstanceState);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.BLACK);
        setContentView(root);

        if (!createWebView()) return;
        if (savedInstanceState == null || web.restoreState(savedInstanceState) == null) web.loadUrl(START_URL);

        showLastCrashIfAny();
        checkWebViewVersion();
    }

    /** Builds the WebView. Returns false (and explains why) if the phone has no working WebView. */
    private boolean createWebView() {
        try {
            web = new WebView(this);
        } catch (Throwable t) {
            // Happens when Android System WebView is missing, disabled or in the middle of updating.
            Log.e(TAG, "WebView unavailable", t);
            showFatal("Pore Studio needs \"Android System WebView\" (or Chrome) to run.\n\n"
                    + "Install or enable it from the Play Store, then open the app again.", true);
            return false;
        }
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        web.setBackgroundColor(Color.BLACK);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(true);
        s.setAllowContentAccess(true);
        s.setAllowFileAccessFromFileURLs(true);
        s.setAllowUniversalAccessFromFileURLs(true);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setLoadWithOverviewMode(true);
        s.setUseWideViewPort(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setTextZoom(100); // keep the layout intact when the phone uses large system fonts
        WebView.setWebContentsDebuggingEnabled(true);

        web.addJavascriptInterface(bridge, "AndroidBridge");
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
                // Without this, Android kills the whole app when the page runs out of memory.
                boolean crashed = Build.VERSION.SDK_INT >= 26 && detail.didCrash();
                Log.e(TAG, "WebView renderer gone, crashed=" + crashed);
                recoverFromRendererLoss(crashed);
                return true;
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = callback;
                boolean multiple = params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE;
                String[] types = cleanMimeTypes(params.getAcceptTypes());
                Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                if (types.length == 1) {
                    intent.setType(types[0]);
                } else {
                    intent.setType(types.length == 0 ? "*/*" : commonType(types));
                    if (types.length > 1) intent.putExtra(Intent.EXTRA_MIME_TYPES, types);
                }
                if (multiple) intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                try {
                    startActivityForResult(Intent.createChooser(intent, "Choose a file"), REQ_FILE);
                    return true;
                } catch (Throwable t) {
                    Log.e(TAG, "file chooser failed", t);
                    fileCallback = null;
                    toast("No app found to pick files");
                    return false;
                }
            }

            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(() -> handleWebPermission(request));
            }

            @Override
            public void onPermissionRequestCanceled(PermissionRequest request) {
                if (request == pendingWebPermission) pendingWebPermission = null;
            }
        });
        return true;
    }

    private void recoverFromRendererLoss(boolean crashed) {
        long now = SystemClock.elapsedRealtime();
        boolean repeated = now - lastRendererCrash < 60_000;
        lastRendererCrash = now;
        if (fileCallback != null) { fileCallback.onReceiveValue(null); fileCallback = null; }
        pendingWebPermission = null;
        bridge.reset();
        if (web != null) {
            root.removeView(web);
            try { web.destroy(); } catch (Throwable ignored) { }
            web = null;
        }
        if (!createWebView()) return;
        web.loadUrl(START_URL);
        String why = crashed ? "The studio stopped unexpectedly and was restarted."
                : "Your phone ran low on memory, so the studio was restarted.";
        if (repeated) {
            new AlertDialog.Builder(this)
                    .setTitle("Studio restarted")
                    .setMessage(why + "\n\nTo keep it smooth on this phone: record at 720p or 1080p, use fewer photos at once, "
                            + "and close other apps.")
                    .setPositiveButton("OK", null)
                    .show();
        } else {
            toast(why);
        }
    }

    private void handleWebPermission(PermissionRequest request) {
        // Only the microphone is ever needed; refuse anything else (e.g. camera) instead of failing later.
        ArrayList<String> wanted = new ArrayList<>();
        for (String r : request.getResources()) if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(r)) wanted.add(r);
        if (wanted.isEmpty()) { request.deny(); return; }
        String[] res = wanted.toArray(new String[0]);
        if (Build.VERSION.SDK_INT < 23 || checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
            request.grant(res);
            return;
        }
        if (pendingWebPermission != null) { try { pendingWebPermission.deny(); } catch (Throwable ignored) { } }
        pendingWebPermission = request;
        requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, REQ_MIC);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_FILE || fileCallback == null) return;
        Uri[] result = null;
        try {
            if (resultCode == RESULT_OK && data != null) {
                ClipData clip = data.getClipData();
                if (clip != null && clip.getItemCount() > 0) {
                    ArrayList<Uri> list = new ArrayList<>();
                    for (int i = 0; i < clip.getItemCount(); i++) {
                        Uri u = clip.getItemAt(i).getUri();
                        if (u != null) list.add(u);
                    }
                    result = list.isEmpty() ? null : list.toArray(new Uri[0]);
                } else if (data.getData() != null) {
                    result = new Uri[]{data.getData()};
                }
            }
        } catch (Throwable t) {
            Log.e(TAG, "reading picked files failed", t);
            result = null;
        }
        fileCallback.onReceiveValue(result);
        fileCallback = null;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_MIC && pendingWebPermission != null) {
            PermissionRequest req = pendingWebPermission;
            pendingWebPermission = null;
            try {
                if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                    req.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
                } else {
                    req.deny();
                    toast("Microphone permission was refused. You can allow it in Settings › Apps › Pore Studio.");
                }
            } catch (Throwable t) {
                Log.e(TAG, "answering mic permission failed", t);
            }
        } else if (requestCode == REQ_STORAGE && bridge.waitingForStorage) {
            bridge.waitingForStorage = false;
            boolean ok = grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED;
            toast(ok ? "Storage allowed. Tap Save video again." : "Storage permission is needed to save videos.");
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (web != null) web.saveState(outState);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onPause() {
        if (web != null) web.onPause();
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        bridge.reset();
        if (web != null) {
            root.removeView(web);
            try { web.destroy(); } catch (Throwable ignored) { }
            web = null;
        }
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }

    // ---------------------------------------------------------------- helpers

    private void toast(String msg) {
        runOnUiThread(() -> Toast.makeText(this, msg, Toast.LENGTH_LONG).show());
    }

    private static String[] cleanMimeTypes(String[] accept) {
        ArrayList<String> out = new ArrayList<>();
        if (accept != null) {
            for (String group : accept) {
                if (group == null) continue;
                for (String t : group.split(",")) {
                    t = t.trim().toLowerCase();
                    if (t.isEmpty()) continue;
                    if (t.startsWith(".")) { // file extensions -> a broad MIME type
                        if (t.matches("\\.(jpe?g|png|webp|gif|heic|heif|bmp)")) t = "image/*";
                        else if (t.matches("\\.(mp3|m4a|aac|wav|ogg|oga|opus|flac)")) t = "audio/*";
                        else continue;
                    }
                    if (t.contains("/") && !out.contains(t)) out.add(t);
                }
            }
        }
        return out.toArray(new String[0]);
    }

    private static String commonType(String[] types) {
        String major = null;
        for (String t : types) {
            String m = t.substring(0, t.indexOf('/'));
            if (major == null) major = m;
            else if (!major.equals(m)) return "*/*";
        }
        return major + "/*";
    }

    private void checkWebViewVersion() {
        int major = 0;
        try {
            Matcher m = Pattern.compile("Chrome/(\\d+)").matcher(WebSettings.getDefaultUserAgent(this));
            if (m.find()) major = Integer.parseInt(m.group(1));
        } catch (Throwable ignored) { }
        if (major > 0 && major < MIN_WEBVIEW) {
            new AlertDialog.Builder(this)
                    .setTitle("Update Android System WebView")
                    .setMessage("This phone's WebView (version " + major + ") is too old, so parts of the studio may not work.\n\n"
                            + "Update \"Android System WebView\" and \"Chrome\" in the Play Store, then reopen the app.")
                    .setPositiveButton("Open Play Store", (d, w) -> openWebViewStore())
                    .setNegativeButton("Later", null)
                    .show();
        }
    }

    private void openWebViewStore() {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=com.google.android.webview")));
        } catch (ActivityNotFoundException e) {
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=com.google.android.webview")));
            } catch (Throwable ignored) { }
        }
    }

    private void showFatal(String message, boolean offerStore) {
        TextView tv = new TextView(this);
        tv.setText(message);
        tv.setTextColor(Color.WHITE);
        tv.setTextSize(17);
        int p = (int) (24 * getResources().getDisplayMetrics().density);
        tv.setPadding(p, p, p, p);
        root.addView(tv);
        AlertDialog.Builder b = new AlertDialog.Builder(this).setTitle("Pore Studio").setMessage(message)
                .setNegativeButton("Close", (d, w) -> finish());
        if (offerStore) b.setPositiveButton("Open Play Store", (d, w) -> openWebViewStore());
        b.show();
    }

    // ---------------------------------------------------------------- crash log

    private File crashFile() { return new File(getFilesDir(), "last_crash.txt"); }

    private void installCrashLogger() {
        final Thread.UncaughtExceptionHandler previous = Thread.getDefaultUncaughtExceptionHandler();
        if (previous instanceof CrashLogger) return;
        Thread.setDefaultUncaughtExceptionHandler(new CrashLogger(getApplicationContext(), previous));
    }

    private static final class CrashLogger implements Thread.UncaughtExceptionHandler {
        private final Context ctx;
        private final Thread.UncaughtExceptionHandler previous;
        CrashLogger(Context ctx, Thread.UncaughtExceptionHandler previous) { this.ctx = ctx; this.previous = previous; }

        @Override
        public void uncaughtException(Thread t, Throwable e) {
            try (FileOutputStream f = new FileOutputStream(new File(ctx.getFilesDir(), "last_crash.txt"))) {
                StringWriter sw = new StringWriter();
                PrintWriter pw = new PrintWriter(sw);
                pw.println("Pore Studio " + BuildConfigInfo.version(ctx) + " on Android " + Build.VERSION.RELEASE
                        + " (API " + Build.VERSION.SDK_INT + "), " + Build.MANUFACTURER + " " + Build.MODEL);
                pw.println("Thread: " + t.getName());
                e.printStackTrace(pw);
                pw.flush();
                f.write(sw.toString().getBytes("UTF-8"));
            } catch (Throwable ignored) { }
            if (previous != null) previous.uncaughtException(t, e);
        }
    }

    private static final class BuildConfigInfo {
        static String version(Context c) {
            try { return c.getPackageManager().getPackageInfo(c.getPackageName(), 0).versionName; }
            catch (Throwable t) { return "?"; }
        }
    }

    private void showLastCrashIfAny() {
        File f = crashFile();
        if (!f.exists()) return;
        String text;
        try (FileInputStream in = new FileInputStream(f)) {
            byte[] buf = new byte[(int) Math.min(f.length(), 16_000)];
            int n = in.read(buf);
            text = new String(buf, 0, Math.max(0, n), "UTF-8");
        } catch (Throwable t) {
            text = "(could not read the crash report)";
        }
        //noinspection ResultOfMethodCallIgnored
        f.delete();
        final String report = text;
        new AlertDialog.Builder(this)
                .setTitle("Pore Studio closed unexpectedly last time")
                .setMessage("Sorry about that. You can copy the report below and send it to the developer.\n\n"
                        + (report.length() > 1500 ? report.substring(0, 1500) + "…" : report))
                .setPositiveButton("Copy report", (d, w) -> {
                    ClipboardManager cm = (ClipboardManager) getSystemService(CLIPBOARD_SERVICE);
                    if (cm != null) cm.setPrimaryClip(ClipData.newPlainText("Pore Studio crash", report));
                    toast("Report copied");
                })
                .setNegativeButton("Dismiss", null)
                .show();
    }

    // ---------------------------------------------------------------- video saving bridge

    /** Called from the page: AndroidBridge.begin(name, mime) -> chunk(base64)... -> end(). */
    private class Bridge {
        private OutputStream out;
        private Uri pendingUri;
        private File legacyFile;
        private String shownPath;
        volatile boolean waitingForStorage;

        @JavascriptInterface
        public synchronized String begin(String name, String mime) {
            try {
                discard();
                if (name == null || name.trim().isEmpty()) name = "pore-extraction.mp4";
                name = name.replaceAll("[\\\\/:*?\"<>|]", "_");
                if (mime == null || mime.isEmpty()) mime = name.endsWith(".webm") ? "video/webm" : "video/mp4";
                if (Build.VERSION.SDK_INT >= 29) {
                    ContentResolver r = getContentResolver();
                    pendingUri = insertMedia(r, MediaStore.Video.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY),
                            name, mime, Environment.DIRECTORY_MOVIES + "/PoreStudio");
                    shownPath = "Gallery › Movies › PoreStudio";
                    if (pendingUri == null) { // some phones refuse WebM in the video collection: fall back to Downloads
                        pendingUri = insertMedia(r, MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY),
                                name, mime, Environment.DIRECTORY_DOWNLOADS + "/PoreStudio");
                        shownPath = "Downloads › PoreStudio";
                    }
                    if (pendingUri == null) return "error: could not create the file";
                    out = r.openOutputStream(pendingUri);
                } else {
                    if (Build.VERSION.SDK_INT >= 23 && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
                        waitingForStorage = true;
                        runOnUiThread(() -> requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE));
                        return "error: allow storage access, then tap Save again";
                    }
                    File dir = new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MOVIES), "PoreStudio");
                    if (!dir.exists() && !dir.mkdirs()) return "error: could not create Movies/PoreStudio";
                    legacyFile = new File(dir, name);
                    out = new FileOutputStream(legacyFile);
                    shownPath = "Movies/PoreStudio";
                }
                return out != null ? "ok" : "error: could not open the file";
            } catch (Throwable e) {
                discard();
                return "error: " + e.getMessage();
            }
        }

        private Uri insertMedia(ContentResolver r, Uri collection, String name, String mime, String relPath) {
            try {
                ContentValues v = new ContentValues();
                v.put(MediaStore.MediaColumns.DISPLAY_NAME, name);
                v.put(MediaStore.MediaColumns.MIME_TYPE, mime);
                v.put(MediaStore.MediaColumns.RELATIVE_PATH, relPath);
                v.put(MediaStore.MediaColumns.IS_PENDING, 1);
                return r.insert(collection, v);
            } catch (Throwable t) {
                Log.w(TAG, "insert into " + collection + " failed", t);
                return null;
            }
        }

        @JavascriptInterface
        public synchronized String chunk(String b64) {
            try {
                if (out == null) return "error: save was not started";
                out.write(Base64.decode(b64, Base64.DEFAULT));
                return "ok";
            } catch (Throwable e) {
                discard();
                return "error: " + (e instanceof OutOfMemoryError ? "out of memory" : e.getMessage());
            }
        }

        @JavascriptInterface
        public synchronized String end() {
            try {
                if (out == null) return "error: save was not started";
                out.flush();
                out.close();
                out = null;
                if (Build.VERSION.SDK_INT >= 29 && pendingUri != null) {
                    ContentValues v = new ContentValues();
                    v.put(MediaStore.MediaColumns.IS_PENDING, 0);
                    getContentResolver().update(pendingUri, v, null, null);
                    pendingUri = null;
                } else if (legacyFile != null) {
                    MediaScannerConnection.scanFile(MainActivity.this, new String[]{legacyFile.getAbsolutePath()}, null, null);
                    legacyFile = null;
                }
                return shownPath;
            } catch (Throwable e) {
                discard();
                return "error: " + e.getMessage();
            }
        }

        @JavascriptInterface
        public boolean isApp() { return true; }

        synchronized void reset() { discard(); }

        /** Closes and removes a half-written file so failed saves don't leave broken videos behind. */
        private void discard() {
            try { if (out != null) out.close(); } catch (Throwable ignored) { }
            out = null;
            if (pendingUri != null) {
                try { getContentResolver().delete(pendingUri, null, null); } catch (Throwable ignored) { }
                pendingUri = null;
            }
            if (legacyFile != null) {
                //noinspection ResultOfMethodCallIgnored
                legacyFile.delete();
                legacyFile = null;
            }
        }
    }
}
