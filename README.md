# FreeFlow

Voice dictation that works in every app. Hold a key, talk, let go, and clean,
punctuated text appears at your cursor. Filler words and false starts are
removed, "no wait, I mean..." corrections are applied, and the tone matches
the app you're in.

FreeFlow is a clean-room re-implementation of the features
[Wispr Flow](https://wisprflow.ai) describes publicly. It contains no code or
assets from Wispr Flow. It runs on your computer with providers you choose:
no word limits and no subscription. Speech recognition can run fully offline
for free, and AI editing is either free (Ollama) or paid per use with your own
Claude API key.

## Install

| | Download | Then |
| --- | --- | --- |
| **macOS** (Apple Silicon) | `FreeFlow-<version>-macOS-arm64.dmg` | Open it and drag **FreeFlow** to **Applications** |
| **Windows 10/11** | `FreeFlow-Setup-<version>.exe` | Run it (no admin rights needed) |

Get the installers from this repository's **Releases** page. Every push also
builds them: open the **Actions** tab, pick the latest "Build installers" run,
and download them under **Artifacts**.

### First launch

**macOS.** The app isn't notarized by Apple yet, so the first time:

1. Double-click FreeFlow in Applications. macOS says it can't verify the
   developer. Click **Done**.
2. Open **System Settings → Privacy & Security**, scroll down, and click
   **Open Anyway** next to FreeFlow.

(Or, in Terminal: `xattr -dr com.apple.quarantine /Applications/FreeFlow.app`.)

**Windows.** If SmartScreen shows "Windows protected your PC", click
**More info → Run anyway**.

### Setup wizard

FreeFlow opens a short setup:

1. **Pick how it works.**
   - *Recommended:* speech recognition on your computer (free) plus Claude for
     editing (your Anthropic API key).
   - *Private and free:* everything on your computer. AI editing uses
     [Ollama](https://ollama.com) if it's installed, otherwise basic cleanup.
   - *Fastest:* Groq cloud speech recognition plus Claude. Best on older
     computers.
2. **Paste your API keys** and choose a Claude model. Keys are stored in the
   macOS Keychain or Windows Credential Manager.
3. **Permissions** (macOS): switch FreeFlow on under **Input Monitoring** and
   **Accessibility**, click **Restart FreeFlow**, and allow the microphone.
   On macOS, also set **System Settings → Keyboard → "Press 🌐 key to" → Do
   Nothing** so the fn key is free for dictation.
4. **Try it** in the box provided.

FreeFlow then lives in the menu bar (macOS) or the system tray (Windows).

## Using it

| Action | macOS | Windows |
| --- | --- | --- |
| Dictate | hold **fn** | hold **Right Ctrl** |
| Hands-free | double-tap, then tap once to finish | same |
| Cancel | **Esc** | **Esc** |
| Command mode | hold **fn + Control** | hold **Right Ctrl + Shift** |
| Paste last result | **Control + Command + V** | **Alt + Shift + Z** |

- A small bar near the bottom of the screen shows a live waveform while you
  talk and dots while it's working.
- **Command mode:** select text, hold the command key and say "make this more
  formal", "translate to Spanish" or "turn this into bullet points". With
  nothing selected it writes what you ask for: "draft a polite no to this
  meeting invite".
- Pressing another key while holding the dictation key (for example Right
  Ctrl + C) cancels the recording, so your shortcuts keep working.
- The tray menu has **Pause dictation**, **Paste last result**, **Settings**
  and **History**.

## Settings

Open them from the tray/menu-bar icon.

- **General:** hotkeys, microphone, how text is inserted, the recording bar,
  sounds, launch at login, history.
- **Speech:** where speech recognition runs (on this computer, Groq, OpenAI,
  or your own server), the model and the language (or automatic detection).
- **AI editing:** Claude, Ollama or off; the model; the output language (for
  example "always write English"); a **Run test** button.
- **Dictionary:** words to spell exactly (names, jargon), replacements
  ("chat gpt" → "ChatGPT"), and snippets (say "my calendar link" and the saved
  text is inserted; snippet text never leaves your computer).
- **Styles:** which apps get which tone, and the instructions for each style.
- **History:** search, copy, words dictated, pace, and time saved.

### What it costs

- On-device speech recognition and Ollama: free.
- Groq speech recognition: very cheap per hour of audio (see Groq's pricing).
- Claude editing, rough estimates for a short dictation (~750 input and ~200
  output tokens): Opus 5.5 about 0.7¢, Sonnet 5.5 about 0.35¢, Haiku 5.5
  about 0.02¢. Haiku handles everyday dictation well; switch models in
  **Settings → AI editing**.

## Features compared with Wispr Flow

| Wispr Flow feature | FreeFlow |
| --- | --- |
| Push-to-talk in any app, hands-free mode | Yes |
| AI auto-edit: fillers, self-corrections, punctuation, lists, numbers | Yes |
| App-aware tone (chat, email, documents, code) | Yes, with custom rules |
| Command Mode (voice-edit selected text) | Yes |
| Personal dictionary, snippets | Yes, plus replacements |
| 100+ languages, whisper mode | Yes (Whisper), with quiet-speech boost |
| Flow bar, menu-bar app, history, stats | Yes |
| Learns words from your later edits | Not yet |
| Reads on-screen text for context | Not yet (uses app name and window title) |
| iPhone / Android | No |

## Privacy

- With on-device speech recognition and Ollama, nothing leaves your computer.
- With cloud providers, audio goes to the speech provider and the transcript
  (plus the app name and window title, for tone) goes to the AI provider.
- History, settings and logs stay in a local folder (Settings → About → Open
  settings folder). History can be turned off or deleted.
- Text is pasted through the clipboard, and your previous clipboard text is
  restored afterwards. If you often copy images, choose "Type it out" in
  Settings → General.

## Troubleshooting

- **Nothing happens when I hold the key (macOS):** check that FreeFlow is
  switched on under Input Monitoring and Accessibility, then quit and reopen
  it. After installing a new version, macOS may ask again.
- **"No speech detected":** pick the right microphone in Settings → General
  and use **Test microphone** in the setup wizard (Settings → About → Run setup
  again).
- **Text doesn't appear in one particular app:** set "Insert text by" to
  "Type it out". On Windows, apps running as Administrator only accept input
  from programs that also run as Administrator.
- **AI editing isn't working:** use Run test in Settings → AI editing. Until a
  key works, FreeFlow falls back to basic cleanup, so you never lose a
  dictation.
- The log file is under Settings → About → Open log.

## Building it yourself

Installers are built by `.github/workflows/build.yml` on GitHub's macOS and
Windows machines. Each build runs `FreeFlow --selftest`, which checks the
packaged app end to end, including an on-device transcription. Pushing a tag
such as `v0.2.0` publishes a release with both installers attached.

To build locally on a Mac or PC (Python 3.10+):

```bash
pip install ".[gui,local]" pyinstaller pillow
```

```bash
python packaging/make_icon.py
```

```bash
pyinstaller packaging/freeflow.spec --noconfirm
```

The macOS app is in `dist/FreeFlow.app`; `bash packaging/macos/make_dmg.sh`
wraps it in a disk image. On Windows, `dist/FreeFlow/FreeFlow.exe` is the app
and `iscc packaging\windows\freeflow.iss` builds the installer
([Inno Setup](https://jrsoftware.org/isinfo.php)).

For a signed and notarized macOS build (no Gatekeeper warning), you need an
Apple Developer ID; sign `dist/FreeFlow.app` with it and notarize the DMG
with `xcrun notarytool`.

## Command-line version

Everything also works without the desktop app, which is handy on Linux:

```bash
pip install -e ".[local]"
```

```bash
freeflow init        # writes config.toml and prints its path
```

```bash
freeflow doctor      # checks the mic, speech model and AI editing
```

```bash
freeflow             # dictate from a terminal session
```

`freeflow transcribe FILE --app Slack`, `freeflow clean "text"`,
`freeflow history` and `freeflow stats` are also available. The desktop app
and the command line share the same settings file and keychain keys. Linux
needs `libportaudio2 xclip xdotool` and an X11 session, and you can run the
desktop app there with `pip install -e ".[gui,local]"` and `freeflow-app`.

## Development

```bash
pip install -e ".[gui,local,dev]"
```

```bash
QT_QPA_PLATFORM=offscreen pytest
```

| Module | Role |
| --- | --- |
| `freeflow/hotkeys.py` | Global key hook and the hold / double-tap / command state machine |
| `freeflow/audio.py` | Recording, levels, silence detection, quiet-speech boost |
| `freeflow/transcribe.py` | faster-whisper, mlx-whisper, Groq, OpenAI, custom servers |
| `freeflow/cleanup.py` | Editing prompts, Claude / Ollama backends, rule-based fallback, snippets |
| `freeflow/context.py` | Focused app detection and style rules |
| `freeflow/output.py` | Paste or type at the cursor; read the selection for command mode |
| `freeflow/app.py` | Wires it together; processing runs off the keyboard thread |
| `freeflow/gui/` | Desktop app: tray, recording bar, setup wizard, settings, self-test |
| `freeflow/apikeys.py`, `autostart.py`, `permissions.py` | Keychain, launch at login, macOS permissions |
| `packaging/` | PyInstaller spec, icon, DMG and Windows installer scripts |
