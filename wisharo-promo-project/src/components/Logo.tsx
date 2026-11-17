import React from "react";
import {Img, interpolate, staticFile, useCurrentFrame} from "remotion";
import {C, curves} from "../theme";

/** Wisharo leaf mark in a gold-ringed medallion. The ring draws on from `at`. */
export const LogoMedallion: React.FC<{size: number; at?: number}> = ({size, at = 0}) => {
  const f = useCurrentFrame();
  const ring = interpolate(f, [at, at + 26], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.enter});
  const sweep = interpolate(f, [at + 10, at + 40], [-120, 220], {extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: curves.editorial});
  const r = size / 2 + 14;
  const circ = 2 * Math.PI * r;
  return (
    <div style={{position: "relative", width: size, height: size}}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "50%",
          overflow: "hidden",
          boxShadow: "0 30px 80px rgba(0,0,0,0.5), 0 0 90px rgba(212,169,79,0.28)",
        }}
      >
        <Img src={staticFile("brand/favicon512.png")} style={{width: "100%", height: "100%", transform: "scale(1.08)"}} />
        <div
          style={{
            position: "absolute",
            top: 0,
            bottom: 0,
            width: "45%",
            left: `${sweep}%`,
            background: "linear-gradient(100deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.55) 50%, rgba(255,255,255,0) 100%)",
            transform: "skewX(-15deg)",
          }}
        />
      </div>
      <svg width={size + 40} height={size + 40} style={{position: "absolute", left: -20, top: -20, overflow: "visible"}}>
        <circle
          cx={(size + 40) / 2}
          cy={(size + 40) / 2}
          r={r}
          fill="none"
          stroke={C.gold}
          strokeWidth={4}
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - ring)}
          strokeLinecap="round"
          transform={`rotate(-90 ${(size + 40) / 2} ${(size + 40) / 2})`}
          style={{filter: "drop-shadow(0 0 10px rgba(212,169,79,0.8))"}}
        />
      </svg>
    </div>
  );
};
