"""Contract tests using only a temporary fake core executable."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

BRIDGE = Path(__file__).resolve().parents[1] / "plugins/hybrid-hands/scripts/hybrid_codex.py"
SPEC = importlib.util.spec_from_file_location("hybrid_codex", BRIDGE)
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bridge space ; ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.core = self.root / "fake core $(no-shell)"
        self.payload = dict(profile="hybrid", role="collect", tier=1, provider="fake",
                            account="fixture", model="fixture-model", effort="fixture-effort",
                            backend="fixture-backend", native=False, native_reason="",
                            guard_blocked=False)
        self.write_core(self.payload)

    def write_core(self, payload, status=0, raw=None):
        output = json.dumps(payload) if raw is None else raw
        self.core.write_text(
            f"#!{sys.executable}\nimport json, os, sys\n"
            "open(os.path.join(os.getcwd(), 'invocation.json'), 'w').write("
            "json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}))\n"
            f"print({output!r})\nprint('SECRET_SENTINEL', file=sys.stderr)\n"
            f"sys.exit({status})\n")
        self.core.chmod(0o700)

    def run_pick(self, **kwargs):
        return bridge.run_core("pick", self.root, self.core, role="collect", **kwargs)

    def test_safe_argv_cwd_and_extra_fields(self):
        self.payload['extra'] = {'accepted': True}
        self.write_core(self.payload)
        payload, status = self.run_pick()
        self.assertEqual((payload, status), (self.payload, 0))
        invocation = json.loads((self.root / 'invocation.json').read_text())
        self.assertEqual(invocation, {'cwd': str(self.root.resolve()), 'argv': [
            'pick', '--cwd', str(self.root), '--json', '--role', 'collect']})

    def test_guard_exit_preserved_in_cli(self):
        self.payload.update(guard_blocked=True, native_reason="fixture guard")
        self.write_core(self.payload, status=7)
        result = subprocess.run([sys.executable, str(BRIDGE), 'pick', '--cwd', str(self.root),
                                 '--core-cli', str(self.core), '--role', 'collect'],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(json.loads(result.stdout), self.payload)
        self.assertEqual(result.stderr, '')

    def test_profile_schema(self):
        self.write_core({'profile': 'gpt-mono', 'roles': {}})
        self.assertEqual(bridge.run_core('profile', self.root, self.core)[0]['roles'], {})
        for bad in ({}, {'profile': []}, {'profile': 'other', 'roles': {}},
                    {'profile': 'hybrid', 'roles': []}):
            with self.subTest(bad=bad):
                self.write_core(bad)
                with self.assertRaises(bridge.AdapterError):
                    bridge.run_core('profile', self.root, self.core)

    def test_invalid_pick_fields(self):
        for field, value in [('native', 1), ('guard_blocked', 'false'), ('model', ''),
                             ('effort', None), ('native_reason', None), ('role', 'code'),
                             ('profile', 'unknown'), ('profile', {}), ('tier', True),
                             ('tier', 2), ('tier', None)]:
            with self.subTest(field=field, value=value):
                self.write_core({**self.payload, field: value})
                with self.assertRaises(bridge.AdapterError):
                    self.run_pick()
        self.write_core({**self.payload, 'native': True, 'guard_blocked': True})
        with self.assertRaises(bridge.AdapterError):
            self.run_pick()

    def test_tier_validation_before_execution(self):
        for role, tier in [('code', 1), ('collect', 0), ('chrome', True), ('other', None)]:
            with self.subTest(role=role, tier=tier), self.assertRaises(bridge.AdapterError):
                bridge.run_core('pick', self.root, self.core, role=role, tier=tier)
        self.assertFalse((self.root / 'invocation.json').exists())
        self.write_core({**self.payload, 'role': 'chrome', 'tier': 2})
        payload, _ = bridge.run_core('pick', self.root, self.core, role='chrome', tier=2)
        self.assertEqual(payload['tier'], 2)

    def test_non_json_failure_is_sanitized(self):
        self.write_core(None, status=2, raw='SECRET_SENTINEL no profile')
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = bridge.main(['profile', '--cwd', str(self.root), '--core-cli', str(self.core)])
        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertNotIn('SECRET_SENTINEL', stderr.getvalue())
        self.assertIn('valid JSON', stderr.getvalue())

    def test_resolution_and_cwd(self):
        with patch.dict(os.environ, {'HYBRID_HANDS_CORE_CLI': str(self.core)}):
            self.assertEqual(bridge.resolve_core(), self.core)
            with self.assertRaises(bridge.AdapterError):
                bridge.resolve_core('relative')
        with patch.dict(os.environ, {}, clear=True), patch.object(Path, 'home', return_value=self.root):
            with self.assertRaises(bridge.AdapterError):
                bridge.resolve_core()
        for cwd in ('relative', self.root / 'missing', self.core):
            with self.assertRaises(bridge.AdapterError):
                bridge.validate_cwd(cwd)

    def test_timeout_is_bounded_and_sanitized(self):
        with patch.object(bridge.subprocess, 'run', side_effect=subprocess.TimeoutExpired('sentinel', 20)) as run:
            with self.assertRaisesRegex(bridge.AdapterError, '20 seconds'):
                self.run_pick()
            self.assertEqual(run.call_args.kwargs['timeout'], 20)
            self.assertNotIn('shell', run.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
