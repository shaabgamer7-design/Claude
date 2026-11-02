# Ghulam Hussain Farms: Blogger Theme

A custom Blogger theme for **ghulamhussainfarms.blogspot.com**. It keeps the design of the original site preview: mango and orchard-green colours, Fraunces and Inter fonts.

```
blogger-theme/
├── ghulam-hussain-farms-theme.xml   ← the theme (paste into Blogger)
├── pages/                            ← page content (paste into each Blogger Page)
│   ├── 1-mango-varieties.html
│   ├── 2-mango-price.html
│   ├── 3-our-orchard.html
│   ├── 4-wholesale-export.html
│   └── 5-contact.html
└── images/                           ← your photos, compressed and ready to upload
```

## What the theme does

- **Same design on phone and desktop.** `b:responsive='true'` makes Blogger serve this theme to phones as well, instead of its plain default mobile view. If `?m=1` still shows in the address bar, a small script removes it. The canonical tag always points to the clean URL.
- **The homepage is short and focused on orders.** In order: hero, trust strip, 4 featured varieties, a short farm story, how to order, a wholesale and export teaser, the latest 3 blog posts, and a final call to action. The longer content lives on separate pages.
- **Order forms go to WhatsApp.** Blogger can't receive form submissions. When a visitor presses the button, WhatsApp opens with their order already written out and addressed to 0314 4419652.
- **Built for search engines.**
  - Semantic page structure (`header`, `nav`, `main`, `article`, `section`, `footer`), with exactly one H1 per page.
  - A separate title and description for each page, plus social-sharing tags (Open Graph) and a canonical URL.
  - Business details for Google (LocalBusiness and WebSite data) on the homepage, and FAQ data on the varieties page.
  - Search results, label pages and the 404 page are set to `noindex`.
- **Quick to load.** Photos load as you scroll, fonts don't block the page, and every tap target is at least 44–48 px.

---

## Step 1: Back up and install the theme

1. Go to **Blogger → Theme**.
2. Click the **▼ arrow** next to **Customize** and choose **Backup**. Download your current theme to be safe.
3. Click **▼** again and choose **Edit HTML**.
4. Select everything in the editor (Ctrl+A) and delete it.
5. Open `ghulam-hussain-farms-theme.xml`, copy all of it, and paste it into the editor.
6. Click **Save** (the floppy-disk icon).
   - If Blogger warns that some widgets will be deleted, click **Delete widgets**. This theme only uses the main Blog widget.

## Step 2: Mobile settings

1. Go to **Theme → ▼ → Mobile settings**.
2. If you see "Show desktop theme on mobile devices", choose **Desktop**. For responsive themes Blogger may grey this out, which is fine because it means the theme is already being used on phones.
3. Check it: open your site on a phone, or add `?m=1` to the end of the URL on your computer. It should look exactly like the desktop design.

## Step 3: Photos (already done)

All photos already load automatically. The theme and pages point to the files in `images/` through jsDelivr, a free fast image CDN serving this public GitHub repo. You don't need to upload anything.

- **If you ever make the GitHub repo private, the photos will stop loading.** In that case, upload the files from `images/` to Blogger and replace each `cdn.jsdelivr.net/...` URL with the Blogger image URL. To get one: open a new post, upload the image, switch to HTML view, copy the `src`, then delete the draft.
- **To change a photo:** Ctrl+F the file name (for example `chaunsa-mango.jpg`) in the theme or page HTML and replace that URL.
- **Lator photo:** the current one is low resolution (299 px). Replace it with a better photo when you have one.

## Step 4: Create the pages

Go to **Pages → New page** and create one page for each file in `pages/`:

1. In the **title** box, type the Title written at the top of the file.
2. Switch the editor to **HTML view** (the `< >` icon). Paste in everything from the file. The comment at the top won't show on the page.
3. In the right-hand **Page settings**:
   - **Permalink → Custom Permalink**: type the permalink exactly as shown in the table below. The menu links depend on it.
   - **Search description**: paste the one written at the top of the file. If you don't see this field, do Step 5 first.
4. Click **Publish**.

| File | Title | Permalink | URL |
|---|---|---|---|
| 1-mango-varieties.html | Types of Mangoes in Pakistan: Our Mango Varieties | `mango-varieties` | /p/mango-varieties.html |
| 2-mango-price.html | Mango Price in Pakistan: Order Fresh from Our Farm | `mango-price` | /p/mango-price.html |
| 3-our-orchard.html | Our Orchard: A Family Mango Farm in Alipur, Punjab | `our-orchard` | /p/our-orchard.html |
| 4-wholesale-export.html | Wholesale & Export Quality Mangoes from Pakistan | `wholesale-export` | /p/wholesale-export.html |
| 5-contact.html | Contact Ghulam Hussain Farms | `contact` | /p/contact.html |

If your Blogger editor has no Permalink option for pages, publish the page once and note the URL Blogger creates. Then, in **Theme → Edit HTML**, Ctrl+F for the old link (for example `/p/mango-varieties.html`) and replace it with the new one. The links appear in the header, the mobile menu, the footer and the homepage.

**Before publishing the Prices page:** replace the "Ask on WhatsApp" cells with your rates once you've set them, and check the box sizes (5 kg / 10 kg) match what you sell.

## Step 5: Blogger settings

In **Settings**:

- **Title**: `Ghulam Hussain Farms`
- **Description**: `Premium Chaunsa, Sindhri, Anwar Ratol and Langra mangoes from our family orchard in Alipur, Muzaffargarh, Punjab.`
- **Meta tags → Enable search description**: turn ON. Then set the home search description to:
  `Buy fresh Chaunsa, Sindhri, Anwar Ratol and Langra mangoes direct from Ghulam Hussain Farms, a family orchard in Alipur, Punjab. Order on WhatsApp.`
- **HTTPS → HTTPS redirect**: turn ON.
- **Crawlers and indexing → Enable custom robots.txt**: leave this OFF. Blogger's default is fine.
- **Posts → Max posts shown on main page**: 6 to 9. The homepage shows the latest 3.

Then add the site to **Google Search Console** (https://search.google.com/search-console) and submit `https://ghulamhussainfarms.blogspot.com/sitemap.xml` and `/sitemap-pages.xml`.

Also link the website from your **Google Business Profile** ("Ghulam Hussain's Farm" on Maps). That builds local trust for searches around Alipur and Muzaffargarh.

## Step 6: Write blog posts (this is where most of your traffic will come from)

Each post shows up automatically on the homepage journal and the Blog page (`/search`). Give every post a featured image, a search description and 1–2 labels (for example `Chaunsa`, `Mango Guide`). Use H2/H3 headings in the post; the post title is already the H1.

Suggested posts, from your keyword data (Pakistan monthly searches):

| Post title idea | Main keyword | Volume | Publish by |
|---|---|---|---|
| Chaunsa Mango: Taste, Season, Types and Price | chaunsa mango | 1,200 | April |
| Sindhri Mango: Pakistan's Early-Season Favourite | sindhri mango | 800 | April |
| Anwar Ratol Mango: Why It's So Sweet (and So Small) | anwar ratol mango | 800 | April |
| Langra Mango in Pakistan: The Green-Skinned Classic | langra mango | 700 | May |
| Fajri Mango: The Late-Season Giant | fajri mango | 300 | May |
| White Chaunsa vs Kala Chaunsa: What's the Difference? | white chaunsa mango | 200 | May |
| Mango Price in Pakistan This Season (update weekly) | mango price in pakistan | 250 | June |
| Sindhri vs Chaunsa: Which Mango Should You Buy? | sindhri mango vs chaunsa | 30 | May |
| How Many Calories in a Chaunsa Mango? | chaunsa mango calories | 30 (+ variants) | Any time |
| Which City Is Famous for Mangoes in Pakistan? | which city is famous for mangoes in pakistan | 70 | Any time |
| How We Pick Mangoes at the Right Stage (orchard diary) | chaunsa mango orchard pakistan | 10 | June |

Searches peak sharply from **June to August**. Pages need a few months to rank, so publish the variety and price content by April. Link every post to `/p/mango-price.html#order`.

## Editing later

- **Phone or WhatsApp number**: in the theme, Ctrl+F for `923144419652` and `0314 4419652`. The forms use the `WA_NUMBER` setting near the bottom of the theme. Also update the page files.
- **Menu**: Ctrl+F for `<nav aria-label='Main'` (desktop menu) and `<div class='mobile-nav'` (mobile menu).
- **Homepage text**: everything between `HOMEPAGE (landing sections)` and `404` in the theme. Lines marked `[SEO]` hold the main keyword headings.
- **Reusable page blocks**: in a page's HTML view you can use these classes:
  - `<div class="band">…</div>`: full-width cream band
  - `<div class="band band--dark">…</div>`: full-width green band
  - `<div class="grid"><div class="box">…</div></div>`: card grid
  - `<div class="variety">image + text</div>`: two-column row
  - `<details><summary>Question</summary><p>Answer</p></details>`: FAQ item
  - `<form class="form" data-wa-form="Name">…</form>`: WhatsApp form. Every field needs an `id`, a `name` and a matching `<label for="…">`.
- **Wording**: the site says "naturally grown" and "chemical inputs used carefully", which matches how you described the farm. Only add the word "organic" if the orchard is certified.
