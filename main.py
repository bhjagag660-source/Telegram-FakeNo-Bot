import telebot
import sqlite3
import os
from datetime import datetime
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

# --- ZORUNLU KANALLAR (YENİ KANAL EKLENDİ) ---
ZORUNLU_KANALLAR = [
    '@sanalnumberki', 
    '@blackfaceno', 
    '@mustiar93', 
    '@Canguvenc',
    'https://t.me/+hz_lk7bOxOM5Mzdk' # Yeni eklenen özel davet bağlantısı
] 

bot = telebot.TeleBot(TOKEN)

# --- VERİTABANI İŞLEMLERİ ---
def veri_hazirla():
    with sqlite3.connect('bot_verisi.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, ad TEXT, puan REAL DEFAULT 0, 
             ref_eden INTEGER, ban INTEGER DEFAULT 0, kayit_tarihi TEXT)''')
        cursor.execute('CREATE TABLE IF NOT EXISTS ayarlar (anahtar TEXT PRIMARY KEY, deger TEXT)')
        cursor.execute('''CREATE TABLE IF NOT EXISTS satislar 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, urun TEXT, fiyat REAL, tarih TEXT, durum TEXT DEFAULT 'Bekliyor')''')
        conn.commit()

def ban_kontrol(uid):
    with sqlite3.connect('bot_verisi.db') as conn:
        res = conn.execute("SELECT ban FROM users WHERE user_id = ?", (uid,)).fetchone()
        return res[0] if res else 0

def profil_verisi_getir(user_id):
    with sqlite3.connect('bot_verisi.db') as conn:
        res = conn.execute("SELECT ad, puan FROM users WHERE user_id = ?", (user_id,)).fetchone()
        ref_count = conn.execute("SELECT COUNT(*) FROM users WHERE ref_eden = ?", (user_id,)).fetchone()[0]
        toplam_uye = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        return res, ref_count, toplam_uye

def kullanici_ekle(user_id, ad, ref_id=None):
    simdi = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect('bot_verisi.db') as conn:
        cursor = conn.cursor()
        if cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
            cursor.execute("INSERT INTO users (user_id, ad, ref_eden, ban, kayit_tarihi) VALUES (?, ?, ?, 0, ?)", (user_id, ad, ref_id, simdi))
            if ref_id and str(ref_id).isdigit() and int(ref_id) != user_id:
                cursor.execute("UPDATE users SET puan = puan + 1 WHERE user_id = ?", (ref_id,))
                try: bot.send_message(ref_id, "🎉 Referansınla biri katıldı! +1 Jeton kazandın.")
                except: pass
            conn.commit()

def abone_mi(user_id):
    for kanal in ZORUNLU_KANALLAR:
        try:
            # Eğer kanal @ ile başlamıyorsa özel linktir, kontrolü @ olanlarla sınırlı tutabiliriz 
            # veya botun bu özel kanalda admin olması şartıyla kontrol edebiliriz.
            if kanal.startswith('@'):
                status = bot.get_chat_member(kanal, user_id).status
                if status not in ['member', 'administrator', 'creator']:
                    return False
        except:
            # Bot kanalda admin değilse veya kanal bulunamazsa hata payı bırakmamak için devam et
            continue
    return True

def ana_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Market", "🏆 Liderlik")
    markup.add("👤 Hesabım", "📦 Siparişlerim")
    if int(uid) in ADMIN_LIST:
        markup.add("⚙️ Admin Paneli")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid, ad = message.from_user.id, (message.from_user.first_name or "Kullanıcı")
    if ban_kontrol(uid) == 1: return bot.send_message(uid, "🚫 **Sistemden yasaklandınız.**")
    
    if not abone_mi(uid):
        m = types.InlineKeyboardMarkup()
        for i, kanal in enumerate(ZORUNLU_KANALLAR, 1):
            if kanal.startswith('@'):
                url = f"https://t.me/{kanal[1:]}"
                txt = f"📢 Kanal {i}"
            else:
                url = kanal
                txt = f"📢 Özel Kanal {i}"
            m.add(types.InlineKeyboardButton(txt, url=url))
        m.add(types.InlineKeyboardButton("✅ Katıldım / Kontrol Et", callback_data="check_sub"))
        return bot.send_message(uid, f"⚠️ Merhaba {ad}, devam etmek için tüm kanallara katılmalısın!", reply_markup=m)
        
    args = message.text.split()
    kullanici_ekle(uid, ad, args[1] if len(args) > 1 else None)
    bot.send_message(uid, f"👋 Hoş geldin {ad}!", reply_markup=ana_menu(uid))

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if abone_mi(call.from_user.id):
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.from_user.id, "✅ Tüm kanallara katılım onaylandı!", reply_markup=ana_menu(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ Hala katılmadığın kanallar var!", show_alert=True)

# --- DİĞER FONKSİYONLAR (DEĞİŞMEDİ) ---
@bot.message_handler(func=lambda m: m.text == "👤 Hesabım")
def profil(message):
    uid = message.from_user.id
    res, ref_sayisi, toplam_uye = profil_verisi_getir(uid)
    ref_linki = f"https://t.me/{BOT_USER}?start={uid}"
    metin = (f"👤 **HESAP BİLGİLERİN**\n\n🆔 **ID:** `{uid}`\n💰 **Mevcut Jeton:** `{res[1]}`\n👥 **Referans Sayın:** `{ref_sayisi}`\n🆕 **Toplam Üye:** `{toplam_uye}`\n\n🔗 **Referans Linkin:**\n`{ref_linki}`")
    bot.send_message(message.chat.id, metin, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛒 Market")
def market(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔴 Tg Fake No — 15 Jeton", callback_data="buy_tg"),
        types.InlineKeyboardButton("🟢 Wp Fake No — 10 Jeton", callback_data="buy_wp"),
        types.InlineKeyboardButton("🟡 BiP Fake No — 5 Jeton", callback_data="buy_bip"),
        types.InlineKeyboardButton("🛡️ Güvence Kanalı", url=GUVENCE_KANAL)
    )
    bot.send_message(message.chat.id, "🛒 **Market Menüsü**", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def satin_al(call):
    uid = call.from_user.id
    uname = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name
    res, _, _ = profil_verisi_getir(uid)
    urunler = {"buy_tg": ["Tg Fake No", 15], "buy_wp": ["Wp Fake No", 10], "buy_bip": ["BiP Fake No", 5]}
    urun_adi, fiyat = urunler[call.data]
    if res[1] >= fiyat:
        with sqlite3.connect('bot_verisi.db') as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET puan = puan - ? WHERE user_id = ?", (fiyat, uid))
            cursor.execute("INSERT INTO satislar (user_id, urun, fiyat, tarih) VALUES (?, ?, ?, ?)", (uid, urun_adi, fiyat, datetime.now().strftime("%Y-%m-%d %H:%M")))
            s_id = cursor.lastrowid
            conn.commit()
        bot.send_message(uid, f"✅ **Sipariş No: #{s_id}**\nTeslimat için @{ADMIN_CONTACT} yaz.")
        for admin in ADMIN_LIST:
            try: bot.send_message(admin, f"🛍️ **YENİ SATIŞ!**\n👤 {uname} ({uid})\n📦 {urun_adi}", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚚 Teslim Et", callback_data=f"onay_{uid}_{s_id}")))
            except: pass
    else: bot.answer_callback_query(call.id, "❌ Yetersiz Jeton!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("onay_"))
def teslim_onay(call):
    if call.from_user.id not in ADMIN_LIST: return
    _, musteri_id, sid = call.data.split("_")
    kanal_metni = f"🛡️ **SİPARİŞ TESLİM EDİLDİ**\n🎫 No: #{sid}\n👤 Alıcı ID: `{musteri_id}`\n✅ Başarıyla Teslim Edildi.\n🌟 @{BOT_USER}"
    with sqlite3.connect('bot_verisi.db') as conn:
        foto = conn.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", ("teslimat_foto",)).fetchone()
        conn.execute("UPDATE satislar SET durum = 'Teslim Edildi' WHERE id = ?", (sid,))
    try:
        if foto: bot.send_photo(LOG_KANAL_ID, foto[0], caption=kanal_metni)
        else: bot.send_message(LOG_KANAL_ID, kanal_metni)
        bot.send_message(musteri_id, "🚚 **Siparişiniz teslim edildi! Güvence kanalından kontrol edebilirsin.**")
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
        with sqlite3.connect('bot_verisi.db') as conn:
            toplam = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        bot.answer_callback_query(call.id, f"Toplam Üye: {toplam}", show_alert=True)
    elif call.data == "adm_coin":
        m = bot.send_message(call.message.chat.id, "ID MİKTAR yaz:")
        bot.register_next_step_handler(m, jeton_islem)
    elif call.data == "adm_msg":
        m = bot.send_message(call.message.chat.id, "Duyuru mesajını yazın:")
        bot.register_next_step_handler(m, duyuru_gonder)

def jeton_islem(message):
    if message.from_user.id not in ADMIN_LIST: return
    try:
        t_id, mik = message.text.split()
        with sqlite3.connect('bot_verisi.db') as conn: conn.execute("UPDATE users SET puan = puan + ? WHERE user_id = ?", (float(mik), int(t_id)))
        bot.send_message(message.chat.id, "✅ Başarılı.")
    except: bot.send_message(message.chat.id, "❌ Hata.")

def duyuru_gonder(message):
    if message.from_user.id not in ADMIN_LIST: return
    with sqlite3.connect('bot_verisi.db') as conn: users = conn.execute("SELECT user_id FROM users").fetchall()
    for u in users:
        try: bot.send_message(u[0], f"📣 **DUYURU**\n\n{message.text}")
        except: pass
    bot.send_message(message.chat.id, "✅ Tamamlandı.")

@bot.message_handler(func=lambda m: m.text == "🏆 Liderlik")
def lead(m):
    with sqlite3.connect('bot_verisi.db') as conn: data = conn.execute("SELECT ad, puan FROM users WHERE ban = 0 ORDER BY puan DESC LIMIT 10").fetchall()
    txt = "🏆 **EN ÇOK REFERANS YAPANLAR**\n\n" + "\n".join([f"{i+1}. {u[0]} - `{u[1]}` Jeton" for i, u in enumerate(data)])
    bot.send_message(m.chat.id, txt, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📦 Siparişlerim")
def sip(m):
    with sqlite3.connect('bot_verisi.db') as conn: data = conn.execute("SELECT urun, durum FROM satislar WHERE user_id = ? ORDER BY id DESC LIMIT 5", (m.from_user.id,)).fetchall()
    bot.send_message(m.chat.id, "📦 Sipariş Geçmişin:\n" + "\n".join([f"- {s[0]}: {s[1]}" for s in data]) if data else "Henüz siparişin yok.")

if __name__ == "__main__":
    veri_hazirla()
    keep_alive()
    bot.infinity_polling()
    
