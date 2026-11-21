# Pore Studio – Android APK build guide (for Claude Code)

## What this is
A complete Android app that wraps the **Pore Extraction Studio** web app
(`app/src/main/assets/index.html`, a single self-contained HTML file) in a full-screen WebView.
The owner wants a signed APK they can install on any Android phone, like an app from APKPure.

Everything the studio does must keep working inside the app:
- Upload photos and audio files (file chooser → `onShowFileChooser`, multiple images allowed)
- Microphone commentary (RECORD_AUDIO runtime permission → `onPermissionRequest` grants it)
- Recording the canvas to video with MediaRecorder; the page prefers MP4 (`video/mp4;codecs=avc1…`)
- **Save video**: the page calls `AndroidBridge.begin(name, mime)`, then `chunk(base64)` per 1 MB,
  then `end()`. Java writes it to `Movies/PoreStudio` (MediaStore on Android 10+, public folder
  plus media scan on Android 7–9). The file appears in the Gallery.
- Screen stays on, rotation doesn't reload the page (`configChanges`).

Project: AGP 8.5.2, compileSdk/targetSdk 34, minSdk 24 (Android 7.0+), Java 17, no AndroidX,
no third-party dependencies. App id `com.porestudio.app`.

## Build steps
1. Make sure JDK 17 is installed (`java -version`). If not, install Temurin 17.
2. Install the Android SDK if `ANDROID_HOME`/`ANDROID_SDK_ROOT` isn't set:
   - Get the "command line tools only" package for this OS from developer.android.com/studio,
     unpack to `<sdk>/cmdline-tools/latest/`.
   - `sdkmanager --licenses` (accept all), then
     `sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"`.
   - Write `local.properties` in the project root: `sdk.dir=<path to sdk>` (escape backslashes on Windows).
3. Create the Gradle wrapper (none is checked in): with any Gradle ≥ 8.7 run
   `gradle wrapper --gradle-version 8.7`, or open the folder in Android Studio once.
4. Build: `./gradlew assembleRelease` (Windows: `gradlew.bat assembleRelease`).
   Release is signed with the debug keystore so it installs directly.
   Output: `app/build/outputs/apk/release/app-release.apk`.
   For a proper release key, create one with `keytool` and add a `signingConfigs.release` block.
5. Copy the APK somewhere easy (e.g. Desktop as `PoreStudio.apk`) and tell the owner where it is.
6. If a phone is connected with USB debugging: `adb install -r app/build/outputs/apk/release/app-release.apk`.

## Things to check (fix anything that fails)
- App opens straight into the studio, no blank screen (`chrome://inspect` works: debugging is on).
- Faces row → Upload opens the gallery/file picker; picked photo loads.
- Extract a spot with each tool; sound plays.
- Record a short video → the result sheet shows MP4 → **Save video** → it appears in the Gallery
  under Movies/PoreStudio.
- Mic switch asks for microphone permission and the level bar moves.
- MP4 depends on the phone's *Android System WebView* (Chromium 126+ records MP4). If a phone only
  records WebM, the app still saves the WebM. Optional improvement: transcode WebM→MP4 natively
  after `end()` (MediaExtractor + MediaCodec + MediaMuxer) before inserting into MediaStore.
- Layout: the page is responsive; check portrait and landscape on a phone-size screen.

Don't rewrite the studio itself unless something breaks inside the WebView; it's the owner's
finished app. Keep the APK light (no extra libraries).
