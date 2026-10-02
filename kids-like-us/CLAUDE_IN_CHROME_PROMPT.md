# Claude in Chrome prompt: Kids Like Us Oct 14 (poster + RSVP page)

Paste everything below the line into Claude in Chrome. You need to be logged in to Canva and to thekidslikeus.com/wp-admin.

---

We're running the same setup as our past Kids Like Us events (the Boom Island poster plus a Formspree RSVP on our site).
Keep everything clean and minimal. Don't add new design elements.

**Event:** Kids Like Us, Wed Oct 14, 6–10 PM. DJ Don on sound, art by ARTCOUX, free food, photo wall,
free merch samples, networking for creators & entrepreneurs. The address is only shared after someone RSVPs.

## Part 1: Poster (Canva)
1. Open https://www.canva.com/d/JfqT_8sRag_t8Eo (the "KIDS LIKE US — OCT 14" copy of the Boom Island poster).
   The text is already updated. Don't change the wording.
2. Swap the background photo for the venue photo I downloaded (check my Downloads folder for the newest image; ask me if you're unsure which one).
   - The background is 2 stacked photo layers with the same image. Replace **both**, or replace one and delete the other.
   - Keep the dark green brush overlays and the vignette. They keep the white text readable.
3. Readability check: all the white text has to read clearly on the new photo. If the photo is bright, darken it
   (Edit photo → Brightness about −20) rather than adding boxes.
4. Make the bottom two text blocks use the same font as "KIDS LIKE US" / "WED OCT 14".
5. Export: PNG at 1080×1920 (story). Then Resize → copy to 1080×1350 (feed post) and fix anything that gets cut off.
   Download both.

## Part 2: RSVP page (WordPress)
1. Go to thekidslikeus.com/wp-admin → Pages. Find the June RSVP page (it was at /june19 or the June 4 meetup page)
   and copy the Formspree ID from the `formspree.io/f/XXXXXXX` URL in its form.
2. Pages → Add New. Title it "RSVP Oct 14" and set the slug (URL) to **oct14**.
3. Add a **Custom HTML** block and paste the code from
   https://github.com/syd-maker/Claude/blob/kids-like-us-oct14-rsvp/kids-like-us/oct14-rsvp-snippet.html
4. Replace `YOUR_FORM_ID`. Ask me for `[NEIGHBORHOOD]` and `[VENUE ADDRESS]`. Don't guess them.
5. Preview, then submit one test RSVP with first name "TEST". Check that the thank-you message shows the address.
6. **Ask me before you hit Publish.**

## Done when
- Both poster PNGs are downloaded.
- thekidslikeus.com/oct14 is live and a test RSVP got through.
