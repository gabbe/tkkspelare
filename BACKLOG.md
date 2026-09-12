# Backlog

Tester feedback and planned work, with a note on how each item can be done in
alphaTab 1.8.4. Items are recorded when they arrive; nothing here is started
until it is picked.

## From the first testers (2026-09-09)

### 1. Always show the short part name (done 2026-09-09)

In a score with many parts it is hard to tell which staff is which after the
first system, where alphaTab prints names only once.

Done via the score stylesheet (`multiTrackTrackNamePolicy = AllSystems`,
`firstSystemTrackNameMode = FullName`, `otherSystemsTrackNameMode = ShortName`;
these are stylesheet properties, not settings). The short
names come from MusicXML `part-abbreviation`, which prepare.py currently
fills with the first three letters of the part name, so Bas 1 and Bas 2 both
become "Bas". Give prepare.py real abbreviations instead: S, A, T, B, S1, S2,
A1, A2, T1, T2, B1, B2, and keep whatever MuseScore provided for anything else.

### 2. Hide muted or damped parts

Plan: a checkbox "Visa bara stämmor som hörs". `api.renderTracks(subset)`
re-renders with only the chosen parts while playback still uses the whole
score, so the cursor and the mixer keep working. Re-rendering takes a moment
on long scores; the checkbox should not re-render on every slider move, only
when mute/solo/damping state changes. Interacts with item 5.

### 3. Spacebar always toggles play/pause (done 2026-09-09)

Today space only works when nothing else has focus; after clicking a button or
a slider the browser gives space to that control.

Plan: one `keydown` listener on `document` that handles space when the target
is not a text field, calls `api.playPause()` and prevents the default. Also
worth adding: Home for "back to start", left/right for bar steps.

### 4. Jump to rehearsal marks (done 2026-09-09)

Plan: alphaTab imports MusicXML `<rehearsal>` into `masterBar.section.marker`,
so the marks are already in the model. List them in the bookmark panel as a
fixed group above the user's own bookmarks ("A", "B", "Vers 2" ...), same jump
mechanism. Also render them, if alphaTab does not already: check
`notation.elements` for section markers.

### 5. Follow one part on a small screen

On a phone the system is taller than the screen. alphaTab scrolls so that the
current bar's system starts at the top, so a lower part is off screen at every
line break, and scrolling down by hand is undone at the next system.

Plan: a "Följ stämma" selector (default: none). When set, turn alphaTab's own
scrolling off (`player.scrollMode = Off`) and on `playerPositionChanged` scroll
the container to the chosen part's staff in the current system, using the
staff bounds from `api.renderer.boundsLookup`. Combined with item 2 (hide the
other parts) this also gives a one-staff "my part" view that fits any screen,
which may be the simpler answer for phones.

### 6. Respect the phone's status bar and notch (iPhone report, 2026-09-09)

On an iPhone the top of the sidebar is hidden behind the clock, Wi-Fi and
battery icons and the camera cut-out. Works otherwise.

Plan: add `viewport-fit=cover` to the viewport meta and pad the top of the
sidebar and the score container with `env(safe-area-inset-top)` (and the other
three insets for landscape and the home indicator). While at it, the page has
no viewport meta at all yet, which is probably why it renders at desktop scale
on phones; adding `width=device-width, initial-scale=1` is part of the same
change and should be checked together with item 5, since both are about the
phone layout.

### 7. iPhone: no sound while the ring/silent switch is on silent (2026-09-12)

Reported by an iPhone user: with the side switch on silent the player is mute,
although media apps still play in that state. iOS treats Web Audio as
"ambient" sound, which the silent switch cuts, unless the page also plays
through an HTML media element, which puts the tab in "playback" mode.

Plan: on the first user gesture (the play button), start a looping, silent
`<audio>` element with `playsinline`, the technique the "unmute" library uses,
and keep it running while the page is open. Alternative if that is not enough:
route alphaTab's output through `MediaStreamAudioDestinationNode` into an
`<audio>` element. Needs testing on a real iPhone; the desktop cannot reproduce
it.

### 8. Patch alphaTab's note spelling locally (issue #2861) (2026-09-12)

Several users are distracted by the wrong enharmonic spelling: a repeated F#
in a flat key drawn as Gb with a flat, and the extra natural on the following
G. The tie case is already handled by prepare.py; the same-bar case cannot be
fixed from outside because the source deliberately omits the accidental.
Second report of item 6 (status bar / notch) came in the same round.

Plan: extend `patch_alphatab.py` with a second marked patch in the MusicXML
importer: when a `<note>` has no `<accidental>` element, derive the spelling
from `<alter>` (1 → ForceSharp, −1 → ForceFlat, 2/−2 → double, 0 → Default,
or ForceNatural when the key signature alters that letter). Whether a sign is
drawn is still decided by alphaTab's accidental helper, so no extra signs
should appear. First check whether the 1.9 alpha already fixed #2861; if it
did, backport that change instead of inventing one. Same anchor-once-or-abort
rule as the existing patch, and a fixture case in `test/make_fixture.py`
(F# quarter, F# quarter, G half in F major) to verify the rendering.

## Device reports

- Android phones: works (several testers).
- iPhone: works, including audio (first report 2026-09-09). Layout issue with
  the status bar and notch, see item 6 (reported twice). Silent switch mutes
  the player, see item 7.
- One Android tablet: playback "extremely choppy" while the same site is fine
  on a phone. Most likely the synthesizer starving in the audio thread on a
  slow device. Things to try, in order: raise `player.bufferTimeInMilliseconds`
  (default 500) and expose it as a setting; check whether that browser gets
  the AudioWorklet output or the ScriptProcessor fallback (alphaTab logs it at
  debug level); try the `.sf2` soundfont instead of `.sf3` in case ogg decoding
  competes for CPU at load; ask the tester for device model, Android version
  and browser, and whether other web audio sites stutter as well.

## Older items, still open

- Instrument presets per part and soundfont selection (a better piano and
  choir sound than SONiVOX).
- Braille: page/line references, the page-turn mark, the syllable marking
  seen in Herr, wenn ich nur dich habe; waiting for Niklas's answers. See
  the BRF workflow notes.
- Remove the alphaTab workarounds as upstream issues #2858–#2862 get fixed.
- Snabbt jagar stormen våra år crashes SMB 25.5.5.1 (39 meter changes); find
  out which SMB version produced the May transcription.
- Deploy with a key as user gabriel instead of root on voldemort (authorized_keys,
  `deploy_dir` owned by gabriel, `deploy_host: voldemort`), so `deploy.py` never
  waits for a password. Agreed 2026-09-12, deferred.
