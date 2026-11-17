import React from "react";
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {PhoneFrame} from "../components/PhoneFrame";
import {C, FONT, PHONE, PHONE_POS, curves} from "../theme";
import {PHONE_IN, PHONE_OUT, SceneId, scene} from "../timeline";
import {CAMERA, LANDS, TAPS} from "../data/flow";
import {AppScreen} from "../screens/AppScreen";

export type Land = {f: number; x: number; y: number; sticker: string};

const PRODUCT: {id: SceneId; num: string; label: string}[] = [
  {id: "pick", num: "01", label: "Pick a wish"},
  {id: "background", num: "02", label: "New Year backgrounds"},
  {id: "stickers", num: "03", label: "Party stickers"},
  {id: "language", num: "04", label: "English → Italiano"},
];

const K = PHONE.screenW / PHONE.cssW;
/** CSS px on the filmed 390x844 page -> canvas px */
const toCanvas = (x: number, y: number) => ({
  x: PHONE_POS.left + PHONE.bezel + x * K,
  y: PHONE_POS.top + PHONE.bezel + y * K,
});

/** camera keys (absolute frames) -> transform */
const cameraTransform = (f: number) => {
  const keys = CAMERA.map((k) => ({f: k.f, s: k.s, ...toCanvas(k.x, k.y)}));
  let i = keys.findIndex((k) => k.f > f);
  if (i === -1) i = keys.length - 1;
  if (i === 0) i = 1;
  const a = keys[i - 1];
  const b = keys[i];
  const opt = {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.editorial} as const;
  const lerp = (u: number, v: number) => interpolate(f, [a.f, Math.max(b.f, a.f + 1)], [u, v], opt);
  // at zoom 1 the phone sits where it was laid out: blend focus toward the layout centre
  const s = lerp(a.s, b.s);
  const w = Math.min(1, Math.max(0, (s - 1) / 0.35));
  const home = toCanvas(195, 422);
  const cx = 540 + (lerp(a.x, b.x) - home.x) * w + (home.x - 540) * 0;
  const cy = 960 + (lerp(a.y, b.y) - 960) * w;
  return `translate(540px, 960px) scale(${s}) translate(${-cx}px, ${-cy}px)`;
};

const TapMark: React.FC<{at: number; x: number; y: number}> = ({at, x, y}) => {
  const f = useCurrentFrame();
  const t = f - at;
  if (t < -10 || t > 26) return null;
  const p = toCanvas(x, y);
  const press = interpolate(t, [-10, -2, 0, 6], [0, 1, 0.82, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const ring = interpolate(t, [0, 22], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.enter});
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: p.x - 34,
          top: p.y - 34,
          width: 68,
          height: 68,
          borderRadius: "50%",
          background: "rgba(255,255,255,0.55)",
          border: "2px solid rgba(255,255,255,0.9)",
          boxShadow: "0 6px 20px rgba(0,0,0,0.3)",
          opacity: press,
          transform: `scale(${0.7 + 0.3 * press})`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: p.x - 30,
          top: p.y - 30,
          width: 60,
          height: 60,
          borderRadius: "50%",
          border: `4px solid ${C.gold}`,
          opacity: t >= 0 ? 1 - ring : 0,
          transform: `scale(${1 + ring * 2.2})`,
          boxShadow: "0 0 18px rgba(212,169,79,0.8)",
        }}
      />
    </>
  );
};

/** A copy of a sticker that pops out of the phone where it lands, then drifts off and fades. */
const StickerBurst: React.FC<{at: number; land: Land; index: number}> = ({at, land, index}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f - at;
  if (t < 0 || t > 40) return null;
  const p = toCanvas(land.x, land.y);
  const s = spring({frame: t, fps, config: {damping: 10, stiffness: 180}});
  const dir = index % 2 === 0 ? -1 : 1;
  const o = interpolate(t, [0, 4, 26, 40], [0, 1, 1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return (
    <Img
      src={staticFile(`stickers/${land.sticker}.svg`)}
      style={{
        position: "absolute",
        left: p.x - 90 + dir * (s * 300),
        top: p.y - 90 - s * 120 - t * 2,
        width: 180,
        height: 180,
        opacity: o * 0.95,
        transform: `scale(${0.4 + 0.8 * s}) rotate(${dir * (1 - s) * 30}deg)`,
        filter: "drop-shadow(0 18px 30px rgba(0,0,0,0.45))",
      }}
    />
  );
};

const StepLabel: React.FC<{num: string; label: string; from: number; to: number}> = ({num, label, from, to}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const s = spring({frame: f - from, fps, config: {damping: 16, stiffness: 170}});
  const out = interpolate(f, [to - 8, to], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  if (f < from - 1 || f > to) return null;
  return (
    <div
      style={{
        position: "absolute",
        top: 205,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        gap: 18,
        opacity: Math.min(1, s * 1.5) * out,
        transform: `translateY(${(1 - s) * -30}px)`,
      }}
    >
      <div
        style={{
          fontFamily: FONT.head,
          fontWeight: 700,
          fontSize: 34,
          color: C.navy,
          background: C.gold,
          borderRadius: 999,
          padding: "8px 20px",
          letterSpacing: 1,
        }}
      >
        {num}
      </div>
      <div style={{fontFamily: FONT.head, fontWeight: 700, fontSize: 56, color: C.ivory, letterSpacing: -1.5, background: "rgba(11,18,32,0.82)", border: "1.5px solid rgba(212,169,79,0.45)", borderRadius: 999, padding: "10px 34px 14px", boxShadow: "0 16px 40px rgba(0,0,0,0.35)"}}>{label}</div>
    </div>
  );
};

/** Absolute-frame component (place in a Sequence starting at 0). */
export const PhoneStage: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (f < PHONE_IN || f >= PHONE_OUT + 10) return null;
  const rise = spring({frame: f - PHONE_IN, fps, config: {damping: 18, stiffness: 80, mass: 1.1}});
  const exit = interpolate(f, [PHONE_OUT - 6, PHONE_OUT + 8], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.exit});
  const tilt = (1 - rise) * 14;
  const breathe = Math.sin((f - PHONE_IN) / 45) * 0.6;

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{transform: cameraTransform(f), transformOrigin: "0 0"}}>
        <AbsoluteFill
          style={{
            transform: `translateY(${(1 - rise) * 1100 + exit * 80}px) perspective(2200px) rotateX(${tilt}deg) rotateY(${breathe}deg) scale(${1 - exit * 0.06})`,
            opacity: 1 - exit,
          }}
        >
          <div style={{position: "absolute", left: PHONE_POS.left, top: PHONE_POS.top}}>
            <PhoneFrame>
              <div style={{position: "absolute", left: 0, top: 0, width: PHONE.cssW, height: PHONE.cssH, transform: `scale(${K})`, transformOrigin: "0 0"}}>
                <AppScreen />
              </div>
            </PhoneFrame>
          </div>
          {/* taps live in canvas space, under the same camera */}
          {TAPS.map((t, i) => (
            <TapMark key={i} at={t.f} x={t.x} y={t.y} />
          ))}
        </AbsoluteFill>
      </AbsoluteFill>
      {PRODUCT.map((p) => (
        <StepLabel key={p.id} num={p.num} label={p.label} from={scene(p.id).from + 4} to={scene(p.id).from + scene(p.id).dur} />
      ))}
      {/* sticker bursts escape the camera so they read big */}
      {LANDS.map((l, i) => (
        <StickerBurst key={i} at={l.f} land={l} index={i} />
      ))}
    </AbsoluteFill>
  );
};

