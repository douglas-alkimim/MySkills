import { Tool } from "@modelcontextprotocol/sdk/types.js";

/**
 * Tool definition for using Gemini's specialized tools
 */
export const useGeminiToolTool: Tool = {
  name: "use_gemini_tool",
  description: `Use one of Gemini's specialized tools for specific tasks.

Available tools:
- **deep_research**: Conduct comprehensive research on a topic using multiple sources
- **create_video**: Create videos using Veo 3.1 (Google's video generation model)
- **create_image**: Generate images using Imagen (Google's image generation model)

Each tool has different capabilities:
- Deep Research: Multi-source synthesis, fact-checking, comprehensive overviews
- Create Video: Text-to-video generation, scene descriptions, motion
- Create Image: Text-to-image generation, artistic styles, photo-realistic outputs

Image and video calls wait for Gemini to finish, download the generated media,
and return absolute local paths in the result's \`files\` array. They also accept
local image attachments with an explicit purpose so Gemini can use visual
references for character, style, or composition consistency.

Example:
\`\`\`
use_gemini_tool({
  tool: "deep_research",
  prompt: "Latest developments in quantum computing 2025",
  session_id: "abc123"
})
\`\`\``,
  inputSchema: {
    type: "object",
    properties: {
      tool: {
        type: "string",
        enum: ["deep_research", "create_video", "create_image"],
        description: "Which Gemini tool to use: 'deep_research', 'create_video', or 'create_image'",
      },
      prompt: {
        type: "string",
        description: "The prompt/query to send to the selected tool",
      },
      session_id: {
        type: "string",
        description: "Optional session ID to use the tool in (uses current session if not provided)",
      },
      attachments: {
        type: "array",
        maxItems: 8,
        description: "Optional local image references for create_image/create_video. Not accepted for deep_research.",
        items: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Absolute or working-directory-relative path to a PNG, JPEG, WebP, or GIF image.",
            },
            purpose: {
              type: "string",
              enum: ["reference", "style", "character", "composition"],
              description: "How Gemini should use this attachment.",
            },
            description: {
              type: "string",
              description: "Optional instruction describing the visual detail to preserve or borrow.",
            },
          },
          required: ["path", "purpose"],
        },
      },
    },
    required: ["tool", "prompt"],
  },
};
