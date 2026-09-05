#!/usr/bin/env python3
"""Fetch alphaTab and patch its playback order so repeats finish before a jump.

alphaTab 1.8.4 executes D.C./D.S. the first time it reaches the bar, even when
that bar also closes a repeat that has not been played the required number of
times. Convention (and MuseScore) is: finish the repeats, then jump. This puts
the pending-repeat check before the direction handling in
MidiPlaybackController._moveNextWithDirections.

Usage:
    py patch_alphatab.py [--version 1.8.4] [--out vendor/alphaTab.js]

Fails loudly if the anchor text is not found exactly once, which is what will
happen when a new alphaTab version changes the code. Re-check the fix then, or
drop the patch once it is fixed upstream.
"""
import argparse, pathlib, urllib.request

ANCHOR = (
    "\t\t\tconst hasDirections = masterBar.directions !== null && masterBar.directions.size > 0;\n"
    "\t\t\tif (this._state === 0 && !hasDirections) return false;\n"
)
PATCH = ANCHOR + (
    "\t\t\t// PATCH (korspelare): a repeat that still has iterations left in this bar\n"
    "\t\t\t// is played before any jump direction placed on the same bar.\n"
    "\t\t\tif (this._state === 0) {\n"
    "\t\t\t\tconst pendingRepeatCount = masterBar.repeatCount - 1;\n"
    "\t\t\t\tif (this._repeatStack.length > 0 && pendingRepeatCount > 0) {\n"
    "\t\t\t\t\tconst pendingRepeat = this._repeatStack[this._repeatStack.length - 1];\n"
    "\t\t\t\t\tif (pendingRepeat.iterations[pendingRepeat.closingIndex] < pendingRepeatCount) return false;\n"
    "\t\t\t\t}\n"
    "\t\t\t}\n"
)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--version', default='1.8.4')
    ap.add_argument('--out', default='vendor/alphaTab.js')
    a = ap.parse_args()
    url = f'https://cdn.jsdelivr.net/npm/@coderline/alphatab@{a.version}/dist/alphaTab.js'
    print('fetching', url)
    src = urllib.request.urlopen(url).read().decode('utf-8')
    n = src.count(ANCHOR)
    if n != 1:
        raise SystemExit(f'anchor found {n} times, expected 1 - alphaTab {a.version} differs, review the patch')
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(src.replace(ANCHOR, PATCH), encoding='utf-8', newline='\n')
    print('wrote', out, f'({out.stat().st_size // 1024} kB), patched MidiPlaybackController')

if __name__ == '__main__':
    main()
