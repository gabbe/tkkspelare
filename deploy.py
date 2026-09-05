#!/usr/bin/env python3
"""Sync the library from Drive and upload the site to the web server over SSH.

    py deploy.py [--all] [--no-sync] [--force]

Reads deploy_host and deploy_dir from sync.local.json (see deploy/SERVER.md).
The site is packed as a tar stream and unpacked on the server into a fresh
directory next to the live one, which is then swapped in, so a half-finished
upload never leaves the site broken. Only ssh is needed on this machine.
"""
import argparse, io, json, pathlib, subprocess, sys, tarfile, time

HERE = pathlib.Path(__file__).resolve().parent
LOCAL = HERE / 'sync.local.json'
SITE_FILES = ['index.html', 'robots.txt', 'library.json']
SITE_DIRS = ['vendor', 'noter', 'test']

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--all', action='store_true', help='sync everything, not only the current folder')
    ap.add_argument('--no-sync', action='store_true', help='skip the Drive sync, upload what is there')
    ap.add_argument('--force', action='store_true', help='re-export every score during the sync')
    a = ap.parse_args()
    cfg = json.loads(LOCAL.read_text(encoding='utf8')) if LOCAL.exists() else {}
    host, remote = cfg.get('deploy_host'), cfg.get('deploy_dir')
    if not host or not remote: sys.exit('deploy_host and deploy_dir missing in sync.local.json')

    if not a.no_sync:
        cmd = [sys.executable, str(HERE / 'sync.py')] + ([] if a.all else ['--only-current']) + (['--force'] if a.force else [])
        if subprocess.run(cmd).returncode != 0: sys.exit('sync failed, nothing uploaded')
    for must in ['index.html', 'library.json', 'vendor/alphaTab.js', 'vendor/soundfont/sonivox.sf3']:
        if not (HERE / must).exists(): sys.exit(f'missing {must}; run patch_alphatab.py / sync.py first')

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        for f in SITE_FILES:
            if (HERE / f).exists(): tar.add(HERE / f, arcname=f)
        for d in SITE_DIRS:
            if (HERE / d).exists(): tar.add(HERE / d, arcname=d, filter=lambda ti: None if ti.name.endswith(('.json',)) and ti.name.startswith('noter/') else ti)
    data = buf.getvalue()
    print(f'uploading {len(data)//1024} kB to {host}:{remote}')
    stamp = time.strftime('%Y%m%d-%H%M%S')
    script = (f'set -e; new="{remote}.new-{stamp}"; mkdir -p "$new"; tar xzf - -C "$new"; '
              f'if [ -d "{remote}" ]; then mv "{remote}" "{remote}.old"; fi; mv "$new" "{remote}"; rm -rf "{remote}.old"; '
              f'echo "deployed $(find "{remote}" -type f | wc -l) files"')
    r = subprocess.run(['ssh', host, script], input=data)
    sys.exit(r.returncode)

if __name__ == '__main__':
    main()
