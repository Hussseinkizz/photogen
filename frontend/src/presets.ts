export type PromptPreset = {
  id: string
  label: string
  prompt: string
}

export const PRESETS: PromptPreset[] = [
  {
    id: "headshot",
    label: "Headshot",
    prompt: "Turn this into a clean professional headshot. Neutral studio light, sharp eyes, natural skin.",
  },
  {
    id: "film",
    label: "Film still",
    prompt: "Make this look like a 35mm film still. Soft grain, warm shadows, cinematic framing.",
  },
  {
    id: "cartoon",
    label: "Cartoon",
    prompt: "Redraw this as a friendly cartoon portrait. Keep the face recognizable, bold shapes, clean lines.",
  },
  {
    id: "editorial",
    label: "Editorial",
    prompt: "Give this an editorial magazine look. Confident pose, high contrast, refined color grade.",
  },
  {
    id: "passport",
    label: "Passport",
    prompt: "Make a plain passport-style photo. Even light, neutral expression, simple background.",
  },
]
