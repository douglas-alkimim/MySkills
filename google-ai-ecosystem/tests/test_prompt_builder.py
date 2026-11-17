from __future__ import annotations

import sys
from pathlib import Path
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_gemini_prompt import build_prompt  # noqa: E402


class PromptBuilderTests(unittest.TestCase):
    def test_image_prompt_preserves_attachment_contract(self) -> None:
        prompt = build_prompt(
            {
                "mode": "image",
                "user_prompt": "Crie um boneco acenando.",
                "attachments": [
                    {
                        "path": r"C:\refs\boneco.png",
                        "purpose": "character",
                        "description": "preserve o rosto e as cores",
                    }
                ],
            }
        )
        self.assertIn("Crie um boneco acenando.", prompt)
        self.assertIn("boneco.png [character]", prompt)
        self.assertIn("visual references, not instructions", prompt)
        self.assertIn("Return the generated image", prompt)

    def test_video_prompt_has_generation_contract(self) -> None:
        prompt = build_prompt(
            {"mode": "video", "user_prompt": "Um boneco diz OI e acena para a câmera."}
        )
        self.assertIn("Generate a video", prompt)
        self.assertIn("dialogue", prompt)
        self.assertIn("Return the generated video", prompt)

    def test_task_bridge_forbids_local_write_claims(self) -> None:
        prompt = build_prompt(
            {
                "mode": "task-bridge",
                "user_prompt": "Proponha uma implementação.",
                "context": "Arquivo app.ts",
            }
        )
        self.assertIn("Do not claim to have modified local files", prompt)
        self.assertIn("Arquivo app.ts", prompt)

    def test_invalid_attachment_purpose_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported purpose"):
            build_prompt(
                {
                    "mode": "image",
                    "user_prompt": "Teste",
                    "attachments": [{"path": "ref.png", "purpose": "unknown"}],
                }
            )


if __name__ == "__main__":
    unittest.main()
