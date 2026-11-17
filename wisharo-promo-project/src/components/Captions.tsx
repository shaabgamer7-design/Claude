import React from "react";
import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {C, FONT} from "../theme";
import {WORDS, sec} from "../timeline";

/** Phrase groups: split after punctuation, max 4 words, so lines stay big. */
const GROUPS: number[][] = (() => {
  const g: number[][] = [];
  let cur: number[] = [];
  WORDS.forEach((w, i) => {
    cur.push(i);
    if (/[.,?!]$/.test(w.text) || cur.length >= 6) {
      g.push(cur);
      cur = [];
    }
  });
  if (cur.length) g.push(cur);
  return g;
})();

/**
 * Word-level animated captions. Each phrase appears as its first word is spoken,
 * the active word turns gold and lifts, and the phrase leaves shortly after its
 * last word. `hidden` frame ranges suppress captions where kinetic type already
 * shows the words.
 */
export const Captions: React.FC<{y?: number; hidden?: [number, number][]}> = ({y = 1430, hidden = []}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (hidden.some(([a, b]) => f >= a && f < b)) return null;

  const gi = GROUPS.findIndex((g, k) => {
    const s = sec(WORDS[g[0]].start) - 2;
    const next = GROUPS[k + 1];
    const e = Math.min(sec(WORDS[g[g.length - 1]].end) + 14, next ? sec(WORDS[next[0]].start) - 2 : 9999);
    return f >= s && f < e;
  });
  if (gi < 0) return null;
  const g = GROUPS[gi];
  const gStart = sec(WORDS[g[0]].start) - 2;
  const gEnd = sec(WORDS[g[g.length - 1]].end) + 14;
  const out = interpolate(f, [gEnd - 6, gEnd], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const boxIn = spring({frame: f - gStart, fps, config: {damping: 18, stiffness: 220}});

  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        right: 60,
        top: y,
        display: "flex",
        justifyContent: "center",
        opacity: out,
        transform: `translateY(${(1 - boxIn) * 24}px)`,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "0 22px",
          padding: "20px 38px 24px",
          borderRadius: 34,
          background: "rgba(11,18,32,0.72)",
          border: "1.5px solid rgba(212,169,79,0.35)",
          boxShadow: "0 18px 50px rgba(0,0,0,0.35)",
          backdropFilter: "blur(10px)",
          maxWidth: 940,
        }}
      >
        {g.map((wi) => {
          const w = WORDS[wi];
          const ws = sec(w.start);
          const we = sec(w.end);
          const pop = spring({frame: f - ws + 1, fps, config: {damping: 13, stiffness: 260, mass: 0.6}});
          const active = f >= ws - 1 && f < Math.max(we, ws + 6);
          const spoken = f >= ws - 1;
          return (
            <span
              key={wi}
              style={{
                fontFamily: FONT.head,
                fontWeight: 800,
                fontSize: 74,
                lineHeight: 1.12,
                letterSpacing: -1.2,
                color: active ? C.gold : C.ivory,
                opacity: spoken ? 1 : 0.28,
                display: "inline-block",
                transform: `translateY(${spoken ? (1 - pop) * 18 - (active ? 4 : 0) : 0}px) scale(${spoken ? 0.86 + 0.14 * pop : 0.92})`,
                textShadow: active ? "0 0 26px rgba(212,169,79,0.55)" : "0 2px 10px rgba(0,0,0,0.4)",
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
