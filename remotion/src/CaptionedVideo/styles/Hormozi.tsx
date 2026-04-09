import React from "react";
import type { CaptionStyleProps } from "../CaptionPage";

const ACTIVE = "#FFE600";
const IDLE = "#FFFFFF";
const STROKE = "#000000";

export const Hormozi: React.FC<CaptionStyleProps> = ({
  page,
  absoluteTimeMs,
  enterProgress,
}) => {
  return (
    <div
      style={{
        fontFamily: "Inter, system-ui, sans-serif",
        fontSize: 96,
        fontWeight: 900,
        letterSpacing: -1,
        textTransform: "uppercase",
        textAlign: "center",
        lineHeight: 1.05,
        whiteSpace: "pre-wrap",
        color: IDLE,
        WebkitTextStroke: `6px ${STROKE}`,
        paintOrder: "stroke fill",
        textShadow: "0 6px 0 rgba(0,0,0,0.85)",
        transform: `translateY(${(1 - enterProgress) * 24}px)`,
        opacity: enterProgress,
        maxWidth: "90%",
      }}
    >
      {page.tokens.map((token) => {
        const isActive =
          token.fromMs <= absoluteTimeMs && token.toMs > absoluteTimeMs;
        return (
          <span
            key={`${token.fromMs}-${token.text}`}
            style={{
              color: isActive ? ACTIVE : IDLE,
              display: "inline-block",
              transform: isActive ? "scale(1.08)" : "scale(1)",
              transition: "transform 60ms linear",
            }}
          >
            {token.text}
          </span>
        );
      })}
    </div>
  );
};
