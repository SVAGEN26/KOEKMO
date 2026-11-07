"""Publish site/dist to the gh-pages branch of a git remote, for GitHub Pages.

    python3 scripts/deploy_pages.py origin [--dry-run]

Builds the site, commits site/dist as one parentless commit and force-pushes it to
<remote>/gh-pages. Each deployment replaces the previous one, so the ~100 MB compiler
never accumulates in history. Set the repository's Pages source to the gh-pages branch.
"""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'site/dist'
LIMIT = 100 * 1024 * 1024  # GitHub rejects files of 100 MiB or more


def git(*args, env=None, capture=False, cwd=ROOT):
    return subprocess.run(['git', *args], cwd=cwd, env=env, check=True, text=True,
                          capture_output=capture).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('remote')
    parser.add_argument('--dry-run', action='store_true', help='build and commit, but do not push')
    args = parser.parse_args()
    if git('status', '--porcelain', '--untracked-files=no', capture=True).strip():
        raise SystemExit('Commit or stash your changes first; the deployment records the source commit.')
    subprocess.run([sys.executable, str(ROOT / 'scripts/build.py')], check=True)
    too_big = [p for p in DIST.rglob('*') if p.is_file() and p.stat().st_size >= LIMIT]
    if too_big:
        raise SystemExit(f'GitHub rejects files of 100 MiB or more: {too_big}. Build the compiler with wasm-opt.')
    source = git('rev-parse', 'HEAD', capture=True).strip()
    with tempfile.TemporaryDirectory() as tmp:
        # A separate index, so the working tree and the real index stay untouched.
        env = {**os.environ, 'GIT_DIR': str(ROOT / '.git'), 'GIT_INDEX_FILE': str(Path(tmp) / 'index'),
               'GIT_WORK_TREE': str(DIST)}
        git('add', '--all', '--force', '.', env=env, cwd=DIST)
        tree = git('write-tree', env=env, capture=True, cwd=DIST).strip()
    commit = git('commit-tree', tree, '-m', f'Deploy site from {source}', capture=True).strip()
    print('Site commit', commit, 'from source', source)
    if args.dry_run:
        print('Dry run: not pushed.')
        return
    git('push', '--force', args.remote, f'{commit}:refs/heads/gh-pages')
    print(f'Pushed to {args.remote}/gh-pages.')


if __name__ == '__main__':
    main()
