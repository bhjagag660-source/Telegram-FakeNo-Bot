import telebot
import sqlite3
import os
from datetime import datetime, timedelta
from telebot import types
from flask import Flask
from threading import Thread

# --- RENDER İÇİN WEB SUNUCUSU (KEEP ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Aktif!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- AYARLAR ---
TOKEN = '8234388592:AAEaplt1NV1t4MRvAXaunI5-RS5HXNmXA00'
BOT_USER = 'CanFakenobot' 
ADMIN_LIST = [8434939976, 7612747743] 
LOG_KANAL_ID = '@Canguvenc'      
GUVENCE_KANAL = 'https://t.me/Canguvenc'
ADMIN_CONTACT = 'Banaporshesurer'

# --- ZORUNLU KANALLAR ---
ZORUNLU_KANALLAR = [
    '@sanalnumberki', 
    '@mustiar93', 
    '@fransaarsiv', 
    '@Canguvenc',
    
] 

bot = telebot.TeleBot(TOKEN)

# --- YENİ: PROFİL YAZISINI GÜNCELLEME FONKSİYONU ---
def profil_yazisini_guncelle():
    """Botun isminin altındaki 'About' kısmını otomatik günceller."""
    ay_once = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            toplam = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            aylik = cursor.execute("SELECT COUNT(*) FROM users WHERE kayit_tarihi > ?", (ay_once,)).fetchone()[0]
        
        # Fotoğraftaki gibi görünmesi için metni ayarla
        yeni_hakkinda = f"{aylik:,} aylık kullanıcı | {toplam:,} toplam üye"
        bot.set_my_short_description(yeni_hakkinda)
    except:
        pass

# --- FONKSİYONLAR ---
def veri_hazirla():
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, ad TEXT, puan REAL DEFAULT 0, 
             ref_eden INTEGER, ban INTEGER DEFAULT 0, kayit_tarihi TEXT)''')
        cursor.execute('CREATE TABLE IF NOT EXISTS ayarlar (anahtar TEXT PRIMARY KEY, deger TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS satislar 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, urun TEXT, fiyat REAL, tarih TEXT, durum TEXT DEFAULT 'Bekliyor')''')
        conn.commit()

def abone_mi(user_id):
    if user_id in ADMIN_LIST: return True
    for kanal in ZORUNLU_KANALLAR:
        try:
            if kanal.startswith('@'):
                status = bot.get_chat_member(kanal, user_id).status
                if status not in ['member', 'administrator', 'creator']:
                    return False
        except: continue
    return True

def zorunlu_kanal_mesaji(message):
    ad = message.from_user.first_name or "Kullanıcı"
    m = types.InlineKeyboardMarkup()
    for i, kanal in enumerate(ZORUNLU_KANALLAR, 1):
        url = f"https://t.me/{kanal[1:]}" if kanal.startswith('@') else kanal
        m.add(types.InlineKeyboardButton(f"📢 Kanal {i}", url=url))
    m.add(types.InlineKeyboardButton("✅ Katıldım / Kontrol Et", callback_data="check_sub"))
    bot.send_message(message.chat.id, f"⚠️ Merhaba {ad}, devam etmek için tüm kanallara katılmalısın!", reply_markup=m)

def kullanici_ekle(user_id, ad, ref_id=None):
    simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        check = cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if check is None:
            if ref_id and str(ref_id) == str(user_id): ref_id = None
            cursor.execute("INSERT INTO users (user_id, ad, ref_eden, puan, ban, kayit_tarihi) VALUES (?, ?, ?, 0, 0, ?)", (user_id, ad, ref_id, simdi))
            if ref_id and str(ref_id).isdigit():
                cursor.execute("UPDATE users SET puan = puan + 1 WHERE user_id = ?", (ref_id,))
                try: bot.send_message(ref_id, "🎉 Referansınla biri katıldı! +1 Jeton kazandın.")
                except: pass
            conn.commit()
            profil_yazisini_guncelle() # Yeni kullanıcıda profili tazele

def profil_verisi_getir(user_id, ad):
    kullanici_ekle(user_id, ad)
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
        res = conn.execute("SELECT ad, puan FROM users WHERE user_id = ?", (user_id,)).fetchone()
        ref_count = conn.execute("SELECT COUNT(*) FROM users WHERE ref_eden = ?", (user_id,)).fetchone()[0]
        toplam_uye = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return res, ref_count, toplam_uye

def ana_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Market", "🏆 Liderlik")
    markup.add("👤 Hesabım", "📦 Siparişlerim")
    if int(uid) in ADMIN_LIST:
        markup.add("⚙️ Admin Paneli")
    return markup

# --- KOMUTLAR VE DİĞERLERİ (BAKİ KALDI) ---
@bot.message_handler(commands=['start'])
def start(message):
    uid, ad = message.from_user.id, (message.from_user.first_name or "Kullanıcı")
    args = message.text.split()
    ref_id = args[1] if len(args) > 1 else None
    kullanici_ekle(uid, ad, ref_id)
    if not abone_mi(uid): return zorunlu_kanal_mesaji(message)
    profil_yazisini_guncelle() # Her startta veriyi tazele
    bot.send_message(uid, f"👋 Hoş geldin {ad}!", reply_markup=ana_menu(uid))

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if abone_mi(call.from_user.id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.from_user.id, "✅ Başarıyla onaylandı!", reply_markup=ana_menu(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ Hala katılmadığın kanallar var!", show_alert=True)

@bot.message_handler(func=lambda m: m.text == "👤 Hesabım")
def profil(message):
    if not abone_mi(message.from_user.id): return zorunlu_kanal_mesaji(message)
    uid, ad = message.from_user.id, (message.from_user.first_name or "Kullanıcı")
    try:
        res, ref_sayisi, toplam_uye = profil_verisi_getir(uid, ad)
        ref_linki = f"https://t.me/{BOT_USER}?start={uid}"
        metin = (f"👤 **HESAP BİLGİLERİN**\n\n🆔 **ID:** `{uid}`\n💰 **Mevcut Jeton:** `{res[1]}`\n👥 **Referans Sayın:** `{ref_sayisi}`\n🆕 **Toplam Üye:** `{toplam_uye}`\n\n🔗 **Referans Linkin:**\n`{ref_linki}`")
        bot.send_message(message.chat.id, metin, parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Hata oluştu, tekrar /start yapın.")

@bot.message_handler(func=lambda m: m.text == "🏆 Liderlik")
def lead(message):
    if not abone_mi(message.from_user.id): return zorunlu_kanal_mesaji(message)
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
        data = conn.execute("SELECT ad, puan FROM users ORDER BY puan DESC LIMIT 10").fetchall()
    txt = "🏆 **EN ÇOK JETONU OLAN İLK 10**\n\n"
    for i, u in enumerate(data, 1):
        txt += f"{i}. {u[0]} — `{u[1]}` Jeton\n"
    bot.send_message(message.chat.id, txt, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛒 Market")
def market(message):
    if not abone_mi(message.from_user.id): return zorunlu_kanal_mesaji(message)
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 Tg Fake No — 15 Jeton", callback_data="buy_tg"),
        types.InlineKeyboardButton("🟢 Wp Fake No — 10 Jeton", callback_data="buy_wp"),
        types.InlineKeyboardButton("🟡 BiP Fake No — 5 Jeton", callback_data="buy_bip"),
        types.InlineKeyboardButton("🛡️ Güvence Kanalı", url=GUVENCE_KANAL)
    )
    bot.send_message(message.chat.id, "🛒 **Market Menüsü**", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📦 Siparişlerim")
def sip(message):
    if not abone_mi(message.from_user.id): return zorunlu_kanal_mesaji(message)
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn: 
        data = conn.execute("SELECT urun, durum FROM satislar WHERE user_id = ? ORDER BY id DESC LIMIT 5", (message.from_user.id,)).fetchall()
    bot.send_message(message.chat.id, "📦 Sipariş Geçmişin:\n" + "\n".join([f"- {s[0]}: {s[1]}" for s in data]) if data else "Henüz siparişin yok.")

# (Satın alma, Admin onay ve Jeton işlemleri yukarıdaki kodun aynısıdır...)
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def satin_al(call):
    if not abone_mi(call.from_user.id): return bot.answer_callback_query(call.id, "⚠️ Önce kanallara katılmalısın!", show_alert=True)
    uid, ad = call.from_user.id, (call.from_user.first_name or "Kullanıcı")
    res, _, _ = profil_verisi_getir(uid, ad)
    urunler = {"buy_tg": ["Tg Fake No", 15], "buy_wp": ["Wp Fake No", 10], "buy_bip": ["BiP Fake No", 5]}
    urun_adi, fiyat = urunler[call.data]
    if res[1] >= fiyat:
        with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET puan = puan - ? WHERE user_id = ?", (fiyat, uid))
            cursor.execute("INSERT INTO satislar (user_id, urun, fiyat, tarih) VALUES (?, ?, ?, ?)", (uid, urun_adi, fiyat, datetime.now().strftime("%Y-%m-%d %H:%M")))
            s_id = cursor.lastrowid
            conn.commit()
        bot.send_message(uid, f"✅ **Sipariş No: #{s_id}**\nTeslimat için @{ADMIN_CONTACT} yaz.")
        for admin in ADMIN_LIST:
            try: bot.send_message(admin, f"🛍️ **YENİ SATIŞ!**\n👤 {ad} ({uid})\n📦 {urun_adi}", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚚 Teslim Et", callback_data=f"onay_{uid}_{s_id}")))
            except: pass
    else: bot.answer_callback_query(call.id, "❌ Yetersiz Jeton!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("onay_"))
def teslim_onay(call):
    if call.from_user.id not in ADMIN_LIST: return
    _, musteri_id, sid = call.data.split("_")
    kanal_metni = f"🛡️ **SİPARİŞ TESLİM EDİLDİ**\n🎫 No: #{sid}\n👤 Alıcı ID: `{musteri_id}`\n✅ Başarıyla Teslim Edildi.\n🌟 @{BOT_USER}"
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
        conn.execute("UPDATE satislar SET durum = 'Teslim Edildi' WHERE id = ?", (sid,))
        conn.commit()
    try:
        bot.send_message(LOG_KANAL_ID, kanal_metni)
        bot.send_message(musteri_id, "🚚 **Siparişiniz teslim edildi!**")
        bot.edit_message_text(f"✅ Sipariş #{sid} teslim edildi.", call.from_user.id, call.message.message_id)
    except: pass

@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Paneli" and m.from_user.id in ADMIN_LIST)
def admin_menu_show(message):
    m = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("📊 İstatistik", callback_data="adm_stats"),
        types.InlineKeyboardButton("📣 Duyuru Yap", callback_data="adm_msg"),
        types.InlineKeyboardButton("💎 Jeton Ver", callback_data="adm_coin"))
    bot.send_message(message.chat.id, "🛠 **Admin Paneli**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def adm_calls(call):
    if call.from_user.id not in ADMIN_LIST: return
    if call.data == "adm_stats":
        with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn:
            toplam = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        bot.answer_callback_query(call.id, f"Toplam Üye: {toplam}", show_alert=True)
    elif call.data == "adm_coin":
        m = bot.send_message(call.message.chat.id, "Jeton verilecek kişinin `ID Miktar` bilgisini yaz:\n(Örn: 8434939976 50)")
        bot.register_next_step_handler(m, jeton_islem)
    elif call.data == "adm_msg":
        m = bot.send_message(call.message.chat.id, "Duyuru mesajını yazın:")
        bot.register_next_step_handler(m, duyuru_gonder)

def jeton_islem(message):
    if message.from_user.id not in ADMIN_LIST: return
    try:
        t_id, mik = message.text.split()
        with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn: 
            conn.execute("UPDATE users SET puan = puan + ? WHERE user_id = ?", (float(mik), int(t_id)))
            conn.commit()
        bot.send_message(message.chat.id, f"✅ `{t_id}` ID'li kullanıcıya `{mik}` jeton başarıyla eklendi.")
        try: bot.send_message(t_id, f"🎁 Admin hesabınıza `{mik}` jeton ekledi!")
        except: pass
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Hata oluştu! Lütfen `ID Miktar` şeklinde yazın.\nHata: {e}")

def duyuru_gonder(message):
    if message.from_user.id not in ADMIN_LIST: return
    with sqlite3.connect('bot_verisi.db', check_same_thread=False) as conn: 
        users = conn.execute("SELECT user_id FROM users").fetchall()
    count = 0
    for u in users:
        try: 
            bot.send_message(u[0], f"📣 **DUYURU**\n\n{message.text}")
            count += 1
        except: pass
    bot.send_message(message.chat.id, f"✅ Duyuru {count} kişiye gönderildi.")

# --- ANA ÇALIŞTIRICI ---
if __name__ == "__main__":
    veri_hazirla()
    keep_alive()
    profil_yazisini_guncelle() # Bot açılırken profil yazısını tazele
    # skip_pending=True Render çakışmalarını önler
    bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
