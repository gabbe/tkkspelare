# Title

MusicXML: `<metronome>` with a beat unit other than a quarter gives the inverse tempo (♪ = 100 plays at 200 BPM, 𝅗𝅥 = 60 at 30 BPM)

<!-- Not yet posted. Draft 2026-09-12 against alphaTab 1.8.4 (CDN build). -->

# Body

> [!NOTE]
> **AI-authored disclosure (`alphatab-ai-authored-v1`)**
>
> Portions of this content were authored by an AI agent. The agent has read
> [AGENTS.md](./AGENTS.md) and the human submitter accepts responsibility for
> compliance with the rules in that document.

## Current Behavior

A MusicXML tempo mark whose `<beat-unit>` is not `quarter` is played at the
wrong speed, in the wrong direction:

- `<beat-unit>eighth</beat-unit><per-minute>100</per-minute>` (♪ = 100, i.e.
  50 quarter notes per minute) plays at **200** quarter notes per minute, four
  times too fast.
- `<beat-unit>half</beat-unit><per-minute>60</per-minute>` (𝅗𝅥 = 60, i.e. 120
  quarter notes per minute) plays at **30**, four times too slow.

Marks with `<beat-unit>quarter</beat-unit>` are fine. The rendered tempo text
is fine as well; only the playback tempo is wrong. A choral score exported from
MuseScore Studio 4.7 with ♪ = 100 at the start (a slow 4/4, so the composer
counted in eighths) plays at a gallop.

## Expected Behavior

The playback tempo should be `per-minute × (beat unit in quarters)`: ♪ = 100
→ 50 quarter BPM, 𝅗𝅥 = 60 → 120 quarter BPM, as in MuseScore, Finale and
Dorico. A dotted beat unit (`<beat-unit-dot/>`) should scale by 1.5.

## Steps to Reproduce

1. Load the attached `C-metronome-eighth.musicxml` (two 4/4 bars of quarter
   notes; bar 1 marked ♪ = 100, bar 2 marked 𝅗𝅥 = 60).
2. Play it and read `api.score.masterBars[0].tempoAutomations[0].value` and
   `[1]`.
3. Observed: 200 and 30. Expected: 50 and 120. Audibly, bar 1 rushes past in
   about 1.2 seconds and bar 2 takes 8 seconds; expected 4.8 and 2 seconds.

## Version and Environment

(paste the output of `alphaTab.Environment.printEnvironmentInfo()` from the
browser where you saw it)

## Possible Solution

—
