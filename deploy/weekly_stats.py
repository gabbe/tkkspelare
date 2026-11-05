#!/usr/bin/env python3
"""Weekly usage summary for the choir player, from the Apache access log.

    weekly_stats.py                 summarise the last complete week (Mon-Sun), if not done yet
    weekly_stats.py --week 2026-W44 one given ISO week (overwrites)
    weekly_stats.py --backfill      every complete week still covered by the logs
    weekly_stats.py --total         only rebuild total.txt from the saved weeks

Writes <out>/<year>-W<week>.json and .txt and rebuilds total.txt. The summaries hold
counts only: visitors are told apart by IP + browser inside one run and never stored.
A song "opened" means its .mxl was fetched; playback itself happens in the browser
and is not in the log. Runs on voldemort from tkkspelare-stats.timer (see SERVER.md).
"""
import argparse, collections, datetime as dt, glob, gzip, json, os, pathlib, re, urllib.parse

LOGS = ['/var/log/apache2/spelare/access.log*', '/var/log/apache2/spelare-access.log*']
SITE = pathlib.Path('/var/www/tkkspelare')
OUT = pathlib.Path('/var/lib/tkkspelare-stats')
LINE = re.compile(r'^(\S+) \S+ (\S+) \[([^\]]+)\] "GET (\S+) [^"]*" (\d{3}) \S+ "[^"]*" "([^"]*)"')
BOT = re.compile(r'bot|crawl|spider|facebookexternalhit|preview|curl|wget|python', re.I)
DAYS = ['mån', 'tis', 'ons', 'tor', 'fre', 'lör', 'sön']

def read_lines():
    for pattern in LOGS:
        for f in glob.glob(pattern):
            opener = gzip.open if f.endswith('.gz') else open
            with opener(f, 'rt', encoding='utf-8', errors='replace') as fh:
                yield from fh

def parse(lines):
    for l in lines:
        m = LINE.match(l)
        if not m: continue
        ip, user, when, path, status, ua = m.groups()
        if status not in ('200', '206', '304') or BOT.search(ua): continue
        t = dt.datetime.strptime(when, '%d/%b/%Y:%H:%M:%S %z')
        yield {'who': ip + '|' + ua, 'user': user, 't': t, 'path': urllib.parse.unquote(path.split('?')[0]), 'ua': ua}

def device(ua):
    return 'iPhone/iPad' if re.search('iPhone|iPad', ua) else 'Android' if 'Android' in ua else 'Dator'

def titles(out):
    """file stem -> title; remembered across runs, so songs that left the library keep their title"""
    cache = out / 'titles.json'
    known = json.loads(cache.read_text()) if cache.exists() else {}
    try:
        for e in json.loads((SITE / 'library.json').read_text()):
            known[pathlib.Path(e['file']).stem] = e['title']
    except (OSError, ValueError): pass
    cache.write_text(json.dumps(known, ensure_ascii=False, indent=1))
    return known

def summarise(hits, monday, names, first=None):
    end = monday + dt.timedelta(days=7)
    vis, dev, login = set(), {}, collections.Counter()
    songs, song_vis = collections.Counter(), collections.defaultdict(set)
    day_vis, day_open, hours = collections.defaultdict(set), collections.Counter(), collections.Counter()
    for h in hits:
        d = h['t'].date()
        if not (monday <= d < end): continue
        vis.add(h['who']); dev[h['who']] = device(h['ua']); day_vis[d.isoformat()].add(h['who'])
        p = h['path']
        if p.endswith('/') or p.endswith('/index.html'):
            login['lösenord' if h['user'] != '-' else 'hemlig länk'] += 1
        if p.endswith('.mxl') and '/noter/' in p:
            stem = pathlib.Path(p).stem
            songs[stem] += 1; song_vis[stem].add(h['who']); day_open[d.isoformat()] += 1; hours[h['t'].hour] += 1
    iso = monday.isocalendar()
    return {
        'week': f'{iso[0]}-W{iso[1]:02d}', 'from': monday.isoformat(), 'to': (end - dt.timedelta(days=1)).isoformat(),
        'log_starts': first.isoformat() if first and first > monday else None,
        'visitors': len(vis), 'opens': sum(songs.values()),
        'devices': dict(collections.Counter(dev.values())), 'page_views': dict(login),
        'days': {(monday + dt.timedelta(days=i)).isoformat(): {'visitors': len(day_vis[(monday + dt.timedelta(days=i)).isoformat()]),
                 'opens': day_open[(monday + dt.timedelta(days=i)).isoformat()]} for i in range(7)},
        'hours': {str(k): v for k, v in sorted(hours.items())},
        'songs': [{'file': s, 'title': names.get(s, ' '.join(s.replace('_', ' ').split())), 'opens': c, 'visitors': len(song_vis[s])}
                  for s, c in songs.most_common()],
    }

def text(w):
    r = [f"Körspelaren vecka {w['week'][-2:]} ({w['from']} – {w['to']})", '',
         *([f"(loggen börjar {w['log_starts']}, veckan är ofullständig)"] if w.get('log_starts') else []),
         f"Besökare: ca {w['visitors']}    Öppnade låtar: {w['opens']}",
         'Enheter: ' + ', '.join(f'{k} {v}' for k, v in sorted(w['devices'].items(), key=lambda x: -x[1])),
         'Sidvisningar: ' + ', '.join(f'{k} {v}' for k, v in w['page_views'].items()), '', 'Per dag (besökare / öppnade):']
    for i, (d, v) in enumerate(w['days'].items()):
        r.append(f"  {DAYS[i]} {d}  {v['visitors']:3d} / {v['opens']:3d}")
    if w['hours']:
        r += ['', 'Öppnade per timme: ' + '  '.join(f'{h}:{c}' for h, c in w['hours'].items())]
    r += ['', 'Låtar (öppnad / besökare):']
    r += [f"  {s['opens']:3d} / {s['visitors']:2d}  {s['title']}" for s in w['songs']] or ['  (inga)']
    return '\n'.join(r) + '\n'

def total(out):
    weeks = [json.loads(f.read_text()) for f in out.glob('*-W*.json')]
    weeks.sort(key=lambda w: w['week'])
    songs, svis = collections.Counter(), collections.Counter()
    for w in weeks:
        for s in w['songs']: songs[s['title']] += s['opens']; svis[s['title']] += s['visitors']
    r = ['Körspelaren, alla sparade veckor', '', 'Vecka      besökare  öppnade']
    r += [f"{w['week']}  {w['visitors']:8d}  {w['opens']:7d}" for w in weeks]
    r += ['', 'Låtar totalt (öppnad / summa veckobesökare):']
    r += [f'  {c:4d} / {svis[t]:3d}  {t}' for t, c in songs.most_common()]
    (out / 'total.txt').write_text('\n'.join(r) + '\n')

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--week', help='ISO week, e.g. 2026-W44')
    ap.add_argument('--backfill', action='store_true')
    ap.add_argument('--total', action='store_true')
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    if not a.total:
        hits = list(parse(read_lines()))
        this_monday = dt.date.today() - dt.timedelta(days=dt.date.today().weekday())
        if a.week:
            y, w = a.week.split('-W'); mondays = [dt.date.fromisocalendar(int(y), int(w), 1)]
        elif a.backfill and hits:
            first = min(h['t'].date() for h in hits); m = first - dt.timedelta(days=first.weekday())
            mondays = []
            while m < this_monday: mondays.append(m); m += dt.timedelta(days=7)
        else:
            mondays = [this_monday - dt.timedelta(days=7)]
        names = titles(out); first = min((h['t'].date() for h in hits), default=None)
        for m in mondays:
            iso = m.isocalendar(); stem = out / f'{iso[0]}-W{iso[1]:02d}'
            if stem.with_suffix('.json').exists() and not a.week: continue
            w = summarise(hits, m, names, first)
            stem.with_suffix('.json').write_text(json.dumps(w, ensure_ascii=False, indent=1))
            stem.with_suffix('.txt').write_text(text(w))
            print(f"{w['week']}: {w['visitors']} besökare, {w['opens']} öppnade")
    total(out)

if __name__ == '__main__':
    main()
