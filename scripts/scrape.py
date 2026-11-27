"""Descarga el programa de Vida y Ministerio desde wol.jw.org y guarda data/AAAA-MM.json.
Uso: python scripts/scrape.py 2026-12 [2027-01 ...]   (sin argumentos: mes actual + 2 siguientes)"""
import re, sys, json, time, datetime as dt, pathlib, requests
from bs4 import BeautifulSoup
B = "https://wol.jw.org"; H = {"User-Agent": "Mozilla/5.0 (uso personal, hoja Vida y Ministerio)"}
SECC = ("TESOROS", "SEAMOS", "NUESTRA VIDA")
def get(u):
    r = requests.get(u, headers=H, timeout=30); r.raise_for_status(); time.sleep(1.5)
    return BeautifulSoup(r.text, "html.parser")
def clean(t): return " ".join(t.replace("\u00a0", " ").replace("\u2002", " ").split())
def mondays(y, m):  # semanas cuyo lunes cae en el mes (igual que tu hoja)
    d = dt.date(y, m, 1)
    while d.month == m:
        if d.weekday() == 0: yield d
        d += dt.timedelta(1)
def doc_url(d):
    iso = d.isocalendar()
    s = get(f"{B}/es/wol/meetings/r4/lp-s/{iso[0]}/{iso[1]}")
    h = s.find(lambda t: t.name in ("h2", "h3") and "Vida y Ministerio" in t.get_text())
    a = (h.find_next("a", href=re.compile(r"/wol/d/")) if h else None) or s.find("a", href=re.compile(r"/wol/d/r4/lp-s/\d+$"))
    return B + a["href"] if a and a["href"].startswith("/") else (a["href"] if a else None)
def parse(url):
    s = get(url); art = s.select_one("#article") or s
    w = {"label": "", "reading": "", "items": []}; cur = None
    for e in art.find_all(["h1", "h2", "h3", "p"]):
        t = clean(e.get_text())
        if not t: continue
        if e.name == "h1": w["label"] = t.upper()
        elif e.name == "h2":
            if not t.upper().startswith(SECC) and not w["reading"]: w["reading"] = t.upper()
        elif e.name == "h3":
            cur = None
            if m := re.match(r"(\d+)\.\s*(.*)$", t):
                cur = {"n": int(m[1]), "title": m[2], "mins": None, "detail": ""}; w["items"].append(cur)
        elif cur and cur["mins"] is None and (m := re.match(r"\((\d+) mins?\.\)\s*(.*)$", t)):
            cur["mins"], cur["detail"] = int(m[1]), m[2]
    txt = clean(art.get_text(" "))
    for k, marca in (("intro_song", ""), ("living_song", "NUESTRA VIDA CRISTIANA"), ("closing_song", "Palabras de conclusión")):
        i = txt.find(marca) if marca else 0
        m = re.search(r"Canci[oó]n\s*(\d+)", txt[i:]) if i >= 0 else None
        if m: w[k] = int(m[1])
        else: print(f"  AVISO: no encontré {k}")
    return w
def month(ym):
    y, m = map(int, ym.split("-")); weeks = []
    for d in mondays(y, m):
        try:
            u = doc_url(d)
            if not u: print(f"  {d}: aún no publicada"); continue
            w = parse(u)
            if len(w["items"]) < 8: print(f"  AVISO {d}: solo {len(w['items'])} puntos, revisa el parser ({u})")
            weeks.append(w); print(f"  {d}: ok ({w['label']})")
        except Exception as ex: print(f"  {d}: error {ex}")
    if weeks:
        p = pathlib.Path("data") / f"{ym}.json"; p.parent.mkdir(exist_ok=True)
        p.write_text(json.dumps({"month": ym, "weeks": weeks}, ensure_ascii=False, indent=1), encoding="utf-8")
if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        t = dt.date.today(); a = [f"{t.year + (t.month + i - 1) // 12}-{(t.month + i - 1) % 12 + 1:02d}" for i in range(3)]
    for ym in a: print(ym); month(ym)
