# Prompt: recreate the June RSVP for Oct 14 (run in Claude Code on Syd's computer)

Copy everything below the line into Claude Code, run from any folder on the computer
that is logged in to Shopify and Formspree.

---

You are setting up the RSVP for the Kids Like Us event on **Wed Oct 14, 6–10 PM**.
Duplicate exactly how the **June 4 Meetup RSVP** worked, then update it. Don't guess. Look first.

## What we know about the June setup
- The form was on **thekidslikeus.com** (Shopify store "THE KIDS LIKE US").
- It posted to **Formspree**. Each RSVP was emailed to syd@ssslighthouse.com with the subject "New Kids Like Us RSVP".
- Fields: `first_name`, `_replyto` (email), `instagram_handle`, `dream`.
- 11 submissions came in June 2–4.

## Steps
1. **Find the June form.**
   - Install the Shopify CLI if it's missing (`npm i -g @shopify/cli`). Then `shopify theme list --store thekidslikeus.myshopify.com`
     (if that store handle is wrong, ask me), and `shopify theme pull --live` into `./klu-theme`.
   - `grep -rn "formspree" ./klu-theme`. Report the file, the section, and the `formspree.io/f/<ID>` value.
   - If nothing turns up, the form may live outside the theme (Shopify page content, or another host).
     Check Online Store > Pages in the admin, and tell me what you find before going on.
2. **Duplicate it.** Copy the June section to a new section/block named `rsvp-oct14`. Keep the same Formspree ID
   (one inbox; the `_subject` and `event` fields keep the two events apart).
   Use `kids-like-us/oct14-rsvp-snippet.html` from github.com/syd-maker/Claude (branch `kids-like-us-oct14-rsvp`)
   as the content. It already has the right fields, the copy, an AJAX submit, and the address-after-RSVP reveal.
   Match the June section's fonts/colors so it looks like the same site.
3. **Fill placeholders.** `YOUR_FORM_ID` comes from step 1. Ask me for `[VENUE ADDRESS]` and `[NEIGHBORHOOD]`.
   Do not invent them.
4. **Preview, don't publish.** Run `shopify theme push --unpublished` and give me the preview link.
5. **Test.** Submit one test RSVP on the preview (first name "TEST"). Confirm the email arrives with the subject
   "New Kids Like Us RSVP — Oct 14", and that the address shows after submit.
6. **Stop and ask me** before publishing the theme live. After I say go, publish and confirm
   `thekidslikeus.com/#rsvp` scrolls to the form.

## Event details (for any copy you touch)
- Wed Oct 14 · 6–10 PM
- DJ Don on sound
- Art by ARTCOUX
- Free food
- Photo wall
- Free merch samples
- Networking for creators & entrepreneurs
- Address only after RSVP

## Don'ts
- Don't delete or edit the June section; duplicate it.
- Don't publish the live theme without my OK.
- Don't change the Formspree notification email.
