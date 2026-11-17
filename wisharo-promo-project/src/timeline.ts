import vo from "./data/vo_timeline.json";
import words from "./data/words.json";

export const FPS = 30;
export const sec = (s: number) => Math.round(s * FPS);

export type SceneId = "problem" | "reveal" | "pick" | "background" | "stickers" | "language" | "cta";

const voById = Object.fromEntries(vo.map((v) => [v.id, v])) as unknown as Record<SceneId, {voStart: number; voEnd: number}>;

/**
 * Scene boundaries come from the narration: each scene starts a beat before its
 * line and runs until the next scene. Total = 900 frames (30.0 s).
 */
const starts: Record<SceneId, number> = {
  problem: 0,
  reveal: sec(voById.reveal.voStart) - 12, // logo lands just before "Meet"
  pick: sec(voById.pick.voStart) - 8,
  background: sec(voById.background.voStart) - 8,
  stickers: sec(voById.stickers.voStart) - 8,
  language: sec(voById.language.voStart) - 8,
  cta: sec(voById.cta.voStart) - 8,
};
const order: SceneId[] = ["problem", "reveal", "pick", "background", "stickers", "language", "cta"];
export const TOTAL = 900;

export const SCENES = order.map((id, i) => {
  const from = starts[id];
  const to = i + 1 < order.length ? starts[order[i + 1]] : TOTAL;
  return {id, from, dur: to - from, voStart: sec(voById[id].voStart), voEnd: sec(voById[id].voEnd)};
});
export const scene = (id: SceneId) => SCENES.find((s) => s.id === id)!;

export type Word = {text: string; start: number; end: number};
export const WORDS = words as Word[];
/** frame at which the first word matching `text` (case-insensitive, after index `after`) starts */
export const wordFrame = (text: string, after = 0) => {
  const i = WORDS.findIndex((w, k) => k >= after && w.text.toLowerCase().replace(/[^a-z-]/g, "") === text.toLowerCase());
  return i < 0 ? 0 : sec(WORDS[i].start);
};
export const wordIndex = (text: string, after = 0) =>
  WORDS.findIndex((w, k) => k >= after && w.text.toLowerCase().replace(/[^a-z-]/g, "") === text.toLowerCase());

/** Phone stage spans the four product scenes plus its entrance at the end of the reveal. */
export const PHONE_IN = scene("pick").from - 30;
export const PHONE_OUT = scene("cta").from;
