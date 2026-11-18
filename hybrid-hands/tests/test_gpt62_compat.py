"""Codex adapter preserves explicit model metadata; the core still owns routing."""
import json
from pathlib import Path
import sys
import tomllib

import pytest

SCRIPTS = Path(__file__).parents[1] / 'plugins/hybrid-hands/scripts'
sys.path.insert(0, str(SCRIPTS))
import hybrid_codex as bridge
import install_agents as installer


@pytest.fixture
def core(tmp_path):
    def make(model, effort, blocked=False):
        rows = {}
        for key, (_, role, tier) in installer.AGENTS.items():
            rows[key] = dict(profile='gpt-mono', role=role, tier=tier, provider='codex',
                             account='fixture', model=model if key == 'code' else 'gpt-6.1-terra',
                             effort=effort if key == 'code' else 'low')
        payload = {'profile': 'gpt-mono', 'roles': rows}
        pick = {**rows['code'], 'backend': 'codex', 'native': False,
                'native_reason': 'fixture guard' if blocked else '', 'guard_blocked': blocked}
        executable = tmp_path / 'core'
        executable.write_text(f'#!{sys.executable}\nimport json,sys\n'
                              f'print(json.dumps({payload!r} if sys.argv[1] == "profile" else {pick!r}))\n'
                              f'sys.exit({7 if blocked else 0})\n')
        executable.chmod(0o700)
        return executable, payload, pick
    return make


@pytest.mark.parametrize('model', ('gpt-6.2-sol', 'gpt-6.2-astra'))
@pytest.mark.parametrize('effort', ('low', 'medium', 'high', 'xhigh'))
def test_explicit_core_model_passes_unchanged_to_pick_and_agent(tmp_path, core, model, effort):
    executable, payload, pick = core(model, effort)
    assert bridge.run_core('profile', tmp_path, executable) == (payload, 0)
    assert bridge.run_core('pick', tmp_path, executable, role='code') == (pick, 0)
    home = tmp_path / 'home'
    generated, status = installer.generate(str(tmp_path), str(executable), home, True)
    assert status == 0 and generated[0]['model'] == model
    parsed = tomllib.loads((home / 'agents/hybrid-code.toml').read_text())
    assert (parsed['model'], parsed['model_reasoning_effort']) == (model, effort)
    for name in ('hybrid-collect-1', 'hybrid-collect-2'):
        parsed = tomllib.loads((home / f'agents/{name}.toml').read_text())
        assert (parsed['model'], parsed['model_reasoning_effort']) == ('gpt-6.1-terra', 'low')


@pytest.mark.parametrize('model', ('gpt-6.2-sol', 'gpt-6.2-astra'))
def test_new_model_does_not_bypass_core_guard(tmp_path, core, model):
    executable, _, pick = core(model, 'high', blocked=True)
    assert bridge.run_core('pick', tmp_path, executable, role='code') == (pick, 7)


def test_existing_core_selection_is_not_upgraded(tmp_path, core):
    executable, payload, pick = core('gpt-6.1-sol', 'low')
    assert bridge.run_core('profile', tmp_path, executable) == (payload, 0)
    assert bridge.run_core('pick', tmp_path, executable, role='code') == (pick, 0)
    result, status = installer.generate(str(tmp_path), str(executable), tmp_path / 'home', False)
    assert status == 0 and result[0]['model'] == 'gpt-6.1-sol'
    assert result[0]['effort'] == 'low'
    assert not (tmp_path / 'home').exists()
