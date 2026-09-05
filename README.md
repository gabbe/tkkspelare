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
- Solo, mute and volume per part, plus "damp the others" to hear your own part
  clearly with the rest in the background
- Pan one part to one speaker and the rest to the other
- Tempo 40–200 %
- Loop a selected range, with repeats and jumps switched off so the selection
  loops exactly those bars
- Change the instrument for all parts (piano, choir, organ, strings ...)
- Repeats and D.C./D.S. al Coda are played in the right order

## Getting started

The page is static, but alphaTab runs in web workers, so it has to be served
over http:

```bash
py patch_alphatab.py          # downloads alphaTab 1.8.4 and writes vendor/alphaTab.js
py -m http.server 8765
```

Open http://127.0.0.1:8765/ . Without a library of your own the player shows
the test fixture `test/fixture.mxl`, an original ten-bar SATB snippet with a
repeat, To Coda, D.C. al Coda, bass divisi and a tie across a bar line.

Your own library: put `.mxl` files in `noter/` and create `library.json`:

```json
[
  {"title": "Rättnu min tid", "file": "noter/rattnu.mxl"},
  {"title": "Stjärntändningen", "file": "noter/stjarn.mxl"}
]
```

Both are ignored by git. Sheet music never goes into the repository.

## prepare.py – make a MuseScore export playable per part

alphaTab mixes per part, not per voice within a part. Choral scores are often
written as S/A on one staff and T/B on another. `prepare.py` rewrites the
export without touching the MuseScore file. Standard library only, no venv.

```bash
py prepare.py in.mxl out.mxl --names "S/A=Sopran,Alt;T/B=Tenor,Bas" --explode "Bas=Bas 1,Bas 2" --copy-lyrics
```

1. Parts holding several voices are split into one part per voice. `--names`
   names them.
2. `--explode` splits divisi written as chords (Bass 1 and Bass 2 on one stem)
   into one part per chord note, top note first. Unison notes go to every part.
3. `--copy-lyrics` gives a voice without text the lyrics of the voice that has
   them, note for note where both start at the same time.
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
song.

## patch_alphatab.py – repeats before jumps

alphaTab 1.8.4 executes D.C./D.S. the first time it reaches the bar, even when
that bar also closes a repeat that has not been played the required number of
times. The convention (and MuseScore) is: finish the repeats, then jump. The
script downloads the exact release from the CDN and inserts the check in
`MidiPlaybackController`. It aborts if the anchor text is not found exactly
once, which is what happens when a new alphaTab version changes the code.
Remove it once fixed upstream. After the jump, repeats are not replayed, as in
MuseScore.

## Known alphaTab quirks (1.8.4)

Documented so they are not rediscovered. Each has a workaround in the code.

- A jump takes precedence over a repeat in the same bar. See patch_alphatab.py.
- `<sound>` inside `<direction>` is read for tempo only. See prepare.py step 5.
- Notes are spelled from the key signature, not from MusicXML step and alter.
  See step 4.
- Instrument change: the importer stores the file's instrument as a beat
  automation that overrides `playbackInfo.program`. Both must be changed.
- `playbackInfo.volume` is used both as MIDI channel volume when generating
  and as mixer volume that alphaTab re-applies in `readyForPlayback` after
  every MIDI load, after `midiLoaded`. The player generates with full channel
  volume and then sets the field to the mixer level.
- A playback range is stored in ticks, which move when repeats are switched on
  or off. The player remembers the range as bar plus offset and re-maps it.
- `api.midiLoaded.on(...)` registered after the first load crashes with
  infinite recursion in `loadedMidiInfo` (a typo in the worker proxy).
  Register before the first load.

## Planned

- Library mirroring the choir's Google Drive, with the current folder as the
  start view
- Bookmarks within a song
- Report an error in a bar to the people digitising
- Instrument presets and soundfont selection
- Password gate in front of the site

## License

MIT, see LICENSE. alphaTab is MPL 2.0 and is not part of the repository.

---

## För körens digitaliserare (svenska)

Så här gör du en ny sång spelbar:

1. Exportera från MuseScore som komprimerad MusicXML (.mxl).
2. Kör `prepare.py` på filen. Ange stämnamnen med `--names`, och `--explode`
   om basen eller någon annan stämma är delad som ackord. Lägg alltid till
   `--copy-lyrics` om texten bara ligger på en av stämmorna i systemet.
3. Lägg resultatet i `noter/` och en rad i `library.json`.
4. Lyssna igenom i spelaren. Kontrollera särskilt repriser, D.C. och att texten
   hamnade rätt på den stämma som inte hade egen text.

Noterna får inte checkas in i git. Mappen `noter/` och `library.json` ignoreras.
