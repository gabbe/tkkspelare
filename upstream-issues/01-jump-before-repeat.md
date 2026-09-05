# Title

D.C./D.S. on a bar that also closes a repeat is taken on the first pass, so the repeat is only played once

<!-- Posted as https://github.com/CoderLine/alphaTab/issues/2858 -->

# Body

> [!NOTE]
> **AI-authored disclosure (`alphatab-ai-authored-v1`)**
>
> Portions of this content were authored by an AI agent. The agent has read
> [AGENTS.md](./AGENTS.md) and the human submitter accepts responsibility for
> compliance with the rules in that document.

## Current Behavior

When a bar both closes a repeat (`\rc 2`) and carries a jump direction
(`\jump DaCapoAlCoda`), playback executes the jump the first time the bar is
reached. The second pass through the repeat is never played.

With the alphaTex below, the playback order (read from
`api.tickCache.masterBars`, and confirmed by listening with the cursor on) is

```
1 2 3 1 2 4
```

The same happens with `DaCapo`, `DaCapoAlFine` and the `DalSegno` variants
placed on a repeat-closing bar, and with a MusicXML file exported from
MuseScore that has a two-bar repeat ending on the "D.C. al Coda" bar.

## Expected Behavior

```
1 2 3 1 2 3 1 2 4
```

The repeat should finish its passes first, then the D.C. should be taken. On
the pass after the D.C., repeats are not replayed, which alphaTab already
does. This is the usual reading of a repeat sign combined with D.C./D.S. on
the same bar, and MuseScore plays the equivalent score that way: all repeat
passes, then da capo, then coda.

## Steps To Reproduce

1. Load this alphaTex (for example in the alphaTab playground or via
   `api.tex(...)`) with the player enabled:

   ```
   \tempo 120
   .
   \ro 3.3*4 |
   \jump DaCoda 3.3*4 |
   \rc 2 \jump DaCapoAlCoda 3.3*4 |
   \jump Coda 3.3*4
   ```

   Bars 1–3 are a repeat played twice; bar 3 also carries *D.C. al Coda*;
   bar 2 is the *To Coda* point; bar 4 is the Coda.

2. Print the playback order:

   ```js
   api.tickCache.masterBars.map(m => m.masterBar.index + 1).join(' ')
   ```

   or press play and follow the cursor.

3. Observe `1 2 3 1 2 4`: bar 3 is played once before the jump.

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
default WebWorker player, SONiVOX soundfont. The `1.9.0-alpha.1891` build from
the CDN behaves the same.

## Platform

Web

## Anything else?

Context: a choir practice player that plays MusicXML exported from MuseScore
Studio 4.7. Songs with a repeated section that ends on the "D.C. al Coda" bar
are common in our repertoire, and singers notice the missing pass. We are
happy to test a fix or contribute one once the issue is accepted.
