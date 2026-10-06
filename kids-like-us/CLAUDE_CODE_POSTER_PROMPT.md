# Claude Code prompt: all-in-one poster + editorial promo pieces

Paste everything below the line into Claude Code on your computer. Before you start, put the photos in one folder (see "Photos").

---

You're designing promo for **Kids Like Us Pop-Up**, a community night for young creatives and entrepreneurs in Minneapolis. I want it to look editorial: like a magazine, a zine or film photography. Not like a Canva template.

## Event facts (use exactly)
- KIDS like us · POP-UP
- Wed 10.14 · 6–10PM · Uptown, Minneapolis · FREE
- for: creatives & entrepreneurs
- DJ DON (@donald.prah): chill house + hip hop
- ARTCOUX (@artcoux): art showcase
- Hosted by SYD MEYER (@syd.mmeyer): global filmmaker · podcast host · 2x agency owner
- free local food · networking + games · photo wall · merch samples
- RSVP for the address → thekidslikeus.com/oct14
- @thekidslikeus
- Last event: June meetup at Boom Island Park (40+ people)

## Brand
- Green #283d3b, deep #142020, white, and one accent: warm yellow #f4d35e
- Fonts (Google Fonts):
  - Rubik 900 for KIDS
  - Poppins for body text
  - Bodoni Moda Italic for DJ DON (it matches his own flyers)
  - Shrikhand for ARTCOUX
- Voice: lowercase and casual, "homies," no em dashes, no emojis

## Photos
Everything is in `./klu-photos/`. List the folder first and look at each image before you use it.
- `venue.jpg` (event space), `group.jpg` (June group at Boom Island), `don.jpg`, `artcoux.jpg`, `syd.jpg` (Syd with a camera at the pyramids)
- Plus June meetup photos: food, people talking, vibes
- Use the June food and vibe shots wherever the design calls for "proof this is real"

## Build
Make each piece as a standalone HTML/CSS file in `./klu-promo/`, then render it to PNG with Playwright. Every piece needs:
- **Feed version:** 1080×1350
- **Story version:** 1080×1920

Rules:
- Keep text inside a safe area of 90px on each side.
- The story versions also need about 250px clear at the top and bottom for Instagram's UI.
- Check every render by viewing the PNG. Fix any overlapping text, cut-off words, or text that's hard to read over a photo before you show me.

### 1. All-in-one poster
Everything on one image, laid out top to bottom:
1. @thekidslikeus
2. KIDS like us
3. POP-UP
4. W/ DJ DON + ARTCOUX
5. for: creatives & entrepreneurs
6. Two even columns:
   - Left: WED 10.14 / 6–10PM / UPTOWN MPLS / FREE ENTRY
   - Right: free local food / networking + games / photo wall / merch samples
7. A row of 3 photo tiles with labels: DJ DON · ARTCOUX · HOST: SYD MEYER
8. A yellow RSVP pill: "RSVP for the address → thekidslikeus.com/oct14"

Use the venue or June group photo as the background, darkened so the text is readable.

Design rules:
- Use 3 text sizes at most.
- Align everything to one center line.
- Keep spacing tight inside each group and looser between groups.

### 2. "The Kids Like Us Times: Issue 02" (newspaper/zine)
A one-page broadsheet in black on off-white newsprint, with a halftone or grain texture on the photos.
- **Masthead:** THE KIDS LIKE US TIMES · ISSUE 02 · MPLS · FREE
- **Headline:** "THE KIDS ARE RUNNING IT BACK"
- **Lead photo:** the June group, with a caption: "Boom Island, June. Strangers in, homies out."
- **Columns:**
  - "On the decks: DJ Don, chill house + hip hop"
  - "On the walls: ARTCOUX"
  - "Your host: Syd Meyer"
- **A food photo** with the caption "free food, again."
- **A "classifieds" box at the bottom:** "WANTED: creatives & entrepreneurs. Wed 10.14, 6–10PM, Uptown. RSVP for address: thekidslikeus.com/oct14"

### 3. "Contact Sheet" (film proof)
A 35mm contact sheet on black, with sprocket holes, frame numbers and a film edge code reading "KIDS LIKE US 400".
- Frames 1–9 are June photos: food, crowd and vibes.
- Mark it up in a marker-style handwriting font (Permanent Marker), as if circled with a grease pencil:
  - Circle 2–3 frames and note "this was june."
  - Leave an empty frame circled with "you, next? 10.14."
- Put the event info on the film's edge strip. The RSVP goes on the bottom margin.
- This ties into the disposable cameras we're putting out at the event. After the event, the same layout can be reused with the new film photos.

### 4. "The Receipt"
A long thermal-paper receipt on a dark background, with a slight curl or shadow. Use a monospace font like Space Mono, with dotted leader lines.
```
KIDS LIKE US POP-UP
UPTOWN MPLS · 10.14 · 6–10PM
--------------------------
DJ DON (chill house/hip hop) ... $0
ARTCOUX art showcase ........... $0
free local food ................ $0
networking + games ............. $0
photo wall ..................... $0
merch samples .................. $0
new homies ..................... priceless
--------------------------
TOTAL ........................ FREE
host: syd meyer
for: creatives & entrepreneurs
```
Add a barcode (a QR code is fine) that links to thekidslikeus.com/oct14, with "RSVP FOR ADDRESS" under it. Make the story version especially tall. It works great as a story.

## Deliver
1. Show me all 8 PNGs: 4 pieces × (feed + story).
2. Write a 2-line caption for each piece in my voice.
3. Tell me which one you'd post first, and why.
4. Don't publish or post anything.
