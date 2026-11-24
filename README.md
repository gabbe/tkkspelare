# Körspelare

A web-based practice player for choir singers. It shows the score, plays it,
and lets each singer bring out their own part. Built on [alphaTab](https://alphatab.net)
and MusicXML exported from MuseScore Studio.

The background is an amateur choir digitising its sheet music in MuseScore,
partly to produce braille music (.brf) for a blind singer, partly so that
everyone can practise at home without installing MuseScore.

The user interface is in Swedish (the choir's language). All UI strings live
in one object at the top of the script in `index.html`, so a translation is a
small change.

## What the player does

- Follows the score during playback; click a bar to jump there
- Full part names on the first system, short names (S, A, T, B1, B2 ...) on
  every following one
- Solo, mute and volume per part, plus "damp the others" to hear your own part
  clearly with the rest in the background
- Pan one part to one speaker and the rest to the other
- Tempo 40–200 %
- Loop a selected range, with repeats and jumps switched off so the selection
  loops exactly those bars
- Change the instrument for all parts (piano, choir, organ, strings ...)
- Repeats and D.C./D.S. al Coda are played in the right order
- Rehearsal marks from the score listed as jump targets, and bookmarks per
  song (stored in the browser), one click to jump back
- Keyboard: space plays/pauses whatever was clicked last, arrows step a bar,
  Home returns to the start
- "Report an error in this bar": opens the singer's mail client with song, bar
  and mixer state prefilled, addressed to the digitisers (set `reportEmail` in
  the `T` object in index.html; the button is hidden while it is empty)

## Getting started

The page is static, but alphaTab runs in web workers, so it has to be served
over http:

```bash
py vendor_alphatab.py         # downloads alphaTab 1.9.0, its font and soundfont into vendor/
py -m http.server 8765
```

Open http://127.0.0.1:8765/ . Without a library of your own the player shows
the test fixture `test/fixture.mxl`, an original ten-bar SATB snippet with a
repeat, To Coda, D.C. al Coda, bass divisi and a tie across a bar line.

Your own library is built by `sync.py` (below) into `noter/` and
`library.json`. Both are ignored by git. Sheet music never goes into the
repository.

## sync.py – mirror the MuseScore scores into the library

```bash
py sync.py --only-current        # the "Aktuellt" folder, about a minute for 30 scores
py sync.py                       # everything under "2. MuseScore" (BU and Pågående are skipped)
py sync.py --braille-dir ../BRF/New   # also write one Tenor file per score for SMB
```

For every `.mscz` it runs MuseScore Studio's command-line export, then
`prepare.py`, and writes the result under `noter/` mirroring the Drive
folders. `library.json` lists title, file, folder, whether the score is in the
current repertoire, and the notes prepare.py printed about the score (voices
split, text borrowed, stray voices dropped), which the player shows to the
digitisers. Scores are re-exported only when the `.mscz` changed.

Paths for this machine go in `sync.local.json` (git-ignored):

```json
{"source": "G:/.../Digitala Noter/2. MuseScore",
 "musescore": "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"}
```

If the working copy travels between machines (Syncthing, a shared drive), put
the machine-specific keys under `hosts`, keyed by host name; that block is
merged over the top-level keys on the matching machine:

```json
{"deploy_host": "voldemort", "deploy_dir": "/var/www/tkkspelare",
 "hosts": {"RADISH": {"source": "G:/.../2. MuseScore",
                      "musescore": "C:/Program Files/MuseScore 4/bin/MuseScore4.exe"},
           "fritz":  {"source": "/home/gabriel/Drive/.../2. MuseScore",
                      "musescore": "/home/gabriel/bin/musescore"}}}
```

A second site with a different selection of songs is an entry under
`instances` in the same file, used with `--instance NAME`; see
"A second instance" in [deploy/SERVER.md](deploy/SERVER.md).

Per-song exceptions go in `songs.json` (committed, it holds titles only),
keyed by the `.mscz` file name without extension: `title`, `names` (extra
two-voice staff names), `explode` (divisi written as chords), `skip`, `keep`
(include a file that looks like a single-part score), `braille_part`.
Common staff names (S/A, T/B, Soprano/alto, Damer, Herrar ...) are mapped to
Sopran, Alt, Tenor, Bas by default. Files named "... - Tenor" or "...Tenor2"
are treated as hand-made single-part scores and skipped, since the braille
file is produced from the full score.

## prepare.py – make a MuseScore export playable per part

alphaTab mixes per part, not per voice within a part. Choral scores are often
written as S/A on one staff and T/B on another. `prepare.py` rewrites the
export without touching the MuseScore file. Standard library only, no venv.

```bash
py prepare.py in.mxl out.mxl --names "S/A=Sopran,Alt;T/B=Tenor,Bas" --explode "Bas=Bas 1,Bas 2" --copy-lyrics --unison-fill
```

1. Parts holding several voices are split into one part per voice. `--names`
   names them, and each new part gets a short name for the staff labels
   (Sopran 2 -> S2, Bas 1 -> B1, Ténor II -> T2).
2. `--explode` splits divisi written as chords (Bass 1 and Bass 2 on one stem)
   into one part per chord note, top note first. Unison notes go to every part.
3. `--copy-lyrics` gives a voice without text the lyrics of the voice that has
   them, note for note where both start at the same time. A whole part without
   text (Bas 1 next to a Bas 2 that carries it) borrows from a related part
   the same way, and the number of notes that got text is reported.
   A bar in which a voice has no notes gets a whole-measure rest, or with
   `--unison-fill` the choral shorthand is resolved: voice 1 is copied
   (unison), and where voice 1 holds chords in such a bar the top note goes to
   the upper part and the bottom note to the lower one. The bars are listed
   either way.
4. Tied notes that continue into a new bar get an explicit accidental copied
   from the start of the tie. alphaTab otherwise spells notes from the key
   signature, so an F# tied over a bar line in a flat key is drawn as Gb in the
   second bar. alphaTab hides the redundant sign on tied notes.
5. Jumps (D.C., D.S., To Coda, Coda, Fine, Segno) that MuseScore writes as
   `<sound>` inside `<direction>` are copied to measure level, the only place
   alphaTab reads them. The player then turns "D.C." plus "To Coda" into
   "D.C. al Coda" (`fixJumps` in index.html).

Step 3 is a guess per note: where the voices have different rhythms, a note
with no simultaneous onset in the neighbouring voice gets no text. Check each
song. Part names are matched after trimming spaces, colons and line breaks,
so `--names "S A=Sopran,Alt"` matches a MuseScore part named "S⏎A".

### Single part for braille: `--only`

```bash
py prepare.py full.mxl tenor.mxl --names "T/B=Tenor,Bas" --copy-lyrics --only "Tenor 2,Tenor"
```

Keeps one part (first name in the list that exists) and drops the rest. This
replaces the MuseScore "Tenor part with the bass hidden" that had to be
maintained by hand for the braille transcription. System marks that MuseScore
writes on the top staff only (tempo, D.C., To Coda, Coda, Segno, Fine,
rehearsal marks, volta endings) are copied into the kept part. The alphaTab workarounds
(steps 4 and 5) are skipped, so the file is MuseScore's own MusicXML minus the
other parts. Verified on Rättnu min tid: every note, rest, tie, slur, lyric
syllable, barline and direction matches the manual Tenor part export.

## Hosting

The site is static files behind HTTP basic auth on Apache; see
[deploy/SERVER.md](deploy/SERVER.md) for the server setup and
`deploy/spelare.thnkk.se.conf` for the site config. `deploy.py` runs the Drive
sync and uploads the site over SSH in one command.

## vendor_alphatab.py – alphaTab, font and soundfont

Downloads the exact alphaTab release from the CDN into `vendor/`, together with
the Bravura font and the SONiVOX soundfont, so the site needs no CDN at
runtime. The build is used unmodified. (Up to 1.8.4 the script was
`patch_alphatab.py` and also patched the playback order; 1.9.0 finishes the
repeats before a D.C./D.S. on the same bar by itself.)

When the version changes, change the `?v=` on the two `vendor/alphaTab.js`
URLs in `index.html` too. The page and its audio worker must run the same
build, and without a new URL a browser can keep using the old file from its
cache.

## Known alphaTab quirks (1.9.0)

Documented so they are not rediscovered. Each has a workaround in the code.
Upstream issue numbers refer to `upstream-issues/`.

- MusicXML `dacapo` + `tocoda` (MuseScore's separate "D.C." and "To Coda"
  marks) is imported as a plain D.C. and plays to the end. `fixJumps` in
  index.html turns it into D.C. al Coda. Upstream #2860, closed as won't fix.
- Voltas: MuseScore closes every ending but the last with a repeat sign without
  a play count. alphaTab counts passes per repeat and reads each sign as
  "twice", so with three endings it plays the first two and runs on into the
  third. `fixEndingRepeats` in index.html raises the count to the ending number
  plus one. Not reported upstream; the 1.9.0 release notes mention the limit.
- A `<sound tempo>` directly under `<measure>` is ignored (inside a
  `<direction>` it works). prepare.py adds a metronome mark, see
  `add_missing_metronome`. Not reported upstream.
- A measure shorter than its time signature is played at full length unless it
  is marked `implicit="yes"`, which MuseScore writes only for a pickup at the
  very start. See `mark_short_measures` in prepare.py. Not reported upstream.
- Bar numbers are drawn only on the first bar of each system by default. The
  player sets `stylesheet.scoreConfig.barNumber` to all bars, since bookmarks
  and error reports go by bar number.
- Instrument change: the importer stores the file's instrument as a beat
  automation that overrides `playbackInfo.program`. Both must be changed.
- `playbackInfo.volume` is used both as MIDI channel volume when generating
  and as mixer volume that alphaTab re-applies in `readyForPlayback` after
  every MIDI load, after `midiLoaded`. The player generates with full channel
  volume and then sets the field to the mixer level.
- A playback range is stored in ticks, which move when repeats are switched on
  or off. The player remembers the range as bar plus offset and re-maps it.

Fixed in 1.9.0, workarounds removed: jump before a finished repeat (#2858),
jump attributes on `<sound>` inside `<direction>` (#2859), note spelling from
the key signature (#2861), `midiLoaded.on()` after the first load (#2862),
and `<metronome>` with a beat unit other than a quarter (draft 06, never
posted). 1.9.0 also plays a first ending only once; 1.8.4 repeated it.

## Planned

- Instrument presets and soundfont selection

## License

MIT, see LICENSE. alphaTab is MPL 2.0 and is not part of the repository.

---

## För körens digitaliserare (svenska)

Så här gör du en ny sång spelbar:

1. Spara sången som vanligt i MuseScore i mappen "2. MuseScore" på Drive
   (i "Aktuellt" om den är på repertoaren). Ingen export behövs.
2. Kör `py sync.py --only-current`. Skriptet exporterar, delar upp stämmorna
   och skriver biblioteket.
3. Läs anmärkningarna som skrivs ut, eller titta på sånger märkta ⚠ i
   spelaren: där står vad skriptet gissat (kopierad text, delade ackord,
   bortplockade lösa stämmor). Rätta i MuseScore om något är fel, eller lägg
   en rad i `songs.json` om sången behöver egna inställningar.
4. Lyssna igenom i spelaren. Kontrollera särskilt repriser, D.C. och att texten
   hamnade rätt på den stämma som inte hade egen text.

Noterna får inte checkas in i git. Mappen `noter/` och `library.json` ignoreras.
