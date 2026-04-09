import React from "react";
import type { CaptionStyleProps } from "../CaptionPage";

const ACTIVE = "#B6FF00";
const IDLE = "#FFFFFF";

const GLOW = (color: string) =>
  `0 0 6px ${color}, 0 0 18px ${color}, 0 0 32px ${color}`;

export const Neon: React.FC<CaptionStyleProps> = ({
  page,
  absoluteTimeMs,
  enterProgress,
}) => {
  return (
    <div
      style={{
        fontFamily: "'Orbitron', Inter, system-ui, sans-serif",
        fontSize: 88,
        fontWeight: 800,
        letterSpacing: 1,
        textAlign: "center",
        lineHeight: 1.1,
        whiteSpace: "pre-wrap",
        color: IDLE,
        textShadow: GLOW("rgba(255,255,255,0.55)"),
        transform: `translateY(${(1 - enterProgress) * 18}px)`,
        opacity: enterProgress,
        maxWidth: "88%",
      }}
    >
      {page.tokens.map((token) => {
        const isActive =
          token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;
        return (
          <span
            key={`${token.fromMs}-${token.text}`}
            style={{
              display: "inline-block",
              color: isActive ? ACTIVE : IDLE,
              textShadow: isActive ? GLOW(ACTIVE) : GLOW("rgba(255,255,255,0.45)"),
              transform: isActive ? "scale(1.05)" : "scale(1)",
              transition: "transform 80ms linear, color 60ms linear",
            }}
          >
            {token.text}
          </span>
        );
      })}
    </div>
  );
};
