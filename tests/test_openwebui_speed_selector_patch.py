import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "scripts" / "patch_openwebui_speed_selector.pl"


class OpenWebUISpeedSelectorPatchTests(unittest.TestCase):
    def test_selector_uses_normalized_vietnamese_labels_and_opens_upward(self):
        source = """<script lang=\"ts\">\n\timport Selector from './ModelSelector/Selector.svelte';\n\tlet selector;\n</script>\n<div class=\"flex min-w-0 max-w-full flex-col items-start\">\n</div>\n"""

        with tempfile.TemporaryDirectory() as directory:
            component = Path(directory) / "ModelSelector.svelte"
            component.write_text(source, encoding="utf-8")
            subprocess.run(["perl", str(PATCH), str(component)], check=True)
            patched = component.read_text(encoding="utf-8")

        self.assertIn("label: 'Nhanh'", patched)
        self.assertIn("label: 'Kỹ'", patched)
        self.assertNotIn(r"\\u1ef9", patched)
        self.assertIn('side="top"', patched)
        self.assertIn('className="ml-1 size-3 rotate-180"', patched)


if __name__ == "__main__":
    unittest.main()
