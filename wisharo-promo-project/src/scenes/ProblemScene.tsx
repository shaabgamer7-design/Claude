import React from "react";
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {NavyBackdrop} from "../components/Backdrop";
import {Particles} from "../components/Particles";
import {C, FONT, curves} from "../theme";
import {wordFrame} from "../timeline";

const WISH = "Wishing you a blessed day";

const Bubble: React.FC<{enter: number; strike: number; index: number}> = ({enter, strike, index}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - enter, fps, config: {damping: 15, stiffness: 170, mass: 0.8}});
  const st = interpolate(f, [strike, strike + 10], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.enter});
  const dim = interpolate(f, [strike + 4, strike + 16], [1, 0.42], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  if (f < enter - 1) return null;
  return (
    <div
      style={{
        alignSelf: "flex-end",
        position: "relative",
        transform: `translateY(${(1 - s) * 90}px) scale(${0.8 + 0.2 * s})`,
        transformOrigin: "100% 100%",
        opacity: Math.min(1, s * 1.4),
        marginRight: index * 14,
      }}
    >
      <div
        style={{
          position: "relative",
          padding: "26px 34px 20px",
          borderRadius: "40px 40px 10px 40px",
          background: "linear-gradient(160deg, #fffdf8 0%, #f3ead8 100%)",
          boxShadow: "0 22px 50px rgba(0,0,0,0.35), inset 0 0 0 1.5px rgba(212,169,79,0.45)",
          filter: `saturate(${dim})`,
          opacity: 0.4 + 0.6 * dim,
        }}
      >
        <div style={{fontFamily: FONT.head, fontSize: 24, fontWeight: 500, color: "#8a7a5a", letterSpacing: 0.4, marginBottom: 6}}>
          ↪ Forwarded
        </div>
        <div style={{fontFamily: FONT.wish, fontStyle: "italic", fontSize: 54, color: C.ink, lineHeight: 1.2}}>{WISH}</div>
        <div style={{fontFamily: FONT.head, fontSize: 22, color: "#9a8f78", textAlign: "right", marginTop: 6}}>9:4{index + 1} ✓✓</div>
        {/* strike-through */}
        <div
          style={{
            position: "absolute",
            left: 22,
            top: "56%",
            height: 7,
            width: `calc(${st * 100}% - ${st * 44}px)`,
            borderRadius: 4,
            background: `linear-gradient(90deg, ${C.gold}, ${C.goldLight})`,
            boxShadow: "0 0 16px rgba(212,169,79,0.7)",
            transform: "rotate(-3deg)",
          }}
        />
      </div>
    </div>
  );
};

const Kinetic: React.FC<{text: string; at: number; x: number; rot: number}> = ({text, at, x, rot}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - at, fps, config: {damping: 11, stiffness: 240, mass: 0.7}});
  if (f < at) return null;
  return (
    <div
      style={{
        fontFamily: FONT.head,
        fontWeight: 800,
        fontSize: 150,
        letterSpacing: -5,
        lineHeight: 0.98,
        color: C.ivory,
        transform: `translateX(${x}px) scale(${0.55 + 0.45 * s}) rotate(${(1 - s) * rot}deg)`,
        opacity: Math.min(1, s * 2),
        textShadow: "0 12px 40px rgba(0,0,0,0.45)",
      }}
    >
      {text}
    </div>
  );
};

export const ProblemScene: React.FC = () => {
  const f = useCurrentFrame();
  const fCopy = wordFrame("copy");
  const fPaste = wordFrame("paste");
  const fSend = wordFrame("send");
  const fSame = wordFrame("same");
  const push = interpolate(f, [0, 160], [1, 1.07], {easing: curves.editorial});
  const kickOut = interpolate(f, [fSame - 4, fSame + 10], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.enter});
  // big gold "x" stamp once all three are struck through
  const xAt = fSame + 22;
  const xp = interpolate(f, [xAt, xAt + 12], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.enter});
  return (
    <AbsoluteFill>
      <NavyBackdrop glow={0.8} />
      <Particles count={40} seed="p1" opacity={0.6} />
      <AbsoluteFill style={{transform: `scale(${push})`}}>
        {/* kinetic words */}
        <div
          style={{
            position: "absolute",
            top: 210,
            left: 90,
            right: 90,
            display: "flex",
            flexDirection: "column",
            gap: 6,
            transform: `translateY(${-kickOut * 40}px)`,
            opacity: 1 - kickOut * 0.75,
          }}
        >
          <Kinetic text="Copy." at={fCopy} x={0} rot={-8} />
          <Kinetic text="Paste." at={fPaste} x={70} rot={6} />
          <Kinetic text="Send." at={fSend} x={140} rot={-5} />
        </div>
        {/* chat stack */}
        <div
          style={{
            position: "absolute",
            left: 110,
            right: 90,
            top: 760,
            display: "flex",
            flexDirection: "column",
            gap: 26,
          }}
        >
          <Bubble enter={fCopy + 4} strike={fSame} index={0} />
          <Bubble enter={fPaste + 4} strike={fSame + 5} index={1} />
          <Bubble enter={fSend + 4} strike={fSame + 10} index={2} />
        </div>
        {/* "x3" stamp */}
        <div
          style={{
            position: "absolute",
            left: 790,
            top: 250,
            width: 190,
            height: 190,
            borderRadius: "50%",
            border: `6px solid ${C.gold}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily: FONT.head,
            fontWeight: 800,
            fontSize: 84,
            color: C.gold,
            transform: `scale(${1.6 - 0.6 * xp}) rotate(${-14 + 4 * xp}deg)`,
            opacity: xp,
            background: "rgba(11,18,32,0.75)",
            boxShadow: "0 0 40px rgba(212,169,79,0.35)",
          }}
        >
          ×3
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
