# Wisharo Studio: 30s vertical promo

| File | What it is |
| --- | --- |
| `wisharo-promo.mp4` | Final video: 1080x1920, 30 fps, H.264 + AAC 48 kHz stereo, 30.0 s, with music |
| `wisharo-promo-no-music.mp4` | Same video, narration + SFX only (add a trending sound on Instagram/TikTok) |
| `wisharo-narration.wav` | Narration only, 48 kHz mono (edge-tts, en-US-AvaNeural) |
| `wisharo-captions.srt` | Captions, timed from a faster-whisper transcription |
| `voice-samples/` | The three voice options (Andrew, Ava, Ryan) |

## About the phone screens
The live site could not be filmed: wisharo.com's hosting firewall (StackProtect) blocks automated browsers.
The phone screens are therefore a code recreation built from the site's real material:
- the real wishes on wisharo.com/tuesday-blessings/ and the real gold copy-card styling with the **Copy** and **Make card** buttons
- the 8 real New Year backgrounds (Midnight Fireworks is the one chosen); "Moonlit Stars" stays off-screen because it contains a crescent
- the real "New Year & Party" stickers from elements.json, recoloured through their {c1}/{c2} colours; the champagne bottle and toast-glasses stickers are left out
- the studio's real English and Italian labels (Templates/Modelli, Text/Testo, Wishes/Auguri, Elements/Elementi, Background/Sfondo, Colour) and its language menu (English, اردو, हिंदी, Roman Urdu, Italiano)
- a real Italian wish from wisharo.com/it/frasi-capodanno/

The editor layout itself is a recreation, so it won't match the live studio pixel for pixel.
If you later relax the firewall or send a phone screen recording, the phone screens can be swapped for real footage.

## Script (as narrated)
Copy. Paste. Send. The same wish everyone else got. / Meet Wisharo Studio. A free card maker. No sign-up. /
Find a wish you love, and tap Make card. / Choose a background. / Add balloons, sparkles, confetti. /
Switch to Italian in seconds. / Make it yours, at wisharo dot com.

"Switch to Italian in one tap" was changed to "in seconds" because the live switcher takes two taps: the pill, then Italiano.

## Sound sources
All sound effects and the music bed were synthesised in code (`scripts/gen_audio.py`: sine waves and seeded noise). No third-party samples are used, so there is nothing to license.
- whoosh on transitions, soft click with a gold ripple on every tap, sparkle chime when a sticker lands, low boom on the logo and on the CTA
- music: a quiet ambient pad and pluck bed at 84 bpm, ducked under the narration

Narration: Microsoft Edge neural TTS (en-US-AvaNeural) via the open-source `edge-tts` tool.
Fonts: Poppins and Lora (Google Fonts, SIL Open Font License).
