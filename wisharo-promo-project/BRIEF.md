# Wisharo Studio: 30s vertical promo (creative brief)

| Field | Plan |
| --- | --- |
| Objective | Drive visits to the free card maker at wisharo.com/greeting-card-maker |
| Audience | People who send daily wishes and blessings on WhatsApp, Instagram and TikTok |
| Platform | Instagram Reels, TikTok, YouTube Shorts: 1080x1920, 30 fps, H.264 + AAC |
| Duration | 30.0 s (900 frames) |
| Core message | Turn a copied wish into your own card: free, no sign-up |
| Hook | Three identical "Wishing you a blessed day" bubbles stacking up, then struck out |
| Visual style | Navy #0b1220, ivory #faf6ef, gold #d4a94f, forest #1f4d3a. Poppins headlines, Lora italic wishes. Light gold particles, premium phone frame |
| Motion | Spring pops, slow camera pushes, zooms on tapped controls, gold wipes between scenes |
| Audio | Ava (edge-tts) narration, procedurally generated SFX and music bed, ducked under VO. A no-music version is exported too |
| Captions | faster-whisper word timings, large animated captions, SRT export |

## Fact check against the live site (17 Nov 2026)
- Copy cards with **Copy** and **Make card** buttons on /tuesday-blessings/: confirmed in page CSS and card-button.js.
- Card maker is free with no sign-up: the page itself says "Free · No sign-up · Nothing uploaded".
- New Year section with 8 backgrounds (Midnight Fireworks, Champagne Gold, Aurora Night, Party Bokeh, Rose Sparkle, Moonlit Stars, Blush Watercolor, Confetti Party): confirmed in studio-addon.js.
- Elements panel "New Year & Party" category (32 items incl. balloons, party popper, sparkles, confetti, gift box, birthday cake): confirmed in elements.json.
- Language switcher: English, Urdu, Hindi, Roman Urdu and Italiano. It is a pill that opens a menu (two taps), so the VO says "Switch to Italian in seconds" instead of "in one tap".

## Content rules
- No religious symbols (crosses, churches, crescents etc.) on screen.
- No alcohol imagery. The "Champagne bottle" and "Toast glasses" stickers are hidden while filming the Elements panel.

## Asset inventory
| Asset | Status | Location | Notes |
| --- | --- | --- | --- |
| Logo | from site | public/brand/favicon512.png | Wisharo leaf mark, 512px |
| Phone screens | code recreation (site firewall blocks automated browsers) | src/screens/AppScreen.tsx | real wishes, backgrounds (public/site/bg), stickers and studio labels |
| Narration | edge-tts en-US-AvaNeural | public/audio/narration.wav | |
| SFX | generated in code | public/audio/sfx_*.wav | scripts/gen_audio.py, original synthesis |
| Music | generated in code | public/audio/music_bed.wav | scripts/gen_audio.py, original synthesis |
| Captions | faster-whisper | src/data/words.json, out/captions.srt | |
