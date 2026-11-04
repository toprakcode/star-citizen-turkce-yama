#!/usr/bin/env python3
"""Yeni Star Citizen yamasi cikinca tek komutla guncelle.

1) Topluluk deposundan en son Ingilizce global.ini'yi indirir
2) Onbellekte olmayan (yeni/degisen) satirlari Claude ile cevirir
3) Sonucu oyun klasorune yazar ve 'yayin' klasorune kopyalar (GitHub Releases icin)

Kullanim:  python guncelle.py              (ya da guncelle.bat'a cift tikla)
           python guncelle.py --sadece-kontrol   (indirir, kac satir degistigini soyler, ceviri yapmaz)
           python guncelle.py --zorla      (kaynak ayni olsa da calistir)
           python guncelle.py --evet       (onay sormadan devam et)
"""
import datetime, io, json, os, shutil, subprocess, sys, urllib.request, zipfile

import sc_turkce as sc

API = "https://api.github.com/repos/Dymerz/StarCitizen-Localization/releases/latest"
ZIP = "https://github.com/Dymerz/StarCitizen-Localization/releases/latest/download/Localization.zip"
AYAR = "ayar.json"
SATIR_MALIYET = 0.00006   # kaba tahmin: ~USD / satir (low effort ile ilk tam cevirideki gerceklesen oran)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sc-turkce-yama"})
    return urllib.request.urlopen(req, timeout=180).read()


def tag_bul():
    try:
        return json.loads(get(API))["tag_name"]
    except Exception:
        # API sinirina takilirsa: "latest" sayfasinin yonlendirmesinden etiketi oku
        req = urllib.request.Request("https://github.com/Dymerz/StarCitizen-Localization/releases/latest",
                                     headers={"User-Agent": "sc-turkce-yama"})
        return urllib.request.urlopen(req, timeout=60).geturl().rstrip("/").split("/")[-1]


def main():
    args = sys.argv[1:]
    ayar = json.load(open(AYAR, encoding="utf-8")) if os.path.exists(AYAR) else {}
    if os.path.exists("key.txt") and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = open("key.txt", encoding="utf-8").read().strip()

    tag = tag_bul()
    print("Topluluk kaynaginin son surumu:", tag)
    if ayar.get("kaynak_tag") == tag and "--zorla" not in args and "--sadece-kontrol" not in args:
        print("Kaynak son isledigin surumle ayni, yeni bir sey yok. (Yine de calistirmak icin: --zorla)")
        return

    z = zipfile.ZipFile(io.BytesIO(get(ZIP)))
    ad = next(n for n in z.namelist() if n.lower().endswith("english/global.ini"))
    open("global.new.ini", "wb").write(z.read(ad))

    rows = sc.parse("global.new.ini")
    cache = json.load(open("sc_turkce_cache.json", encoding="utf-8")) if os.path.exists("sc_turkce_cache.json") else {}
    todo = {sc.h(v) for k, v in rows if k is not None and sc.translatable(v, 0) and sc.h(v) not in cache}
    n = len(todo)
    print(f"Cevrilmesi gereken yeni/degisen satir: {n}  (tahmini maliyet ~${n * SATIR_MALIYET:.2f}, kaba tahmin)")
    if "--sadece-kontrol" in args:
        print("Sadece kontrol: ceviri yapilmadi.")
        return

    if n > 0 and "--evet" not in args:
        if input("Devam edilsin mi? (e/h): ").strip().lower() not in ("e", "evet", "y"):
            print("Iptal edildi.")
            return

    game = ayar.get("game") or input(r"Star Citizen LIVE klasoru (ornek S:\StarCitizen\LIVE): ").strip().strip('"')
    if os.path.exists("global.ini"):
        shutil.copy2("global.ini", "global.prev.ini")
    shutil.copy2("global.new.ini", "global.ini")

    cmd = [sys.executable, "sc_turkce.py", "--source", "global.ini", "--game", game,
           "--latin1", "--short-ascii", "40", "--max-usd", "3"]
    if n == 0:
        cmd.append("--offline")
    if subprocess.call(cmd) != 0:
        print("Ceviri adiminda hata oldu, durduruldu.")
        return

    ayar.update({"game": game, "kaynak_tag": tag})
    json.dump(ayar, open(AYAR, "w", encoding="utf-8"))
    os.makedirs("yayin", exist_ok=True)
    cikti = os.path.join(game, "data", "Localization", "english", "global.ini")
    shutil.copy2(cikti, os.path.join("yayin", "global.ini"))
    surum = tag.replace("live-", "")
    open(os.path.join("yayin", "SURUM.txt"), "w", encoding="utf-8").write(
        f"Onerilen etiket: {surum}-tr1\nKaynak: {tag}\nTarih: {datetime.date.today()}\nYeni/degisen satir: {n}\n")
    print("\nHazir! Yeni dosya: yayin\\global.ini")
    print(f"GitHub'da yeni release olustur: etiket {surum}-tr1, dosyalar: yayin\\global.ini ve kur.bat")


if __name__ == "__main__":
    main()
