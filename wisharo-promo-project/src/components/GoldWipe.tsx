import React from "react";
import {AbsoluteFill, interpolate, useCurrentFrame} from "remotion";
import {C, curves} from "../theme";

/**
 * A diagonal gold band that sweeps across the frame. Place it so its midpoint
 * (frame = dur/2) sits on the scene cut: the band fully covers the cut.
 */
export const GoldWipe: React.FC<{dur?: number; toColor?: string}> = ({dur = 18, toColor = C.navy}) => {
  const f = useCurrentFrame();
  const p = interpolate(f, [0, dur], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.editorial});
  const x = interpolate(p, [0, 1], [-1.6, 1.6]);
  return (
    <AbsoluteFill style={{pointerEvents: "none", overflow: "hidden"}}>
      <div
        style={{
          position: "absolute",
          left: "-50%",
          top: "-25%",
          width: "200%",
          height: "150%",
          transform: `translateX(${x * 100}%) skewX(-18deg)`,
          background: `linear-gradient(90deg, rgba(212,169,79,0) 0%, ${C.goldDeep} 18%, ${C.gold} 30%, ${C.goldLight} 38%, ${toColor} 46%, ${toColor} 54%, ${C.goldLight} 62%, ${C.gold} 70%, ${C.goldDeep} 82%, rgba(212,169,79,0) 100%)`,
          opacity: 0.98,
        }}
      />
    </AbsoluteFill>
  );
};
