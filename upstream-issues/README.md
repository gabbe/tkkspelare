# Upstream issue drafts for alphaTab

Drafts of bug reports for https://github.com/CoderLine/alphaTab/issues, one
problem per file. Written 2026-09-05 against the unmodified CDN build of
alphaTab 1.8.4; the same behaviour is present in the 1.9.0-alpha.1891 build.

| file | problem | our workaround | posted |
|---|---|---|---|
| 01-jump-before-repeat.md | D.C./D.S. on a bar that also closes an unfinished repeat is taken before the repeat | patch_alphatab.py | [#2858](https://github.com/CoderLine/alphaTab/issues/2858) |
| 02-musicxml-sound-in-direction.md | Jump attributes on `<sound>` inside `<direction>` are ignored | prepare.py step 5 | [#2859](https://github.com/CoderLine/alphaTab/issues/2859) |
| 03-musicxml-dacapo-without-coda.md | `dacapo` + `tocoda` plays to the end instead of jumping to the coda | `fixJumps` in index.html | [#2860](https://github.com/CoderLine/alphaTab/issues/2860) |
| 04-musicxml-spelling.md | Notes without `<accidental>` are spelled from the key signature (F# drawn as Gb) | prepare.py step 4, partial | |
| 05-loadedmidiinfo-recursion.md | `api.midiLoaded.on()` after the first load throws a stack overflow | register before first load | |

## alphaTab's rules, and what they mean for you

alphaTab has an `AGENTS.md` that binds AI assistants and a `CONTRIBUTING.md`
for humans. The drafts follow them, and you need to know four things before
posting:

1. **The AI disclosure block stays.** Each draft starts with a quoted note
   containing the token `alphatab-ai-authored-v1`. Their rules require it on
   any AI-assisted text and they route such issues to a review checklist. Do
   not remove or reword it. You, as the submitter, take responsibility for the
   content.
2. **Problems, not solutions.** The drafts describe what a user observes and
   expects, with reproductions. They deliberately contain no code analysis, no
   file or line references and no proposed fixes. Our own analysis stays in
   this repository's README. If the maintainer asks, you can point to
   `patch_alphatab.py`.
3. **Real environment output.** The "Version and Environment" field must be
   the actual output of `alphaTab.Environment.printEnvironmentInfo()`. The
   drafts contain output captured in the Claude desktop app's embedded
   Chromium. Replace it with the output from your own browser: open the
   harness (below), copy the block it prints.
4. **You should have seen the problem yourself.** You have: 01 (D.C. in
   Rättnu), 02 and 03 (D.C. ignored before we pre-processed), 04 (Gb in
   bar 11), and all five through the harness in Brave and Firefox.

## Verify the reproductions in your own browser

```bash
cd upstream-issues/repro
py -m http.server 8766
```

Open http://127.0.0.1:8766/ , wait for "ready", press each button. Issue 04 has
two buttons, 4a (same bar) and 4b (tie), one per example; the rendering of
the last pressed button stays on screen. The page
prints the playback order, the imported directions, the note spelling and the
environment block. `?v=1.9.0-alpha.1891` runs the same against the alpha.

## Posting

Use the "Bug report" template. The drafts are laid out in the template's field
order: Current Behavior, Expected Behavior, Steps To Reproduce, Version and
Environment, Platform (Web), Anything else. Tick "I have searched the existing
issues" (searched 2026-09-05, nothing matching) and "I have read
CONTRIBUTING.md and AGENTS.md" only after you have. In the "AI authorship"
dropdown choose "AI-assisted".

File 01 first. 02 and 03 refer to it in "Anything else". Post them one at a
time and give the maintainer a chance to respond; he may want them merged or
split differently.
