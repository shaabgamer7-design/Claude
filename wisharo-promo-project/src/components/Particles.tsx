import React from "react";
import {AbsoluteFill, random, useCurrentFrame} from "remotion";
import {C, VIDEO} from "../theme";

/** Light gold dust drifting upward. Fully deterministic (seeded). */
export const Particles: React.FC<{count?: number; seed?: string; opacity?: number; color?: string}> = ({
  count = 60,
  seed = "dust",
  opacity = 1,
  color = C.goldLight,
}) => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{pointerEvents: "none", opacity}}>
      {new Array(count).fill(0).map((_, i) => {
        const r = (k: string) => random(`${seed}-${i}-${k}`);
        const size = 2 + r("s") * 5;
        const speed = 0.25 + r("v") * 0.9;
        const x0 = r("x") * VIDEO.width;
        const y0 = r("y") * (VIDEO.height + 200);
        const y = ((y0 - frame * speed) % (VIDEO.height + 200) + VIDEO.height + 200) % (VIDEO.height + 200) - 100;
        const x = x0 + Math.sin(frame / (40 + r("w") * 60) + r("p") * 6.28) * (14 + r("a") * 26);
        const tw = 0.35 + 0.65 * Math.abs(Math.sin(frame / (12 + r("t") * 26) + r("q") * 6.28));
        const blur = r("b") > 0.75 ? 2.5 : 0;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: "50%",
              background: color,
              opacity: tw * (0.35 + r("o") * 0.55),
              filter: blur ? `blur(${blur}px)` : undefined,
              boxShadow: `0 0 ${size * 3}px ${color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
