# Site source

The website at the repository root is generated from this folder. Run `python3 build.py` here after any change; it rewrites the pages at the root (`index.html`, `censors.html`, `covers/`, `img/` and so on). Open `../index.html` to preview, then commit and push.

## How the Censors section works

1. `censors.html` shows a timeline with one bar per source (Persian Government, Russian forces, British forces, north, …). Selecting a bar shows that source's covers below, grouped by censor mark. The selection is in the address (`censors.html#british-north`), so links and the Back button work.
2. Selecting a cover opens `covers/<id>.html?from=<source>`. The page shows the front and back, numbered notes on what the cover shows, the journey, and the details.
3. The bar at the top of a cover page keeps you oriented: breadcrumb back to the source, previous and next cover from the same source in date order, and a small timeline showing where the cover falls. A cover read by several sources links to each ("Also read by …"), and the page follows whichever source you came from.
4. "Back to all … covers" returns to the source on the timeline page and outlines the cover you just viewed.

`censors/cp-XX.html` lists every cover carrying one mark.

## Editing

Everything is generated from `data/censors.json`. After editing it, run:

```
cd redesign
python3 build.py
```

Scans are read from `../images` (`<id>_front.jpg`, `<id>_back.jpg`). With Pillow installed (`pip3 install pillow`) the build writes web-sized copies and detail crops to `img/`.

### Data

- `sources`: the censoring authorities, in timeline order, with a colour and a short description.
- `strikes`: one row per mark on each item: `["CP-79", "ink colour or empty", "<item id>", "<source id>"]`.
- `covers`: one entry per item: `kind`, `from`, `to`, `via`, `sent`, `received` (YYYY-MM-DD) or `year`, `rate`, `stamps`, `text`.
- Optional per cover:
  - `features`: the numbered notes. Each has `side` (`front` or `back`), `x` and `y` (position of the number, as fractions of the scan's width and height), `box` (the detail crop as `[left, top, right, bottom]` fractions), `title`, `text`, and `censor: true` for censor marks (numbered in rust). Item 40229 is the worked example.
  - `context` and `context_title`: a short historical note shown beside the cover.
- `marks`: optional `name`, `place` and `meaning` for each mark.


## The other pages

Education, Rates, Forgeries, Collection and Resources are built from `content/<page>.html`. These hold the text of the old pages, cleaned up: each old collapsible box is now a `<section>` with a heading, and each `<x-item key="..."></x-item>` is replaced by that item's card (scans, title, description) from `data/items.json`, which replaces the old `items.js`. Edit the text in `content/`, the items in `data/items.json`, and run `python3 build.py`.

An "On this page" list is generated from the h2 and h3 headings of each page.
