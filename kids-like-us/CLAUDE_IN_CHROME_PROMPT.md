# Claude in Chrome prompt: Kids Like Us Oct 14 (RSVP page + poster)

Copy everything below the line into Claude in Chrome. Be logged in to Bluehost (WordPress) and Canva.

---

You're helping me set up the RSVP page and poster for a Kids Like Us event. Work in my browser and ask me before anything goes public.

**Event:** Kids Like Us, Wed Oct 14, 6–10 PM. DJ Don on sound, art by ARTCOUX, free food, photo wall, free merch samples,
networking for creators & entrepreneurs. The address is only shown to people after they RSVP.

## Part 1: RSVP page at thekidslikeus.com/oct14 (WordPress on Bluehost)

1. Go to the Bluehost dashboard and open WordPress admin for thekidslikeus.com (or go straight to thekidslikeus.com/wp-admin).
2. **Find the old form ID.** Under Pages, find the page from our June meetup RSVP (probably at /june19, or titled June / RSVP / Meetup).
   Open it in the editor and find the URL that looks like `https://formspree.io/f/XXXXXXXX`. Write down the part after `/f/`.
   If you can't find it, tell me. Don't make one up.
3. **Ask me** for (a) the neighborhood to show publicly and (b) the full venue address. Wait for my answer.
4. Pages → Add New. Title: "RSVP Oct 14". In the page settings set the URL slug to `oct14`.
5. Add a **Custom HTML** block and paste the code below. Before saving, replace:
   - `YOUR_FORM_ID` with the ID from step 2
   - `[NEIGHBORHOOD]` and `[VENUE ADDRESS]` with my answers from step 3
6. If the theme puts a big title or sidebar on the page, set the page template to full width / no title if that option exists.
7. Click **Preview**. On the preview, submit one test RSVP (first name: TEST, my email). Confirm:
   - the "You're in" message shows the address
   - the page looks clean on a phone-width window
8. **Stop and ask me before clicking Publish.** After I say go, publish it and open thekidslikeus.com/oct14 to confirm it loads.

### Code for step 5
```html
<section id="rsvp" class="klu-rsvp">
  <h2>RSVP · Wed Oct 14 · 6–10 PM</h2>
  <p>
    🎧 DJ Don · 🎨 Art by ARTCOUX · 🍽 Free food<br>
    📸 Photo wall · 🧢 Free merch samples · 🤝 Networking for creators &amp; entrepreneurs<br>
    📍 [NEIGHBORHOOD] — address sent after you RSVP
  </p>

  <form id="klu-rsvp-form" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
    <input type="hidden" name="_subject" value="New Kids Like Us RSVP — Oct 14">
    <input type="hidden" name="event" value="Oct 14 Night">
    <input type="text" name="_gotcha" style="display:none" tabindex="-1" autocomplete="off">

    <label>First name
      <input type="text" name="first_name" required>
    </label>
    <label>Email
      <input type="email" name="_replyto" required>
    </label>
    <label>Instagram
      <input type="text" name="instagram_handle" placeholder="@">
    </label>
    <label>Bringing anyone?
      <select name="plus_ones">
        <option value="0">Just me</option>
        <option value="1">+1</option>
        <option value="2">+2</option>
      </select>
    </label>
    <label>What are you building / dreaming about?
      <textarea name="dream" rows="3"></textarea>
    </label>

    <button type="submit">I'm in</button>
    <p id="klu-rsvp-error" class="klu-msg" hidden>Something went wrong. Try again or DM @thekidslikeus.</p>
  </form>

  <div id="klu-rsvp-done" class="klu-msg" hidden>
    <h3>You're in. 🖤</h3>
    <p><strong>Wed Oct 14 · 6–10 PM</strong><br>[VENUE ADDRESS]</p>
    <p>Screenshot this. We'll send a reminder the day before.</p>
  </div>
</section>

<script>
  (function () {
    var form = document.getElementById('klu-rsvp-form');
    if (!form) return;
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var btn = form.querySelector('button');
      btn.disabled = true;
      fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { Accept: 'application/json' }
      }).then(function (res) {
        if (!res.ok) throw new Error(res.status);
        form.hidden = true;
        document.getElementById('klu-rsvp-done').hidden = false;
      }).catch(function () {
        document.getElementById('klu-rsvp-error').hidden = false;
        btn.disabled = false;
      });
    });
  })();
</script>

<style>
  .klu-rsvp { max-width: 520px; margin: 48px auto; padding: 0 16px; }
  .klu-rsvp form { display: grid; gap: 14px; }
  .klu-rsvp label { display: grid; gap: 6px; font-weight: 600; }
  .klu-rsvp input, .klu-rsvp select, .klu-rsvp textarea {
    font: inherit; padding: 12px; border: 1px solid currentColor; border-radius: 6px; background: transparent; color: inherit;
  }
  .klu-rsvp button {
    font: inherit; font-weight: 700; padding: 14px; border: 0; border-radius: 6px;
    background: #000; color: #fff; cursor: pointer;
  }
  .klu-rsvp button:disabled { opacity: .5; }
</style>
```

## Part 2: Poster background (Canva)

1. Open https://www.canva.com/d/JfqT_8sRag_t8Eo (the "KIDS LIKE US — OCT 14" poster). Don't change any text.
2. Upload the newest **.webp** in my Downloads folder (the venue photo; ask me if there's more than one) to Canva Uploads.
3. Drag it onto the background photo to replace it. There are 2 stacked background photo layers. Replace both, or replace one and delete the other.
   Keep the dark green overlays.
4. If the white text is hard to read, select the photo → Edit → Adjust → Brightness about −20.
5. Change the two small bottom lines to the same font as "WED 10.14 · 6–10PM" so the whole poster uses one typeface.
6. Download as PNG. Then Resize → Copy & resize to 1080×1350 for a feed post, fix anything that got cut off, and download that too.

## Done when
- thekidslikeus.com/oct14 is live and the test RSVP showed up in my email (subject "New Kids Like Us RSVP — Oct 14")
- I have 2 poster PNGs: story (1080×1920) and feed (1080×1350)
