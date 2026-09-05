# Title

MusicXML: a note without an `<accidental>` element is spelled from the key signature instead of its `<step>`/`<alter>` (F# rendered as Gb)

<!-- Posted as https://github.com/CoderLine/alphaTab/issues/2861 -->

# Body

> [!NOTE]
> **AI-authored disclosure (`alphatab-ai-authored-v1`)**
>
> Portions of this content were authored by an AI agent. The agent has read
> [AGENTS.md](./AGENTS.md) and the human submitter accepts responsibility for
> compliance with the rules in that document.

## Current Behavior

In a key with flats, a note whose pitch is `<step>F</step><alter>1</alter>`
(F sharp) is drawn as G flat unless that particular `<note>` carries an
`<accidental>sharp</accidental>` element. Notation programs only write the
`<accidental>` element where a sign is actually printed, so this hits:

- the second and later F sharps within the same bar (the sign is only printed
  on the first), and
- a note tied over a bar line (the sign is never reprinted on the tied note).

Example 1 (F major, bar: F# quarter with accidental, F# quarter without, G
half) renders as **♯F, ♭G, ♮G**: three different note heads, the second F#
sits on the G line with a flat, and the following G then gets a natural sign.

Example 2 (F major, whole-note F# with accidental tied to a whole-note F#
without) renders as **♯F tied to ♭G**: the tie visibly connects two different
staff lines, which reads as a pitch change.

Playback is correct in both cases (MIDI 66); only the notation is wrong.

## Expected Behavior

Example 1: ♯F, F, G, all three on their own lines, with one accidental.
Example 2: ♯F tied to F on the same line, no accidental in bar 2.

In MusicXML the spelling of a note is defined by `<step>` and `<alter>`;
`<accidental>` only says which sign is printed
(https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/pitch/ ,
https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/accidental/).
MuseScore renders both examples as expected. The problem is very common in
choral music: any leading note in a minor key with flats (C# in D minor, F#
in G minor) is affected whenever the accidental is not reprinted.

## Steps To Reproduce

1. Save example 1 as `same-bar.musicxml`:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <score-partwise version="4.0">
     <part-list><score-part id="P1"><part-name>Music</part-name></score-part></part-list>
     <part id="P1">
       <measure number="1">
         <attributes><divisions>1</divisions><key><fifths>-1</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>
         <note><pitch><step>F</step><alter>1</alter><octave>4</octave></pitch><duration>1</duration><voice>1</voice><type>quarter</type><accidental>sharp</accidental></note>
         <note><pitch><step>F</step><alter>1</alter><octave>4</octave></pitch><duration>1</duration><voice>1</voice><type>quarter</type></note>
         <note><pitch><step>G</step><octave>4</octave></pitch><duration>2</duration><voice>1</voice><type>half</type></note>
       </measure>
     </part>
   </score-partwise>
   ```

2. Save example 2 as `tie.musicxml` (same header, two bars):

   ```xml
       <measure number="1">
         <attributes><divisions>1</divisions><key><fifths>-1</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>
         <note><pitch><step>F</step><alter>1</alter><octave>4</octave></pitch><duration>4</duration><tie type="start"/><voice>1</voice><type>whole</type><accidental>sharp</accidental><notations><tied type="start"/></notations></note>
       </measure>
       <measure number="2">
         <note><pitch><step>F</step><alter>1</alter><octave>4</octave></pitch><duration>4</duration><tie type="stop"/><voice>1</voice><type>whole</type><notations><tied type="stop"/></notations></note>
       </measure>
   ```

3. Load each with `api.load(...)` and look at the rendering.

4. Observe the flat G (and the natural on the following G) in example 1, and
   the tie between two different lines in example 2.

## Link to jsFiddle, CodePen, Project

(none)

## Version and Environment

```
[AlphaTab][VersionInfo] alphaTab 1.8.4
[AlphaTab][VersionInfo] commit: 022a45c8e42370f9e12e68949d11eada370da83d
[AlphaTab][VersionInfo] build date: 2026-07-05T14:46:18.224Z
[AlphaTab][VersionInfo] High DPI: 1
[AlphaTab][VersionInfo] Platform: Browser
[AlphaTab][VersionInfo] WebPack: false
[AlphaTab][VersionInfo] Vite: false
[AlphaTab][VersionInfo] Browser: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Claude/1.46388.3 Chrome/148.0.7778.280 Safari/537.36 MSIX
[AlphaTab][VersionInfo] Window Size: 0x0
[AlphaTab][VersionInfo] Screen Size: 2560x1440
```

Loaded from `https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js`,
SVG rendering. Same with the `1.9.0-alpha.1891` CDN build. First seen in a
MuseScore Studio 4.7.4 export of a Bb major choral piece with an F# tied over a
bar line in the tenor.

## Platform

Web

## Anything else?

For the tie case we can work around it by adding the omitted `<accidental>`
to the tied note before loading, and alphaTab then draws no extra sign. For the
same-bar case there is no clean workaround from outside, since the source
deliberately omits the element.
