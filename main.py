import telebot
import sqlite3
import os
from datetime import datetime
from telebot import types

# --- AYARLAR ---
TOKEN = '8234388592:AAEaplt1NV1t4MRvAXaunI5-RS5HXNmXA00'
BOT_USER = 'CanFakenobot' 
ADMIN_ID = 8434939976
LOG_KANAL_ID = '@Canguvenc'      
GUVENCE_KANAL = 'https://t.me/Canguvenc'
ADMIN_CONTACT = 'Banaporshesurer'

# --- ZORUNLU KANALLAR ---
ZORUNLU_KANALLAR = ['@sanalnumberki', '@blackfaceno', '@mustiar93', '@Canguvenc'] 

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
    bugun = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect('bot_verisi.db') as conn:
        res = conn.execute("SELECT ad, puan FROM users WHERE user_id = ?", (user_id,)).fetchone()
        ref_count = conn.execute("SELECT COUNT(*) FROM users WHERE ref_eden = ?", (user_id,)).fetchone()[0]
        bugun_gelen = conn.execute("SELECT COUNT(*) FROM users WHERE kayit_tarihi LIKE ?", (bugun + '%',)).fetchone()[0]
        return res, ref_count, bugun_gelen

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

# --- ÇOKLU KANAL KONTROLÜ ---
def abone_mi(user_id):
    for kanal in ZORUNLU_KANALLAR:
        try:
            status = bot.get_chat_member(kanal, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except:
            return False
    return True

# --- ANA MENÜ ---
def ana_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🛒 Market", "🏆 Liderlik")
    markup.add("👤 Hesabım", "📦 Siparişlerim")
    if int(uid) == ADMIN_ID:
        markup.add("⚙️ Admin Paneli")
    return markup

# --- KOMUTLAR ---
@bot.message_handler(commands=['start'])
def start(message):
    uid, ad = message.from_user.id, (message.from_user.first_name or "Kullanıcı")
    if ban_kontrol(uid) == 1: return bot.send_message(uid, "🚫 **Sistemden yasaklandınız.**")
    
    if not abone_mi(uid):
        m = types.InlineKeyboardMarkup()
        for i, kanal in enumerate(ZORUNLU_KANALLAR, 1):
            # @ işaretini kaldırarak sadece ismi göster
            kanal_ismi = kanal[1:]
            m.add(types.InlineKeyboardButton(f"📢 {kanal_ismi} - Katıl", url=f"https://t.me/{kanal_ismi}"))
        m.add(types.InlineKeyboardButton("✅ Katıldım / Kontrol Et", callback_data="check_sub"))
        return bot.send_message(uid, f"⚠️ Merhaba {ad}, devam etmek için tüm kanallara katılmalısın!", reply_markup=m)
        
    args = message.text.split()
    kullanici_ekle(uid, ad, args[1] if len(args) > 1 else None)
    bot.send_message(uid, f"👋 Hoş geldin {ad}!", reply_markup=ana_menu(uid))

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if abone_mi(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.from_user.id, "✅ Tüm kanallara katılım onaylandı!", reply_markup=ana_menu(call.from_user.id))
    else:
        bot.answer_callback_query(call.id, "❌ Hala katılmadığın kanallar var!", show_alert=True)

# --- HESABIM ---
@bot.message_handler(func=lambda m: m.text == "👤 Hesabım")
def profil(message):
    uid = message.from_user.id
    res, ref_sayisi, bugun_uye = profil_verisi_getir(uid)
    ref_linki = f"https://t.me/{BOT_USER}?start={uid}"
    
    metin = (f"👤 **HESAP BİLGİLERİN**\n\n"
             f"🆔 **ID:** `{uid}`\n"
             f"💰 **Mevcut Jeton:** `{res[1]}`\n"
             f"👥 **Referans Sayın:** `{ref_sayisi}`\n"
             f"🆕 **Bugün Gelen Toplam Üye:** `{bugun_uye}`\n\n"
             f"🔗 **Referans Linkin:**\n`{ref_linki}`")
    bot.send_message(message.chat.id, metin, parse_mode="Markdown")

# --- MARKET ---
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
        bot.send_message(ADMIN_ID, f"🛍️ **YENİ SATIŞ!**\n👤 {uname} ({uid})\n📦 {urun_adi}", 
                         reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚚 Teslim Et", callback_data=f"onay_{uid}_{s_id}")))
    else: bot.answer_callback_query(call.id, "❌ Yetersiz Jeton!", show_alert=True)

# --- TESLİMAT SİSTEMİ ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("onay_"))
def teslim_onay(call):
    _, musteri_id, sid = call.data.split("_")
    kanal_metni = f"🛡️ **SİPARİŞ TESLİM EDİLDİ**\n🎫 No: #{sid}\n👤 Alıcı ID: `{musteri_id}`\n✅ Başarıyla Teslim Edildi.\n🌟 @{BOT_USER}"
    
    with sqlite3.connect('bot_verisi.db') as conn:
        foto = conn.execute("SELECT deger FROM ayarlar WHERE anahtar = ?", ("teslimat_foto",)).fetchone()
        conn.execute("UPDATE satislar SET durum = 'Teslim Edildi' WHERE id = ?", (sid,))
    
    try:
        if foto: bot.send_photo(LOG_KANAL_ID, foto[0], caption=kanal_metni)
        else: bot.send_message(LOG_KANAL_ID, kanal_metni)
        bot.send_message(musteri_id, "🚚 **Siparişiniz teslim edildi! Güvence kanalından kontrol edebilirsin.**")
        bot.edit_message_text(f"✅ Sipariş #{sid} teslim edildi ve kanala atıldı.", ADMIN_ID, call.message.message_id)
    except: pass

@bot.message_handler(content_types=['photo'])
def admin_foto(message):
    if message.from_user.id == ADMIN_ID:
        file_id = message.photo[-1].file_id
        with sqlite3.connect('bot_verisi.db') as conn:
            conn.execute("INSERT OR REPLACE INTO ayarlar (anahtar, deger) VALUES (?, ?)", ("teslimat_foto", file_id))
        bot.reply_to(message, "✅ **Teslimat fotoğrafı güncellendi.**")

# --- ADMİN PANELİ ---
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin Paneli" and m.from_user.id == ADMIN_ID)
def admin_menu_show(message):
    m = types.InlineKeyboardMarkup(row_width=2).add(
        types.InlineKeyboardButton("📊 İstatistik", callback_data="adm_stats"),
        types.InlineKeyboardButton("📣 Duyuru Yap", callback_data="adm_msg"),
        types.InlineKeyboardButton("💎 Jeton Ver", callback_data="adm_coin"),
        types.InlineKeyboardButton("🚫 Kullanıcı Ban", callback_data="adm_ban"))
    bot.send_message(message.chat.id, "🛠 **Admin Paneli**", reply_markup=m)

@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_"))
def adm_calls(call):
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
    try:
        t_id, mik = message.text.split()
        with sqlite3.connect('bot_verisi.db') as conn: conn.execute("UPDATE users SET puan = puan + ? WHERE user_id = ?", (float(mik), int(t_id)))
        bot.send_message(message.chat.id, "✅ İşlem başarılı.")
    except: bot.send_message(message.chat.id, "❌ Hata (ID Miktar).")

def duyuru_gonder(message):
    with sqlite3.connect('bot_verisi.db') as conn: users = conn.execute("SELECT user_id FROM users").fetchall()
    for u in users:
        try: bot.send_message(u[0], f"📣 **DUYURU**\n\n{message.text}")
        except: pass
    bot.send_message(message.chat.id, "✅ Duyuru iletildi.")

# --- DİĞER FONKSİYONLAR ---
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
    bot.infinity_polling()
  
