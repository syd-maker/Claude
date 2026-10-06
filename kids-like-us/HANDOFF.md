# Kids Like Us Pop-Up (Wed Oct 14): full handoff

Paste this whole file into a new Claude session on your computer. It has everything done so far and what's left.

---

## 1. Event facts
- **Name:** Kids Like Us Pop-Up
- **When:** Wednesday, October 14, 6–10 PM
- **Where:** Uptown, Minneapolis (near Bde Maka Ska). Peerspace listing: https://peerspace.app.link/PXVOZjTMS6b
- **Exact address:** NOT confirmed yet. It's in the Peerspace booking or your messages with the host. It only goes out to RSVPs, the day before.
- **Price:** Free
- **For:** creatives & entrepreneurs
- **Lineup:**
  - DJ Don (@donald.prah): chill house + hip hop
  - ARTCOUX (Jacob, @artcoux): art showcase
  - Host: Syd Meyer (@syd.mmeyer): global filmmaker · podcast host · 2x agency owner
- **Extras:** free local food, networking/games, photo wall, merch samples
- **Last event:** June 4 meetup at Boom Island Park (w/ North East Tea House). About 40 people in the group photo.

## 2. RSVP page
- **Live URL:** https://thekidslikeus.com/oct14. Tested Oct 2: a test RSVP reached the inbox.
- **Hosting:** Bluehost, plain HTML files (not WordPress). The file is at `public_html/website_a9437115/oct14/index.html`. june19.html lives in the same folder.
- **Form:** Formspree form ID `meewrgbb`. RSVPs email syd@ssslighthouse.com with the subject "New Kids Like Us RSVP — Oct 14".
- **The live version is the OLD, plain one.** A redesigned version (venue hero, lineup photo cards, June group photo, guest dropdown up to +5) is on GitHub but **not uploaded yet**:
  - Code: https://raw.githubusercontent.com/syd-maker/Claude/kids-like-us-oct14-rsvp/kids-like-us/oct14/index.html
  - It needs 5 photos in the same `oct14/` folder, named exactly: `venue.jpg`, `group.jpg`, `don.jpg`, `artcoux.jpg`, `syd.jpg`.
  - The photos are in the Canva design **"KLU Oct14 - RSVP page photos"**: https://www.canva.com/d/BA0DHyIwBHDbHAs. Pages 1–5 are venue, group, don, artcoux and syd. Download all pages as JPG and rename them.
- **Small to-dos:**
  - Rename the Formspree form from "June 19 Meetup RSVP" to "Oct 14 Pop-Up RSVP".
  - Bluehost disk is at 96%, so clean it up before more uploads.

### Prompt for Claude in Chrome (upload the redesign)
> In Bluehost File Manager, open `public_html/website_a9437115/oct14/`. Don't touch anything outside this folder.
> 1. Replace the contents of `index.html` with the text at https://raw.githubusercontent.com/syd-maker/Claude/kids-like-us-oct14-rsvp/kids-like-us/oct14/index.html and save.
> 2. Upload these 5 photos from my Downloads folder into the same folder, named exactly venue.jpg, group.jpg, don.jpg, artcoux.jpg, syd.jpg. (They come from the Canva design "KLU Oct14 - RSVP page photos", pages 1–5 in that order.)
> 3. Open thekidslikeus.com/oct14 with a hard refresh at phone width. Confirm all photos show, then submit a test RSVP (first name TEST, email lindsey@ssslighthouse.com) and confirm the form disappears and "You're in." shows.

## 3. Canva designs
- **Main carousel (yours, the one to post):** "Handmade Collage Meetup Flyer", https://www.canva.com/design/DAHKvBR4_nw. It has 5 slides:
  1. Main poster
  2. DJ DON X KIDS
  3. ARTCOUX X KIDS
  4. Host (pyramids)
  5. we're running it back
- **All-in-one poster: NOT finished.** It's a copy resized to 1080×1350, https://www.canva.com/d/TJPBxu2NLxYorkt. The layout edits didn't save because Canva timed out. Finish it in Canva:
  - "POP-UP" overlaps "W/ DJ DON + ARTCOUX". Shrink POP-UP (about 60) and move it up, just under KIDS.
  - Move "for: creatives & entrepreneurs", the info box and the two columns down about 90px.
  - Add a row of 3 photos above the RSVP line (DJ Don, ARTCOUX, Syd at the pyramids), each about 300×290, with white bold labels underneath: DJ DON · ARTCOUX · HOST: SYD MEYER.
  - Delete the extra right-side arrow and keep one arrow under the RSVP line.
- **Fonts used:** bubble font for KIDS, Bodoni Moda Italic for DJ DON (matches his flyer), Shrikhand for ARTCOUX, Poppins for body text. The brand green is #283d3b.

## 4. Instagram caption (no emojis)
```
for the kids who can feel the ambition and desire for something more.

back in june, 40+ of you showed up at Boom Island to meet strangers who turned into homies.

we're running it back.

DJ Don on the decks, chill house + hip hop
art from ARTCOUX
free local food
photo wall
merch samples
networking + games

for creatives & entrepreneurs.
wed 10.14 · 6–10pm · uptown mpls · FREE

RSVP for the address, link in bio.
bring the friend who needs to be in this room.

@donald.prah @artcoux
```
- Post as an Instagram Collab with @donald.prah and @artcoux.
- Set the bio link to thekidslikeus.com/oct14.

## 5. Stories plan
1. Reshare the carousel with "we're running it back" and a Link sticker to thekidslikeus.com/oct14.
2. DJ Don slide at 9:16, tagging @donald.prah.
3. ARTCOUX slide at 9:16, tagging @artcoux.
4. Host slide with a Countdown sticker: "KIDS POP-UP · Oct 14, 6PM".
5. DM Don and Jacob their 9:16 slides so they repost.

Later: a "who's coming?" poll around Oct 9, a setup story on Oct 13, and a "tonight" story at 4 PM on Oct 14.

## 6. Email to the June RSVPs (Gmail draft, NOT sent)
- In Gmail Drafts, subject "we're running it back (Wed 10.14)", sent from syd@ssslighthouse.com, addressed to you with 10 people in BCC:
  zach@naigateway.com, supersam1106@gmail.com, jarpey4@gmail.com, jaycurated@gmail.com, mackenzie.hagen16@gmail.com, rodneeyang@gmail.com, jamessaskew@gmail.com, ashleyramoss222@gmail.com, mustafa@platii.com, isaseverson@gmail.com
- Send it once the RSVP page is updated.

```
What's up homie,

Back in June we met you at the Kids Like Us meetup at Boom Island Park. We're running it back with another group of people who can move your life forward. Ambitious, unconventional artists and builders.

We've got DJ Don on the music, art from ARTCOUX, free food, a photo wall, free merch samples, and a room full of the kids like us.

Wednesday, October 14 · 6 to 10 PM · Minneapolis

RSVP: thekidslikeus.com/oct14
Address goes out to everyone who RSVPs the day before.

Bring a friend.

Syd
```

## 7. Still to do (in order)
1. Get the exact venue address (Peerspace booking or host messages).
2. Finish the all-in-one poster in Canva (section 3).
3. Upload the redesigned RSVP page and photos (section 2 prompt).
4. Post the carousel and caption, send collab invites, set the bio link.
5. Send the June RSVP email.
6. Oct 13: email the address to everyone who RSVPed. The RSVPs are in your inbox under the subject "New Kids Like Us RSVP — Oct 14".
7. Oct 14, 4 PM: post the "tonight" story.

## 8. Reference
- Voice guide: Notion, "05 — Voice Guide v2 (How Syd Sounds)". Use "homies," no em dashes, scene first.
- Code and prompts on GitHub, repo syd-maker/Claude, branch `kids-like-us-oct14-rsvp`, folder `kids-like-us/`.
