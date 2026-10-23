#!/usr/bin/env python3
"""Build The Working Accord into docs/ (GitHub Pages).

Each src/pages/*.html starts with an HTML comment holding JSON meta:
  <!--meta {"path": "/faq/", "title": "...", "description": "...", "crumb": "FAQ", "type": "faq"} -->
Q&A pairs marked <section class="qa"><h2>Q</h2><div class="a">A</div></section> become FAQPage JSON-LD.

  python3 build.py            # production: canonical + indexable, base "/"
  STAGING=1 BASE=/working-accord/ python3 build.py   # GitHub Pages preview: noindex + preview bar
"""
import html, json, os, re, shutil, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SRC, OUT = ROOT / "src", ROOT / "docs"
SITE = "https://workingaccord.ca"
BASE = os.environ.get("BASE", "/")
STAGING = os.environ.get("STAGING") == "1"
TODAY = date.today().isoformat()

ORG = {"@type": "Organization", "@id": f"{SITE}/#org", "name": "The Working Accord", "url": SITE + "/",
       "logo": SITE + "/assets/icon-512.png",
       "founder": {"@type": "Organization", "name": "mode40", "url": "https://mode40.com"},
       "areaServed": "CA"}
AUTHOR = {"@type": "Organization", "name": "mode40", "url": "https://mode40.com",
          "member": [{"@type": "Person", "name": "Cameron Bergen", "jobTitle": "Founder and CEO"},
                     {"@type": "Person", "name": "Tracy Gromniski", "jobTitle": "Chief Product Officer"}]}


def strip_tags(s):
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", s)
    s = re.sub(r"<sup>.*?</sup>|<a [^>]*class=\"fn\"[^>]*>.*?</a>", "", s)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def load_pages():
    pages = []
    for f in sorted((SRC / "pages").glob("*.html")):
        raw = f.read_text()
        m = re.match(r"<!--meta\s+(\{.*?\})\s*-->", raw, re.S)
        if not m:
            sys.exit(f"{f.name}: missing <!--meta {{...}} -->")
        meta = json.loads(m.group(1))
        meta["body"] = raw[m.end():]
        meta["file"] = f.name
        pages.append(meta)
    return sorted(pages, key=lambda p: p.get("order", 50))


def jsonld(p):
    url = SITE + p["path"]
    graph = [ORG, {"@type": "WebSite", "@id": f"{SITE}/#site", "url": SITE + "/", "name": "The Working Accord",
                   "inLanguage": "en-CA", "publisher": {"@id": f"{SITE}/#org"}}]
    page = {"@type": "WebPage", "@id": url, "url": url, "name": p["title"], "description": p["description"],
            "inLanguage": "en-CA", "isPartOf": {"@id": f"{SITE}/#site"}, "dateModified": TODAY,
            "author": AUTHOR, "publisher": {"@id": f"{SITE}/#org"}}
    if p.get("type") == "article":
        page["@type"] = ["WebPage", "Article"]
        page["headline"] = p["title"]
        page["image"] = SITE + "/assets/og.jpg"
    graph.append(page)
    if p["path"] != "/":
        graph.append({"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": p["crumb"], "item": url}]})
    qa = re.findall(r'<section class="qa"[^>]*>\s*<h2[^>]*>(.*?)</h2>\s*<div class="a">(.*?)</div>', p["body"], re.S)
    if qa:
        graph.append({"@type": "FAQPage", "@id": url + "#faq", "mainEntity": [
            {"@type": "Question", "name": strip_tags(q),
             "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in qa]})
    rules = re.findall(r'<li class="rule[ "][^>]*>.*?<h[23][^>]*>(.*?)</h[23]>', p["body"], re.S)
    if rules:
        graph.append({"@type": "ItemList", "name": "The ten rules of The Working Accord", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": strip_tags(r)} for i, r in enumerate(rules)]})
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


def examples_html(body):
    """Render src/examples.json into the {{EXAMPLES}} slot (server-side, so search engines see every example)."""
    if "{{EXAMPLES}}" not in body:
        return body
    data = json.loads((SRC / "examples.json").read_text())
    sectors = sorted({e["sector"] for e in data})
    slug = lambda s: re.sub(r"[^a-z]+", "-", s.lower()).strip("-")
    chips = "\n    ".join(f'<button type="button" class="chip" aria-pressed="false" data-sector="{slug(s)}">{html.escape(s)}</button>' for s in sectors)
    kinds = {"study": "Study", "changed": "A job that changed", "composite": "Illustration"}
    rows = []
    for i, e in enumerate(data, 1):
        rules = ", ".join(f'<a href="{{{{base}}}}accord/#rule-{r}">{r}</a>' for r in e["rules"])
        src = f'<a href="{{{{base}}}}sources/#s{e["source"]}" class="fn" aria-label="Source {e["source"]}">{e["source"]}</a>' if e.get("source") else ""
        rows.append(f"""<li class="ex ex-{e.get('kind','composite')}" data-sector="{slug(e['sector'])}" id="ex-{i}">
      <div class="ex-who"><p class="ex-kind">{kinds.get(e.get('kind','composite'))}</p><h3>{html.escape(e['role'])}</h3><p class="ex-place">{html.escape(e['place'])}</p></div>
      <div class="ex-before"><p class="ex-label">Before</p><p>{html.escape(e['before'])}</p></div>
      <div class="ex-after"><p class="ex-label">With AI on the team</p><p>{html.escape(e['after'])}{src}</p><p class="ex-rules">Rules {rules}</p></div>
    </li>""")
    return (body.replace("{{EXAMPLES}}", "\n    ".join(rows)).replace("{{SECTOR_CHIPS}}", chips)
            .replace("{{EXAMPLE_COUNT}}", str(len(data))))


def render(p, layout, nav):
    body = examples_html(p["body"])
    preview = ('<div class="preview-bar" role="note">Concept preview, not launched. '
               'Nothing you enter is sent.</div>') if STAGING else ""
    out = (layout.replace("{{title}}", html.escape(p["title"]))
           .replace("{{description}}", html.escape(p["description"]))
           .replace("{{canonical}}", SITE + p["path"])
           .replace("{{robots}}", "noindex, nofollow" if STAGING or p["path"] == "/404" else "index, follow, max-image-preview:large")
           .replace("{{jsonld}}", jsonld(p))
           .replace("{{preview}}", preview)
           .replace("{{bodyclass}}", p.get("bodyclass", "page"))
           .replace("{{nav}}", nav(p["path"]))
           .replace("{{content}}", body))
    out = re.sub(r"[ \t]*<!--.*?-->", "", out, flags=re.S)  # internal review notes never ship
    return out.replace("{{base}}", BASE)


def main():
    layout = (SRC / "layout.html").read_text()
    pages = load_pages()

    def nav(current):
        items = [p for p in pages if p.get("nav")]
        return "\n".join(
            f'<a href="{{{{base}}}}{p["path"].lstrip("/")}"{" aria-current=\"page\"" if p["path"] == current else ""}>{p["nav"]}</a>'
            for p in items)

    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SRC / "assets", OUT / "assets")
    full = ["# The Working Accord: full text", ""]
    for p in pages:
        dest = OUT / p["path"].lstrip("/") / "index.html" if p["path"] != "/404" else OUT / "404.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(p, layout, nav))
        if p["path"] != "/404":
            full += [f"## {p['title']}", f"URL: {SITE}{p['path']}", "", strip_tags(p["body"]), ""]

    real = [p for p in pages if p["path"] != "/404"]
    (OUT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
        "".join(f"  <url><loc>{SITE}{p['path']}</loc><lastmod>{TODAY}</lastmod></url>\n" for p in real) + "</urlset>\n")
    (OUT / "robots.txt").write_text(
        ("User-agent: *\nDisallow: /\n" if STAGING else
         "User-agent: *\nAllow: /\n\n# AI answer engines are welcome to read and cite this site.\n"
         "User-agent: GPTBot\nAllow: /\nUser-agent: OAI-SearchBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\n"
         "User-agent: PerplexityBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\n") +
        f"\nSitemap: {SITE}/sitemap.xml\n")
    (OUT / "llms.txt").write_text((SRC / "llms.txt").read_text().replace("{{site}}", SITE))
    (OUT / "llms-full.txt").write_text("\n".join(full))
    (OUT / ".nojekyll").write_text("")
    check()
    print(f"built {len(pages)} pages -> {OUT} (staging={STAGING}, base={BASE})")


def check():
    """Fail the build on leftovers, em dashes, 'Mode40', or internal links that go nowhere."""
    bad = []
    for f in OUT.rglob("*.html"):
        t = f.read_text()
        rel = f.relative_to(OUT)
        if "{{" in t: bad.append(f"{rel}: unreplaced {{{{")
        if "—" in t: bad.append(f"{rel}: em dash")
        if "Mode40" in t: bad.append(f"{rel}: Mode40")
        if t.count("<h1") != 1: bad.append(f"{rel}: {t.count('<h1')} h1 tags")
        for href in re.findall(r'href="' + re.escape(BASE) + r'([^"#?]*)', t):
            if href.startswith("assets/") or href.endswith((".txt", ".xml")):
                target = OUT / href
            else:
                target = OUT / href / "index.html"
            if not target.exists(): bad.append(f"{rel}: broken link {BASE}{href}")
    if bad:
        sys.exit("CHECK FAILED\n" + "\n".join(sorted(set(bad))))


if __name__ == "__main__":
    main()
