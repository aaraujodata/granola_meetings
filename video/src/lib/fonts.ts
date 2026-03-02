import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadJetBrainsMono } from "@remotion/google-fonts/JetBrainsMono";

const { fontFamily: interFamily } = loadInter("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

const { fontFamily: monoFamily } = loadJetBrainsMono("normal", {
  weights: ["400"],
  subsets: ["latin"],
});

export const fontFamilySans = interFamily;
export const fontFamilyMono = monoFamily;
