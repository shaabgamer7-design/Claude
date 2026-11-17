import React from "react";
import {AbsoluteFill, interpolate, useCurrentFrame} from "remotion";
import {C} from "../theme";

/** Deep navy stage with a slow-moving warm glow and vignette. */
export const NavyBackdrop: React.FC<{glow?: number}> = ({glow = 1}) => {
  const f = useCurrentFrame();
  const gx = 50 + Math.sin(f / 90) * 12;
  const gy = 38 + Math.cos(f / 110) * 8;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 70% 45% at ${gx}% ${gy}%, rgba(212,169,79,${0.16 * glow}) 0%, rgba(212,169,79,0) 60%),
          radial-gradient(ellipse 80% 50% at 50% 100%, rgba(31,77,58,${0.38 * glow}) 0%, rgba(31,77,58,0) 70%),
          linear-gradient(180deg, ${C.navy} 0%, ${C.navy2} 55%, ${C.navy} 100%)`,
      }}
    >
      <AbsoluteFill style={{background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.45) 100%)"}} />
      <AbsoluteFill
        style={{
          opacity: 0.05,
          backgroundImage:
            "repeating-linear-gradient(115deg, rgba(255,255,255,0.6) 0px, rgba(255,255,255,0.6) 1px, transparent 1px, transparent 9px)",
          transform: `translateX(${interpolate(f, [0, 900], [0, -60])}px)`,
        }}
      />
    </AbsoluteFill>
  );
};

export const IvoryBackdrop: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 75% 45% at 50% ${40 + Math.sin(f / 70) * 4}%, #fffdf8 0%, ${C.ivory} 45%, ${C.ivory2} 100%)`,
      }}
    >
      <AbsoluteFill style={{background: "radial-gradient(ellipse at center, rgba(0,0,0,0) 60%, rgba(120,90,30,0.10) 100%)"}} />
    </AbsoluteFill>
  );
};
