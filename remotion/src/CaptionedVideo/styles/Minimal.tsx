import React from "react";
import type { CaptionStyleProps } from "../CaptionPage";

const IDLE = "#FFFFFF";
const ACTIVE = "#FFFFFF";

export const Minimal: React.FC<CaptionStyleProps> = ({
  page,
  absoluteTimeMs,
  enterProgress,
}) => {
  return (
    <div
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        fontSize: 72,
        fontWeight: 600,
        letterSpacing: -0.5,
        textAlign: "center",
        lineHeight: 1.2,
        whiteSpace: "pre-wrap",
        color: IDLE,
        textShadow: "0 2px 18px rgba(0,0,0,0.6)",
        transform: `translateY(${(1 - enterProgress) * 12}px)`,
        opacity: enterProgress,
        maxWidth: "80%",
      }}
    >
      {page.tokens.map((token) => {
        const isActive =
          token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;
        return (
          <span
            key={`${token.fromMs}-${token.text}`}
            style={{
              color: isActive ? ACTIVE : "rgba(255,255,255,0.55)",
              transition: "color 80ms linear",
            }}
          >
            {token.text}
          </span>
        );
      })}
    </div>
  );
};
