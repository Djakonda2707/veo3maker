import { z } from "zod";

export const PRESET_KEYS = ["hormozi", "beast", "neon", "minimal"] as const;

export const captionSchema = z.object({
  text: z.string(),
  startMs: z.number(),
  endMs: z.number(),
  timestampMs: z.number().nullable(),
  confidence: z.number().nullable(),
});

export const captionedVideoSchema = z.object({
  videoSrc: z.string(),
  captions: z.array(captionSchema),
  presetKey: z.enum(PRESET_KEYS),
  durationInSeconds: z.number().positive(),
  fps: z.number().positive(),
});

export type CaptionedVideoProps = z.infer<typeof captionedVideoSchema>;
export type CaptionInput = z.infer<typeof captionSchema>;
export type PresetKey = (typeof PRESET_KEYS)[number];
