import React from "react";
import type { CaptionStyleProps } from "../CaptionPage";

const ACTIVE_BG = "#E10600";
const IDLE = "#FFFFFF";
const STROKE = "#000000";

export const Beast: React.FC<CaptionStyleProps> = ({
  page,
  absoluteTimeMs,
  enterProgress,
}) => {
  return (
    <div
      style={{
        fontFamily: "'Luckiest Guy', Impact, system-ui, sans-serif",
        fontSize: 104,
        fontWeight: 900,
        letterSpacing: 1,
        textTransform: "uppercase",
        textAlign: "center",
        lineHeight: 1.0,
        whiteSpace: "pre-wrap",
        color: IDLE,
        WebkitTextStroke: `7px ${STROKE}`,
        paintOrder: "stroke fill",
        textShadow: "0 8px 0 rgba(0,0,0,0.9)",
        transform: `scale(${0.9 + 0.1 * enterProgress})`,
        opacity: enterProgress,
        maxWidth: "92%",
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
              padding: isActive ? "0 14px" : 0,
              margin: isActive ? "0 4px" : 0,
              backgroundColor: isActive ? ACTIVE_BG : "transparent",
              borderRadius: isActive ? 12 : 0,
              transform: isActive ? "scale(1.1) rotate(-2deg)" : "scale(1)",
              transition: "transform 80ms ease-out",
              color: IDLE,
            }}
          >
            {token.text}
          </span>
        );
      })}
    </div>
  );
};
