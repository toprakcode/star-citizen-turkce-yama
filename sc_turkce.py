#!/usr/bin/env python3
"""Star Citizen global.ini -> Turkce (Claude API ile).

Kullanim:
  pip install anthropic
  set ANTHROPIC_API_KEY=sk-ant-...      (PowerShell: $env:ANTHROPIC_API_KEY="sk-ant-...")
  python sc_turkce.py --source english_global.ini --estimate     # once maliyet tahmini
  python sc_turkce.py --source english_global.ini --limit 150    # kucuk deneme
  python sc_turkce.py --source english_global.ini                # tamami
"""
import argparse, json, os, re, shutil, sys, threading, hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

MODEL = "claude-haiku-5-5"
PRICE_IN, PRICE_OUT = 0.10 / 1e6, 0.50 / 1e6   # USD / token (<=100K istekler)
DEFAULT_GAME = r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE"

GLOSSARY = """cargo=kargo; hauling=kargo tasimaciligi; bounty=odul avi (bounty); salvage=hurda toplama (salvage);
mining=madencilik; refinery=rafineri; quantum travel=kuantum seyahati; quantum drive=kuantum surucusu;
mission=gorev; contract=sozlesme; reputation=itibar; wanted=aranan; criminal=suclu; hangar=hangar;
landing zone=inis bolgesi; spaceport=uzay limani; outpost=ileri karakol (outpost); shields=kalkanlar;
armistice zone=ateskes bolgesi; Advocacy=Advocacy (ozel ad)."""

SYSTEM = f"""Sen Star Citizen oyununun resmi olmayan Turkce yerellestirmesini yapan bir ceviricisin.
Girdi, [{{"id":1,"t":"..."}}, ...] bicimli bir JSON dizisidir. Her "t" degerini dogal, akici Turkceye cevir
ve ayni bicimde yalnizca JSON dizisi dondur (aciklama, kod blogu yok).
Kurallar:
- §1§ gibi isaretleri (yer tutucular) AYNEN koru, sayisini ve sirasini degistirme.
- Ozel adlari CEVIRME: gemi adlari, ureticiler (Aegis, Drake...), yer/gezegen/istasyon adlari, hizipler,
  madenler ve emtia adlari (Quantanium, Laranite...), kisi adlari, aUEC/UEC, tus ve komut adlari.
- Menu/arayuz metinleri kisa ve net olsun. Hikaye/gorev metinleri akici ve dogal olsun.
- Bas ve sondaki bosluklari ve noktalama isaretlerini koru.
- Asagidaki terimleri tutarli kullan:
{GLOSSARY}"""

PH = re.compile(r"(~\w+\([^)]*\)|%[0-9.]*l?[sdfi]|\{[^{}]*\}|<[^<>]+>|\\n|\\t)")
ASCII_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
LATIN1_MAP = str.maketrans("şğıŞĞİ", "sgiSGI")   # oyun yazi tipinde olmayan 6 harf; ç ö ü Ç Ö Ü kalir


def mask(text):
    holders = []
    def sub(m):
        holders.append(m.group(0))
        return f"§{len(holders)}§"
    return PH.sub(sub, text), holders


def unmask(text, holders):
    for i, h in enumerate(holders, 1):
        if f"§{i}§" not in text:
            return None
        text = text.replace(f"§{i}§", h)
    return None if "§" in text else text


def parse(path):
    lines = open(path, encoding="utf-8-sig").read().splitlines()
    out = []
    for ln in lines:
        if "=" in ln and not ln.lstrip().startswith("//"):
            k, v = ln.split("=", 1)
            out.append((k, v))
        else:
            out.append((None, ln))
    return out


def h(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def translatable(v, min_len):
    return len(v.strip()) >= max(min_len, 2) and re.search(r"[A-Za-z]{2,}", PH.sub("", v)) is not None


def call(client, items, effort="low"):
    payload = json.dumps([{"id": i, "t": t} for i, t in items], ensure_ascii=False)
    r = client.messages.create(model=MODEL, max_tokens=12000, system=SYSTEM,
                               extra_body={"output_config": {"effort": effort}},
                               messages=[{"role": "user", "content": payload}])
    cost = r.usage.input_tokens * PRICE_IN + r.usage.output_tokens * PRICE_OUT
    text = "".join(b.text for b in r.content if b.type == "text").strip()
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        data = json.loads(text[text.index("["): text.rindex("]") + 1])
        return {int(d["id"]): d["t"] for d in data}, cost
    except Exception:
        return {}, cost   # okunamadi: cagiran parti ikiye bolup tekrar dener


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", required=True, help="Ingilizce global.ini yolu")
    ap.add_argument("--game", default=DEFAULT_GAME, help="StarCitizen\\LIVE klasoru")
    ap.add_argument("--cache", default="sc_turkce_cache.json")
    ap.add_argument("--limit", type=int, default=0, help="sadece ilk N benzersiz satir (deneme)")
    ap.add_argument("--min-len", type=int, default=0, help="bu uzunluktan kisa satirlari cevirme")
    ap.add_argument("--max-usd", type=float, default=5.0, help="harcama sigortasi")
    ap.add_argument("--batch", type=int, default=40)
    ap.add_argument("--effort", default="low", choices=["low", "medium", "high"], help="dusuk = ucuz ve hizli")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--ascii", action="store_true", help="Turkce harfleri sadelestir (yazi tipi sorunu olursa)")
    ap.add_argument("--latin1", action="store_true", help="oneri: sadece s,g,i harflerini sadelestir (c,o,u kalir)")
    ap.add_argument("--offline", action="store_true", help="API kullanma, sadece onbellekten dosyayi yeniden yaz")
    ap.add_argument("--estimate", action="store_true", help="sadece maliyet tahmini yap")
    a = ap.parse_args()

    rows = parse(a.source)
    cache = json.load(open(a.cache, encoding="utf-8")) if os.path.exists(a.cache) else {}
    uniq = {}
    for k, v in rows:
        if k is not None and translatable(v, a.min_len) and h(v) not in cache:
            uniq.setdefault(h(v), v)
    todo = list(uniq.items())
    if a.limit:
        todo = todo[: a.limit]

    if a.offline:
        todo = []
    chars = sum(len(v) for _, v in todo)
    est = chars / 3.5 * PRICE_IN + chars / 3.0 * 1.3 * PRICE_OUT   # kaba tahmin
    print(f"Cevrilecek benzersiz satir: {len(todo)} | onbellekte: {len(cache)} | tahmini maliyet: ~${est:.2f}")
    if a.estimate:
        return

    client = None
    if todo:
        from anthropic import Anthropic
        client = Anthropic(max_retries=5)
    lock = threading.Lock()
    state = {"spent": 0.0, "failed": 0, "done": 0}

    def run(batch):
        if state["spent"] >= a.max_usd:
            return
        items, meta = [], {}
        for n, (hh, v) in enumerate(batch, 1):
            m, holders = mask(v)
            items.append((n, m))
            meta[n] = (hh, holders)
        try:
            res, cost = call(client, items, a.effort)
        except Exception as e:
            with lock:
                state["failed"] += len(batch)
            print("Parti hatasi:", e)
            return
        with lock:
            state["spent"] += cost
        if not res and len(batch) > 1:      # cevap okunamadi -> ikiye bol, tekrar dene
            mid = len(batch) // 2
            run(batch[:mid])
            run(batch[mid:])
            return
        with lock:
            for n, (hh, holders) in meta.items():
                t = unmask(res.get(n, ""), holders) if res.get(n) else None
                if t:
                    cache[hh] = t
                    state["done"] += 1
                else:
                    state["failed"] += 1
            json.dump(cache, open(a.cache, "w", encoding="utf-8"), ensure_ascii=False)
            proj = state["spent"] / max(state["done"], 1) * len(todo)
            print(f"  {state['done']}/{len(todo)} satir | harcanan ~${state['spent']:.2f} | tahmini toplam ~${proj:.2f} | basarisiz {state['failed']}")

    def work(batch):
        run(batch)

    batches = [todo[i:i + a.batch] for i in range(0, len(todo), a.batch)]
    with ThreadPoolExecutor(a.workers) as ex:
        for f in as_completed([ex.submit(work, b) for b in batches]):
            f.result()
    if state["spent"] >= a.max_usd:
        print(f"Harcama siniri (${a.max_usd}) doldu. Ayni komutu tekrar calistirirsan kaldigi yerden devam eder.")

    out_dir = os.path.join(a.game, "data", "Localization", "english")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "global.ini")
    if os.path.exists(out) and not os.path.exists(out + ".en.bak"):
        shutil.copy2(out, out + ".en.bak")
    lines = []
    for k, v in rows:
        if k is None:
            lines.append(v)
        else:
            t = cache.get(h(v), v)
            t = t.translate(ASCII_MAP) if a.ascii else (t.translate(LATIN1_MAP) if a.latin1 else t)
            lines.append(f"{k}={t}")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")

    cfg = os.path.join(a.game, "user.cfg")
    text = open(cfg, encoding="utf-8").read() if os.path.exists(cfg) else ""
    if "g_language" not in text:
        with open(cfg, "a", encoding="utf-8") as f:
            f.write(("\n" if text and not text.endswith("\n") else "") + "g_language = english\n")
    print("Bitti ->", out)


if __name__ == "__main__":
    sys.exit(main())
