import React from "react";
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {LogoMedallion} from "../components/Logo";
import {C, FONT, curves} from "../theme";
import {PHONE_IN, scene, wordFrame} from "../timeline";

const Chip: React.FC<{text: string; at: number; dot?: boolean}> = ({text, at}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - at, fps, config: {damping: 14, stiffness: 200}});
  return (
    <div
      style={{
        padding: "18px 34px",
        borderRadius: 999,
        border: `2px solid ${C.gold}`,
        background: "rgba(212,169,79,0.12)",
        color: C.goldLight,
        fontFamily: FONT.head,
        fontWeight: 600,
        fontSize: 40,
        letterSpacing: 0.3,
        opacity: Math.min(1, s * 1.5),
        transform: `translateY(${(1 - s) * 30}px) scale(${0.85 + 0.15 * s})`,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

/** Rendered inside a Sequence starting at scene("reveal").from: local frames. */
export const RevealScene: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const S = scene("reveal").from;
  const logoAt = 6;
  const fMeet = wordFrame("meet") - S;
  const fFree = wordFrame("free") - S;
  const fNo = wordFrame("no") - S;
  const leave = PHONE_IN - S; // phone begins to rise here

  const logoS = spring({frame: f - logoAt, fps, config: {damping: 13, stiffness: 120, mass: 1}});
  const flare = interpolate(f, [logoAt, logoAt + 6, logoAt + 30], [0, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const up = interpolate(f, [leave - 4, leave + 24], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.standard});

  const title = "Wisharo Studio".split("");
  return (
    <AbsoluteFill>
      {/* flare on landing */}
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at 50% 36%, rgba(243,220,158,${0.55 * flare}) 0%, rgba(212,169,79,${0.2 * flare}) 25%, rgba(0,0,0,0) 55%)`,
        }}
      />
      <AbsoluteFill
        style={{
          transform: `translateY(${-up * 520}px) scale(${1 - up * 0.55})`,
          transformOrigin: "50% 30%",
          opacity: 1 - interpolate(up, [0.6, 1], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}),
        }}
      >
        <div style={{position: "absolute", top: 470, left: 0, right: 0, display: "flex", justifyContent: "center"}}>
          <div style={{transform: `scale(${0.3 + 0.7 * logoS}) rotate(${(1 - logoS) * -40}deg)`, opacity: Math.min(1, logoS * 2)}}>
            <LogoMedallion size={300} at={logoAt} />
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            top: 860,
            left: 0,
            right: 0,
            textAlign: "center",
            fontFamily: FONT.head,
            fontWeight: 700,
            fontSize: 118,
            letterSpacing: -3.5,
            color: C.ivory,
          }}
        >
          {title.map((ch, i) => {
            const s = spring({frame: f - (fMeet + 2 + i * 1.6), fps, config: {damping: 14, stiffness: 200}});
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  whiteSpace: "pre",
                  color: i >= 8 ? C.gold : C.ivory,
                  opacity: Math.min(1, s * 1.6),
                  transform: `translateY(${(1 - s) * 60}px) rotate(${(1 - s) * 8}deg)`,
                }}
              >
                {ch}
              </span>
            );
          })}
        </div>
        <div style={{position: "absolute", top: 1040, left: 0, right: 0, display: "flex", justifyContent: "center", gap: 22}}>
          {f >= fFree - 1 && <Chip text="Free card maker" at={fFree} />}
          {f >= fNo - 1 && <Chip text="No sign-up" at={fNo} />}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
