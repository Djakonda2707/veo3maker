import React, { useMemo } from "react";
import { AbsoluteFill, Sequence, useVideoConfig } from "remotion";
import { Video } from "@remotion/media";
import { createTikTokStyleCaptions } from "@remotion/captions";
import type { Caption } from "@remotion/captions";
import { CaptionPage } from "./CaptionPage";
import type { CaptionedVideoProps } from "./schema";

const SWITCH_CAPTIONS_EVERY_MS = 1200;

export const CaptionedVideo: React.FC<CaptionedVideoProps> = ({
  videoSrc,
  captions,
  presetKey,
}) => {
  const { fps } = useVideoConfig();

  const { pages } = useMemo(() => {
    return createTikTokStyleCaptions({
      captions: captions as Caption[],
      combineTokensWithinMilliseconds: SWITCH_CAPTIONS_EVERY_MS,
    });
  }, [captions]);

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Video
        src={videoSrc}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
        }}
      />
      {pages.map((page, index) => {
        const nextPage = pages[index + 1] ?? null;
        const startFrame = (page.startMs / 1000) * fps;
        const endFrame = Math.min(
          nextPage ? (nextPage.startMs / 1000) * fps : Infinity,
          startFrame + (SWITCH_CAPTIONS_EVERY_MS / 1000) * fps,
        );
        const durationInFrames = Math.max(1, Math.round(endFrame - startFrame));

        if (durationInFrames <= 0) {
          return null;
        }

        return (
          <Sequence
            key={`${page.startMs}-${index}`}
            from={Math.round(startFrame)}
            durationInFrames={durationInFrames}
          >
            <CaptionPage page={page} presetKey={presetKey} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
