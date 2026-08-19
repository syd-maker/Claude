# Clause Reader

A single-page read-aloud tool for working through contract language on a phone.

Open the page, paste the clause text, tap **Read aloud**. It uses the browser's
built-in speech engine, so there is nothing to install and nothing leaves the device.

## What it does

- **Tap any line to start reading from there** — useful for re-hearing one clause.
- **Speed control** from 0.7x to 2.0x, and a voice picker for whatever voices the
  device provides.
- **Keeps your place.** Text, position, speed and voice are saved locally, so closing
  the tab and coming back resumes where you stopped.
- **Progress and time remaining**, so you know how much of a schedule is left.
- **Keyboard control** on a laptop: space to play/pause, arrow keys to step by line.

## How the text is handled

The text shown on screen is always exactly what was pasted — the reader never rewrites it.
Two transformations happen underneath:

1. **Splitting.** Paragraphs are broken into short lines at sentence punctuation, with
   periods shielded where they do not end a sentence: abbreviations (`Inc.`, `Sec.`,
   `i.e.`), decimals (`8.2`), and leading clause numbers (`12.`). Long sentences are cut
   further at commas and dashes. Every line is a contiguous slice of the original string,
   so nothing drifts.
2. **Spoken form.** Only what is sent to the speech engine is normalised: `§` becomes
   "Section", `%` becomes "percent", `$250,000` becomes "250,000 dollars", `i.e.` becomes
   "that is", and leader dots are dropped.

## Known limit

Browser speech stops when the phone screen locks or you switch apps, so the tab has to
stay open while listening. For lock-screen or hands-free playback, render the text to an
audio file instead.

## Files

- `clause-reader.html` — the whole thing. No build step, no dependencies. Fonts load from
  Google Fonts, with system fallbacks if they are unavailable.
