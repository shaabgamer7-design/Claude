/**
 * Code recreation of the wisharo.com flow on a 390x844 phone screen, built from
 * the site's real wish text, New Year backgrounds, stickers and studio labels.
 * Every visible change is driven by the absolute frame (see data/flow.ts).
 */
import React from "react";
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {C, FONT, curves} from "../theme";
import {
  BGS, BG_TILE_Y, CANVAS, CARD_H, F, GOLD_SWATCH, GRID, IT_WISHES, LANGS, LANG_PILL, PAGE_WISHES, PLACED,
  SCROLL, SWATCHES, SWATCH_Y, TABS, TARGET, bgTileX, cardTop, gridPos, langRowY, swatchX, tabX,
} from "../data/flow";

const clamp = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const ease = (f: number, a: number, b: number, e = curves.enter) => interpolate(f, [a, b], [0, 1], {...clamp, easing: e});

const GREEN = "#1f4b38";
const SITE_GOLD = "#b8995a";
const SANS = FONT.head;

/* ---------------------------------- page ---------------------------------- */

const CopyCard: React.FC<{i: number; text: string; pressed: number}> = ({i, text, pressed}) => (
  <div
    style={{
      position: "absolute",
      left: 16,
      right: 16,
      top: cardTop(i),
      height: CARD_H,
      borderRadius: 16,
      padding: "16px 16px 0 16px",
      background: "linear-gradient(160deg, #fffaf0 0%, #fbf1dc 100%)",
      border: `1.5px solid ${SITE_GOLD}`,
      boxShadow: i === TARGET ? `0 8px 22px rgba(184,153,90,${0.18 + pressed * 0.3})` : "0 4px 12px rgba(31,75,56,0.06)",
    }}
  >
    <div style={{fontFamily: FONT.wish, fontStyle: "italic", fontSize: 18.5, lineHeight: 1.38, color: "#16231c"}}>{text}</div>
    <div
      style={{
        position: "absolute",
        right: 120,
        bottom: 14,
        minWidth: 112,
        height: 32,
        borderRadius: 999,
        border: `1px solid ${SITE_GOLD}`,
        background: i === TARGET && pressed > 0 ? `rgba(184,153,90,${0.25 * pressed})` : "#fff",
        color: "#6b5428",
        fontFamily: SANS,
        fontWeight: 600,
        fontSize: 12.2,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 6,
        transform: `scale(${1 - pressed * 0.06})`,
      }}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={SITE_GOLD} strokeWidth="2">
        <rect x="4" y="3" width="16" height="18" rx="2" />
        <path d="M8 15l3-3 2 2 3-4" />
      </svg>
      Make card
    </div>
    <div
      style={{
        position: "absolute",
        right: 12,
        bottom: 14,
        minWidth: 96,
        height: 32,
        borderRadius: 999,
        border: `1px solid ${GREEN}`,
        background: "#fff",
        color: GREEN,
        fontFamily: SANS,
        fontWeight: 600,
        fontSize: 12.2,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      Copy
    </div>
  </div>
);

const Page: React.FC = () => {
  const f = useCurrentFrame();
  const scroll = interpolate(f, [F.scrollStart, F.scrollEnd], [0, SCROLL], {...clamp, easing: curves.editorial});
  const pressed = interpolate(f, [F.tapMake - 4, F.tapMake, F.tapMake + 8], [0, 1, 0.6], clamp);
  return (
    <AbsoluteFill style={{background: "linear-gradient(160deg, #e3f4ea 0%, #fdf3e3 45%, #fbe6ea 100%)", overflow: "hidden"}}>
      <div style={{position: "absolute", left: 0, right: 0, top: 0, transform: `translateY(${-scroll}px)`}}>
        <div style={{position: "absolute", left: 8, right: 8, top: 104, height: 1400, borderRadius: 22, background: "rgba(255,255,255,0.88)"}} />
        <div style={{position: "absolute", left: 24, top: 120, fontFamily: SANS, fontSize: 13, color: "#4c6b5a"}}>Home › Daily Blessings</div>
        <div style={{position: "absolute", left: 24, right: 24, top: 142, fontFamily: SANS, fontWeight: 700, fontSize: 25, lineHeight: 1.18, color: "#17231c", letterSpacing: -0.4}}>
          Tuesday Blessings: 160 Messages, Wishes and Quotes to Share
        </div>
        <div style={{position: "absolute", left: 24, top: 256, fontFamily: FONT.serif, fontWeight: 700, fontSize: 21, color: "#17382a"}}>Short Tuesday Blessings</div>
        {PAGE_WISHES.map((w, i) => (
          <CopyCard key={i} i={i} text={w} pressed={i === TARGET ? pressed : 0} />
        ))}
      </div>
      {/* sticky header */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 0,
          height: 100,
          paddingTop: 44,
          background: "linear-gradient(90deg, rgba(220,245,232,0.97), rgba(253,240,214,0.97))",
          boxShadow: scroll > 4 ? "0 4px 14px rgba(0,0,0,0.08)" : "none",
          display: "flex",
          alignItems: "center",
          gap: 10,
          paddingLeft: 16,
        }}
      >
        <Img src={staticFile("brand/favicon512.png")} style={{width: 38, height: 38, borderRadius: 19}} />
        <div>
          <div style={{fontFamily: FONT.serif, fontWeight: 700, fontSize: 24, color: "#17382a", lineHeight: 1}}>Wisharo</div>
          <div style={{fontFamily: SANS, fontSize: 7.5, letterSpacing: 1.6, color: "#8a6d2f", marginTop: 3}}>BEAUTIFUL WORDS. MEANINGFUL BLESSINGS.</div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* --------------------------------- editor --------------------------------- */

const Icon: React.FC<{k: string; color: string}> = ({k, color}) => {
  const p = {fill: "none", stroke: color, strokeWidth: 1.9, strokeLinecap: "round", strokeLinejoin: "round"} as const;
  return (
    <svg width="22" height="22" viewBox="0 0 24 24">
      {k === "grid" && <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" {...p} /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" {...p} /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" {...p} /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" {...p} /></>}
      {k === "text" && <><path d="M5 6V4.5h14V6M12 4.5v15M9 19.5h6" {...p} /></>}
      {k === "quote" && <><path d="M4.5 6.5a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H11l-4 3.5v-3.5H6.5a2 2 0 0 1-2-2z" {...p} /><path d="M8.5 9.5h7M8.5 12.5h4.5" {...p} /></>}
      {k === "star" && <path d="M12 3.5l2.4 5.2 5.6.6-4.2 3.8 1.2 5.5L12 15.8l-5 2.8 1.2-5.5L4 9.3l5.6-.6z" {...p} />}
      {k === "image" && <><rect x="3.5" y="4.5" width="17" height="15" rx="2" {...p} /><path d="M6.5 16.5l4-4 3 3 2-2 2.5 3" {...p} /><circle cx="15.5" cy="9" r="1.6" {...p} /></>}
    </svg>
  );
};

const Sticker: React.FC<{name: string; size: number; style?: React.CSSProperties}> = ({name, size, style}) => (
  <Img src={staticFile(`stickers/${name}.svg`)} style={{width: size, height: size, ...style}} />
);

const Editor: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const it = f >= F.translated;
  const L = (en: string, itx: string) => (it ? itx : en);

  const bgDark = ease(f, F.bgChange, F.bgChange + 12, curves.standard);
  const wishSwap = ease(f, F.itWish, F.itWish + 10, curves.standard);

  // which panel the bottom sheet shows, and how open it is
  type Sheet = "bg" | "el" | "colour" | "wishes";
  const sheet: Sheet = f >= F.wishSheet ? "wishes" : f >= F.tapSelect + 2 ? "colour" : f >= F.elSheet ? "el" : "bg";
  const sheetStart = {bg: F.bgSheet, el: F.elSheet, colour: F.tapSelect + 2, wishes: F.wishSheet}[sheet];
  const sheetIn = ease(f, sheetStart, sheetStart + 10);
  const openAmt =
    f < F.wishSheet && f >= F.tapLang - 4
      ? 1 - ease(f, F.tapLang - 4, F.tapLang + 4, curves.exit)
      : f >= F.wishSheet
        ? ease(f, F.wishSheet, F.wishSheet + 10)
        : ease(f, F.bgSheet, F.bgSheet + 10);
  const activeTab =
    f >= F.tapWishesTab ? 2 : f >= F.tapLang - 4 ? -1 : f >= F.tapElTab ? 3 : f >= F.tapBgTab ? 4 : -1;
  const recolour = ease(f, F.tapGold + 2, F.tapGold + 12, curves.standard);
  const selected = f >= F.tapSelect && f < F.tapGold + 24;
  const menu = f >= F.langMenu && f < F.tapItaliano + 8;
  const menuIn = ease(f, F.langMenu, F.langMenu + 8);
  const menuOut = 1 - ease(f, F.tapItaliano + 2, F.tapItaliano + 8, curves.exit);
  const coach = interpolate(f, [F.editorIn + 16, F.editorIn + 24, F.tapBgTab - 6, F.tapBgTab], [0, 1, 1, 0], clamp);

  const sheetY = 776 - 262; // top of sheet when open
  return (
    <AbsoluteFill style={{background: "linear-gradient(180deg, #f6f1e7 0%, #efe7d6 100%)"}}>
      {/* top bar */}
      <div style={{position: "absolute", left: 0, right: 0, top: 44, height: 52, display: "flex", alignItems: "center", padding: "0 14px"}}>
        <div style={{width: 34, height: 34, borderRadius: 17, background: "#fff", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 2px 6px rgba(0,0,0,0.08)", fontFamily: SANS, fontSize: 16, color: "#33413a"}}>✕</div>
        <div style={{marginLeft: 12, fontFamily: SANS, fontWeight: 700, fontSize: 15, color: "#17382a"}}>
          Wisharo <span style={{color: "#a8853a"}}>Studio</span>
        </div>
      </div>
      {/* language pill (real switcher: pill + menu) */}
      <div
        style={{
          position: "absolute",
          left: LANG_PILL.x - 54,
          top: LANG_PILL.y - 16,
          width: 108,
          height: 32,
          borderRadius: 999,
          border: "1px solid rgba(0,0,0,0.16)",
          background: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 5,
          fontFamily: SANS,
          fontSize: 12.5,
          color: "#222",
          transform: `scale(${1 - interpolate(f, [F.tapLang - 3, F.tapLang, F.tapLang + 5], [0, 0.07, 0], clamp)})`,
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#555" strokeWidth="1.8">
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18" />
        </svg>
        {it ? "Italiano" : "English"} <span style={{fontSize: 8, opacity: 0.6}}>▼</span>
      </div>

      {/* canvas card */}
      <div
        style={{
          position: "absolute",
          left: CANVAS.x,
          top: CANVAS.y,
          width: CANVAS.w,
          height: CANVAS.h,
          borderRadius: 6,
          overflow: "hidden",
          boxShadow: "0 14px 34px rgba(40,30,10,0.22)",
          background: "#fbf6ea",
        }}
      >
        <div style={{position: "absolute", inset: 12, border: `1.5px solid ${SITE_GOLD}`, borderRadius: 3, opacity: 1 - bgDark}} />
        <Img src={staticFile("site/bg/midnight-fireworks-4x5.png")} style={{position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", opacity: bgDark}} />
        {/* wish text */}
        {[
          {text: PAGE_WISHES[TARGET], o: 1 - wishSwap},
          {text: IT_WISHES[0], o: wishSwap},
        ].map((w, k) => (
          <div
            key={k}
            style={{
              position: "absolute",
              left: 34,
              right: 34,
              top: 150,
              height: 140,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              fontFamily: FONT.wish,
              fontStyle: "italic",
              fontWeight: 500,
              fontSize: 24,
              lineHeight: 1.32,
              color: bgDark > 0.5 ? "#fbf3df" : "#17382a",
              textShadow: bgDark > 0.5 ? "0 0 14px rgba(212,169,79,0.65)" : "none",
              opacity: w.o,
              transform: `translateY(${k === 1 ? (1 - wishSwap) * 10 : -wishSwap * 10}px)`,
            }}
          >
            {w.text}
          </div>
        ))}
        <div style={{position: "absolute", bottom: 14, left: 0, right: 0, textAlign: "center", fontFamily: SANS, fontSize: 9, letterSpacing: 1, color: bgDark > 0.5 ? "rgba(243,220,158,0.8)" : "#8a7a5a"}}>
          wisharo.com
        </div>
        {/* placed stickers */}
        {PLACED.map((p, k) => {
          const s = spring({frame: f - p.at - 2, fps, config: {damping: 11, stiffness: 190, mass: 0.7}});
          if (f < p.at + 2) return null;
          const x = p.x - CANVAS.x;
          const y = p.y - CANVAS.y;
          return (
            <div key={k} style={{position: "absolute", left: x - p.size / 2, top: y - p.size / 2, width: p.size, height: p.size, transform: `scale(${s}) rotate(${(1 - s) * -25}deg)`}}>
              <Sticker name={p.sticker} size={p.size} style={{position: "absolute", opacity: k === 0 ? 1 - recolour : 1}} />
              {k === 0 && <Sticker name="balloons_gold" size={p.size} style={{position: "absolute", opacity: recolour}} />}
              {k === 0 && selected && (
                <div style={{position: "absolute", inset: -6, border: "1.5px dashed #3d6fd1", borderRadius: 4}}>
                  {[[-4, -4], [p.size + 4, -4], [-4, p.size + 4], [p.size + 4, p.size + 4]].map(([cx, cy], q) => (
                    <div key={q} style={{position: "absolute", left: cx - 5, top: cy - 5, width: 10, height: 10, borderRadius: 5, background: "#fff", border: "1.5px solid #3d6fd1"}} />
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
      <div style={{position: "absolute", left: 0, right: 0, top: 492, textAlign: "center", fontFamily: SANS, fontSize: 12.5, color: "#6a5a3a", opacity: coach}}>
        Tap any words on the card
      </div>

      {/* bottom sheet */}
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: sheetY,
          height: 262,
          borderRadius: "20px 20px 0 0",
          background: "#fff",
          boxShadow: "0 -8px 24px rgba(0,0,0,0.10)",
          transform: `translateY(${(1 - openAmt) * 280}px)`,
        }}
      >
        <div style={{position: "absolute", top: 8, left: 175, width: 40, height: 4, borderRadius: 2, background: "#ddd"}} />
        <div style={{position: "absolute", inset: 0, opacity: sheet === "bg" || sheet === "wishes" ? 1 : sheetIn, transform: `translateY(${sheet === "bg" || sheet === "wishes" ? 0 : (1 - sheetIn) * 14}px)`}}>
          {sheet === "bg" && (
            <>
              <div style={{position: "absolute", left: 18, top: 24, fontFamily: SANS, fontWeight: 700, fontSize: 15, color: "#17231c"}}>New Year backgrounds</div>
              <div style={{position: "absolute", left: 18, top: 46, fontFamily: SANS, fontSize: 12, color: "#7a6a4a"}}>Tap one to use it</div>
              {BGS.map((b, i) => {
                const chosen = i === 0 && f >= F.tapMidnight;
                return (
                  <div key={b.id} style={{position: "absolute", left: bgTileX(i) - 46, top: BG_TILE_Y - sheetY - 46}}>
                    <Img
                      src={staticFile(`site/bg/${b.id}-thumb.png`)}
                      style={{width: 92, height: 92, borderRadius: 12, objectFit: "cover", boxShadow: chosen ? `0 0 0 3px ${C.gold}` : "0 2px 6px rgba(0,0,0,0.12)"}}
                    />
                    <div style={{width: 96, marginTop: 6, fontFamily: SANS, fontSize: 10.5, color: "#33413a", textAlign: "center", whiteSpace: "nowrap"}}>{b.name}</div>
                  </div>
                );
              })}
            </>
          )}
          {sheet === "el" && (
            <>
              <div style={{position: "absolute", left: 14, top: 22, display: "flex", gap: 8}}>
                {["New Year & Party", "Florals", "Love", "Celebration"].map((c, i) => (
                  <div
                    key={c}
                    style={{
                      padding: "6px 12px",
                      borderRadius: 999,
                      fontFamily: SANS,
                      fontSize: 12,
                      fontWeight: 600,
                      whiteSpace: "nowrap",
                      background: i === 0 ? C.gold : "#f3eee3",
                      color: i === 0 ? "#fff" : "#5a4a2a",
                    }}
                  >
                    {c}
                  </div>
                ))}
              </div>
              {GRID.map((g, i) => {
                const p = gridPos(i);
                const tapped = PLACED.find((q) => q.grid === i);
                const press = tapped ? interpolate(f, [tapped.at - 3, tapped.at, tapped.at + 6], [0, 1, 0], clamp) : 0;
                return (
                  <div
                    key={g}
                    style={{
                      position: "absolute",
                      left: p.x - 38,
                      top: p.y - sheetY - 38,
                      width: 76,
                      height: 76,
                      borderRadius: 14,
                      background: press > 0 ? `rgba(212,169,79,${0.25 * press})` : "#faf6ef",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      transform: `scale(${1 - press * 0.08})`,
                    }}
                  >
                    <Sticker name={g} size={58} />
                  </div>
                );
              })}
            </>
          )}
          {sheet === "colour" && (
            <>
              <div style={{position: "absolute", left: 18, top: 24, fontFamily: SANS, fontWeight: 700, fontSize: 15, color: "#17231c"}}>Colour</div>
              <div style={{position: "absolute", left: 18, top: 46, fontFamily: SANS, fontSize: 12, color: "#7a6a4a"}}>Balloon bunch</div>
              {SWATCHES.map((c, i) => {
                const on = i === GOLD_SWATCH ? f >= F.tapGold : i === 0 && f < F.tapGold;
                return (
                  <div
                    key={c}
                    style={{
                      position: "absolute",
                      left: swatchX(i) - 18,
                      top: SWATCH_Y - sheetY - 18,
                      width: 36,
                      height: 36,
                      borderRadius: 18,
                      background: c,
                      border: "1px solid rgba(0,0,0,0.12)",
                      boxShadow: on ? `0 0 0 3px #fff, 0 0 0 5px ${C.gold}` : "none",
                    }}
                  />
                );
              })}
            </>
          )}
          {sheet === "wishes" && (
            <>
              <div style={{position: "absolute", left: 18, top: 24, fontFamily: SANS, fontWeight: 700, fontSize: 15, color: "#17231c"}}>Auguri e frasi</div>
              {IT_WISHES.map((w, i) => {
                const press = i === 0 ? interpolate(f, [F.tapItWish - 3, F.tapItWish, F.tapItWish + 8], [0, 1, 0.4], clamp) : 0;
                return (
                  <div
                    key={i}
                    style={{
                      position: "absolute",
                      left: 14,
                      right: 14,
                      top: 56 + i * 62,
                      height: 52,
                      borderRadius: 12,
                      border: `1px solid ${press > 0.1 ? C.gold : "#eee4cf"}`,
                      background: press > 0 ? `rgba(212,169,79,${0.18 * press})` : "#fffaf0",
                      padding: "0 14px",
                      display: "flex",
                      alignItems: "center",
                      fontFamily: FONT.wish,
                      fontStyle: "italic",
                      fontSize: 15.5,
                      color: "#17231c",
                    }}
                  >
                    {w}
                  </div>
                );
              })}
            </>
          )}
        </div>
      </div>

      {/* tab bar */}
      <div style={{position: "absolute", left: 0, right: 0, top: 776, height: 68, background: "#fff", borderTop: "1px solid #eee4cf"}}>
        {TABS.map((t, i) => {
          const on = i === activeTab;
          const col = on ? "#a8853a" : "#59655f";
          return (
            <div key={t.en} style={{position: "absolute", left: tabX(i) - 39, top: 6, width: 78, display: "flex", flexDirection: "column", alignItems: "center", gap: 2}}>
              <Icon k={t.icon} color={col} />
              <div style={{fontFamily: SANS, fontSize: 10.5, fontWeight: on ? 700 : 500, color: col}}>{L(t.en, t.it)}</div>
            </div>
          );
        })}
        <div style={{position: "absolute", bottom: 7, left: 128, width: 134, height: 5, borderRadius: 3, background: "#111"}} />
      </div>

      {/* language menu */}
      {menu && (
        <div
          style={{
            position: "absolute",
            left: 170,
            top: 92,
            width: 206,
            borderRadius: 12,
            background: "#fff",
            border: "1px solid rgba(0,0,0,0.12)",
            boxShadow: "0 14px 36px rgba(0,0,0,0.2)",
            padding: 6,
            opacity: menuIn * menuOut,
            transform: `translateY(${(1 - menuIn) * -8}px) scale(${0.96 + 0.04 * menuIn})`,
            transformOrigin: "100% 0%",
          }}
        >
          {LANGS.map((l, i) => {
            const chosen = i === 4 ? f >= F.tapItaliano : i === 0 && f < F.tapItaliano;
            return (
              <div
                key={l.small}
                style={{
                  position: "absolute",
                  left: 6,
                  right: 6,
                  top: langRowY(i) - 92 - 18,
                  height: 36,
                  borderRadius: 8,
                  background: chosen ? "#efe3c4" : "transparent",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0 12px",
                  fontFamily: SANS,
                  fontSize: 14,
                  fontWeight: chosen ? 600 : 400,
                  color: "#222",
                }}
              >
                <span>{l.native}</span>
                <span style={{fontSize: 11, opacity: 0.6}}>{l.small}</span>
              </div>
            );
          })}
          <div style={{height: LANGS.length * 42 + 2}} />
        </div>
      )}
    </AbsoluteFill>
  );
};

export const AppScreen: React.FC = () => {
  const f = useCurrentFrame();
  const slide = ease(f, F.editorIn, F.editorIn + 14, curves.enter);
  return (
    <AbsoluteFill style={{overflow: "hidden"}}>
      {f < F.editorIn + 16 && (
        <AbsoluteFill style={{transform: `translateY(${-slide * 120}px)`, filter: `brightness(${1 - slide * 0.25})`}}>
          <Page />
        </AbsoluteFill>
      )}
      {f >= F.editorIn && (
        <AbsoluteFill style={{transform: `translateY(${(1 - slide) * 844}px)`, borderRadius: 24, overflow: "hidden", boxShadow: "0 -10px 30px rgba(0,0,0,0.2)"}}>
          <Editor />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
