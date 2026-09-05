# Title

MusicXML: `dacapo`, `tocoda`, `coda`, `segno`, `fine` on a `<sound>` inside `<direction>` are not imported (only measure-level `<sound>` is)

<!-- Posted as https://github.com/CoderLine/alphaTab/issues/2859 -->

# Body

> [!NOTE]
> **AI-authored disclosure (`alphatab-ai-authored-v1`)**
>
> Portions of this content were authored by an AI agent. The agent has read
> [AGENTS.md](./AGENTS.md) and the human submitter accepts responsibility for
> compliance with the rules in that document.

## Current Behavior

A MusicXML score with *To Coda*, *D.C. al Coda* and a *Coda*, written the way
MuseScore Studio exports them (the `<sound>` element as a child of
`<direction>`), plays straight through. Of the three marks only the coda
symbol arrives in the score model:

```js
api.score.masterBars.map((m, i) => m.directions ? (i + 1) + ':' + [...m.directions] : null).filter(Boolean)
// ["4:3"]   (bar 4, TargetCoda) — nothing on bars 2 and 3
api.tickCache.masterBars.map(m => m.masterBar.index + 1).join(' ')
// "1 2 3 4"
```

If the very same `<sound tocoda="coda1"/>` and `<sound dacapo="yes"/>` elements
are moved out of `<direction>` and placed directly in `<measure>`, they are
imported (bars 2 and 3 get directions). So the jump attributes are only read
from a measure-level `<sound>`, not from the `<direction>`-level one that
notation programs write. (What happens after they are imported is a separate
report.)

## Expected Behavior

Jump attributes on `<sound>` should be honoured in both positions. The MusicXML
schema allows `<sound>` as a child of `<direction>` and as a direct child of
`<measure>` (https://www.w3.org/2021/06/musicxml40/musicxml-reference/elements/sound/),
and MuseScore, like the MusicXML examples, uses the `<direction>` form for
D.C., D.S., To Coda, Coda, Segno and Fine. Tempo from the same element is
already read in that position.

Expected for the file below: directions on bars 2 (to coda), 3 (da capo) and
4 (coda), and playback `1 2 3 1 2 4`.

## Steps To Reproduce

1. Save this as `repro.musicxml` (four whole notes; bar 2 is *To Coda*, bar 3
   is *D.C. al Coda*, bar 4 is the Coda):

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
         <direction placement="above"><direction-type><words>To Coda</words></direction-type><sound tocoda="coda1"/></direction>
         <note><pitch><step>D</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
       <measure number="3">
         <direction placement="above"><direction-type><words>D.C. al Coda</words></direction-type><sound dacapo="yes"/></direction>
         <note><pitch><step>E</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
       <measure number="4">
         <direction placement="above"><direction-type><coda/></direction-type><sound coda="coda1"/></direction>
         <note><pitch><step>F</step><octave>4</octave></pitch><duration>4</duration><voice>1</voice><type>whole</type></note>
       </measure>
     </part>
   </score-partwise>
   ```

2. Load it with the player enabled (`api.load('repro.musicxml')`).

3. Inspect `api.score.masterBars[i].directions` and the playback order as
   above, or press play: the piece plays bars 1–4 once, no da capo.

4. Optional: move each `<sound .../>` so it follows its `</direction>` as a
   direct child of `<measure>`, reload, and see that bars 2 and 3 now carry
   directions.

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
Same result with the `1.9.0-alpha.1891` CDN build. Real-world files showing it:
any MuseScore Studio 4.7.4 export containing D.C. al Coda.

## Platform

Web

## Anything else?

Related: once the attributes are imported, `dacapo` together with `tocoda`
plays to the end instead of jumping to the coda (#2860). Also related, the
ordering of a jump versus a repeat on the same bar (#2858).
