import React from "react";
import {C, PHONE, PHONE_OUTER} from "../theme";

/** Premium phone shell: graphite body, warm gold edge light, dynamic island, layered soft shadows. */
export const PhoneFrame: React.FC<{children: React.ReactNode}> = ({children}) => {
  return (
    <div
      style={{
        position: "relative",
        width: PHONE_OUTER.w,
        height: PHONE_OUTER.h,
        borderRadius: PHONE.radius + PHONE.bezel,
        background: "linear-gradient(145deg, #3a3f4a 0%, #15181f 28%, #0a0c10 60%, #2a2e36 100%)",
        boxShadow: [
          "0 0 0 2px rgba(243,220,158,0.55)",
          "0 0 0 3.5px rgba(20,22,28,1)",
          "0 4px 10px rgba(0,0,0,0.35)",
          "0 30px 60px rgba(0,0,0,0.45)",
          "0 80px 140px rgba(0,0,0,0.55)",
          "0 0 120px rgba(212,169,79,0.18)",
        ].join(", "),
      }}
    >
      {/* side buttons */}
      {[
        {top: 250, h: 70, side: "left"},
        {top: 350, h: 110, side: "left"},
        {top: 480, h: 110, side: "left"},
        {top: 330, h: 170, side: "right"},
      ].map((b, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            top: b.top,
            [b.side]: -5,
            width: 6,
            height: b.h,
            borderRadius: 3,
            background: "linear-gradient(90deg, #4a4f5a, #1a1d23)",
          }}
        />
      ))}
      <div
        style={{
          position: "absolute",
          left: PHONE.bezel,
          top: PHONE.bezel,
          width: PHONE.screenW,
          height: PHONE.screenH,
          borderRadius: PHONE.radius,
          overflow: "hidden",
          background: C.ivory,
        }}
      >
        {children}
        {/* glass reflection */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "linear-gradient(125deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.02) 32%, rgba(255,255,255,0) 50%)",
            pointerEvents: "none",
          }}
        />
        {/* dynamic island */}
        <div
          style={{
            position: "absolute",
            top: 16,
            left: "50%",
            width: 150,
            height: 42,
            marginLeft: -75,
            borderRadius: 22,
            background: "#050608",
          }}
        />
      </div>
    </div>
  );
};
