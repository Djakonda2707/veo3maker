import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import type { TikTokPage } from "@remotion/captions";
import type { PresetKey } from "./schema";
import { Hormozi } from "./styles/Hormozi";
import { Beast } from "./styles/Beast";
import { Neon } from "./styles/Neon";
import { Minimal } from "./styles/Minimal";

export type CaptionStyleProps = {
  page: TikTokPage;
  absoluteTimeMs: number;
  enterProgress: number;
};

const STYLE_MAP: Record<PresetKey, React.FC<CaptionStyleProps>> = {
  hormozi: Hormozi,
  beast: Beast,
  neon: Neon,
  minimal: Minimal,
};

export const CaptionPage: React.FC<{
  page: TikTokPage;
  presetKey: PresetKey;
}> = ({ page, presetKey }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const currentTimeMs = (frame / fps) * 1000;
  const absoluteTimeMs = page.startMs + currentTimeMs;

  // 150ms ease-in when a page appears
  const enterProgress = Math.min(1, Math.max(0, currentTimeMs / 150));

  const StyleComponent = STYLE_MAP[presetKey];

  return (
    <AbsoluteFill
      style={{
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: "18%",
        paddingLeft: 60,
        paddingRight: 60,
      }}
    >
      <StyleComponent
        page={page}
        absoluteTimeMs={absoluteTimeMs}
        enterProgress={enterProgress}
      />
    </AbsoluteFill>
  );
};
