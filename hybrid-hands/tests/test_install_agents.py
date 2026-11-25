"""Focused installer checks, using only synthetic core responses and temporary homes."""
import json
from pathlib import Path
import sys
import tomllib

import pytest

SCRIPTS = Path(__file__).parents[1] / 'plugins/hybrid-hands/scripts'
sys.path.insert(0, str(SCRIPTS))
import install_agents as installer


@pytest.fixture
def core(tmp_path):
    rows = {}
    for key, (_, role, tier) in installer.AGENTS.items():
        rows[key] = dict(profile='hybrid', role=role, tier=tier, provider='codex',
                         account='fixture-account', model='fixture-model-"quoted"', effort='fixture-effort')
    payload = {'profile': 'hybrid', 'roles': rows}
    executable = tmp_path / 'fake core'
    executable.write_text('#!/usr/bin/env python3\nimport json\nprint(' + repr(json.dumps(payload)) + ')\n')
    executable.chmod(0o700)
    return executable, payload


def install(tmp_path, core, apply=False):
    return installer.generate(str(tmp_path), str(core), tmp_path / 'home', apply)


def test_dry_run_creates_nothing(tmp_path, core):
    result, status = install(tmp_path, core[0])
    assert status == 0 and len(result) == 3
    assert not (tmp_path / 'home').exists()
    assert result[0]['model'] == core[1]['roles']['code']['model']


def test_apply_exact_config_and_law(tmp_path, core):
    install(tmp_path, core[0], True)
    path = tmp_path / 'home/agents/hybrid-code.toml'
    parsed = tomllib.loads(path.read_text())
    assert parsed['model'] == core[1]['roles']['code']['model']
    assert parsed['model_reasoning_effort'] == 'fixture-effort'
    assert installer.DATA_LAW in parsed['developer_instructions']
    assert 'Generation is not native approval' in parsed['description']
    assert path.stat().st_mode & 0o777 == 0o600
    assert not (tmp_path / 'home/agents/hand.toml').exists()


def test_skip_non_codex(tmp_path, core, monkeypatch):
    core[1]['roles']['collect.1']['provider'] = 'claude'
    monkeypatch.setattr(installer, 'run_core', lambda *args: (core[1], 0))
    result, status = install(tmp_path, core[0], True)
    assert result[1]['status'] == 'skipped'
    assert not (tmp_path / 'home/agents/hybrid-collect-1.toml').exists()


def test_entire_preflight_collision(tmp_path, core):
    agents = tmp_path / 'home/agents'
    agents.mkdir(parents=True)
    collision = agents / 'hybrid-collect-2.toml'
    collision.write_text('user file')
    with pytest.raises(installer.AdapterError):
        install(tmp_path, core[0], True)
    assert list(agents.iterdir()) == [collision]
    assert collision.read_text() == 'user file'


def test_symlink_ancestor_refused(tmp_path, core):
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    (tmp_path / 'home').symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(installer.AdapterError):
        install(tmp_path, core[0], True)
    assert list(elsewhere.iterdir()) == []


def test_managed_noop_and_update_backup(tmp_path, core, monkeypatch):
    install(tmp_path, core[0], True)
    path = tmp_path / 'home/agents/hybrid-code.toml'
    before = path.read_bytes()
    mtime = path.stat().st_mtime_ns
    result, _ = install(tmp_path, core[0], True)
    assert result[0]['status'] == 'unchanged'
    assert path.stat().st_mtime_ns == mtime
    core[1]['roles']['code']['model'] = 'next-fixture-model'
    monkeypatch.setattr(installer, 'run_core', lambda *args: (core[1], 0))
    install(tmp_path, core[0], True)
    backups = list(path.parent.glob('hybrid-code.toml.bak.*'))
    assert len(backups) == 1 and backups[0].read_bytes() == before
    assert backups[0].suffix != '.toml'
    assert tomllib.loads(path.read_text())['model'] == 'next-fixture-model'


def test_home_precedence(monkeypatch, tmp_path):
    monkeypatch.setenv('CODEX_HOME', str(tmp_path / 'environment'))
    assert installer.target_home(str(tmp_path / 'explicit')) == tmp_path / 'explicit'
    assert installer.target_home(None) == tmp_path / 'environment'
    with pytest.raises(installer.AdapterError):
        installer.target_home('relative')


@pytest.mark.parametrize('field,value', [('tier', True), ('profile', 'wrong'), ('role', 'chrome'), ('model', ''), ('account', None)])
def test_invalid_rows_no_writes(tmp_path, core, monkeypatch, field, value):
    core[1]['roles']['collect.1'][field] = value
    monkeypatch.setattr(installer, 'run_core', lambda *args: (core[1], 0))
    with pytest.raises(installer.AdapterError):
        install(tmp_path, core[0], True)
    assert not (tmp_path / 'home').exists()


def test_core_exit_preserved_without_writes(tmp_path, core, monkeypatch):
    monkeypatch.setattr(installer, 'run_core', lambda *args: ({}, 7))
    assert install(tmp_path, core[0], True) == ([], 7)
    assert not (tmp_path / 'home').exists()


@pytest.mark.parametrize('key', list(installer.AGENTS))
def test_generated_git_authorization_contract(core, key):
    row = installer.validate_rows(core[1])[list(installer.AGENTS).index(key)]
    instructions = tomllib.loads(installer.render(row).decode())['developer_instructions']
    assert installer.GIT_POLICY in instructions
    for requirement in (
        'Do not commit or push by default.',
        'Only an explicit brain packet may authorize commit and/or push',
        'repository, each permitted action, target branch, and remote for push',
        'successful tests never imply commit or push authorization',
        "never stage another person's work",
        'Higher-priority instructions and runtime bans still apply',
        'Destructive actions, merge, force push, and history rewriting remain forbidden',
        'commit SHA, branch, and remote/push result',
    ):
        assert requirement in instructions
    assert 'Do not commit, push, or perform destructive actions.' not in instructions
