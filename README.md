# FreeFlow

Voice dictation for Windows that works in every app. Hold a key, talk, let go,
and clean, punctuated text appears at your cursor. Filler words and false
starts are removed, "no wait, I mean..." corrections are applied, and the tone
matches the app you're in.

FreeFlow is a clean-room re-implementation of the features
[Wispr Flow](https://wisprflow.ai) describes publicly. It contains no code or
assets from Wispr Flow. It runs on your computer with providers you choose:
no word limits and no subscription. Speech recognition can run fully offline
for free, and AI editing is either free (Ollama) or paid per use with your own
Claude API key.

## Install

1. Download **`FreeFlow-Setup-<version>.exe`** (Windows 10/11, 64-bit):
   - from this repository's **Releases** page, or
   - from the **Actions** tab: open the latest "Build Windows installer" run
     and download **FreeFlow-Windows** under **Artifacts** (it's a zip with
     the installer inside).
2. Run it. No administrator rights are needed. You can choose to start
   FreeFlow when you sign in and to add a desktop shortcut.
3. If SmartScreen says "Windows protected your PC", click **More info → Run
   anyway**. This appears because the installer isn't code-signed.

To uninstall, use **Settings → Apps → Installed apps → FreeFlow**.

### Setup wizard

On first launch FreeFlow walks you through setup:

1. **Pick how it works.**
   - *Recommended:* speech recognition on your computer (free) plus Claude for
     editing (your Anthropic API key).
   - *Private and free:* everything on your computer. AI editing uses
     [Ollama](https://ollama.com) if it's installed, otherwise basic cleanup.
   - *Fastest:* Groq cloud speech recognition plus Claude. Best on older PCs.
2. **Paste your API keys** and choose a Claude model. Keys are stored in
   Windows Credential Manager.
3. **Test your microphone.**
4. **Try it** in the box provided. The first time, the speech model downloads
   once (a few hundred MB).

FreeFlow then lives in the system tray (click the **^** arrow next to the
clock if you don't see it). Click the icon to open Settings.

## Using it

| Action | Keys |
| --- | --- |
| Dictate | hold **Right Ctrl**, speak, let go |
| Hands-free | double-tap **Right Ctrl**, then tap once to finish |
| Cancel | **Esc** |
| Command mode | hold **Right Ctrl + Shift** |
| Paste last result | **Alt + Shift + Z** |

- A small bar near the bottom of the screen shows a live waveform while you
  talk and dots while it's working.
- **Command mode:** select text, hold the command keys and say "make this more
  formal", "translate to Spanish" or "turn this into bullet points". With
  nothing selected it writes what you ask for: "draft a polite no to this
  meeting invite".
- Pressing another key while holding Right Ctrl (for example Right Ctrl + C)
  cancels the recording, so your shortcuts keep working.
- No Right Ctrl on your keyboard? Pick another key in **Settings → General**,
  such as Ctrl + Windows, Right Alt or F9.
- The tray menu has **Pause dictation**, **Paste last result**, **Settings**
  and **History**.

## Settings

- **General:** hotkeys, microphone, how text is inserted, the recording bar,
  sounds, start at sign-in, history.
- **Speech:** where speech recognition runs (on this PC, Groq, OpenAI, or your
  own server), the model and the language (or automatic detection).
- **AI editing:** Claude, Ollama or off; the model; the output language (for
  example "always write English"); a **Run test** button.
- **Dictionary:** words to spell exactly (names, jargon), replacements
  ("chat gpt" → "ChatGPT"), and snippets (say "my calendar link" and the saved
  text is inserted; snippet text never leaves your PC).
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
| Flow bar, tray app, history, stats | Yes |
| Learns words from your later edits | Not yet |
| Reads on-screen text for context | Not yet (uses app name and window title) |
| Phone apps | No |

## Privacy

- With on-device speech recognition and Ollama, nothing leaves your PC.
- With cloud providers, audio goes to the speech provider and the transcript
  (plus the app name and window title, for tone) goes to the AI provider.
- History, settings and logs stay in `%APPDATA%\FreeFlow` (Settings → About →
  Open settings folder). History can be turned off or deleted.
- Text is pasted through the clipboard, and your previous clipboard text is
  restored afterwards. If you often copy images, choose "Type it out" in
  Settings → General.

## Troubleshooting

- **"No speech detected":** pick the right microphone in Settings → General,
  and check **Windows Settings → Privacy & security → Microphone** allows
  desktop apps. You can re-run the mic test from Settings → About → Run setup
  again.
- **Text doesn't appear in one particular app:** set "Insert text by" to
  "Type it out". Apps running as Administrator only accept input from
  programs that also run as Administrator.
- **AI editing isn't working:** use Run test in Settings → AI editing. Until a
  key works, FreeFlow falls back to basic cleanup, so you never lose a
  dictation.
- **Antivirus warning:** FreeFlow uses a global keyboard hook to notice the
  dictation key, which some antivirus tools flag. You can review all of the
  code in this repository.
- The log file is under Settings → About → Open log.

## How the installer is built

`.github/workflows/build.yml` builds the installer on GitHub's Windows
machines on every push. Each build runs `FreeFlow.exe --selftest`, which
checks the packaged app end to end: audio, keyboard hook, Credential Manager,
the Claude client, the speech-model download and an on-device transcription,
and every window. The report appears on the run's summary page. Pushing a tag
such as `v0.2.0` publishes a GitHub Release with the installer attached.

To build it yourself on Windows (Python 3.10+):

```bash
pip install ".[gui,local]" pyinstaller pillow
```

```bash
python packaging/make_icon.py
```

```bash
pyinstaller packaging/freeflow.spec --noconfirm
```

`dist\FreeFlow\FreeFlow.exe` is the app. To build the installer, install
[Inno Setup](https://jrsoftware.org/isinfo.php) and run
`iscc packaging\windows\freeflow.iss`.

## Command-line version

Everything also works without the desktop app:

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
freeflow             # dictate from a terminal window
```

`freeflow transcribe FILE --app Slack`, `freeflow clean "text"`,
`freeflow history` and `freeflow stats` are also available. The desktop app
and the command line share the same settings file and stored keys.

## Development

```bash
pip install -e ".[gui,local,dev]"
```

```bash
pytest
```

Set `QT_QPA_PLATFORM=offscreen` to run the window tests without a display.

| Module | Role |
| --- | --- |
| `freeflow/hotkeys.py` | Global key hook and the hold / double-tap / command state machine |
| `freeflow/audio.py` | Recording, levels, silence detection, quiet-speech boost |
| `freeflow/transcribe.py` | faster-whisper, Groq, OpenAI, custom servers |
| `freeflow/cleanup.py` | Editing prompts, Claude / Ollama backends, rule-based fallback, snippets |
| `freeflow/context.py` | Focused app detection and style rules |
| `freeflow/output.py` | Paste or type at the cursor; read the selection for command mode |
| `freeflow/app.py` | Wires it together; processing runs off the keyboard thread |
| `freeflow/gui/` | Desktop app: tray, recording bar, setup wizard, settings, self-test |
| `freeflow/apikeys.py`, `autostart.py` | Credential Manager keys, start at sign-in |
| `packaging/` | PyInstaller spec, icon, Windows installer script |
