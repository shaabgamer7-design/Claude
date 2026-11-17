import React from "react";
import {AbsoluteFill, Img, interpolate, random, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {IvoryBackdrop} from "../components/Backdrop";
import {LogoMedallion} from "../components/Logo";
import {Particles} from "../components/Particles";
import {C, FONT, curves} from "../theme";
import {scene, wordFrame, wordIndex} from "../timeline";

const FLOATERS = [
  {src: "stickers/goldballoons.svg", x: 70, y: 210, s: 230, r: -10},
  {src: "stickers/sparkles.svg", x: 820, y: 300, s: 150, r: 12},
  {src: "stickers/balloons.svg", x: 790, y: 1240, s: 230, r: 8},
  {src: "stickers/confetti.svg", x: 60, y: 1300, s: 190, r: -6},
  {src: "stickers/sparkles.svg", x: 120, y: 760, s: 90, r: 0},
];

export const CtaScene: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const S = scene("cta").from;
  const words = ["Make", "it", "yours."];
  const iMake = wordIndex("make", 30);
  const fAt = wordFrame("at", iMake) - S;
  const pill = spring({frame: f - fAt, fps, config: {damping: 14, stiffness: 160}});
  const shimmer = interpolate(f, [fAt + 18, fAt + 48], [-40, 140], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.editorial});
  const push = interpolate(f, [0, 110], [1.04, 1], {easing: curves.enter});
  const logoS = spring({frame: f - 2, fps, config: {damping: 15, stiffness: 140}});

  return (
    <AbsoluteFill>
      <IvoryBackdrop />
      <Particles count={45} seed="cta" color={C.gold} opacity={0.7} />
      <AbsoluteFill style={{transform: `scale(${push})`}}>
        {FLOATERS.map((fl, i) => {
          const s = spring({frame: f - 6 - i * 4, fps, config: {damping: 12, stiffness: 120}});
          const bob = Math.sin((f + i * 20) / 18) * 10;
          return (
            <Img
              key={i}
              src={staticFile(fl.src)}
              style={{
                position: "absolute",
                left: fl.x,
                top: fl.y + bob,
                width: fl.s,
                height: fl.s,
                opacity: s * 0.95,
                transform: `scale(${s}) rotate(${fl.r + Math.sin(f / 25 + i) * 4}deg)`,
                filter: "drop-shadow(0 14px 22px rgba(80,60,20,0.18))",
              }}
            />
          );
        })}
        <div style={{position: "absolute", top: 470, left: 0, right: 0, display: "flex", justifyContent: "center"}}>
          <div style={{transform: `scale(${logoS})`, opacity: logoS}}>
            <LogoMedallion size={170} at={2} />
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            top: 720,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: FONT.head,
            fontWeight: 800,
            fontSize: 128,
            letterSpacing: -5,
            lineHeight: 1,
            color: C.navy,
          }}
        >
          {words.map((w, i) => {
            const at = wordFrame(w.replace(".", "").toLowerCase(), iMake) - S;
            const s = spring({frame: f - at, fps, config: {damping: 12, stiffness: 220, mass: 0.7}});
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  marginRight: i < 2 ? 28 : 0,
                  color: i === 2 ? C.forest : C.navy,
                  opacity: Math.min(1, s * 1.8),
                  transform: `translateY(${(1 - s) * 70}px) scale(${0.7 + 0.3 * s})`,
                }}
              >
                {w}
              </span>
            );
          })}
          <div
            style={{
              height: 8,
              width: 360 * interpolate(f, [12, 30], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.enter}),
              margin: "28px auto 0",
              borderRadius: 4,
              background: `linear-gradient(90deg, ${C.goldDeep}, ${C.gold}, ${C.goldLight})`,
            }}
          />
        </div>
        <div style={{position: "absolute", top: 1000, left: 0, right: 0, display: "flex", justifyContent: "center"}}>
          <div
            style={{
              position: "relative",
              overflow: "hidden",
              padding: "30px 46px",
              borderRadius: 999,
              background: `linear-gradient(160deg, ${C.forestLight} 0%, ${C.forest} 55%, #163a2b 100%)`,
              border: `3px solid ${C.gold}`,
              boxShadow: "0 24px 60px rgba(31,77,58,0.35), 0 0 0 10px rgba(212,169,79,0.12)",
              color: C.ivory,
              fontFamily: FONT.head,
              fontWeight: 600,
              fontSize: 46,
              letterSpacing: 0.2,
              opacity: Math.min(1, pill * 1.5),
              transform: `translateY(${(1 - pill) * 60}px) scale(${0.8 + 0.2 * pill})`,
              whiteSpace: "nowrap",
            }}
          >
            wisharo.com<span style={{color: C.goldLight}}>/greeting-card-maker</span>
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                left: `${shimmer}%`,
                width: "30%",
                background: "linear-gradient(100deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.35) 50%, rgba(255,255,255,0) 100%)",
                transform: "skewX(-20deg)",
              }}
            />
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            top: 1150,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: FONT.head,
            fontWeight: 500,
            fontSize: 36,
            color: "#5c6a62",
            letterSpacing: 4,
            textTransform: "uppercase",
            opacity: interpolate(f, [fAt + 14, fAt + 28], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}),
          }}
        >
          Free · No sign-up
        </div>
      </AbsoluteFill>
      {/* gold confetti burst on landing */}
      <AbsoluteFill style={{pointerEvents: "none"}}>
        {new Array(36).fill(0).map((_, i) => {
          const a = random(`c-a-${i}`) * Math.PI * 2;
          const v = 18 + random(`c-v-${i}`) * 26;
          const t = Math.max(0, f - 4);
          const x = 540 + Math.cos(a) * v * t * 0.9;
          const y = 820 + Math.sin(a) * v * t * 0.9 + 0.9 * t * t;
          const o = interpolate(t, [0, 4, 34], [0, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: x,
                top: y,
                width: 12,
                height: 22,
                borderRadius: 3,
                background: i % 3 === 0 ? C.forest : i % 3 === 1 ? C.gold : C.goldLight,
                opacity: o,
                transform: `rotate(${t * (8 + i)}deg)`,
              }}
            />
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
