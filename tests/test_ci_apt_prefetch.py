"""Task 045 / F-11(a): bounded apt downloads with one mirror fail-over.

Runs the real tools/ci_apt_prefetch.sh under bash with stub sudo/timeout/apt-get
on PATH; no package is downloaded or installed and /etc/apt is never touched.
"""
from pathlib import Path
import os, shutil, subprocess, sys, tempfile, unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'tools/ci_apt_prefetch.sh'
SETUP = ROOT / '.integration/tools/setup_ci_environment.sh'
MIRRORS = ('http://azure.archive.ubuntu.com/ubuntu/\tpriority:1\n'
           'https://archive.ubuntu.com/ubuntu/\tpriority:2\n'
           'https://security.ubuntu.com/ubuntu/\tpriority:3\n')
STUBS = {
    'sudo': '#!/bin/sh\nexec "$@"\n',
    # timeout --kill-after=15 <seconds> cmd...: record the bound, run the command.
    'timeout': '#!/bin/sh\necho "$2" >> "$FAKE_LOG.bounds"\nshift 2\nexec "$@"\n',
    # apt-get: record arguments; exit with the next planned code for downloads.
    'apt-get': ('#!/bin/sh\necho "$*" >> "$FAKE_LOG"\n'
                'case "$*" in *--download-only*) ;; *) exit 0 ;; esac\n'
                'n=$(cat "$FAKE_LOG.n" 2>/dev/null || echo 0); echo $((n+1)) > "$FAKE_LOG.n"\n'
                'code=$(echo "$FAKE_PLAN" | cut -d, -f$((n+1)))\nexit "${code:-0}"\n'),
}


@unittest.skipUnless(shutil.which('bash') and sys.platform != 'win32', 'bash required')
class AptPrefetch(unittest.TestCase):
    def run_helper(self, plan, script, mirrors=MIRRORS, budget=480, sources=None):
        work = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, work)
        stub = work / 'bin'; stub.mkdir()
        for name, body in STUBS.items():
            (stub / name).write_text(body); (stub / name).chmod(0o755)
        (stub / 'python').symlink_to(sys.executable)
        mirror_file = work / 'apt-mirrors.txt'
        if mirrors is not None: mirror_file.write_text(mirrors)
        etc = work / 'etc-apt'; (etc / 'sources.list.d').mkdir(parents=True)     # never the machine's own /etc/apt
        for name, text in (sources or {}).items(): (etc / name).write_text(text)
        self.etc = etc
        env = dict(os.environ, PATH=f'{stub}:{os.environ["PATH"]}', FAKE_LOG=str(work / 'log'),
                   FAKE_PLAN=plan, APT_MIRRORS=str(mirror_file), APT_BUDGET_S=str(budget),
                   APT_SOURCES_DIR=str(etc))
        result = subprocess.run(['bash', '-c', f'set -euo pipefail; source "{HELPER}"; {script}'],
                                env=env, capture_output=True, text=True, timeout=60)
        read = lambda p: p.read_text().splitlines() if p.exists() else []
        return (result, read(work / 'log'), [int(x) for x in read(work / 'log.bounds')],
                mirror_file.read_text() if mirror_file.exists() else None)

    def test_healthy_mirror_downloads_once_per_set_and_changes_nothing(self):
        result, calls, bounds, mirrors = self.run_helper('0,0', 'apt_prefetch --no-install-recommends a b; apt_prefetch c')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(calls, ['-q -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 '
                                 'install -y --download-only --no-install-recommends a b',
                                 '-q -o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30 '
                                 'install -y --download-only c'])
        self.assertEqual(bounds, [180, 180]); self.assertEqual(mirrors, MIRRORS)
        self.assertNotIn('::', result.stdout)

    def test_slow_regional_mirror_fails_over_once_within_budget(self):
        result, calls, bounds, mirrors = self.run_helper('124,0,0', 'apt_prefetch a; apt_prefetch b')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mirrors, MIRRORS.split('\n', 1)[1])            # only the regional line dropped
        self.assertIn('::warning title=APT mirror fail-over (F-11)::', result.stdout)
        self.assertEqual([c.split(' -o Acquire::https::Timeout=30 ')[1] for c in calls],
                         ['install -y --download-only a', 'update', 'install -y --download-only a',
                          'install -y --download-only b'])
        # first try capped; after fail-over the rest of the one shared deadline, never more
        self.assertEqual(bounds[:2], [180, 90])
        self.assertTrue(480 >= bounds[2] >= bounds[3] > 180)

    def test_still_slow_after_fail_over_is_a_clear_bounded_failure(self):
        result, calls, bounds, mirrors = self.run_helper('124,124', 'apt_prefetch a; echo NOT_REACHED')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('::error title=APT download bound (F-11)::', result.stdout)
        self.assertNotIn('NOT_REACHED', result.stdout)
        self.assertEqual(sum(1 for c in calls if '--download-only' in c), 2)
        self.assertTrue(all(0 < b <= 480 for b in bounds))  # each bound is what is left of one deadline

    def test_second_set_gets_no_extra_fail_over_or_retry(self):
        result, calls, bounds, mirrors = self.run_helper('124,0,124', 'apt_prefetch a; apt_prefetch b')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sum(1 for c in calls if c.endswith(' update')), 1)
        self.assertIn('::error title=APT download bound (F-11)::', result.stdout)

    def test_ec2_regional_mirror_is_regional_too(self):
        # PR #167 run on bbd4d746 (18 November 2026): the image's own list, read from the "APT sources (F-11)" notice
        ec2 = ('http://us-east-2.ec2.archive.ubuntu.com/ubuntu/\tpriority:1\n'
               'https://archive.ubuntu.com/ubuntu/\tpriority:2\n'
               'https://security.ubuntu.com/ubuntu/\tpriority:3\n')
        result, calls, bounds, mirrors = self.run_helper('124,0', 'apt_prefetch a', mirrors=ec2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mirrors, ec2.split('\n', 1)[1])                 # only the regional line dropped
        self.assertIn("using the image's next listed mirror", result.stdout)
        self.assertNotIn('no second mirror listed', result.stdout)
        self.assertEqual(sum(1 for c in calls if c.endswith(' update')), 1)

    def test_regional_only_ec2_list_points_at_the_primary_archive(self):
        only = 'http://us-east-2.ec2.archive.ubuntu.com/ubuntu/\tpriority:1\n# a comment line\n'
        result, calls, bounds, mirrors = self.run_helper('124,0', 'apt_prefetch a', mirrors=only)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mirrors, 'http://archive.ubuntu.com/ubuntu/\tpriority:1\n# a comment line\n')  # a comment is no mirror

    def test_regional_only_list_fails_over_to_the_primary_archive(self):
        only = 'http://azure.archive.ubuntu.com/ubuntu/\tpriority:1\n'
        result, calls, bounds, mirrors = self.run_helper('124,0', 'apt_prefetch a', mirrors=only)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(mirrors, 'http://archive.ubuntu.com/ubuntu/\tpriority:1\n')   # only the host changed
        self.assertIn("no second mirror listed; using Ubuntu's primary archive (archive.ubuntu.com) in apt-mirrors.txt",
                      result.stdout)
        self.assertIn('::notice title=APT sources (F-11)::mirror-list http://azure.archive.ubuntu.com/ubuntu/', result.stdout)
        self.assertEqual([c.split(' -o Acquire::https::Timeout=30 ')[1] for c in calls],
                         ['install -y --download-only a', 'update', 'install -y --download-only a'])
        self.assertEqual(bounds[:2], [180, 90])

    def test_deb822_sources_without_a_mirror_list_fail_over_too(self):
        ubuntu = ('Types: deb\nURIs: http://westus.azure.archive.ubuntu.com/ubuntu/\nSuites: noble noble-updates\n'
                  'Components: main universe\nSigned-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg\n\n'
                  'Types: deb\nURIs: http://security.ubuntu.com/ubuntu/\nSuites: noble-security\nComponents: main\n')
        result, calls, bounds, mirrors = self.run_helper('124,0', 'apt_prefetch a', mirrors=None,
                                                         sources={'sources.list.d/ubuntu.sources': ubuntu})
        self.assertEqual(result.returncode, 0, result.stderr)
        after = (self.etc / 'sources.list.d/ubuntu.sources').read_text()
        self.assertEqual(after, ubuntu.replace('westus.azure.archive.ubuntu.com', 'archive.ubuntu.com'))  # host only
        self.assertIn('Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg', after)                # trust unchanged
        self.assertIn('ubuntu.sources http://westus.azure.archive.ubuntu.com/ubuntu/', result.stdout)
        self.assertIn('in ubuntu.sources', result.stdout)
        self.assertEqual(sum(1 for c in calls if c.endswith(' update')), 1)

    def test_unknown_mirror_layout_is_not_rewritten(self):
        for layout in (None, 'https://archive.ubuntu.com/ubuntu/\tpriority:1\n',      # the primary and security hosts
                       'http://archive.ubuntu.com/ubuntu/\nhttp://security.ubuntu.com/ubuntu/\n'):  # are never regional
            result, calls, bounds, mirrors = self.run_helper('124,0', 'apt_prefetch a', mirrors=layout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(mirrors, layout)
            self.assertIn('no second mirror listed; retrying the same mirror', result.stdout)
            self.assertFalse(any(c.endswith(' update') for c in calls))

    def test_exhausted_budget_never_starts_a_download(self):
        result, calls, bounds, mirrors = self.run_helper('0', 'apt_prefetch a', budget=0)
        self.assertNotEqual(result.returncode, 0); self.assertEqual(calls, []); self.assertEqual(mirrors, MIRRORS)
        self.assertIn('::error title=APT download bound (F-11)::', result.stdout)

    def parse(self, text):
        work = Path(tempfile.mkdtemp()); self.addCleanup(shutil.rmtree, work)
        (work / 'python').symlink_to(sys.executable)
        return subprocess.run(['bash', '-c', f'source "{HELPER}"; apt_packages_from_playwright_dry_run'],
                              input=text, capture_output=True, text=True, timeout=60,
                              env=dict(os.environ, PATH=f'{work}:{os.environ["PATH"]}'))

    def test_playwright_dry_run_parse_is_exact(self):
        names = ('libasound2t64 libatk-bridge2.0-0t64 libnss3 xvfb fonts-noto-color-emoji '
                 'fonts-wqy-zenhei fonts-freefont-ttf')
        for prefix in ('sh -c', 'sudo -- sh -c'):  # root and non-root forms of playwright 1.57.0
            result = self.parse(f'{prefix} "apt-get update&& apt-get install -y --no-install-recommends {names}"\n')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.split(), names.split())
        for bad in ('', 'apt-get install -y libfoo\n',
                    'sh -c "apt-get install -y --no-install-recommends a; apt-get install -y --no-install-recommends b"',
                    'sh -c "apt-get install -y --no-install-recommends a $(id)"',
                    'sh -c "apt-get install -y --no-install-recommends "'):
            result = self.parse(bad)
            self.assertNotEqual(result.returncode, 0, bad)
            self.assertEqual(result.stdout, '')

    def test_setup_prefetches_before_the_unchanged_installs(self):
        text = SETUP.read_text(encoding='utf-8')
        order = ['source "$GITHUB_WORKSPACE/tools/ci_apt_prefetch.sh"',
                 'apt_prefetch --no-install-recommends "${PLAYWRIGHT_DEBS[@]}"',
                 'python -m playwright install --with-deps chromium',
                 'apt_prefetch "${SYSTEM_DEBS[@]}"',
                 'sudo apt-get install -y "${SYSTEM_DEBS[@]}"']
        self.assertEqual([text.count(line) for line in order], [1] * len(order))
        self.assertEqual(sorted(order, key=text.index), order)
        self.assertIn('SYSTEM_DEBS=(ffmpeg bubblewrap libseccomp2 apparmor apparmor-utils)', text)
        self.assertNotIn('--no-install-recommends "${SYSTEM_DEBS', text)  # governed set unchanged


if __name__ == '__main__':
    unittest.main()
