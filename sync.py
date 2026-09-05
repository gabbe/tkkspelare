#!/usr/bin/env python3
"""Mirror the choir's MuseScore scores into the player's library.

    py sync.py [--source DIR] [--only-current] [--force] [--braille-dir DIR]

For every .mscz under the source folder (the choir's "2. MuseScore" on Drive):
  1. export it to compressed MusicXML with MuseScore Studio's command line,
  2. run prepare.py on the export so every voice becomes its own part,
  3. write the result under noter/ mirroring the folder structure,
  4. optionally write a single-part file for braille transcription.
Then library.json is written for the player: title, file, folder, whether the
score is in the current repertoire ("Aktuellt"), and any warnings prepare.py
printed, so the digitisers can see which scores need a look.

Scores are only re-exported when the .mscz is newer than the existing output,
so after the first run the sync takes seconds.

Per-song settings live in songs.json (committed; it holds titles, not music):
  {
    "Olle_Adolphson_Rättnu_min_tid": {"names": {"S/A": ["Sopran", "Alt"], "T/B": ["Tenor", "Bas"]},
                                      "explode": {"Bas": ["Bas 1", "Bas 2"]},
                                      "title": "Rättnu min tid"},
    "Some_other_score": {"skip": true}
  }
keyed by the .mscz file name without extension. DEFAULT_NAMES below covers the
usual two-voice staves; songs.json only needs the exceptions.

Machine-specific paths go in sync.local.json (git-ignored):
  {"source": "G:/.../Digitala Noter/2. MuseScore", "musescore": "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"}
"""
import argparse, json, os, pathlib, re, shutil, subprocess, sys, tempfile, time, zipfile
import xml.etree.ElementTree as ET

try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception: pass

HERE = pathlib.Path(__file__).resolve().parent
NOTER = HERE / 'noter'
LIBRARY = HERE / 'library.json'
SONGS = HERE / 'songs.json'
LOCAL = HERE / 'sync.local.json'
CURRENT_FOLDER = 'Aktuellt'
SKIP_DIRS = {'.mscbackup', 'BU'}
# Hand-made single-part scores for braille ("... - Tenor.mscz", "...Tenor2.mscz") duplicate the
# full score in the library; the braille file is produced from the full score instead.
PART_SCORE = re.compile(r'[-_ ]\s*tenor\s*2?$', re.I)

# Two-voice staves as the choir usually names them -> one part per voice.
DEFAULT_NAMES = {
    'S/A': ['Sopran', 'Alt'], 'S A': ['Sopran', 'Alt'], 'SA': ['Sopran', 'Alt'],
    'Sopran/Alt': ['Sopran', 'Alt'], 'Soprano/alto': ['Sopran', 'Alt'], 'Soprano/Alto': ['Sopran', 'Alt'],
    'Damer': ['Sopran', 'Alt'], 'Women': ['Sopran', 'Alt'],
    'T/B': ['Tenor', 'Bas'], 'T B': ['Tenor', 'Bas'], 'TB': ['Tenor', 'Bas'],
    'Tenor/Bas': ['Tenor', 'Bas'], 'Tenor/bas': ['Tenor', 'Bas'], 'Tenor/Basso': ['Tenor', 'Bas'], 'Tenor/Bass': ['Tenor', 'Bas'],
    'Herrar': ['Tenor', 'Bas'], 'Men': ['Tenor', 'Bas'],
}
BRAILLE_PART = ['Tenor 2', 'Tenor II', 'T2', 'Ténor 2', 'Tenor', 'T', 'Ténor', 'Tenor 1', 'T1', 'Tenor/Bas', 'Tenor/bas', 'T/B']

def load_json(path, default):
    return json.loads(path.read_text(encoding='utf8')) if path.exists() else default

def names_arg(mapping):
    return ';'.join(f'{k}={",".join(v)}' for k, v in mapping.items())

def musicxml_title(mxl):
    try:
        z = zipfile.ZipFile(mxl); n = [x for x in z.namelist() if x.endswith('.xml') and not x.startswith('META')][0]
        root = ET.fromstring(z.read(n))
        t = root.findtext('work/work-title') or root.findtext('movement-title')
        if not t:
            for c in root.iter('credit-words'):
                if c.text and c.text.strip(): t = c.text.strip(); break
        return ' '.join((t or '').split()) or None
    except Exception:
        return None

def export(musescore, src, dst):
    r = subprocess.run([musescore, '-o', str(dst), str(src)], capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not dst.exists():
        raise RuntimeError(f'MuseScore export failed (exit {r.returncode}): {r.stderr.strip()[-300:]}')

def prepare(src, dst, names, explode, only=None):
    cmd = [sys.executable, str(HERE / 'prepare.py'), str(src), str(dst), '--copy-lyrics', '--unison-fill', '--names', names_arg(names)]
    if explode: cmd += ['--explode', names_arg(explode)]
    if only: cmd += ['--only', ','.join(only)]
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    r = subprocess.run(cmd, capture_output=True, text=True, encoding='utf8', errors='replace', env=env)
    if r.returncode != 0:
        raise RuntimeError(f'prepare.py failed: {(r.stderr or r.stdout).strip()[-400:]}')
    # anything prepare.py reports about the score (not the routine "kept" / "wrote" lines)
    return [l.strip() for l in r.stdout.splitlines()
            if l.strip() and not re.match(r'(wrote|.*: 1 voice, kept|tied-over notes|jump directions|system marks|kept only)', l.strip())]

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    local = load_json(LOCAL, {})
    ap.add_argument('--source', default=local.get('source'), help='folder with the .mscz files (default from sync.local.json)')
    ap.add_argument('--musescore', default=local.get('musescore', r'C:\Program Files\MuseScore 4\bin\MuseScore4.exe'))
    ap.add_argument('--only-current', action='store_true', help=f'only the "{CURRENT_FOLDER}" subfolder')
    ap.add_argument('--force', action='store_true', help='re-export everything')
    ap.add_argument('--braille-dir', help='also write <title>-<part>.mxl single-part files here (for SMB)')
    ap.add_argument('--limit', type=int, default=0, help='stop after N scores (for testing)')
    a = ap.parse_args()
    if not a.source: sys.exit('no --source and no sync.local.json')
    source = pathlib.Path(a.source)
    if a.only_current: source = source / CURRENT_FOLDER
    songs = load_json(SONGS, {})
    NOTER.mkdir(exist_ok=True)

    entries = []; done = 0; t0 = time.time()
    files = sorted(p for p in source.rglob('*.mscz') if not (set(p.relative_to(source).parts[:-1]) & SKIP_DIRS))
    print(f'{len(files)} scores under {source}')
    for src in files:
        rel = src.relative_to(source)
        key = src.stem
        cfg = songs.get(key, {})
        if cfg.get('skip'): print(f'- {rel}: skipped (songs.json)'); continue
        if PART_SCORE.search(key) and not cfg.get('keep'):
            print(f'- {rel}: looks like a single-part score for braille, skipped (set "keep": true in songs.json to include)'); continue
        folder = str(rel.parent).replace('\\', '/') if rel.parent != pathlib.Path('.') else ''
        if a.only_current: folder = CURRENT_FOLDER + ('/' + folder if folder else '')
        out = NOTER / (folder + '/' if folder else '') / (key + '.mxl')
        out.parent.mkdir(parents=True, exist_ok=True)
        meta_path = out.with_suffix('.json')
        fresh = out.exists() and meta_path.exists() and out.stat().st_mtime >= src.stat().st_mtime and not a.force
        if fresh:
            meta = load_json(meta_path, {})
        else:
            names = dict(DEFAULT_NAMES); names.update(cfg.get('names', {}))
            try:
                with tempfile.TemporaryDirectory() as td:
                    full = pathlib.Path(td) / 'full.mxl'
                    export(a.musescore, src, full)
                    warnings = prepare(full, out, names, cfg.get('explode'))
                    # MuseScore's title field is unreliable (placeholders, OCR leftovers), so the
                    # file name is the default and songs.json can override; the field is kept as a hint.
                    title = cfg.get('title') or ' '.join(key.replace('_', ' ').split())
                    hint = musicxml_title(full)
                    if a.braille_dir:
                        bdir = pathlib.Path(a.braille_dir); bdir.mkdir(parents=True, exist_ok=True)
                        try:
                            prepare(full, bdir / f'{title}-Tenor.mxl', names, None, only=cfg.get('braille_part', BRAILLE_PART))
                        except RuntimeError as e:
                            warnings.append('braille: ' + str(e).splitlines()[-1])
                meta = {'title': title, 'score_title': hint, 'warnings': warnings, 'source': str(src), 'exported': time.strftime('%Y-%m-%d %H:%M')}
                meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding='utf8')
                done += 1
                print(f'+ {rel} -> {title}' + (f'  [{len(warnings)} note(s)]' if warnings else ''))
                for w in warnings: print('     ', w)
            except Exception as e:
                print(f'! {rel}: {e}'); meta = {'title': key.replace('_', ' '), 'warnings': [f'EXPORT FAILED: {e}'], 'source': str(src)}
                if not out.exists(): continue
        entries.append({'title': meta['title'], 'file': out.relative_to(HERE).as_posix(), 'folder': folder,
                        'current': folder.split('/')[0] == CURRENT_FOLDER, 'warnings': meta.get('warnings', []),
                        'score_title': meta.get('score_title')})
        if a.limit and done >= a.limit: break

    entries.sort(key=lambda e: (not e['current'], e['folder'].lower(), e['title'].lower()))
    LIBRARY.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding='utf8')
    print(f'library.json: {len(entries)} scores, {done} exported, {time.time()-t0:.0f} s')

if __name__ == '__main__':
    main()
