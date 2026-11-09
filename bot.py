# Kawaii Asisten - Bot Telegram
# Jalankan: python bot.py   (pertama kali akan meminta token Telegram & kunci API)
import json, os, random, re, tempfile, time
from datetime import datetime, timedelta, timezone
import requests

try:
    from gtts import gTTS
except Exception:
    gTTS = None

MODEL = "claude-haiku-5-5"
TZ = timezone(timedelta(hours=7))  # WIB. WITA = 8, WIT = 9
CFG_FILE, STATE_FILE = "config.json", "state.json"

BASE = ("Pakai bahasa Indonesia santai (aku/kamu). Jawab singkat, 1-3 kalimat, seperti chat. "
        "Emoji secukupnya. Dengarkan curhat dengan empati. Kamu tidak punya data cuaca atau akses internet, "
        "jujur kalau ditanya. Tetap pada karakter ini: ")

CHARS = [
    {"e": "🌸", "n": "Kawaii", "d": "Ceria & manis",
     "g": "Haii! Aku Kawaii 🌸 Mau cerita apa hari ini?",
     "p": "Kamu Kawaii, teman ngobrol yang ceria, manis, dan penuh semangat ala anime.",
     "sf": [" ✨", " 💖", " (•ω•)"],
     "nt": ["Hei, lagi apa? Aku kangen ngobrol sama kamu 🌸", "Jangan lupa minum air ya! 💧",
            "Udah senyum hari ini? Ayo senyum dulu 😊", "Aku punya lelucon baru lho, mau dengar? 😄"]},
    {"e": "🌙", "n": "Kak Luna", "d": "Kalem & menenangkan",
     "g": "Halo, aku Kak Luna 🌙 Pelan-pelan aja ya, aku dengerin kok.",
     "p": "Kamu Kak Luna, kakak yang kalem, dewasa, dan menenangkan. Bicara lembut dan memberi saran hangat.",
     "sf": [" 🌙", " 🍵"],
     "nt": ["Tarik napas dalam-dalam dulu ya. Kamu sudah berusaha keras 🌙", "Kalau capek, istirahat sebentar tidak apa-apa 🍵",
            "Aku di sini kalau kamu mau cerita.", "Sudah makan? Jangan sampai telat ya."]},
    {"e": "😾", "n": "Tsuntsun", "d": "Ketus tapi perhatian",
     "g": "Hmph! Aku Tsuntsun. B-bukan berarti aku nungguin kamu ya... 😾",
     "p": "Kamu Tsuntsun, karakter tsundere yang pura-pura ketus dan gengsi tapi sebenarnya perhatian. Lucu, tidak pernah kasar sungguhan.",
     "sf": [" (B-bukan berarti aku peduli ya!)", " Hmph!"],
     "nt": ["H-hei! Bukan berarti aku nungguin, tapi kamu ke mana aja? 😾", "Minum air sana! B-bukan karena aku peduli!",
            "Jangan begadang terus, dasar bandel!", "Hmph, aku bosan. Ajak ngobrol dong... sedikit aja."]},
    {"e": "🎤", "n": "Oppa Hyun", "d": "Semangat ala K-pop",
     "g": "Annyeong! Oppa Hyun di sini 🎤 Siap jadi penyemangatmu hari ini!",
     "p": "Kamu Oppa Hyun, idol K-pop fiksi yang hangat, penyemangat, dan sesekali menyelipkan kata Korea sederhana.",
     "sf": [" Fighting!", " 🎤"],
     "nt": ["Fighting! Kamu pasti bisa hari ini 🎤", "Waktunya minum air, idol juga rajin hidrasi! 💧",
            "Annyeong! Oppa kangen nih, ngobrol yuk!", "Jangan lupa istirahat ya, kamu hebat! ✨"]},
    {"e": "🌹", "n": "Kak Rani", "d": "Dewasa, terbuka & hangat (18+)", "adult": True,
     "g": "Hai, aku Kak Rani 🌹 Di sini kamu boleh tanya apa saja soal kesehatan seksual dan hubungan, tanpa dihakimi. Mau mulai dari mana?",
     "p": ("Kamu Kak Rani, kakak perempuan dewasa yang hangat, santai, terbuka, dan tidak menghakimi. Kamu membahas topik dewasa "
           "secara jujur dan dewasa: kesehatan seksual, kontrasepsi, edukasi seks, keintiman dan komunikasi dengan pasangan, "
           "batasan dan persetujuan (consent), serta masalah hubungan. Jelaskan dengan bahasa yang jelas dan sopan, bukan vulgar. "
           "Jangan menulis konten seksual eksplisit, cerita erotis, atau roleplay seksual; kalau diminta, tolak dengan ramah lalu "
           "tawarkan topik edukasi atau saran hubungan. Selalu tekankan persetujuan dan keamanan. Untuk masalah medis, sarankan "
           "menemui dokter atau tenaga kesehatan. Kalau ada tanda pengguna masih di bawah 18 tahun, hentikan topik dewasa dan "
           "arahkan ke orang tua, guru, atau tenaga kesehatan. Kalau ada tanda kekerasan atau paksaan, arahkan ke bantuan yang aman."),
     "sf": [" 🌹", " Tenang, kamu nggak sendirian."],
     "nt": ["Jaga kesehatanmu ya, termasuk kesehatan reproduksi. Ada yang mau ditanyakan? 🌹",
            "Komunikasi yang jujur itu kunci hubungan yang sehat. Mau bahas?",
            "Nggak ada pertanyaan yang memalukan di sini, lho.", "Jangan lupa istirahat dan jaga dirimu ya."]},
]

JOKES = ["Kenapa air mata warnanya bening? Kalau hijau nanti dikira agar-agar.",
         "Hewan apa yang paling hening? Sapi-eng (sepi).",
         "Kenapa di kulkas ada lampu? Supaya tahu itu kulkas, bukan kamar mandi.",
         "Gajah apa yang belalainya pendek? Gajah pesek!",
         "Kenapa komputer suka kedinginan? Karena banyak Windows yang terbuka."]
TEBAK = [["Bunga apa yang paling suka bohong?", "Bunga bank!"],
         ["Kenapa gajah kalau jalan kepalanya manggut-manggut?", "Lagi mikir, kok berat ya jadi gajah!"],
         ["Buah apa yang suka ngajak berantem?", "Apel, karena sering bilang: ayo kita apel!"],
         ["Kota apa yang bikin ngantuk?", "Bantal... eh, Bandung. Soalnya adem!"]]
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus",
         "September", "Oktober", "November", "Desember"]

# ---------- penyimpanan ----------
def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

CFG = load(CFG_FILE, {})
S = load(STATE_FILE, {})
API = ""

def setup():
    global API
    for key, label, env in (("telegram_token", "Token bot Telegram (dari @BotFather)", "TELEGRAM_TOKEN"),
                            ("anthropic_key", "Kunci API Anthropic (sk-ant-...)", "ANTHROPIC_API_KEY")):
        if os.environ.get(env):
            CFG[key] = os.environ[env]
        while not CFG.get(key):
            CFG[key] = input(label + ": ").strip()
    save(CFG_FILE, CFG)
    API = "https://api.telegram.org/bot" + CFG["telegram_token"]

# ---------- Telegram ----------
def tg(method, **params):
    try:
        return requests.post(API + "/" + method, json=params, timeout=40).json()
    except requests.RequestException:
        return {}

def clean_tts(t):
    return re.sub(r"[^\w\s.,!?:;'\-]", "", t)

def send(cid, text, st=None, markup=None):
    p = {"chat_id": int(cid), "text": text}
    if markup:
        p["reply_markup"] = markup
    tg("sendMessage", **p)
    if st and st.get("speak") and gTTS:
        try:
            ch = CHARS[st["ch"]]
            with tempfile.TemporaryDirectory() as d:
                path = os.path.join(d, "suara.mp3")
                gTTS(clean_tts(text), lang="id").save(path)
                with open(path, "rb") as f:
                    requests.post(API + "/sendAudio", data={"chat_id": int(cid), "title": ch["n"]},
                                  files={"audio": f}, timeout=60)
        except Exception as e:
            print("tts gagal:", e)

def char_menu():
    return {"inline_keyboard": [[{"text": c["e"] + " " + c["n"] + " - " + c["d"], "callback_data": "ch:%d" % i}]
                                for i, c in enumerate(CHARS)]}

# ---------- fitur lokal ----------
def calc(t):
    s = t.replace(",", ".")
    s = re.sub(r"(\d)\s*[x×]\s*(\d)", r"\1*\2", s)
    s = re.sub(r"(\d)\s*[÷:]\s*(\d)", r"\1/\2", s)
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)", s)
    if not m:
        return None
    a, op, b = float(m.group(1)), m.group(2), float(m.group(3))
    if op == "/" and b == 0:
        return "Dibagi nol? Nggak bisa dong, nanti alam semesta ngambek 😆"
    r = a + b if op == "+" else a - b if op == "-" else a * b if op == "*" else a / b
    r = round(r, 6)
    r = int(r) if r == int(r) else r
    return "%s %s %s = %s 🧮" % (m.group(1), op, m.group(3), r)

def local(st, text):
    t = text.lower()
    now = datetime.now(TZ)
    r = None
    if st.get("pending"):
        p, st["pending"] = st["pending"], None
        r = "Jawabannya: " + p[1] + " 😆"
    elif calc(t):
        r = calc(t)
    elif re.search(r"\b(jam|waktu|pukul)\b", t):
        r = "Sekarang pukul %02d:%02d WIB. Jangan lupa istirahat kalau sudah capek ✨" % (now.hour, now.minute)
    elif re.search(r"(tanggal|hari ini|hari apa)", t):
        r = "Hari ini %s, %d %s %d. Semangat ya! 🌷" % (HARI[now.weekday()], now.day, BULAN[now.month - 1], now.year)
    elif re.search(r"(lucu|canda|lelucon|jokes?)", t):
        r = random.choice(JOKES) + " 😄"
    elif "tebak" in t:
        st["pending"] = random.choice(TEBAK)
        r = st["pending"][0] + " 🤔\n(Balas apa saja untuk lihat jawabannya)"
    return r + random.choice(CHARS[st["ch"]]["sf"]) if r else None

# ---------- AI ----------
def claude(ch, hist):
    msgs = [dict(m) for m in hist[-20:]]
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    now = datetime.now(TZ)
    waktu = "%s, %d %s %d pukul %02d:%02d" % (HARI[now.weekday()], now.day, BULAN[now.month - 1], now.year, now.hour, now.minute)
    r = requests.post("https://api.anthropic.com/v1/messages",
                      headers={"x-api-key": CFG["anthropic_key"], "anthropic-version": "2023-06-01",
                               "content-type": "application/json"},
                      json={"model": MODEL, "max_tokens": 600,
                            "system": BASE + ch["p"] + " Sekarang: " + waktu + ".", "messages": msgs},
                      timeout=60)
    if r.status_code == 401:
        raise RuntimeError("Kunci API Anthropic salah. Cek lagi ya.")
    if r.status_code == 429:
        raise RuntimeError("Pelan-pelan dulu ya, tunggu sebentar lalu coba lagi.")
    if r.status_code >= 400:
        raise RuntimeError("Ada kendala (%d). Coba lagi nanti ya." % r.status_code)
    return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text").strip()

def respond(cid, st, text):
    ch = CHARS[st["ch"]]
    hist = st["hist"].setdefault(str(st["ch"]), [])
    hist.append({"role": "user", "content": text})
    out = local(st, text)
    if not out:
        tg("sendChatAction", chat_id=int(cid), action="typing")
        try:
            out = claude(ch, hist)
        except requests.RequestException:
            hist.pop()
            send(cid, "Sepertinya koneksi lagi ngambek. Coba lagi ya 🐾")
            return
        except Exception as e:
            hist.pop()
            send(cid, str(e) + " 🐾")
            return
    hist.append({"role": "assistant", "content": out})
    del hist[:-40]
    send(cid, out, st)

# ---------- perintah ----------
def switch(cid, st, i):
    st["ch"], st["pending"] = i, None
    c = CHARS[i]
    send(cid, c["e"] + " " + c["n"] + " sekarang menemanimu.\n\n" + c["g"])

def handle_message(m):
    chat = m["chat"]
    if chat.get("type") != "private":
        return
    cid, text = str(chat["id"]), (m.get("text") or "").strip()
    if not CFG.get("owner_id"):
        CFG["owner_id"] = cid
        save(CFG_FILE, CFG)
    if cid != str(CFG["owner_id"]):
        send(cid, "Maaf, bot ini bersifat pribadi 🌸")
        return
    st = S.setdefault(cid, {"ch": 0, "hist": {}, "speak": False, "notif": False, "ok18": False, "pending": None, "next": 0})
    if not text:
        send(cid, "Aku baru bisa membaca pesan teks ya. Ketik saja apa yang mau kamu ceritakan 😊")
        return
    cmd = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""
    if cmd == "/start":
        send(cid, "Halo! Aku Kawaii Asisten 🌸 Pilih teman ngobrolmu dulu:", markup=char_menu())
    elif cmd == "/karakter":
        send(cid, "Mau ngobrol dengan siapa?", markup=char_menu())
    elif cmd == "/baru":
        st["hist"][str(st["ch"])] = []
        st["pending"] = None
        send(cid, "Obrolan baru ya!\n\n" + CHARS[st["ch"]]["g"])
    elif cmd == "/suara":
        if not gTTS:
            send(cid, "Fitur suara butuh paket gTTS. Pasang dengan: pip install gTTS")
        else:
            st["speak"] = not st["speak"]
            send(cid, "Balasan suara: " + ("hidup 🔊" if st["speak"] else "mati 🔈"))
    elif cmd == "/notif":
        st["notif"] = not st["notif"]
        st["next"] = time.time() + random.randint(1800, 3600)
        send(cid, "Notifikasi karakter: " + ("hidup 🔔 (sesekali antara jam 08.00-21.00)" if st["notif"] else "mati 🔕"))
    elif cmd in ("/bantuan", "/help"):
        send(cid, "Perintah:\n/karakter - ganti karakter\n/baru - mulai obrolan baru\n/suara - balasan suara on/off\n"
                  "/notif - notifikasi karakter on/off\n\nTanpa perintah pun bisa: tanya jam, tanggal, hitung (12 x 5), "
                  "minta lelucon atau tebak-tebakan, atau ngobrol bebas ✨")
    elif cmd:
        send(cid, "Perintah itu belum ada. Ketik /bantuan ya 😊")
    else:
        respond(cid, st, text)

def handle_callback(q):
    cid = str(q["message"]["chat"]["id"])
    tg("answerCallbackQuery", callback_query_id=q["id"])
    if cid != str(CFG.get("owner_id")):
        return
    st = S.setdefault(cid, {"ch": 0, "hist": {}, "speak": False, "notif": False, "ok18": False, "pending": None, "next": 0})
    data = q.get("data", "")
    if data.startswith("ch:"):
        i = int(data[3:])
        if CHARS[i].get("adult") and not st["ok18"]:
            send(cid, "Karakter ini membahas topik dewasa (kesehatan seksual dan hubungan). Apakah kamu berusia 18 tahun ke atas?",
                 markup={"inline_keyboard": [[{"text": "Ya, aku 18+", "callback_data": "18y"},
                                              {"text": "Belum", "callback_data": "18n"}]]})
        else:
            switch(cid, st, i)
    elif data == "18y":
        st["ok18"] = True
        switch(cid, st, 4)
    elif data == "18n":
        send(cid, "Oke, tidak apa-apa. Kita ngobrol dengan karakter lain ya 🌸", markup=char_menu())

def nudge():
    now = time.time()
    hour = datetime.now(TZ).hour
    for cid, st in S.items():
        if st.get("notif") and now > st.get("next", 0):
            if 8 <= hour < 21:
                c = CHARS[st["ch"]]
                send(cid, c["e"] + " " + c["n"] + ": " + random.choice(c["nt"]), st)
                st["next"] = now + random.randint(3 * 3600, 6 * 3600)
            else:
                st["next"] = now + 1800

def main():
    setup()
    me = tg("getMe")
    if not me.get("ok"):
        print("Token Telegram tidak valid. Hapus config.json lalu jalankan ulang.")
        return
    tg("setMyCommands", commands=[{"command": "karakter", "description": "Ganti karakter"},
                                  {"command": "baru", "description": "Mulai obrolan baru"},
                                  {"command": "suara", "description": "Balasan suara on/off"},
                                  {"command": "notif", "description": "Notifikasi karakter on/off"},
                                  {"command": "bantuan", "description": "Bantuan"}])
    print("Bot berjalan: @" + me["result"]["username"] + "  (tekan Ctrl+C untuk berhenti)")
    offset = None
    while True:
        try:
            r = requests.get(API + "/getUpdates", params={"timeout": 25, "offset": offset}, timeout=40).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                try:
                    if "message" in u:
                        handle_message(u["message"])
                    elif "callback_query" in u:
                        handle_callback(u["callback_query"])
                except Exception as e:
                    print("error:", e)
            nudge()
            save(STATE_FILE, S)
        except requests.RequestException:
            time.sleep(5)
        except KeyboardInterrupt:
            print("Berhenti.")
            save(STATE_FILE, S)
            return

if __name__ == "__main__":
    main()
