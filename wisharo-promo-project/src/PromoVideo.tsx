import React from "react";
import {AbsoluteFill, interpolate, Sequence, staticFile} from "remotion";
import {Audio} from "@remotion/media";
import {NavyBackdrop} from "./components/Backdrop";
import {Particles} from "./components/Particles";
import {GoldWipe} from "./components/GoldWipe";
import {Captions} from "./components/Captions";
import {ProblemScene} from "./scenes/ProblemScene";
import {RevealScene} from "./scenes/RevealScene";
import {PhoneStage} from "./scenes/PhoneStage";
import {CtaScene} from "./scenes/CtaScene";
import {C} from "./theme";
import {PHONE_IN, TOTAL, scene, sec} from "./timeline";
import vo from "./data/vo_timeline.json";
import {LANDS, TAPS} from "./data/flow";

export type PromoProps = {music: boolean};


const WIPE = 18;
const CUTS = {reveal: scene("reveal").from, cta: scene("cta").from};

type Sfx = {at: number; src: string; vol: number};
const SFX: Sfx[] = (() => {
  const s: Sfx[] = [
    {at: CUTS.reveal - 9, src: "audio/sfx_whoosh.wav", vol: 0.55},
    {at: CUTS.reveal + 4, src: "audio/sfx_boom.wav", vol: 0.8},
    {at: PHONE_IN - 2, src: "audio/sfx_whoosh.wav", vol: 0.4},
    {at: scene("background").from - 6, src: "audio/sfx_whoosh.wav", vol: 0.38},
    {at: scene("stickers").from - 6, src: "audio/sfx_whoosh.wav", vol: 0.38},
    {at: scene("language").from - 6, src: "audio/sfx_whoosh.wav", vol: 0.38},
    {at: CUTS.cta - 9, src: "audio/sfx_whoosh.wav", vol: 0.55},
    {at: CUTS.cta + 3, src: "audio/sfx_boom.wav", vol: 0.75},
  ];
  // problem-scene bubbles each "send" with a click
  for (const w of ["copy", "paste", "send"]) {
    const i = ["copy", "paste", "send"].indexOf(w);
    s.push({at: [0, 38, 70][i] + 4, src: "audio/sfx_click.wav", vol: 0.5});
  }
  TAPS.forEach((t) => s.push({at: t.f, src: "audio/sfx_click.wav", vol: 0.7}));
  LANDS.forEach((l, k) => s.push({at: l.f, src: `audio/sfx_chime${k % 3}.wav`, vol: 0.45}));
  return s.filter((x) => x.at >= 0);
})();

/** Music volume: bed level with a smooth duck under every narration line. */
const musicVolume = (f: number) => {
  const BED = 0.34;
  const DUCK = 0.12;
  let v = BED;
  for (const l of vo) {
    const a = sec(l.voStart);
    const b = sec(l.voEnd);
    const d = interpolate(f, [a - 6, a, b, b + 10], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
    v = Math.min(v, BED - (BED - DUCK) * d);
  }
  const fadeIn = interpolate(f, [0, 20], [0, 1], {extrapolateRight: "clamp"});
  const fadeOut = interpolate(f, [TOTAL - 45, TOTAL - 2], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return v * fadeIn * fadeOut;
};

export const PromoVideo: React.FC<PromoProps> = ({music}) => {
  const rev = scene("reveal");
  const cta = scene("cta");
  return (
    <AbsoluteFill style={{background: C.navy}}>
      {/* problem */}
      <Sequence durationInFrames={rev.from + WIPE}>
        <ProblemScene />
      </Sequence>
      {/* reveal + product stage share the navy backdrop */}
      <Sequence from={rev.from} durationInFrames={cta.from - rev.from + 10}>
        <NavyBackdrop />
        <Particles count={70} seed="main" />
      </Sequence>
      <Sequence from={rev.from} durationInFrames={PHONE_IN - rev.from + 40}>
        <RevealScene />
      </Sequence>
      <PhoneStage />
      <Sequence from={cta.from}>
        <CtaScene />
      </Sequence>

      {/* gold wipes centred on the cuts */}
      <Sequence from={rev.from - WIPE / 2} durationInFrames={WIPE}>
        <GoldWipe dur={WIPE} toColor={C.navy} />
      </Sequence>
      <Sequence from={cta.from - WIPE / 2} durationInFrames={WIPE}>
        <GoldWipe dur={WIPE} toColor={C.ivory} />
      </Sequence>

      {/* captions: hidden where kinetic type already shows the words */}
      <Captions
        hidden={[
          [0, sec(3.2)],
          [rev.from, scene("pick").voStart - 3],
          [cta.from, TOTAL],
        ]}
      />

      {/* audio */}
      <Audio src={staticFile("audio/narration.wav")} volume={1} />
      {music && <Audio src={staticFile("audio/music_bed.wav")} volume={(f) => musicVolume(f)} />}
      {SFX.map((s, i) => (
        <Sequence key={i} from={s.at} durationInFrames={90} layout="none">
          <Audio src={staticFile(s.src)} volume={s.vol} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
