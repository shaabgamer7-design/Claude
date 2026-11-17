/**
 * The on-phone story, in absolute frames, keyed to the narration's word times
 * (see words.json). Coordinates are CSS px on a 390x844 phone screen.
 */
import {wordFrame} from "../timeline";

const MAKE = wordFrame("make", 20); // "...tap Make card"
const CHOOSE = wordFrame("choose");
const BACKGROUND = wordFrame("background");
const BALLOONS = wordFrame("balloons");
const SPARKLES = wordFrame("sparkles");
const CONFETTI = wordFrame("confetti");
const SWITCH = wordFrame("switch");
const ITALIAN = wordFrame("italian");

export const F = {
  scrollStart: 292,
  scrollEnd: MAKE - 12,
  tapMake: MAKE + 2,
  editorIn: MAKE + 10,
  tapBgTab: CHOOSE + 4,
  bgSheet: CHOOSE + 8,
  tapMidnight: BACKGROUND + 2,
  bgChange: BACKGROUND + 6,
  tapElTab: wordFrame("add", 29) + 3,
  elSheet: wordFrame("add", 29) + 7,
  tapBalloons: BALLOONS,
  tapPopper: BALLOONS + 12,
  tapSparkles: SPARKLES,
  tapConfetti: CONFETTI,
  tapSelect: CONFETTI + 20,
  tapGold: CONFETTI + 36,
  tapLang: SWITCH + 2,
  langMenu: SWITCH + 6,
  tapItaliano: ITALIAN + 2,
  translated: ITALIAN + 6,
  tapWishesTab: ITALIAN + 18,
  wishSheet: ITALIAN + 22,
  tapItWish: ITALIAN + 38,
  itWish: ITALIAN + 42,
};

/** Toolbar tabs (real studio labels, English | Italiano). */
export const TABS = [
  {en: "Templates", it: "Modelli", icon: "grid"},
  {en: "Text", it: "Testo", icon: "text"},
  {en: "Wishes", it: "Auguri", icon: "quote"},
  {en: "Elements", it: "Elementi", icon: "star"},
  {en: "Background", it: "Sfondo", icon: "image"},
] as const;
export const tabX = (i: number) => 39 + i * 78;
export const TAB_Y = 800;

/** Tuesday Blessings page: real wishes from wisharo.com/tuesday-blessings/ */
export const PAGE_WISHES = [
  "Happy Tuesday. Hope the day hands you something good.",
  "Sending you a calm Tuesday and a clear head.",
  "You handled Monday. Tuesday doesn’t stand a chance.",
  "Wishing you small wins and a good lunch today.",
  "Blessings on your Tuesday and the people at your table.",
  "One day down, and today’s already looking brighter.",
  "Hope your Tuesday brings one piece of good news.",
];
export const TARGET = 3;
export const CARD_TOP = 300;
export const CARD_H = 128;
export const CARD_GAP = 14;
export const SCROLL = 262;
export const cardTop = (i: number) => CARD_TOP + i * (CARD_H + CARD_GAP);
export const MAKE_BTN = {x: 198, y: cardTop(TARGET) + CARD_H - 30 - SCROLL};

/** Real Italian New Year wish from wisharo.com/it/frasi-capodanno/ */
export const IT_WISHES = [
  "Buon 2027! Fai il pieno di cose belle.",
  "Che il 2027 sia gentile con te.",
  "Felice anno nuovo a te e a chi ami.",
];

/** New Year backgrounds in studio order (Moonlit Stars sits off-screen in the row). */
export const BGS = [
  {id: "midnight-fireworks", name: "Midnight Fireworks"},
  {id: "champagne-gold", name: "Champagne Gold"},
  {id: "aurora", name: "Aurora Night"},
  {id: "purple-bokeh", name: "Party Bokeh"},
  {id: "rose-sparkle", name: "Rose Sparkle"},
];
export const bgTileX = (i: number) => 16 + 46 + i * 104;
export const BG_TILE_Y = 640;

/** Elements grid, New Year & Party (no bottle/glasses stickers shown). */
export const GRID = ["balloons", "popper", "sparkles", "confetti", "gift", "cake", "goldballoons", "streamers"];
export const gridPos = (i: number) => ({x: 52 + (i % 4) * 95, y: 622 + Math.floor(i / 4) * 86});

/** Canvas (4:5 card) geometry and where each sticker lands on it */
export const CANVAS = {x: 45, y: 104, w: 300, h: 375};
export const PLACED = [
  {sticker: "balloons", at: F.tapBalloons, x: 92, y: 178, size: 96, grid: 0},
  {sticker: "popper", at: F.tapPopper, x: 296, y: 412, size: 78, grid: 1},
  {sticker: "sparkles", at: F.tapSparkles, x: 300, y: 160, size: 66, grid: 2},
  {sticker: "confetti", at: F.tapConfetti, x: 196, y: 138, size: 86, grid: 3},
];
export const SWATCHES = ["#d94f6b", "#3d6fd1", "#d4a94f", "#1f4d3a", "#8e4fd1", "#faf6ef", "#0b1220"];
export const swatchX = (i: number) => 52 + i * 48;
export const SWATCH_Y = 640;
export const GOLD_SWATCH = 2;

export const LANGS = [
  {native: "English", small: "English"},
  {native: "اردو", small: "Urdu"},
  {native: "हिंदी", small: "Hindi"},
  {native: "Roman Urdu", small: "Roman Urdu"},
  {native: "Italiano", small: "Italian"},
];
export const LANG_PILL = {x: 322, y: 70};
export const langRowY = (i: number) => 116 + i * 42;

export type Tap = {f: number; x: number; y: number};
export const TAPS: Tap[] = [
  {f: F.tapMake, ...MAKE_BTN},
  {f: F.tapBgTab, x: tabX(4), y: TAB_Y},
  {f: F.tapMidnight, x: bgTileX(0), y: BG_TILE_Y},
  {f: F.tapElTab, x: tabX(3), y: TAB_Y},
  ...PLACED.map((p) => ({f: p.at, ...gridPos(p.grid)})),
  {f: F.tapSelect, x: PLACED[0].x, y: PLACED[0].y},
  {f: F.tapGold, x: swatchX(GOLD_SWATCH), y: SWATCH_Y},
  {f: F.tapLang, ...LANG_PILL},
  {f: F.tapItaliano, x: 290, y: langRowY(4)},
  {f: F.tapWishesTab, x: tabX(2), y: TAB_Y},
  {f: F.tapItWish, x: 195, y: 640},
];

/** Sticker landings: chime + a copy bursting out of the phone. */
export const LANDS = PLACED.map((p) => ({f: p.at + 4, x: p.x, y: p.y, sticker: p.sticker}));

/** Camera keys: s = zoom, (x, y) = CSS point brought to frame centre. */
export const CAMERA: {f: number; s: number; x: number; y: number}[] = [
  {f: 285, s: 1, x: 195, y: 422},
  {f: 336, s: 1.08, x: 195, y: 440},
  {f: F.tapMake - 10, s: 1.75, x: MAKE_BTN.x, y: MAKE_BTN.y - 30},
  {f: F.tapMake + 8, s: 1.75, x: MAKE_BTN.x, y: MAKE_BTN.y - 30},
  {f: F.editorIn + 22, s: 1.12, x: 195, y: 400},
  {f: F.tapBgTab - 6, s: 1.12, x: 195, y: 410},
  {f: F.bgSheet + 10, s: 1.7, x: 200, y: 600},
  {f: F.tapMidnight + 6, s: 1.7, x: 195, y: 600},
  {f: F.bgChange + 18, s: 1.5, x: 195, y: 300},
  {f: F.tapElTab - 4, s: 1.45, x: 195, y: 330},
  {f: F.elSheet + 10, s: 1.62, x: 195, y: 580},
  {f: F.tapConfetti + 2, s: 1.6, x: 195, y: 560},
  {f: F.tapSelect - 4, s: 1.55, x: 195, y: 330},
  {f: F.tapGold - 2, s: 1.5, x: 195, y: 430},
  {f: F.tapGold + 16, s: 1.5, x: 195, y: 300},
  {f: F.tapLang - 8, s: 1.55, x: 250, y: 220},
  {f: F.langMenu + 8, s: 1.95, x: 290, y: 190},
  {f: F.tapItaliano + 6, s: 1.95, x: 290, y: 200},
  {f: F.wishSheet + 6, s: 1.5, x: 195, y: 520},
  {f: F.tapItWish + 4, s: 1.5, x: 195, y: 500},
  {f: F.itWish + 18, s: 1.5, x: 195, y: 300},
];
