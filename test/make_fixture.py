#!/usr/bin/env python3
"""Generate test/fixture.mxl: a small original SATB piece that exercises everything
prepare.py and the player have to handle, with no copyrighted material.

  - two staves (S/A and T/B), two voices per staff, lyrics on one voice only
  - bass divisi written as chords in bars 5-6 (unison elsewhere)
  - a repeat over bars 3-4
  - To Coda at bar 4, D.C. al Coda at bar 8, Coda at bar 9
  - an F# tied over the bar line 6->7 in F major (spelling test)

Expected playback order after prepare.py + the patched alphaTab:
  1 2 3 4 3 4 5 6 7 8 1 2 3 4 9 10
"""
import zipfile, pathlib

DIV = 4  # divisions per quarter

def note(step, octave, dur, voice, typ, alter=None, lyric=None, chord=False, tie=None, acc=None, stem='up'):
    x = ['<note>']
    if chord: x.append('<chord/>')
    x.append(f'<pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter is not None else '') + f'<octave>{octave}</octave></pitch>')
    x.append(f'<duration>{dur}</duration>')
    if tie in ('start', 'stop'): x.append(f'<tie type="{tie}"/>')
    x.append(f'<voice>{voice}</voice><type>{typ}</type>')
    if acc: x.append(f'<accidental>{acc}</accidental>')
    x.append(f'<stem>{stem}</stem>')
    if tie in ('start', 'stop'): x.append(f'<notations><tied type="{tie}"/></notations>')
    if lyric: x.append(f'<lyric number="1"><syllabic>single</syllabic><text>{lyric}</text></lyric>')
    x.append('</note>')
    return ''.join(x)

def backup(dur): return f'<backup><duration>{dur}</duration></backup>'

WORDS = ['Vi', 'sjung', 'er', 'glatt', 'i', 'kö', 'ren', 'här', 'och', 'nu', 'och', 'se', 'dan', 'slu', 'tar', 'vi']
w = iter(WORDS * 4)

def sa_measure(n):
    """Soprano voice 1 with lyrics, alto voice 2 without."""
    s = [note('C', 5, 4, 1, 'quarter', lyric=next(w)), note('D', 5, 4, 1, 'quarter', lyric=next(w)),
         note('E', 5, 8, 1, 'half', lyric=next(w))]
    a = [note('A', 4, 4, 2, 'quarter', stem='down'), note('B', 4, 4, 2, 'quarter', alter=-1, acc='flat', stem='down'),
         note('C', 5, 8, 2, 'half', stem='down')]
    return ''.join(s) + backup(16) + ''.join(a)

def tb_measure(n):
    """Tenor voice 1 with lyrics; bass voice 2, divisi chords in bars 5-6, F# tie 6->7."""
    if n == 6:
        t = [note('G', 3, 8, 1, 'half', lyric=next(w)), note('F', 3, 8, 1, 'half', alter=1, acc='sharp', lyric=next(w), tie='start')]
    elif n == 7:
        t = [note('F', 3, 8, 1, 'half', alter=1, tie='stop'), note('G', 3, 8, 1, 'half', lyric=next(w))]
    else:
        t = [note('E', 3, 4, 1, 'quarter', lyric=next(w)), note('F', 3, 4, 1, 'quarter', lyric=next(w)),
             note('G', 3, 8, 1, 'half', lyric=next(w))]
    if n in (5, 6):
        b = [note('F', 2, 8, 2, 'half', stem='down'), note('F', 3, 8, 2, 'half', chord=True, stem='down'),
             note('C', 3, 8, 2, 'half', stem='down'), note('C', 2, 8, 2, 'half', chord=True, stem='down')]
    else:
        b = [note('F', 2, 8, 2, 'half', stem='down'), note('C', 3, 8, 2, 'half', stem='down')]
    return ''.join(t) + backup(16) + ''.join(b)

def attrs(first):
    if not first: return ''
    return (f'<attributes><divisions>{DIV}</divisions><key><fifths>-1</fifths></key>'
            '<time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>CLEF</sign><line>LINE</line></clef></attributes>')

def directions(n):
    d = ''
    if n == 1: d += '<direction placement="above"><direction-type><metronome><beat-unit>quarter</beat-unit><per-minute>100</per-minute></metronome></direction-type><sound tempo="100"/></direction>'
    if n == 4: d += '<direction placement="above"><direction-type><words>To Coda</words></direction-type><sound tocoda="coda"/></direction>'
    if n == 9: d += '<direction placement="above"><direction-type><coda/></direction-type><sound coda="coda"/></direction>'
    return d

def barlines(n):
    b = ''
    if n == 3: b += '<barline location="left"><bar-style>heavy-light</bar-style><repeat direction="forward"/></barline>'
    if n == 4: b += '<barline location="right"><bar-style>light-heavy</bar-style><repeat direction="backward"/></barline>'
    if n == 8: b += ('<direction placement="above"><direction-type><words>D.C. al Coda</words></direction-type><sound dacapo="yes"/></direction>'
                     '<barline location="right"><bar-style>light-heavy</bar-style></barline>')
    if n == 10: b += '<barline location="right"><bar-style>light-heavy</bar-style></barline>'
    return b

def part(pid, measure_fn, clef, line):
    out = [f'<part id="{pid}">']
    for n in range(1, 11):
        out.append(f'<measure number="{n}">')
        out.append(attrs(n == 1).replace('CLEF', clef).replace('LINE', line))
        out.append(directions(n))
        left = barlines(n) if n == 3 else ''
        out.append(left)
        out.append(measure_fn(n))
        if n != 3: out.append(barlines(n))
        out.append('</measure>')
    out.append('</part>')
    return ''.join(out)

def scorepart(pid, name, abbr, prog):
    return (f'<score-part id="{pid}"><part-name>{name}</part-name><part-abbreviation>{abbr}</part-abbreviation>'
            f'<score-instrument id="{pid}-I1"><instrument-name>Voice</instrument-name></score-instrument>'
            f'<midi-instrument id="{pid}-I1"><midi-channel>1</midi-channel><midi-program>{prog}</midi-program><volume>78</volume><pan>0</pan></midi-instrument></score-part>')

xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
       '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n'
       '<score-partwise version="4.0"><work><work-title>Testsång</work-title></work>'
       '<identification><creator type="composer">Testfixtur</creator><encoding><software>make_fixture.py</software></encoding></identification>'
       '<part-list>' + scorepart('P1', 'S/A', 'S/A', 53) + scorepart('P2', 'T/B', 'T/B', 53) + '</part-list>'
       + part('P1', sa_measure, 'G', '2') + part('P2', tb_measure, 'F', '4') + '</score-partwise>')

out = pathlib.Path(__file__).with_name('fixture.mxl')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('META-INF/container.xml', '<?xml version="1.0" encoding="UTF-8"?><container><rootfiles>'
               '<rootfile full-path="score.xml" media-type="application/vnd.recordare.musicxml+xml"/></rootfiles></container>')
    z.writestr('score.xml', xml)
print('wrote', out)
