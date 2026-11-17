import {Easing} from "remotion";
import {loadFont as loadPoppins} from "@remotion/google-fonts/Poppins";
import {loadFont as loadLora} from "@remotion/google-fonts/Lora";

const poppins = loadPoppins("normal", {weights: ["400", "500", "600", "700", "800"], subsets: ["latin"]});
const lora = loadLora("italic", {weights: ["400", "500", "600"], subsets: ["latin"]});
loadLora("normal", {weights: ["600", "700"], subsets: ["latin"]});

export const FONT = {
  head: poppins.fontFamily,
  wish: lora.fontFamily,
  serif: lora.fontFamily,
};

export const C = {
  navy: "#0b1220",
  navy2: "#131d33",
  navy3: "#1b2742",
  ivory: "#faf6ef",
  ivory2: "#f1e9da",
  gold: "#d4a94f",
  goldLight: "#f3dc9e",
  goldDeep: "#a87f2c",
  forest: "#1f4d3a",
  forestLight: "#2c6a50",
  ink: "#16231c",
};

export const VIDEO = {width: 1080, height: 1920, fps: 30, durationInFrames: 900};

/** 9:16 safe area: keep key content out of platform UI (top bar, right rail, caption/description area). */
export const SAFE = {top: 170, bottom: 1540, left: 70, right: 930};

export const curves = {
  enter: Easing.bezier(0.16, 1, 0.3, 1),
  exit: Easing.in(Easing.cubic),
  standard: Easing.bezier(0.4, 0, 0.2, 1),
  editorial: Easing.bezier(0.45, 0, 0.55, 1),
  pop: Easing.bezier(0.34, 1.56, 0.64, 1),
};

export const spring1 = {damping: 16, stiffness: 160, mass: 0.8};
export const springSoft = {damping: 22, stiffness: 90, mass: 1};

/** Phone geometry inside the 1080x1920 canvas. Footage is filmed at 390x844 CSS px. */
export const PHONE = {
  screenW: 560,
  screenH: Math.round((560 * 844) / 390), // 1212
  bezel: 18,
  radius: 86,
  cssW: 390,
  cssH: 844,
};
export const PHONE_OUTER = {
  w: PHONE.screenW + PHONE.bezel * 2,
  h: PHONE.screenH + PHONE.bezel * 2,
};
export const PHONE_POS = {
  left: (VIDEO.width - PHONE_OUTER.w) / 2,
  top: 380,
};
