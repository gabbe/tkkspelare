# Title

`api.midiLoaded.on()` registered after the MIDI is loaded throws "RangeError: Maximum call stack size exceeded" (WebWorker player)

<!-- REVIEWER NOTE (remove before posting): replace the environment block with
     the output from your own browser, see README.md in this folder. -->

# Body

> [!NOTE]
> **AI-authored disclosure (`alphatab-ai-authored-v1`)**
>
> Portions of this content were authored by an AI agent. The agent has read
> [AGENTS.md](./AGENTS.md) and the human submitter accepts responsibility for
> compliance with the rules in that document.

## Current Behavior

With the default (WebWorker) player, calling `api.midiLoaded.on(handler)`
*after* a score has been loaded and its MIDI generated throws immediately:

```
RangeError: Maximum call stack size exceeded
    at get loadedMidiInfo (https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js:51:517921)
    at get loadedMidiInfo (https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js:51:517921)
    at get loadedMidiInfo (https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js:51:517921)
    ...
```

Firefox reports the same recursion with its own wording:

```
InternalError: too much recursion
get loadedMidiInfo@https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js:51:517906
get loadedMidiInfo@https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js:51:517909
get loadedMidiInfo@https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/alphaTab.min.js:51:517909
...
```

The same registration made *before* the first load works, and the handler is
then called on every later `loadMidiForScore()`.

## Expected Behavior

Registering a `midiLoaded` handler at any time should work. Other events
(`scoreLoaded`, `playerReady`) accept late registration and immediately hand
the current value to the new handler; `midiLoaded` should do the same instead
of throwing.

## Steps To Reproduce

1. Create the API with the player enabled and load any score:

   ```js
   const api = new alphaTab.AlphaTabApi(el, {
     player: { enablePlayer: true, soundFont: 'https://cdn.jsdelivr.net/npm/@coderline/alphatab@1.8.4/dist/soundfont/sonivox.sf2' }
   });
   api.tex('\\tempo 120 . 3.3*4');
   ```

2. Wait until `playerReady` has fired (the MIDI is generated and loaded).

3. Run

   ```js
   api.midiLoaded.on(e => console.log('midi loaded', e));
   ```

4. Observe the `RangeError` above. Repeating step 3 before step 1's load
   instead works.

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
default player mode (AlphaSynth in a WebWorker). Reproduced in Brave
(Chromium) and Firefox on Windows 11. Same with the `1.9.0-alpha.1891` CDN
build.

## Platform

Web

## Anything else?

(nothing)
