#!/usr/bin/env python3
"""Prepare a MuseScore MusicXML export for the alphaTab web player.

Usage:
    py prepare.py IN.mxl OUT.mxl [--names "S/A=Sopran,Alt;T/B=Tenor,Bas"]
                                 [--explode "Bas=Bas 1,Bas 2"] [--copy-lyrics]

Standard library only. Reads .mxl (zip) or .musicxml/.xml and writes the same kind.

What it does, in order:
  1. Split parts that hold several voices (S/A on one staff) into one part per
     voice, so the player can mute/solo/pan each voice.  --names gives them names.
  2. --explode: split a part where divisi is written as chords (Bas 1 + Bas 2 on
     one stem) into one part per chord note, top note first.  Unison notes go to
     every resulting part.
  3. --copy-lyrics: a voice without text borrows the lyrics of the voice that has
     them, note for note where both start at the same time.
  4. Tied notes that continue into a new bar get an explicit <accidental> copied
     from the start of the tie.  alphaTab spells notes from the key signature
     unless an <accidental> is present, so without this an F# tied over a bar
     line in a flat key is drawn as Gb in the second bar.  alphaTab hides the
     redundant sign on tied notes, so nothing extra is drawn.
  5. Jump directions (D.C., D.S., To Coda, Coda, Fine, Segno) that MuseScore
     writes as <sound> inside <direction> are copied to a measure-level <sound>,
     which is the only place alphaTab reads them.  The player then turns
     "D.C." + "To Coda" into "D.C. al Coda" (see index.html).
  6. --only "Tenor 2,Tenor": keep a single part (first match wins) and drop the
     rest, producing the one-part file the braille transcription needs, so no
     "Tenor part with the bass hidden" has to be maintained in MuseScore.
     System marks that MuseScore writes on the top staff only (tempo, D.C.,
     To Coda, Coda, Segno, Fine, rehearsal marks) are carried into the kept
     part. Steps 4 and 5 are alphaTab workarounds and are skipped with --only.
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as ET

STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
JUMP_ATTRS = ('dacapo', 'dalsegno', 'tocoda', 'coda', 'segno', 'fine')
# element order inside <note>, so inserted children land where the schema wants them
NOTE_ORDER = ['grace', 'cue', 'chord', 'pitch', 'unpitched', 'rest', 'tie', 'duration', 'instrument',
              'footnote', 'level', 'voice', 'type', 'dot', 'accidental', 'time-modification', 'stem',
              'notehead', 'notehead-text', 'staff', 'beam', 'notations', 'lyric', 'play', 'listen']

# ---------- file handling ----------
def read(path):
    if path.lower().endswith('.mxl'):
        z = zipfile.ZipFile(path)
        root = [n for n in z.namelist() if n.endswith('.xml') and not n.startswith('META')][0]
        return z.read(root), root
    return open(path, 'rb').read(), None

def write(path, data, inner):
    if path.lower().endswith('.mxl'):
        inner = inner or 'score.xml'
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('META-INF/container.xml',
                '<?xml version="1.0" encoding="UTF-8"?><container><rootfiles>'
                f'<rootfile full-path="{inner}" media-type="application/vnd.recordare.musicxml+xml"/>'
                '</rootfiles></container>')
            z.writestr(inner, data)
    else:
        open(path, 'wb').write(data)

# ---------- helpers ----------
def duration(el):
    d = el.find('duration')
    return int(d.text) if d is not None else 0

def voice_of(el):
    v = el.find('voice')
    return v.text.strip() if v is not None and v.text else '1'

def is_chord_note(n): return n.find('chord') is not None
def is_grace(n): return n.find('grace') is not None

def pitch_value(n):
    p = n.find('pitch')
    if p is None: return None
    return int(p.findtext('octave')) * 12 + STEP[p.findtext('step')] + int(float(p.findtext('alter') or 0))

def insert_ordered(note, child):
    rank = NOTE_ORDER.index(child.tag)
    for i, k in enumerate(list(note)):
        if k.tag in NOTE_ORDER and NOTE_ORDER.index(k.tag) > rank:
            note.insert(i, child); return
    note.append(child)

def walk(measure):
    """Yield (element, position) for every child, tracking the musical position."""
    pos = 0
    for el in measure:
        yield el, pos
        if el.tag == 'backup': pos -= duration(el)
        elif el.tag == 'forward': pos += duration(el)
        elif el.tag == 'note' and not is_chord_note(el) and not is_grace(el): pos += duration(el)

def clone_scorepart(sp, new_id, name):
    nsp = copy.deepcopy(sp); nsp.set('id', new_id)
    nsp.find('part-name').text = name
    ab = nsp.find('part-abbreviation')
    if ab is not None: ab.text = name[:3]
    for el in nsp.findall('score-instrument') + nsp.findall('midi-instrument'):
        el.set('id', el.get('id') + '-' + new_id)
    return nsp

def replace_part(root, partlist, sp, part, replacements):
    """Swap one (score-part, part) for a list of (score-part, part) pairs, in place."""
    si = list(partlist).index(sp); pi = list(root).index(part)
    partlist.remove(sp); root.remove(part)
    for k, (nsp, npart) in enumerate(replacements):
        partlist.insert(si + k, nsp); root.insert(pi + k, npart)

# ---------- 1. voices -> parts ----------
def lyric_map(measure, voice):
    return {pos: el.findall('lyric') for el, pos in walk(measure)
            if el.tag == 'note' and voice_of(el) == voice and not is_chord_note(el) and el.findall('lyric')}

def split_measure(measure, voice, donor=None):
    lyr = lyric_map(measure, donor) if donor else {}
    m = ET.Element('measure', measure.attrib)
    started = False
    for el, pos in walk(measure):
        tag = el.tag
        if tag == 'backup': continue
        if tag == 'forward':
            if voice_of(el) == voice and started: m.append(copy.deepcopy(el))
            continue
        if tag == 'note':
            if voice_of(el) != voice: continue
            if not started:
                started = True
                if pos > 0:
                    fw = ET.SubElement(m, 'forward'); ET.SubElement(fw, 'duration').text = str(pos)
            n = copy.deepcopy(el)
            if (pos in lyr and not n.findall('lyric') and n.find('rest') is None
                    and not is_chord_note(n) and not is_grace(n)):
                for l in lyr[pos]: n.append(copy.deepcopy(l))
            m.append(n); continue
        if tag in ('direction', 'harmony', 'figured-bass'):
            v = el.find('voice')
            if v is not None and v.text and v.text.strip() != voice: continue
        m.append(copy.deepcopy(el))
    for v in m.iter('voice'): v.text = '1'
    return m

def split_voices(root, partlist, names, copy_lyrics):
    for sp in list(partlist.findall('score-part')):
        pid = sp.get('id'); part = root.find(f"part[@id='{pid}']")
        pname = sp.findtext('part-name') or pid
        voices = sorted({voice_of(n) for n in part.iter('note')}, key=int)
        if len(voices) < 2:
            print(f'{pname}: 1 voice, kept'); continue
        newnames = names.get(pname) or [f'{pname} {v}' for v in voices]
        counts = {v: sum(1 for n in part.iter('note') if voice_of(n) == v and n.find('lyric') is not None) for v in voices}
        donor = max(counts, key=counts.get) if copy_lyrics else None
        print(f'{pname}: voices {voices} -> {newnames}, lyrics per voice {counts}'
              + (f', copying text from voice {donor}' if donor else ''))
        reps = []
        for i, v in enumerate(voices):
            nid = f'{pid}v{v}'
            nsp = clone_scorepart(sp, nid, newnames[i] if i < len(newnames) else f'{pname} {v}')
            npart = ET.Element('part', {'id': nid})
            for meas in part.findall('measure'):
                npart.append(split_measure(meas, v, donor if v != donor else None))
            reps.append((nsp, npart))
        replace_part(root, partlist, sp, part, reps)

# ---------- 2. chords -> parts ----------
def explode_measure(measure, index, count):
    """Keep chord note number `index` (0 = top) of every chord; unison notes stay."""
    m = ET.Element('measure', measure.attrib)
    children = list(measure); i = 0
    while i < len(children):
        el = children[i]
        if el.tag != 'note':
            m.append(copy.deepcopy(el)); i += 1; continue
        group = [el]; i += 1
        while i < len(children) and children[i].tag == 'note' and is_chord_note(children[i]):
            group.append(children[i]); i += 1
        first = group[0]
        if len(group) == 1:
            m.append(copy.deepcopy(first)); continue
        ordered = sorted(group, key=lambda n: -(pitch_value(n) or 0))
        pick = copy.deepcopy(ordered[min(index, len(ordered) - 1)])
        c = pick.find('chord')
        if c is not None: pick.remove(c)
        # the first written note carries lyrics, beams and notations for the whole chord
        for tag in ('lyric', 'beam', 'notations', 'stem'):
            if not pick.findall(tag):
                for extra in first.findall(tag): insert_ordered(pick, copy.deepcopy(extra))
        m.append(pick)
    return m

def explode_chords(root, partlist, explode):
    for pname, newnames in explode.items():
        sp = next((s for s in partlist.findall('score-part') if (s.findtext('part-name') or '') == pname), None)
        if sp is None:
            print(f'--explode: no part named {pname!r}; have',
                  [s.findtext('part-name') for s in partlist.findall('score-part')]); continue
        part = root.find(f"part[@id='{sp.get('id')}']")
        chords = sum(1 for n in part.iter('note') if is_chord_note(n))
        print(f'{pname}: {chords} chord notes -> {newnames}')
        reps = []
        for i, name in enumerate(newnames):
            nid = f"{sp.get('id')}c{i+1}"
            nsp = clone_scorepart(sp, nid, name)
            npart = ET.Element('part', {'id': nid})
            for meas in part.findall('measure'):
                npart.append(explode_measure(meas, i, len(newnames)))
            reps.append((nsp, npart))
        replace_part(root, partlist, sp, part, reps)

# ---------- 4. accidentals on tied notes ----------
def fix_tie_accidentals(root):
    fixed = 0
    for part in root.findall('part'):
        pending = {}
        for m in part.findall('measure'):
            for note in m.findall('note'):
                p = note.find('pitch')
                if p is None: continue
                key = (p.findtext('step'), p.findtext('alter'), p.findtext('octave'))
                ties = {t.get('type') for t in note.findall('tie')}
                acc = note.find('accidental')
                if 'stop' in ties and acc is None and key in pending:
                    a = ET.Element('accidental'); a.text = pending[key]
                    insert_ordered(note, a); fixed += 1
                if 'start' in ties:
                    if acc is not None: pending[key] = acc.text
                    elif key not in pending:
                        alt = p.findtext('alter')
                        pending[key] = {'1': 'sharp', '-1': 'flat', '2': 'double-sharp', '-2': 'flat-flat'}.get(alt, 'natural')
                elif 'stop' in ties:
                    pending.pop(key, None)
    print(f'tied-over notes given an explicit accidental: {fixed}')

# ---------- 5. jump directions to measure level ----------
def hoist_jumps(root):
    n = 0
    for part in root.findall('part'):
        for m in part.findall('measure'):
            for d in list(m.findall('direction')):
                s = d.find('sound')
                if s is None: continue
                attrs = {k: v for k, v in s.attrib.items() if k in JUMP_ATTRS}
                if not attrs: continue
                m.insert(list(m).index(d) + 1, ET.Element('sound', attrs)); n += 1
    print(f'jump directions copied to measure level: {n}')

# ---------- 6. keep a single part (for braille transcription) ----------
def carry_system_marks(top, kept):
    """MuseScore writes system-wide marks (tempo, D.C., To Coda, Coda, Segno, Fine,
    rehearsal marks) on the top staff only. Copy those the kept part lacks, at the
    same musical position in the same measure."""
    SYSTEM = ('words', 'coda', 'segno', 'rehearsal', 'metronome')
    n = 0
    for mt, mk in zip(top.findall('measure'), kept.findall('measure')):
        have = {ET.tostring(d) for d in mk if d.tag in ('direction', 'sound')}
        for el, pos in list(walk(mt)):
            if el.tag == 'direction':
                dt = el.find('direction-type')
                if dt is None or not any(c.tag in SYSTEM for c in dt): continue
            elif el.tag == 'sound':
                if not any(k in JUMP_ATTRS for k in el.attrib): continue
            else:
                continue
            if ET.tostring(el) in have: continue
            # insert before the first element of the kept measure at or after `pos`
            target = len(mk)
            for i, (kel, kpos) in enumerate(walk(mk)):
                if kel.tag in ('note', 'forward', 'backup', 'barline') and kpos >= pos:
                    target = i; break
                if kel.tag == 'barline' and kel.get('location') == 'right':
                    target = i; break
            mk.insert(target, copy.deepcopy(el)); n += 1
    print(f'system marks carried from top part: {n}')

def keep_only(root, partlist, preference):
    """Keep the first part (by preference order) whose name matches; drop the rest.
    Returns the kept name. Replaces MuseScore's 'Tenor part with the bass hidden'."""
    names = {sp.findtext('part-name'): sp for sp in partlist.findall('score-part')}
    pick = next((n for n in preference if n in names), None)
    if pick is None:
        raise SystemExit(f'--only: none of {preference} found; parts are {list(names)}')
    top = root.find('part'); kept = root.find(f"part[@id='{names[pick].get('id')}']")
    if kept is not top:
        carry_system_marks(top, kept)
    for sp in list(partlist.findall('score-part')):
        if sp is not names[pick]:
            part = root.find(f"part[@id='{sp.get('id')}']")
            partlist.remove(sp); root.remove(part)
    for pg in list(partlist.findall('part-group')):   # brackets/braces around removed parts
        partlist.remove(pg)
    print(f'kept only {pick!r}')
    return pick

def parse_map(s):
    out = {}
    for item in filter(None, s.split(';')):
        k, v = item.split('=')
        out[k.strip()] = [x.strip() for x in v.split(',')]
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--names', default='', help='rename split voices: "S/A=Sopran,Alt;T/B=Tenor,Bas"')
    ap.add_argument('--explode', default='', help='split chord divisi: "Bas=Bas 1,Bas 2" (applied after --names)')
    ap.add_argument('--copy-lyrics', action='store_true', help='text-less voices borrow the text of the voice that has it')
    ap.add_argument('--only', default='', help='keep a single part, first match wins: "Tenor 2,Tenor" (for braille)')
    a = ap.parse_args()

    data, inner = read(a.src)
    root = ET.fromstring(data)
    partlist = root.find('part-list')
    split_voices(root, partlist, parse_map(a.names), a.copy_lyrics)
    if a.explode: explode_chords(root, partlist, parse_map(a.explode))
    if a.only:
        # A single-part file is for braille transcription, not for alphaTab: leave the
        # MusicXML as MuseScore wrote it (no extra accidentals, no duplicated <sound>).
        keep_only(root, partlist, [x.strip() for x in a.only.split(',')])
    else:
        fix_tie_accidentals(root)
        hoist_jumps(root)

    out = ET.tostring(root, encoding='utf-8', xml_declaration=True)
    m = re.search(rb'<!DOCTYPE[^>]*>', data)
    if m: out = out.replace(b'?>', b'?>\n' + m.group(0), 1)
    write(a.dst, out, inner)
    print('wrote', a.dst)

if __name__ == '__main__':
    main()
