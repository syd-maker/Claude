# Recreate the June RSVP for Oct 14 (WordPress)

thekidslikeus.com resolves to 162.241.218.121, a Bluehost/HostGator-range IP, so the site is WordPress on shared hosting.
The June RSVP was a Formspree form on that site.

## Manual (about 10 min, no code tools needed)
1. Log in at **thekidslikeus.com/wp-admin** (or through the Bluehost dashboard > WordPress > Log in).
2. Go to **Pages** (and check **Posts** too). Open the page with the June 4 RSVP.
   The form is usually in a **Custom HTML** block, or in a contact-form plugin set to Formspree.
3. Find `formspree.io/f/XXXXXXX` in that block and copy the ID.
4. **Pages > Add New** and title it "RSVP". Set the slug to `rsvp`.
5. Add a **Custom HTML** block and paste in `oct14-rsvp-snippet.html`.
   Replace `YOUR_FORM_ID`, `[NEIGHBORHOOD]` and `[VENUE ADDRESS]`.
6. **Preview**, then submit a test RSVP (first name "TEST"). Confirm the email arrives with the subject "New Kids Like Us RSVP — Oct 14"
   and the address shows after submit.
7. Publish. Link in bio: **thekidslikeus.com/rsvp**

Leave the June page alone.

## If running it with Claude Code on your computer
Paste this:

> Help me duplicate the Kids Like Us June 4 RSVP for Oct 14 on my WordPress site (thekidslikeus.com).
> Walk me through wp-admin step by step using `kids-like-us/RECREATE_RSVP_PROMPT.md` and
> `kids-like-us/oct14-rsvp-snippet.html` from github.com/syd-maker/Claude (branch `kids-like-us-oct14-rsvp`).
> Ask me for the Formspree ID, neighborhood, and venue address; don't invent them. Don't publish until I say go.
> Event: Wed Oct 14, 6–10 PM. DJ Don, art by ARTCOUX, free food, photo wall, free merch samples,
> networking for creators & entrepreneurs. Address only after RSVP.

## Note
This repo is public. Don't commit the real venue address here; put it only into WordPress.
