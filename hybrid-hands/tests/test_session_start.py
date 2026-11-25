"""Exercise packaged SessionStart command without touching runtime configuration."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "hybrid-hands"
SCRIPT = PLUGIN / "scripts" / "session_start.py"


class SessionStartTests(unittest.TestCase):
    def run_hook(self, raw: str) -> dict:
        result = subprocess.run([sys.executable, str(SCRIPT)], input=raw,
                                text=True, capture_output=True, cwd="/", check=True)
        return json.loads(result.stdout)

    def test_startup_and_resume_include_complete_packaged_skill(self):
        skill = (PLUGIN / "skills/hybrid-hands/SKILL.md").read_text()
        for source in ("startup", "resume"):
            with self.subTest(source=source):
                output = self.run_hook(json.dumps({"hook_event_name": "SessionStart", "source": source}))
                specific = output["hookSpecificOutput"]
                self.assertEqual(specific["hookEventName"], "SessionStart")
                self.assertTrue(specific["additionalContext"].endswith(skill))
                self.assertIn(str(PLUGIN.resolve()), specific["additionalContext"])
                manifest = json.loads((PLUGIN / "hooks/hooks.json").read_text())
                limit = manifest["hooks"]["SessionStart"][0]["hooks"][0]["additionalContextLimit"]
                self.assertLess(len(specific["additionalContext"]), limit)

    def test_malformed_or_unrelated_inputs_are_noop(self):
        for raw in ("", "{", "[]", "null", "{}",
                    '{"hook_event_name":"SessionStart","source":[]}',
                    '{"hook_event_name":"SubagentStart","source":"startup"}',
                    '{"hook_event_name":"SessionStart","source":"fork"}'):
            with self.subTest(raw=raw):
                self.assertEqual(self.run_hook(raw), {})

    def test_explicit_hand_or_subagent_metadata_is_noop(self):
        for key, value in (("agent_type", "hand"), ("agent_name", "hybrid-code"),
                           ("subagent_type", "worker"), ("agent_id", "child")):
            self.assertEqual(self.run_hook(json.dumps({"hook_event_name": "SessionStart",
                             "source": "startup", key: value})), {})

    def test_missing_skill_does_not_block(self):
        spec = importlib.util.spec_from_file_location("session_start", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(module.build_output({"hook_event_name": "SessionStart", "source": "startup"},
                                                Path(directory) / "missing.md"), {})


if __name__ == "__main__":
    unittest.main()
