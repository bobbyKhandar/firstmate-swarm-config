#!/usr/bin/env python3
"""Real Git regressions; only GitHub's remote API is faked."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'bin/swarm-branches'


class Branches(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.com')
        self.git('remote', 'add', 'origin', 'https://github.com/acme/app.git')
        self.write('shared.txt', 'base\n')
        self.commit('base')
        self.base = self.git('rev-parse', 'HEAD')
        self.ref('task', self.base)
        self.plan = self.root / 'plan.json'
        self.data = {'project': 'acme/app', 'name': 'task', 'base': 'main',
                     'workers': [{'id': f'task-worker-{n}', 'owns': [], 'depends_on': []}
                                 for n in (1, 2)]}
        self.save()
        self.api = self.root / 'api.json'
        self.api.write_text('[]')
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        fake = self.bin / 'gh'
        fake.write_text('#!/usr/bin/env python3\nimport os,sys\nfrom pathlib import Path\n'
                        'if os.environ.get("API_FAIL"): sys.exit(1)\n'
                        'print(Path(os.environ["API_FILE"]).read_text())\n')
        fake.chmod(0o755)
        self.env = {**os.environ, 'PATH': str(self.bin) + os.pathsep + os.environ['PATH'],
                    'API_FILE': str(self.api), 'GIT_CONFIG_GLOBAL': '/dev/null',
                    'GIT_CONFIG_NOSYSTEM': '1'}

    def git(self, *args, ok=True):
        result = subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def write(self, path, text):
        (self.repo / path).write_text(text)

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def ref(self, name, sha):
        self.git('update-ref', 'refs/remotes/origin/' + name, sha)

    def save(self):
        self.plan.write_text(json.dumps(self.data))

    def worker(self, n, content, path='shared.txt', base=None):
        self.git('checkout', '-q', '--detach', base or self.base)
        self.write(path, content)
        sha = self.commit('worker')
        self.ref(f'task-worker-{n}', sha)
        return sha

    def run_cli(self, command='conflicts', expected=0, fetch=False):
        args = [sys.executable, str(SCRIPT), command, str(self.plan), '--repo', str(self.repo)]
        if command != 'reconcile' and not fetch:
            args.append('--no-fetch')
        p = subprocess.run(args, capture_output=True, text=True, env=self.env)
        self.assertEqual(p.returncode, expected, p.stdout + p.stderr)
        return p.stdout + p.stderr

    def merge(self, head, squash=False):
        self.git('checkout', '-q', '--detach', 'origin/task')
        self.git('merge', '--squash' if squash else '--no-ff', head, '-m', 'integrate')
        if squash:
            self.git('commit', '-qm', 'squash')
        sha = self.git('rev-parse', 'HEAD')
        self.ref('task', sha)
        return sha

    def test_landed_dependent_workers_are_not_remerged(self):
        one = self.worker(1, 'one\n')
        first = self.merge(one)
        two = self.worker(2, 'one plus two\n', base=first)
        self.merge(two)
        self.assertIn('All worker revisions accounted for', self.run_cli())

    def test_simulated_merges_preserve_worker_ancestry(self):
        one = self.worker(1, 'one\n')
        self.worker(2, 'one plus two\n', base=one)
        self.assertIn('No merge conflicts', self.run_cli())

    def test_missing_worker_is_not_ready(self):
        self.worker(1, 'one\n')
        self.assertIn('missing', self.run_cli(expected=1))

    def test_exact_paths_and_both_sides(self):
        for path in ['shared file.txt', 'tab\tname.txt', 'unicodé.txt', 'quote".txt', 'line\nbreak.txt', ':(exclude)magic.txt', '[pattern].txt']:
            with self.subTest(path=path):
                self.worker(1, 'one\n', path)
                self.worker(2, 'two\n', path)
                report = self.run_cli(expected=1)
                display = json.dumps(path, ensure_ascii=False) if any(c in path for c in '\t\n"') else path
                self.assertIn(display, report)
                self.assertIn('+one', report)
                self.assertIn('+two', report)
                self.assertNotIn('(no textual diff', report)

    def legacy(self):
        one = self.worker(1, 'one\n')
        first = self.merge(one, squash=True)
        two = self.worker(2, 'one plus two\n', base=first)
        second = self.merge(two, squash=True)
        prs = []
        for n, head, merge in [(1, one, first), (2, two, second)]:
            prs.append({'number': n, 'html_url': f'https://github.com/acme/app/pull/{n}',
                        'merged_at': '2026-10-16T00:00:00Z', 'merge_commit_sha': merge,
                        'base': {'ref': 'task', 'repo': {'full_name': 'acme/app'}},
                        'head': {'ref': f'task-worker-{n}', 'sha': head,
                                 'repo': {'full_name': 'acme/app'}}})
        self.api.write_text(json.dumps(prs))
        # Reconcile fetches: use a real local bare remote with the planned GitHub URL rewritten.
        remote = self.root / 'remote.git'
        subprocess.run(['git', 'clone', '-q', '--bare', str(self.repo), str(remote)], check=True)
        for name in ['task', 'task-worker-1', 'task-worker-2']:
            self.git('push', str(remote), f'refs/remotes/origin/{name}:refs/heads/{name}')
        self.git('config', f'url.{remote}.insteadOf', 'https://github.com/acme/app.git')
        return prs

    def test_legacy_reconcile_is_idempotent_and_skips_squashes(self):
        self.legacy()
        self.run_cli('reconcile')
        saved = self.plan.read_bytes()
        self.run_cli('reconcile')
        self.assertEqual(saved, self.plan.read_bytes())
        self.assertIn('All worker revisions accounted for', self.run_cli())
        self.worker(1, 'unexpected new revision\n')
        self.assertIn('head', self.run_cli(expected=1))

    def test_reconcile_failure_does_not_write_partial_records(self):
        prs = self.legacy()
        for mutation in ['wrong-base', 'wrong-repo', 'wrong-head', 'bad-merge', 'ambiguous', 'unavailable']:
            with self.subTest(mutation=mutation):
                changed = json.loads(json.dumps(prs))
                if mutation == 'wrong-base': changed[1]['base']['ref'] = 'main'
                if mutation == 'wrong-repo': changed[1]['head']['repo']['full_name'] = 'other/app'
                if mutation == 'wrong-head': changed[1]['head']['sha'] = self.base
                if mutation == 'bad-merge': changed[1]['merge_commit_sha'] = '0' * 40
                if mutation == 'ambiguous': changed.append(changed[1])
                self.api.write_text(json.dumps(changed))
                self.env['API_FAIL'] = '1' if mutation == 'unavailable' else ''
                before = self.plan.read_bytes()
                self.run_cli('reconcile', expected=1)
                self.assertEqual(before, self.plan.read_bytes())

    def test_cached_evidence_is_rechecked_and_stale_ancestry_rejected(self):
        self.legacy()
        self.run_cli('reconcile')
        self.api.write_text('[]')
        before = self.plan.read_bytes()
        self.run_cli('reconcile', expected=1)
        self.assertEqual(before, self.plan.read_bytes())
        self.ref('task', self.base)
        self.run_cli(expected=1)

    def test_wrong_clone_is_rejected(self):
        self.git('remote', 'set-url', 'origin', 'https://github.com/wrong/app.git')
        self.assertIn('repository', self.run_cli('reconcile', expected=1))

    def test_binary_conflict_is_explicit(self):
        self.worker(1, 'one\0binary')
        self.worker(2, 'two\0binary')
        self.assertIn('GIT binary patch', self.run_cli(expected=1))

    def test_modify_delete_conflict_shows_deleted_side(self):
        self.worker(1, 'changed\n')
        self.git('checkout', '-q', '--detach', self.base)
        self.git('rm', 'shared.txt')
        self.ref('task-worker-2', self.commit('delete'))
        self.assertIn('deleted file mode', self.run_cli(expected=1))

    def test_boundary_and_overlap_preserve_renamed_unusual_paths(self):
        self.git('checkout', '-q', '--detach', self.base)
        self.git('mv', 'shared.txt', 'new name.txt')
        self.ref('task-worker-1', self.commit('rename'))
        self.worker(2, 'edit\n')
        self.data['workers'][0]['owns'] = ['new name.txt']
        self.save()
        self.assertIn('shared.txt', subprocess.run([sys.executable, str(SCRIPT), 'boundary', str(self.plan),
                                      'task-worker-1', '--repo', str(self.repo), '--no-fetch'],
                                     capture_output=True, text=True, env=self.env).stdout)
        self.assertIn('shared.txt: task-worker-1, task-worker-2', self.run_cli('overlap'))

    def test_rename_rename_report_includes_both_destinations(self):
        for n, name in [(1, 'first name.txt'), (2, 'second name.txt')]:
            self.git('checkout', '-q', '--detach', self.base)
            self.git('mv', 'shared.txt', name)
            self.ref(f'task-worker-{n}', self.commit('rename'))
        report = self.run_cli(expected=1)
        self.assertIn('first name.txt', report)
        self.assertIn('second name.txt', report)
        self.assertIn('rename from shared.txt', report)
        self.assertIn('rename to first name.txt', report)
        self.assertIn('rename to second name.txt', report)

    def test_rename_modify_preserves_incoming_edit_before_and_after_prefix(self):
        self.write('shared.txt', 'base\n' + 'context\n' * 10)
        self.base = self.commit('long base')
        self.ref('task', self.base)
        self.git('mv', 'shared.txt', 'renamed.txt')
        self.write('renamed.txt', 'one\n' + 'context\n' * 10)
        one = self.commit('rename and modify')
        self.ref('task-worker-1', one)
        self.worker(2, 'two\n' + 'context\n' * 10)
        for landed in (False, True):
            if landed:
                self.merge(one)
            report = self.run_cli(expected=1)
            self.assertIn('+one', report)
            self.assertIn('+two', report)
            self.assertIn('renamed.txt', report)

    def test_resolution_preserves_original_head_and_uses_fresh_name(self):
        one = self.worker(1, 'one\n')
        two = self.worker(2, 'two\n')
        self.merge(one)
        self.ref('task-resolve-1', self.base)
        report = self.run_cli(expected=1)
        self.assertIn('task-resolve-2', report)
        self.assertIn('integration', report)
        self.git('checkout', '-q', '--detach', 'origin/task')
        self.git('merge', '--no-ff', two, ok=False)
        self.write('shared.txt', 'one and two\n')
        resolution = self.commit('resolve both intentions')
        self.merge(resolution)
        self.assertIn('All worker revisions accounted for', self.run_cli())
        self.assertEqual((self.repo / 'shared.txt').read_text(), 'one and two\n')


if __name__ == '__main__':
    unittest.main()
