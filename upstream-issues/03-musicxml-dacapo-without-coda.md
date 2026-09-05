# Title

MusicXML: `<sound dacapo="yes"/>` with a `<sound tocoda>` elsewhere plays to the end after the da capo instead of jumping to the coda

<!-- Posted as https://github.com/CoderLine/alphaTab/issues/2860 -->

# Body

> [!NOTE]
> **AI-authored disclosure (`alphatab-ai-authored-v1`)**
>
> Portions of this content were authored by an AI agent. The agent has read
> [AGENTS.md](./AGENTS.md) and the human submitter accepts responsibility for
> compliance with the rules in that document.

## Current Behavior

A MusicXML score with a *To Coda* mark (`<sound tocoda="coda1"/>`) in bar 2, a
*D.C. al Coda* (`<sound dacapo="yes"/>`) in bar 3 and the *Coda*
(`<sound coda="coda1"/>`) in bar 4 plays

```
1 2 3 1 2 3 4
```

After the da capo, playback runs past the *To Coda* mark and through bar 3
again, and only then reaches the coda. The imported directions are

```
2: JumpDaCoda, 3: JumpDaCapo, 4: TargetCoda
```

(In this repro the `<sound>` elements are direct children of `<measure>`, so
that they are imported at all; see the separate report about
`<direction>`-level `<sound>`.)

## Expected Behavior

```
1 2 3 1 2 4
```

In MusicXML the "al Coda" is not a separate attribute. "D.C. al Coda" is
expressed as `dacapo` on the D.C. bar plus `tocoda` on the bar where the jump
to the coda happens; `tocoda` applies on the pass after the da capo or dal
segno (https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/sound/).
Likewise `dalsegno` + `tocoda` means "D.S. al Coda", and `dacapo`/`dalsegno`
+ `fine` means "al Fine". MuseScore, which wrote the real files we see this
with, plays them that way. The same score entered in alphaTex with
`\jump DaCapoAlCoda` plays `1 2 3 1 2 4`.

## Steps To Reproduce

1. Save this as `repro.musicxml`:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <score-partwise version="4.0">
     <part-list><score-part id="P1"><part-name>Music</part-name></score-part></part-list>
     <part id="P1">
       <measure number="1">
         <attributes><divisions>1</divisions><key><fifths>0</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>
         <note><pitch><step>C</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
       <measure number="2">
         <direction placement="above"><direction-type><words>To Coda</words></direction-type></direction>
         <sound tocoda="coda1"/>
         <note><pitch><step>D</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
       <measure number="3">
         <direction placement="above"><direction-type><words>D.C. al Coda</words></direction-type></direction>
         <sound dacapo="yes"/>
         <note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
       <measure number="4">
         <direction placement="above"><direction-type><coda/></direction-type></direction>
         <sound coda="coda1"/>
         <note><pitch><step>F</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
     </part>
   </score-partwise>
   ```

2. Load it with the player enabled and print

   ```js
   api.tickCache.masterBars.map(m => m.masterBar.index + 1).join(' ')
   ```

   or press play and follow the cursor.

3. Observe `1 2 3 1 2 3 4`.

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

Loaded from `https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js`.
Same result with the `1.9.0-alpha.1891` CDN build.

## Platform

Web

## Anything else?

Related to the report about `<sound>` inside `<direction>` not being imported
(#2859), and to the jump-versus-repeat ordering in #2858. Real-world source: MuseScore Studio 4.7.4 exports of choral pieces with
D.C. al Coda.
