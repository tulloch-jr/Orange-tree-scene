import os
import shutil
import subprocess

REPO = 'C:/MayaScripts/OrangeTree'


def _git_exe():
    exe = shutil.which('git')
    if exe:
        return exe
    for guess in ('C:/Program Files/Git/cmd/git.exe',
                  'C:/Program Files (x86)/Git/cmd/git.exe'):
        if os.path.exists(guess):
            return guess
    raise RuntimeError('Git was not found. Install Git for Windows and restart Maya.')


def run(args, repo=REPO, timeout=120):
    env = dict(os.environ)
    env['GIT_TERMINAL_PROMPT'] = '0'
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    result = subprocess.run([_git_exe()] + list(args), cwd=repo,
                            capture_output=True, text=True,
                            encoding='utf-8', errors='replace',
                            env=env, timeout=timeout, creationflags=flags)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def status():
    code, out = run(['status', '--short', '--branch'])
    print(out if out else 'Clean.')
    return code == 0


def log(count=5):
    code, out = run(['log', '--oneline', '-n', str(count)])
    print(out)
    return code == 0


def commit_and_push(message):
    code, out = run(['add', '-A'])
    if code != 0:
        print('git add failed:', out)
        return False
    code, out = run(['status', '--porcelain'])
    if not out:
        print('Nothing to commit. Everything is already saved.')
        return True
    code, out = run(['commit', '-m', message])
    print(out)
    if code != 0:
        print('git commit failed.')
        return False
    code, out = run(['push'])
    print(out)
    if code != 0:
        print('git push failed. Read the message above.')
        return False
    print('Pushed to GitHub.')
    return True
