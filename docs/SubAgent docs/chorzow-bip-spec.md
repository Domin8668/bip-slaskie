# Chorzów BIP — Scraping Spec for uchwały Rady Miasta

**Researched:** 2026-03-09  
**Source:** Live probing of https://bip.chorzow.eu

---

## 1. Confirmed Base URL

```
https://bip.chorzow.eu
```

All URLs in the site use the pattern `https://bip.chorzow.eu/index.php?kat=<ID>` (category/document) or `https://bip.chorzow.eu/index.php?id=<ID>` (content page). Both `kat` and `id` appear equivalent in practice (navigating to either renders the same category content).

---

## 2. URL Path to uchwały Listing

### Top-level UCHWAŁY page (lists terms/kadencje)
```
https://bip.chorzow.eu/index.php?id=105532512922596723
```
This page shows links for the council terms:
- **IX kadencja (2024-2029):** `kat=171559651914468222`
- VIII kadencja (2018-2023): `kat=154271464529125912`
- VII kadencja (2014-2018): `kat=141710286623926731`
- VI kadencja (2010-2014): `kat=129172798213377937`
- V kadencja (2006-2010): `kat=116522678419266786`
- IV kadencja (2002-2006): `kat=116522665947438619`

### IX kadencja (2024-2029) — current main entry point
```
https://bip.chorzow.eu/index.php?kat=171559651914468222
```

### Year sub-pages (IX kadencja)
| Year     | URL                                                         |
|----------|-------------------------------------------------------------|
| ROK 2024 | `https://bip.chorzow.eu/index.php?kat=171559656116689972`  |
| ROK 2025 | `https://bip.chorzow.eu/index.php?kat=173885236812798835`  |
| ROK 2026 | `https://bip.chorzow.eu/index.php?kat=177038046033538206`  |

---

## 3. Site Navigation Hierarchy

```
UCHWAŁY (id=105532512922596723)
└── IX kadencja (kat=171559651914468222)
    ├── ROK 2024 (kat=171559656116689972)
    │   ├── SESJA I - ... (kat=SESSION_ID)
    │   │   ├── SPIS UCHWAŁ  ← skip
    │   │   ├── UCHWAŁA Nr I/... (kat=ACT_ID)  ← individual act
    │   │   └── ...
    │   └── ...
    ├── ROK 2025 (kat=173885236812798835)
    │   ├── SESJA XII - 30.01.2025 r. (kat=173885248227029298)
    │   │   ├── SPIS UCHWAŁ (skip)
    │   │   ├── UCHWAŁA Nr XII/120/2025 (kat=173885335939018127)
    │   │   ├── UCHWAŁA Nr XII/121/2025 (kat=173885345912557165)
    │   │   └── ... (12+ acts)
    │   ├── SESJA XIII - 27.02.2025 r. (kat=174127249112259140)
    │   └── ... (15 sessions total in 2025)
    └── ROK 2026 (kat=177038046033538206)
        ├── SESJA XXVII - 30.01.2026 r. (kat=177037672928909782)
        └── SESJA XXVIII - 26.02.2026 r. (kat=177272648315658973)
```

---

## 4. Page Structure: Session Page (acts listing)

When fetching a **session page** (`kat=SESSION_ID`), the relevant acts appear inside the main content area. The structure is a JavaScript accordion rendered server-side when the session's `kat` is the page context.

### Key HTML elements on a session page:

```html
<td class="content00" id="maincontent">
  <div class="content10">
    <div class="menu00">
      <div class="TYT1">IX kadencja (2024-2029)</div>
      <ul class="menu2">
        <!-- Year → Session hierarchy -->
        <li class="W2Kopen1 CL001">  <!-- current year, expanded -->
          <ul class="submenu" style="display: block;">
            <li class="W2Kopen1 CL001">  <!-- current session, expanded -->
              <ul class="submenu" style="display: block;">

                <!-- SKIP THIS: -->
                <li class="W2Kempty">
                  <a href="/index.php?kat=SPIS_ID">SPIS UCHWAŁ</a>
                </li>

                <!-- Each individual act: -->
                <li class="W2Kempty">
                  <a id="ka173885335939018127.78"
                     href="/index.php?kat=173885335939018127"
                     target="_self">
                    UCHWAŁA Nr XII/120/2025 z dnia 30.01.2025 r. w sprawie przyjęcia planów pracy komisji Rady Miasta Chorzów na rok 2025
                  </a>
                </li>

                <li class="W2Kempty">
                  <a href="/index.php?kat=173885345912557165">
                    UCHWAŁA Nr XII/121/2025 z dnia 30.01.2025 r. o zmianie uchwały Nr II/6/2024 ...
                  </a>
                </li>

              </ul>
            </li>
          </ul>
        </li>
      </ul>
    </div>
  </div>
</td>
```

### CSS selectors for extracting acts from a session page:
- **Container of acts:** `li.W2Kempty > a[href*="kat="]`
- **Individual act anchor text** = full title (includes act number and date)
- **Act URL** = value of `href` attribute on the anchor

**IMPORTANT:** The first `W2Kempty` item in each session is "SPIS UCHWAŁ" — it must be filtered out. Check that the title starts with `UCHWAŁA` or `UCHWAŁA NR`.

---

## 5. Data Extraction from Title Text

Titles follow a consistent pattern:

```
UCHWAŁA Nr XII/120/2025 z dnia 30.01.2025 r. w sprawie ...
UCHWAŁA NR XXVII/305/2026 z dnia 30.01.2026 r. w sprawie ...
```

Note: Both `Nr` and `NR` variants are used.

### Regex patterns:
```python
import re

TITLE_PATTERN = re.compile(
    r'UCHWAŁA\s+(?:Nr|NR)\s+(?P<number>[A-Z]+/\d+/\d{4})'
    r'\s+z\s+dnia\s+(?P<date>\d{2}\.\d{2}\.\d{4})\s+r\.',
    re.IGNORECASE
)
```

Extracted fields:
| Field | Example | Source |
|-------|---------|--------|
| `act_number` | `XII/120/2025` | regex group `number` from title |
| `date` | `30.01.2025` (→ parse as `%d.%m.%Y`) | regex group `date` from title |
| `title` | `UCHWAŁA Nr XII/120/2025 z dnia 30.01.2025 r. w sprawie ...` | full anchor text (strip) |
| `url` | `https://bip.chorzow.eu/index.php?kat=173885335939018127` | href with base prefix |
| `doc_id` | `173885335939018127` | `kat` query param from URL |

---

## 6. Individual Act Page Structure

URL: `https://bip.chorzow.eu/index.php?kat=173885335939018127`

```html
<td class="content00" id="maincontent">
  <div class="content10">
    <!-- Title heading with "powrót | TITLE" -->
    <div class="TYT1">
      <a href="/index.php?kat=171559651914468222">powrót</a>
       | UCHWAŁA Nr XII/120/2025 z dnia 30.01.2025 r. w sprawie ...
    </div>

    <!-- PDF download link -->
    <div>
      <p class="zeromargin">
        pobierz plik:
        <a href="file/u__120.pdf" target="file">
          [ UCHWAŁA Nr XII/120/2025 z dnia 30.01.2025 r. w sprawie ... ]
        </a>
      </p>
    </div>

    <!-- Metadata (creation date, author) -->
    <div class="TYT1">
      <span style="font-size: 70%">
        osoba odpowiedzialna za treść: Magdalena Jakubiec, dnia: 2025-02-06
        <br>utworzony: 06-02-2025 / modyfikowany: 06-03-2025
        <br>wprowadził(a): Magdalena Jakubiec
        <a href="/index.php?RUN=REJESTR&id=173885335939018127">rejestr zmian</a>
      </span>
    </div>
  </div>
</td>
```

**CSS selectors on individual act page:**
- Title: `div.TYT1:first-of-type` text (after stripping "powrót |" prefix)
- PDF link: `a[href$=".pdf"]` → absolute URL: `https://bip.chorzow.eu/add_www/` + href value
  - Note: base href is `<base href="/add_www/">` in the `<head>`

---

## 7. Stable Unique ID

The `kat` parameter in the URL is the stable unique ID for each act. It is a large numeric string (18 digits), e.g.:
```
173885335939018127
```

These IDs appear to be timestamp-derived (Unix timestamp × 10^9 or similar), ensuring global uniqueness across all documents.

**Recommended ID format:** `chorzow-{kat_value}`, e.g., `chorzow-173885335939018127`

---

## 8. Pagination

**None.** All acts within a session are presented on a single page (no next-page links). Sessions typically contain 5–20 resolutions each.

---

## 9. Scraping Approach

### Strategy: Session-based traversal

```
For current year (and optionally previous year):
  1. Fetch year page (e.g., kat=177038046033538206 for ROK 2026)
  2. Parse session IDs from W2K submenu items (the W2Kopen1 expanded year submenu)
  3. For each session:
     a. Fetch session page (kat=SESSION_ID)
     b. Parse from the innermost expanded submenu:
        - All <li class="W2Kempty"> anchors
        - Filter: skip items with text "SPIS UCHWAŁ"
        - Extract: title (anchor text), url (href → absolute), kat ID (from href)
     c. For each act link, parse title+date+number from anchor text (no need to visit act page)
  4. Return acts as LegalAct objects
```

**No need to visit individual act pages** — all necessary data (title, number, date) is extractable from the session listing anchor text.

### Session page parsing notes:
- When fetching `kat=SESSION_ID`, the session is auto-expanded (W2Kopen1 + display:block submenu)
- Acts are in the deepest `<ul class="submenu">` → `<li class="W2Kempty">` elements
- The year ID and session ID are repeated across pages; use the expanded `W2Kopen1` item's nested `div.submenu` with `display: block`

### BeautifulSoup selector recommendation:
```python
# On session page, find all act links:
soup = BeautifulSoup(html, "html.parser")
maincontent = soup.find(id="maincontent")

# Find all W2Kempty list items with links
act_items = maincontent.select("li.W2Kempty a[href]")
for a in act_items:
    text = a.get_text(strip=True)
    if not text.startswith("UCHWAŁA"):
        continue  # skip SPIS UCHWAŁ and other non-act items
    href = a["href"]  # e.g., "/index.php?kat=173885335939018127"
    kat_id = href.split("kat=")[1]
    url = f"https://bip.chorzow.eu{href}"
    # parse title, date, number from text
```

---

## 10. Sample Act Entries

### From SESJA XII – 30.01.2025 (kat=173885248227029298):

| act_number | date | title (abbreviated) | kat_id | url |
|------------|------|---------------------|--------|-----|
| XII/120/2025 | 30.01.2025 | UCHWAŁA Nr XII/120/2025 ... w sprawie przyjęcia planów pracy komisji | 173885335939018127 | https://bip.chorzow.eu/index.php?kat=173885335939018127 |
| XII/121/2025 | 30.01.2025 | UCHWAŁA Nr XII/121/2025 ... o zmianie uchwały Nr II/6/2024 ... składy osobowe komisji | 173885345912557165 | https://bip.chorzow.eu/index.php?kat=173885345912557165 |
| XII/126/2025 | 30.01.2025 | UCHWAŁA Nr XII/126/2025 ... o zmianie uchwały Nr XI/113/2024 ... uchwała budżetowa 2025 | 173885353447637067 | https://bip.chorzow.eu/index.php?kat=173885353447637067 |
| XII/128/2025 | 30.01.2025 | UCHWAŁA Nr XII/128/2025 ... wybór metody ustalenia opłaty za gospodarowanie odpadami | 173885355622995005 | https://bip.chorzow.eu/index.php?kat=173885355622995005 |

### From SESJA XXVII – 30.01.2026 (kat=177037672928909782):

| act_number | date | title (abbreviated) | kat_id | url |
|------------|------|---------------------|--------|-----|
| XXVII/305/2026 | 30.01.2026 | UCHWAŁA NR XXVII/305/2026 ... uchwała budżetowa Miasta Chorzów na rok 2026 | 177037814130328607 | https://bip.chorzow.eu/index.php?kat=177037814130328607 |
| XXVII/306/2026 | 30.01.2026 | UCHWAŁA NR XXVII/306/2026 ... uchwalenie Wieloletniej Prognozy Finansowej | 177037815019407209 | https://bip.chorzow.eu/index.php?kat=177037815019407209 |
| XXVII/307/2026 | 30.01.2026 | UCHWAŁA NR XXVII/307/2026 ... o zmianie uchwały Nr II/6/2024 ... składy komisji | 177037817914917078 | https://bip.chorzow.eu/index.php?kat=177037817914917078 |
| XXVII/309/2026 | 30.01.2026 | UCHWAŁA NR XXVII/309/2026 ... zamiar przekształcenia VII LO Zespołu Szkół Technicznych | 177037830541159811 | https://bip.chorzow.eu/index.php?kat=177037830541159811 |

---

## 11. Key IDs Reference

| Level | Description | kat ID |
|-------|-------------|--------|
| Kadencja | IX kadencja (2024-2029) | `171559651914468222` |
| Year | ROK 2024 | `171559656116689972` |
| Year | ROK 2025 | `173885236812798835` |
| Year | ROK 2026 | `177038046033538206` |
| Session | SESJA XII (30.01.2025) | `173885248227029298` |
| Session | SESJA XIII (27.02.2025) | `174127249112259140` |
| Session | SESJA XXVII (30.01.2026) | `177037672928909782` |
| Session | SESJA XXVIII (26.02.2026) | `177272648315658973` |

---

## 12. Additional Notes

- **PDF base path:** Individual PDFs are at `https://bip.chorzow.eu/add_www/file/u__NNN.pdf` (the page sets `<base href="/add_www/">`).
- **No authentication required** — all pages are publicly accessible without cookies (aside from styling).
- **Robot-friendliness:** The site does not appear to have a `robots.txt` restriction on these paths.
- **Title variations:** Some sessions have a "SESJA XXI UROCZYSTA" with `_brak uchwał` meaning no resolutions — these should be skipped gracefully.
- **Session "SPIS UCHWAŁ" item:** Each session has a first child `W2Kempty` item linking to a summary list (kat=SPIS_ID). This should be skipped; filter by checking `text.upper().startswith("UCHWAŁA")`.
- **Existing scraper file:** `src/bip_scraper/cities/chorzow.py` — currently a stub with empty `scrape_acts()`.
