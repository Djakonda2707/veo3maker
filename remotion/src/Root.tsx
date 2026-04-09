import React from "react";
import { Composition, CalculateMetadataFunction } from "remotion";
import { CaptionedVideo } from "./CaptionedVideo";
import {
  captionedVideoSchema,
  type CaptionedVideoProps,
} from "./CaptionedVideo/schema";

const FPS = 30;
const WIDTH = 1080;
const HEIGHT = 1920;

const calculateCaptionedVideoMetadata: CalculateMetadataFunction<
  CaptionedVideoProps
> = ({ props }) => {
  const durationInFrames = Math.max(
    1,
    Math.round(props.durationInSeconds * props.fps),
  );
  return {
    durationInFrames,
    fps: props.fps,
  };
};

const defaultCaptionedVideoProps: CaptionedVideoProps = {
  videoSrc: "",
  captions: [],
  presetKey: "hormozi",
  durationInSeconds: 10,
  fps: FPS,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CaptionedVideo"
        component={CaptionedVideo}
        durationInFrames={FPS * 10}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
        schema={captionedVideoSchema}
        defaultProps={defaultCaptionedVideoProps}
        calculateMetadata={calculateCaptionedVideoMetadata}
      />
    </>
  );
};
