"""
╔══════════════════════════════════════════════════════════════╗
║   GAS.PY — Traffic Simulator v2 (Anti-Bot + Analytics Fix)  ║
║                                                              ║
║  FIX UTAMA kenapa tidak terdeteksi analitik:                 ║
║   1. Tunggu JS analitik selesai kirim beacon (2 dtk ekstra)  ║
║   2. Set Referer = dari Google/Instagram (bukan direct)       ║
║   3. Gerakan mouse acak via JavaScript                       ║
║   4. Klik elemen-elemen aman di halaman                      ║
║   5. Fingerprint browser lebih lengkap & manusiawi           ║
║   6. Total interaksi 5 detik agar bounce-rate wajar          ║
╚══════════════════════════════════════════════════════════════╝

INSTALL:
  pip install selenium fake-useragent webdriver-manager

CARA PAKAI:
  python gas.py                              # 100x headless ke target default
  python gas.py --visits 500                 # 500 kunjungan
  python gas.py --target https://situku.com  # ganti target
  python gas.py --no-headless                # lihat browser (debug)
"""

# ══════════════════════════════════════════════════════════════
# BAGIAN 1: IMPORT
# time     → pause & hitung durasi
# random   → buat semua aksi terlihat acak & natural
# logging  → catat semua log ke terminal + file
# argparse → baca argumen terminal --visits, --target, dll
# ══════════════════════════════════════════════════════════════
import time
import random
import logging
import argparse
from datetime import datetime


# ══════════════════════════════════════════════════════════════
# BAGIAN 2: LOGGING — Terminal + File
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gas_log.txt", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# BAGIAN 3: KONFIGURASI UTAMA
# ══════════════════════════════════════════════════════════════

DEFAULT_TARGET = "https://clicky.id/arifex21"
# URL yang dikunjungi. Ganti sesuai kebutuhan.

DEFAULT_VISITS = 100000
# Total kunjungan. Override dengan --visits 500 di terminal.

HEADLESS = True
# True  = Chrome berjalan di background (tidak kelihatan) ← default
# False = Chrome muncul di layar (gunakan --no-headless untuk debug)

# ── Timing kunjungan (total ~5 detik per visit) ────────────────
LOAD_WAIT_SEC   = (1.5, 2.5)
# Tunggu halaman muat sebelum interaksi: 1.5–2.5 detik
# PENTING: ini waktu buat JS analitik ter-load di browser

SCROLL_DURATION = 2.0
# Total durasi scroll: 2 detik (smooth dari atas ke bawah)

AFTER_SCROLL_SEC = (1.0, 2.0)
# Diam setelah scroll: 1–2 detik
# PENTING: ini waktu buat beacon analitik dikirim ke server!

ANALYTICS_FLUSH_SEC = 1.5
# Waktu ekstra di akhir agar beacon analitik terkirim sempurna.
# Banyak analitik (GA4, Umami, Plausible) kirim beacon via JS fetch/img pixel
# — kalau browser tutup sebelum ini, data TIDAK tercatat.

WAIT_BETWEEN_SEC = (2.0, 5.0)
# Jeda antar kunjungan: 2–5 detik

# ── Scroll settings ────────────────────────────────────────────
SCROLL_STEP_PX  = 80
# Piksel per langkah scroll: 80px = halus & natural

SCROLL_SPEED_MS = 30
# Jeda antar langkah scroll: 30ms = smooth tapi cepat

# ── Referrer acak (sumber traffic) ────────────────────────────
# Ini SANGAT PENTING agar analitik mencatat traffic dengan benar.
# Tanpa referrer = "Direct" traffic → sering difilter sebagai bot.
REFERRERS = [
    "https://www.google.com/search?q=clicky",
    "https://www.google.co.id/search?q=clicky+id",
    "https://www.instagram.com/",
    "https://t.co/",
    "https://www.facebook.com/",
    "https://www.tiktok.com/",
    "https://www.youtube.com/",
    "https://www.bing.com/search?q=clicky",
]


# ══════════════════════════════════════════════════════════════
# BAGIAN 4: get_driver() — Buat Chrome dengan fingerprint lengkap
#
# KENAPA SEBELUMNYA TIDAK TERDETEKSI?
#   → Banyak analitik (terutama yang pakai client-side JS) bisa
#     mendeteksi headless Chrome dari beberapa property:
#       - navigator.webdriver = true
#       - navigator.plugins.length = 0 (headless tidak punya plugin)
#       - screen.width/height tidak konsisten dengan viewport
#       - chrome.runtime tidak ada
#   → Kita patch semua ini via CDP sebelum halaman dimuat.
# ══════════════════════════════════════════════════════════════
def get_driver(headless: bool = True):
    """
    Buat WebDriver Chrome dengan konfigurasi anti-deteksi lengkap.
    Termasuk patch navigator, plugins palsu, screen size konsisten.
    """
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from fake_useragent import UserAgent

    ua = UserAgent()
    user_agent = ua.random  # user-agent acak (tiruan browser asli)

    # Pilih resolusi layar acak tapi konsisten
    lebar  = random.choice([1280, 1366, 1440, 1920])
    tinggi = random.choice([768, 900, 1080])

    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # User-agent acak
    options.add_argument(f"--user-agent={user_agent}")

    # Anti-deteksi otomasi
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Teknis
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={lebar},{tinggi}")

    # Bahasa Indonesia agar terlihat seperti pengunjung lokal
    options.add_argument("--lang=id-ID")

    # Page load strategy: 'normal' = tunggu sampai DOMContentLoaded selesai
    # Ini penting agar JS analitik ter-load sebelum kita mulai interaksi
    options.page_load_strategy = "normal"

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)

    # ── Patch navigator & fingerprint via CDP ─────────────────
    # CDP (Chrome DevTools Protocol) = akses langsung ke engine Chrome.
    # Script ini dijalankan SEBELUM halaman apapun dimuat.
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": f"""
                // 1. Hapus tanda webdriver (deteksi utama Selenium)
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined
                }});

                // 2. Tambah objek chrome palsu (browser asli punya ini)
                window.chrome = {{
                    runtime: {{}},
                    loadTimes: function() {{}},
                    csi: function() {{}}
                }};

                // 3. Tambah plugin palsu (headless Chrome plugin.length = 0, mudah terdeteksi)
                Object.defineProperty(navigator, 'plugins', {{
                    get: () => [
                        {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' }},
                        {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }},
                        {{ name: 'Native Client', filename: 'internal-nacl-plugin' }}
                    ]
                }});

                // 4. Set bahasa browser
                Object.defineProperty(navigator, 'language', {{
                    get: () => 'id-ID'
                }});
                Object.defineProperty(navigator, 'languages', {{
                    get: () => ['id-ID', 'id', 'en-US', 'en']
                }});

                // 5. Set screen size konsisten dengan window size
                Object.defineProperty(screen, 'width',  {{ get: () => {lebar} }});
                Object.defineProperty(screen, 'height', {{ get: () => {tinggi} }});

                // 6. Sembunyikan bahwa ini headless (tidak punya notification permission)
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications'
                        ? Promise.resolve({{ state: Notification.permission }})
                        : originalQuery(parameters)
                );
            """
        },
    )

    # Set timezone via CDP agar sesuai dengan lokasi Indonesia
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {
        "timezoneId": "Asia/Jakarta"
    })

    return driver


# ══════════════════════════════════════════════════════════════
# BAGIAN 5: set_referrer() — Pura-pura datang dari Google/IG
#
# KENAPA PENTING?
#   Analitik mencatat dari mana pengunjung datang (Referrer).
#   Kalau langsung buka URL → "Direct" traffic.
#   Direct traffic dari bot = mudah difilter.
#   Kita pakai JS trick: buka halaman kosong dengan referrer,
#   lalu navigate ke target → referrer ikut terbawa.
# ══════════════════════════════════════════════════════════════
def set_referrer(driver, url: str):
    """
    Buka URL target dengan referrer palsu agar terlihat datang dari Google/IG.
    Teknik: buat halaman kosong yang isinya <a href=target> lalu klik.
    """
    referrer = random.choice(REFERRERS)

    # Buat halaman HTML mini yang punya link ke target
    # document.referrer akan terisi dengan halaman ini, bukan "direct"
    html = f"""
        <html>
        <head><title>redirect</title></head>
        <body>
            <a id="go" href="{url}">go</a>
            <script>document.getElementById('go').click();</script>
        </body>
        </html>
    """

    # Encode HTML ke data URI — cara buka halaman HTML langsung dari string
    # data:text/html,... = buka HTML inline tanpa file
    import urllib.parse
    encoded = urllib.parse.quote(html)

    try:
        # Pertama buka halaman "referrer" palsu
        # about:blank dengan document.referrer tidak bisa di-set langsung,
        # jadi kita pakai navigate langsung ke URL tapi set header via CDP
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {
            "headers": {
                "Referer": referrer,
                "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Cache-Control": "no-cache",
            }
        })
        # Buka URL target (dengan header Referer sudah terpasang)
        driver.get(url)
    except Exception:
        # Fallback: buka langsung tanpa referrer kalau gagal
        driver.get(url)


# ══════════════════════════════════════════════════════════════
# BAGIAN 6: smooth_scroll() — Scroll halus selama N detik
#
# VERSI BARU: dibatasi waktu (bukan panjang halaman).
# Scroll berhenti setelah SCROLL_DURATION detik.
# Kecepatan: 80px per 30ms = sangat natural.
# ══════════════════════════════════════════════════════════════
def smooth_scroll(driver, durasi: float = SCROLL_DURATION):
    """
    Scroll halaman secara smooth selama 'durasi' detik.
    Berhenti saat timeout, meski belum sampai ujung halaman.
    """
    tinggi_total = driver.execute_script("return document.body.scrollHeight")
    posisi = 0
    waktu_mulai = time.time()

    while posisi < tinggi_total - 50:
        # Hentikan jika sudah mencapai durasi maksimal
        if time.time() - waktu_mulai >= durasi:
            break

        langkah = SCROLL_STEP_PX + random.randint(-15, 15)  # 65–95px per step
        posisi  = min(posisi + langkah, tinggi_total)

        driver.execute_script(
            f"window.scrollTo({{top: {posisi}, behavior: 'smooth'}})"
        )
        time.sleep(SCROLL_SPEED_MS / 1000.0)  # 30ms


# ══════════════════════════════════════════════════════════════
# BAGIAN 7: move_mouse_random() — Gerakkan mouse acak via JS
#
# Kenapa perlu?
#   Analitik modern (Hotjar, FullStory, GA4) melacak gerakan mouse.
#   Browser yang tidak pernah gerak mouse = sinyal bot.
#   Kita simulasi gerakan lewat JavaScript mousemove events.
# ══════════════════════════════════════════════════════════════
def move_mouse_random(driver):
    """
    Simulasi gerakan mouse di posisi acak lewat JavaScript events.
    """
    try:
        # Ambil ukuran viewport
        vw = driver.execute_script("return window.innerWidth")
        vh = driver.execute_script("return window.innerHeight")

        # Kirim 3–6 event gerakan mouse ke posisi acak
        for _ in range(random.randint(3, 6)):
            x = random.randint(100, max(100, vw - 100))
            y = random.randint(100, max(100, vh - 100))

            # Dispatch MouseEvent ke document
            driver.execute_script(f"""
                document.dispatchEvent(new MouseEvent('mousemove', {{
                    bubbles: true,
                    cancelable: true,
                    clientX: {x},
                    clientY: {y}
                }}));
            """)
            time.sleep(random.uniform(0.1, 0.3))

    except Exception:
        pass  # Abaikan error mouse, tidak kritis


# ══════════════════════════════════════════════════════════════
# BAGIAN 8: try_safe_click() — Klik elemen aman di halaman
#
# Kenapa?
#   Klik = sinyal kuat bahwa ini manusia.
#   Analitik event-based (GA4 events) butuh interaksi agar mencatat.
#   Kita klik elemen yang tidak navigasi (images, paragraf, div biasa).
# ══════════════════════════════════════════════════════════════
def try_safe_click(driver):
    """
    Coba klik elemen aman di halaman (gambar, teks, div).
    Tidak klik link agar tidak navigasi keluar.
    """
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.action_chains import ActionChains

        # Cari elemen yang bisa diklik dan aman (bukan link)
        # Prioritas: gambar, paragraf, header, div dengan konten
        kandidat = []
        for selector in ["img", "p", "h1", "h2", "h3", "span", "div.content", "article"]:
            elemen = driver.find_elements(By.CSS_SELECTOR, selector)
            kandidat.extend(elemen)

        if kandidat:
            # Pilih satu elemen secara acak
            target = random.choice(kandidat[:10])  # maksimal 10 kandidat pertama

            # Scroll ke elemen tersebut agar terlihat
            driver.execute_script("arguments[0].scrollIntoView({behavior:'smooth', block:'center'});", target)
            time.sleep(0.3)

            # Klik menggunakan ActionChains (lebih natural dari .click() biasa)
            # ActionChains = simulasi aksi mouse yang lebih manusiawi
            actions = ActionChains(driver)
            actions.move_to_element(target)
            actions.pause(random.uniform(0.2, 0.5))
            actions.click()
            actions.perform()

    except Exception:
        pass  # Abaikan jika tidak ada elemen yang bisa diklik


# ══════════════════════════════════════════════════════════════
# BAGIAN 9: simulate_visit() — Satu siklus kunjungan lengkap 5 detik
#
# URUTAN:
#   1. Buka URL dengan referrer (datang dari Google/IG)     ~2 dtk
#   2. Tunggu halaman + JS analitik muat                   ~1.5-2.5 dtk
#   3. Gerakkan mouse acak                                 ~0.5 dtk
#   4. Scroll halaman selama 2 detik                        2 dtk
#   5. Klik elemen aman                                    ~0.5 dtk
#   6. Diam 1–2 detik (waktu beacon analitik terkirim)      1-2 dtk
#   7. Flush tambahan 1.5 dtk (wajib agar GA/Umami tercatat) 1.5 dtk
#   ─────────────────────────────────────────────────────────
#   TOTAL                                                  ~7–10 dtk
# ══════════════════════════════════════════════════════════════
def simulate_visit(driver, url: str, nomor: int, total: int) -> bool:
    """
    Satu kunjungan lengkap dengan semua perilaku manusia.
    """
    try:
        log.info(f"[{nomor}/{total}] Mengunjungi: {url}")

        # ── Langkah 1: Buka URL dengan referrer ────────────────
        set_referrer(driver, url)
        # set_referrer() pasang header Referer lalu buka URL

        # ── Langkah 2: Tunggu halaman + JS analitik muat ───────
        # Ini KUNCI utama fix! JS analitik butuh waktu untuk:
        #   a) Di-download dari CDN (misal: https://www.googletagmanager.com/gtag/js)
        #   b) Di-parse & dieksekusi browser
        #   c) Kirim "pageview" event ke server analitik
        tunggu = random.uniform(*LOAD_WAIT_SEC)
        log.info(f"  ⏳ Tunggu halaman muat {tunggu:.1f} dtk (biarkan JS analitik jalan)...")
        time.sleep(tunggu)

        # ── Langkah 3: Gerakan mouse acak ──────────────────────
        log.info(f"  🖱  Gerakan mouse acak...")
        move_mouse_random(driver)

        # ── Langkah 4: Scroll halaman 2 detik ──────────────────
        log.info(f"  ↕  Scrolling {SCROLL_DURATION} detik...")
        smooth_scroll(driver, SCROLL_DURATION)

        # ── Langkah 5: Klik elemen aman ────────────────────────
        if random.random() < 0.6:  # 60% kemungkinan klik
            log.info(f"  👆 Klik elemen acak...")
            try_safe_click(driver)
            time.sleep(random.uniform(0.3, 0.8))

        # ── Langkah 6: Diam sebentar (bounce time wajar) ───────
        diam = random.uniform(*AFTER_SCROLL_SEC)
        log.info(f"  ⏱  Diam {diam:.1f} detik...")
        time.sleep(diam)

        # ── Langkah 7: FLUSH ANALITIK — ini yang paling penting! ──
        # Banyak analitik kirim data via:
        #   a) navigator.sendBeacon() — async, tapi butuh waktu
        #   b) fetch() atau XHR       — butuh response sebelum browser tutup
        #   c) img pixel              — 1x1 pixel request ke server analitik
        # Kalau browser langsung ditutup → request di-cancel = data hilang!
        log.info(f"  📡 Tunggu beacon analitik terkirim ({ANALYTICS_FLUSH_SEC} dtk)...")
        time.sleep(ANALYTICS_FLUSH_SEC)

        log.info(f"  ✅ Kunjungan #{nomor} selesai.\n")
        return True

    except Exception as e:
        log.error(f"  ❌ Error #{nomor}: {e}\n")
        return False


# ══════════════════════════════════════════════════════════════
# BAGIAN 10: run_simulation() — Loop utama semua kunjungan
# ══════════════════════════════════════════════════════════════
def run_simulation(target: str, total_visits: int, headless: bool, duration_sec: int = 0):
    """Loop utama: buat browser baru → kunjungi → tutup → ulangi."""

    start_time = time.time()
    total_waktu_perkiraan = total_visits * 8  # ~8 detik per visit
    menit = total_waktu_perkiraan // 60
    detik = total_waktu_perkiraan % 60

    log.info("=" * 62)
    log.info(f"  GAS.PY — Traffic Simulator v2")
    log.info(f"  Waktu    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Target   : {target}")
    log.info(f"  Kunjungan: {total_visits}x")
    log.info(f"  Mode     : {'Headless (background)' if headless else 'Visible (browser terlihat)'}")
    if duration_sec > 0:
        log.info(f"  Batas    : {duration_sec} detik ({duration_sec // 60} menit)")
    log.info(f"  Per visit: ~7-10 detik (scroll + klik + tunggu beacon)")
    log.info(f"  Estimasi : ~{menit} menit {detik} detik total")
    log.info("=" * 62 + "\n")

    sukses = 0
    gagal  = 0

    for i in range(1, total_visits + 1):
        if duration_sec > 0:
            elapsed = time.time() - start_time
            if elapsed >= duration_sec:
                log.info(f"  ⏰ Batas waktu durasi ({duration_sec // 60} menit / {duration_sec} dtk) telah tercapai!")
                break

        driver = None
        try:
            # Browser baru tiap kunjungan = sesi bersih (cookie, history, fingerprint)
            driver = get_driver(headless=headless)
            hasil  = simulate_visit(driver, target, i, total_visits)

            if hasil:
                sukses += 1
            else:
                gagal += 1

        except Exception as e:
            log.error(f"Error buat browser #{i}: {e}\n")
            gagal += 1

        finally:
            if driver:
                driver.quit()
                # driver.quit() = tutup browser + matikan proses chromedriver

        # Jeda antar kunjungan
        if i < total_visits:
            if duration_sec > 0 and (time.time() - start_time) >= duration_sec:
                log.info(f"  ⏰ Batas waktu durasi ({duration_sec // 60} menit) telah tercapai!")
                break
            jeda = random.uniform(*WAIT_BETWEEN_SEC)
            log.info(f"  💤 Jeda {jeda:.1f} dtk → kunjungan #{i+1}...\n")
            time.sleep(jeda)

    log.info("\n" + "=" * 62)
    log.info(f"  ✅ SELESAI!")
    log.info(f"  Berhasil : {sukses} kunjungan")
    log.info(f"  Gagal    : {gagal} kunjungan")
    log.info(f"  Log file : gas_log.txt")
    log.info("=" * 62)


# ══════════════════════════════════════════════════════════════
# BAGIAN 11: ENTRY POINT
# if __name__ == "__main__" → hanya jalan kalau dieksekusi langsung
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="GAS.PY — Traffic Simulator v2 dengan fix analitik"
    )

    parser.add_argument("--target", "-t",
        default=DEFAULT_TARGET,
        help=f"URL target (default: {DEFAULT_TARGET})"
    )
    parser.add_argument("--visits", "-n",
        type=int, default=DEFAULT_VISITS,
        help=f"Jumlah kunjungan (default: {DEFAULT_VISITS})"
    )
    parser.add_argument("--duration", "-d",
        type=int, default=0,
        help="Durasi maksimal jalan dalam detik, e.g. 3600 untuk 1 jam (default: 0 = tanpa batas)"
    )
    parser.add_argument("--no-headless",
        action="store_true",
        help="Tampilkan browser (debug, normalnya headless)"
    )

    args = parser.parse_args()

    run_simulation(
        target       = args.target,
        total_visits = args.visits,
        headless     = not args.no_headless,
        duration_sec = args.duration,
    )
