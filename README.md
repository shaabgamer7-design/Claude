# FreeFlow

Self-hosted voice dictation that works in every app. Hold a key, talk, let go,
and clean, punctuated, formatted text appears at your cursor. Filler words and
false starts are removed, self-corrections are applied, and the writing style
adjusts to the app you're in.

FreeFlow is a clean-room re-implementation of the features
[Wispr Flow](https://wisprflow.ai) describes publicly. It contains no code or
assets from Wispr Flow. It runs on your machine with providers you choose, so
there are no word quotas or subscriptions. You pay your speech/AI provider
directly, or nothing at all with the fully offline setup.

## Features

| Feature | FreeFlow |
| --- | --- |
| Push-to-talk in any app | Hold the hotkey (`fn` on macOS, right `Ctrl` on Windows/Linux) |
| Hands-free mode | Double-tap the hotkey; tap again to finish, `Esc` to cancel |
| AI auto-edit | Removes "um/uh/like", stutters and false starts; applies "no wait, I mean..." corrections; fixes punctuation; follows "new line", "bullet point", spoken punctuation; formats numbers, dates, emails, URLs |
| App-aware style | Casual in Slack/Discord/Messages, full sentences in Mail/Gmail/Outlook, polished in Docs/Notion/Word, identifier-safe in VS Code/Cursor/terminals. Add your own rules. |
| Command mode | Select text, hold the command hotkey, say "make this more formal", "translate to Spanish", "turn into bullets". With nothing selected, it writes what you ask for ("draft a polite no to this meeting"). |
| Personal dictionary | Names and jargon are passed to both the speech model and the editor so they're spelled right |
| Replacements | Deterministic find → replace on every result (`"chat gpt" = "ChatGPT"`) |
| Snippets | Say "my calendar link" and the saved text is inserted verbatim. The expansion never leaves your machine. |
| 99+ languages | Whisper auto-detects; optional "always output English" translation |
| Whisper mode | Quiet or whispered speech is boosted before transcription |
| Paste last result | `Ctrl+Cmd+V` (macOS) / `Alt+Shift+Z` (Windows/Linux) |
| History & stats | Local SQLite: `freeflow history`, `freeflow stats` (words, pace, time saved) |
| Never lose a dictation | If the AI is down it falls back to rule-based cleanup; if speech-to-text fails the audio is saved for `freeflow transcribe` |

Not included (yet): Wispr's floating on-screen bar (FreeFlow uses a tray icon
and sound cues), learning dictionary words automatically from your later edits,
reading on-screen text for extra context, mobile keyboards, and team sync.

## Install

Python 3.10+.

```bash
git clone https://github.com/shaabgamer7-design/Claude freeflow
```

```bash
cd freeflow
```

Pick the speech-to-text option you want (you can change it later):

```bash
pip install -e '.[local,tray]'    # offline Whisper on CPU / NVIDIA GPU
```

```bash
pip install -e '.[mlx,tray]'      # offline Whisper on Apple Silicon (fastest on M-series Macs)
```

```bash
pip install -e '.[tray]'          # cloud speech-to-text only (Groq / OpenAI)
```

Platform extras:

- **macOS**: run FreeFlow from a terminal app and grant that app **Microphone**,
  **Accessibility** and **Input Monitoring** in System Settings → Privacy &
  Security. To use `fn` as the hotkey, set System Settings → Keyboard →
  "Press 🌐 key to" → **Do Nothing**.
- **Windows**: nothing extra. Apps running as Administrator only receive pasted
  text if FreeFlow also runs as Administrator.
- **Linux (X11)**: `sudo apt install libportaudio2 xclip xdotool`. Global
  hotkeys don't work under Wayland; use an X11 session.

## Quick start

```bash
freeflow init        # writes the config file and prints its path
```

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # for AI cleanup with Claude
```

```bash
freeflow doctor      # checks mic, speech model, and cleanup end to end
```

```bash
freeflow             # start dictating
```

Then hold the hotkey in any text field and speak. With an offline provider the
first start downloads the Whisper model once (a few hundred MB to ~1.5 GB,
depending on `model`).

## Choosing providers

Edit the config file (`freeflow init` prints where it is) under `[transcription]` and `[cleanup]`.

**Completely free and offline.** No accounts, nothing leaves your computer.

```toml
[transcription]
provider = "local"          # or "mlx" on Apple Silicon
model = "large-v3-turbo"    # "small" is faster on older CPUs

[cleanup]
provider = "ollama"         # install from ollama.com, then: ollama pull llama3.2
model = "llama3.2"
```

**Fastest and most accurate** (closest to the Wispr Flow experience):

```toml
[transcription]
provider = "groq"           # export GROQ_API_KEY=...  (whisper-large-v3-turbo)

[cleanup]
provider = "claude"         # export ANTHROPIC_API_KEY=...
model = "claude-opus-5-5"
effort = "low"
```

About Claude costs: the default is Claude Opus 5.5 ($4 / $20 per million
input/output tokens). A typical short dictation uses a few hundred tokens, so
it costs on the order of one cent. Claude Haiku 5.5 ($0.10 / $0.50) is much
cheaper and faster for this kind of light editing: set `model = "claude-haiku-5-5"`
and compare the results on your own dictation. Command mode uses
`command_effort` (default `medium`), because rewriting text benefits from more
thinking.

Other options: `provider = "openai"` (OPENAI_API_KEY, `gpt-4o-transcribe`),
`provider = "custom"` with `base_url` for any self-hosted OpenAI-compatible
transcription server (whisper.cpp server, speaches, ...), and
`[cleanup] provider = "none"` for rule-based cleanup only.

## Everyday use

| Action | Default hotkey |
| --- | --- |
| Dictate | hold `fn` / right `Ctrl` |
| Hands-free | double-tap, then tap once to finish |
| Command mode | hold `fn+Ctrl` / right `Ctrl+Shift` |
| Cancel | `Esc` |
| Paste last result | `Ctrl+Cmd+V` / `Alt+Shift+Z` |

Pressing any other key while holding the dictation key (for example right
`Ctrl+C`) cancels the recording, so your shortcuts still work.

Useful commands:

```bash
freeflow transcribe meeting-note.m4a --app Slack   # run the full pipeline on a file
```

```bash
freeflow clean "um so yeah lets uh ship it friday no monday"   # test cleanup on text
```

```bash
freeflow history --search invoice
```

```bash
freeflow stats
```

```bash
freeflow devices     # list microphones; put the name or number in [audio] device
```

## Personalizing

```toml
[dictionary]
words = ["Anthropic", "Kubernetes", "Siobhan", "PostgreSQL"]

[replacements]
"chat gpt" = "ChatGPT"

[snippets]
"my email" = "me@example.com"
"my calendar link" = "https://cal.com/me"

[[styles]]
match = ["linear", "jira"]    # whole-word match on app name or window title
style = "formal"

[style_prompts]
casual = "All lowercase. No period at the end of a single sentence."
```

Built-in styles are `default`, `casual`, `email`, `formal` and `code`. You can
override any of them or add new ones in `[style_prompts]`.

## Privacy

- With `local`/`mlx` + `ollama`, audio and text never leave your computer.
- With cloud providers, the audio goes to the transcription provider and the
  transcript goes to the cleanup provider (with the app name and window title
  for style). Snippet expansions are filled in locally and never sent.
- History stays in a local SQLite file next to the config (`[history] enabled = false`
  turns it off; `freeflow clear-history` deletes it).
- Pasting goes through the clipboard and restores the previous text afterwards.
  Images on the clipboard are not restored; set `[output] method = "type"`
  if that matters to you.

## How it works

```
hotkey (pynput) → state machine → mic (sounddevice) → Whisper → AI editor → clipboard + Cmd/Ctrl+V
                                        ↑ active app + window title picks the style
```

| Module | Role |
| --- | --- |
| `freeflow/hotkeys.py` | Global key hook and the hold / double-tap / command state machine |
| `freeflow/audio.py` | Recording, silence detection, quiet-speech boost, cue sounds |
| `freeflow/transcribe.py` | faster-whisper, mlx-whisper, Groq, OpenAI, custom servers |
| `freeflow/cleanup.py` | Editing prompts, Claude / Ollama backends, rule-based fallback, snippets |
| `freeflow/context.py` | Frontmost app detection (macOS, Windows, Linux) and style rules |
| `freeflow/output.py` | Paste or type at the cursor; read the selection for command mode |
| `freeflow/app.py` | Wires it together; processing runs off the keyboard thread |
| `freeflow/history.py` | SQLite history and stats |

## Development

```bash
pip install -e '.[dev]'
```

```bash
pytest
```

The tests cover the hotkey state machine, cleanup and its fallbacks, the Claude
request shape, config parsing, history, and the full pipeline with fake
providers. They don't need a microphone, a display, or API keys.
