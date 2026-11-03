# Star Citizen Türkçe Yama (resmi olmayan)

Star Citizen'ın arayüz, görev, sözleşme ve hikaye metinlerini Türkçeye çeviren, **yapay zeka (Claude) ile hazırlanmış** resmi olmayan bir yama. Oyunun `global.ini` yerelleştirme dosyasını kullanır.

> Resmi olmayan bir hayran projesidir. Cloud Imperium Games ile bağlantısı yoktur. Oyun metinleri ve marka CIG'e aittir.

## Hızlı kurulum (çeviri hazır, ücretsiz)
1. **Releases** sayfasından en son sürümdeki `global.ini` dosyasını indir. Sürüm numarası oyunun sürümüyle (örn. 4.10.2) eşleşmeli.
2. `global.ini` ile `kur.bat` dosyasını **aynı klasöre** koy. (`kur.bat` bu depoda.)
3. `kur.bat` dosyasına çift tıkla, Star Citizen'ın **LIVE klasörünü** yaz (örn. `S:\StarCitizen\LIVE`, içinde `Data.p4k` olan klasör).
4. Oyunu tamamen kapatıp yeniden aç. Oyundaki dil ayarı **English** kalsın.

Geri almak için `kaldir.bat`'ı çalıştır (kurulumda orijinalin yedeği alınır).

## Önemli notlar
- **Oyun güncellenince** yama eskiyebilir. Çevrilmemiş ya da değişmiş satırlar İngilizce görünebilir. Yeni sürüm için Releases sayfasını takip et.
- Çeviri **makine çevirisidir**, hatalar olabilir. Hata görürsen Issue aç (ekran görüntüsü ve oyun içi metinle).
- `ş, ğ, ı, İ, Ş, Ğ` harfleri oyunun yazı tipinde sorunlu olduğu için **s, g, i, I, S, G** olarak yazılır. `ç, ö, ü` korunur.
- Resmi olarak desteklenen diller listesinde Türkçe yok. Bu yama, `english` klasörüne konan çevrilmiş dosya ve `user.cfg` içindeki `g_language = english` ayarıyla çalışır. Bu yöntem CIG tarafından "deneysel" olarak tanımlanıyor, sorun çıkabilir.

## Kendi çevirini üretmek (isteyenler için)
`sc_turkce.py`, İngilizce `global.ini` dosyasını Claude API ile çevirir. Kendi API anahtarın ve kredin gerekir.
```
pip install -r requirements.txt
python sc_turkce.py --source global.ini --game "S:\StarCitizen\LIVE" --latin1 --max-usd 5
```
- Çeviriler önbelleğe alınır. Yeni oyun sürümünde sadece değişen satırlar çevrilir.
- `--estimate` maliyet tahmini verir, `--limit 150` küçük deneme yapar, `--offline` API kullanmadan dosyayı yeniden yazar.
- **API anahtarını asla bu depoya yükleme.** `.gitignore` bunu engellemeye çalışır ama kontrol sende.

## Katkı
Hatalı çeviri, terim önerisi ve iyileştirmeler için Issue ya da Pull Request açabilirsin.

## Lisans
Kod ve belgeler MIT lisanslıdır (bkz. `LICENSE`). Oyun metinleri CIG'e aittir.
