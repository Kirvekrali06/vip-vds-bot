import random
import time
import threading
from flask import Flask
import telebot
from telebot import types

# ---------------------------------------------------------
# SİZİN BİLGİLERİNİZ
# ---------------------------------------------------------
TOKEN = "8832669136:AAHNum5pWkXYJ6-5omtSNYcPrQMpG2r06sM"
ADMIN_ID = 6734911869
KURUCU_LINK = "https://t.me/kirvelerinkrali"

bot = telebot.TeleBot(TOKEN)

users = {}
banned_users = set()  # Banlanan Kullanıcı ID'leri
admin_states = {}

# ---------------------------------------------------------
# FLASK SUNUCUSU (7/24 Render & UptimeRobot İçin)
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Casino Bot 7/24 Aktif!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------
def register_user(user):
    if user.id not in users:
        users[user.id] = {
            "username": (user.username or "Yok").lower(),
            "first_name": user.first_name or "Kullanıcı",
            "balance": 1000
        }
    else:
        users[user.id]["username"] = (user.username or "Yok").lower()

def is_banned(user_id):
    """Kullanıcının banlı olup olmadığını kontrol eder."""
    return user_id in banned_users

def get_main_inline_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_kumar = types.InlineKeyboardButton("🎰 Kumar", callback_data="menu_kumar")
    btn_market = types.InlineKeyboardButton("🛒 Market", callback_data="menu_market")
    btn_yardim = types.InlineKeyboardButton("🆘 Yardım Paneli", callback_data="menu_yardim")
    btn_bakiye = types.InlineKeyboardButton("💰 Bakiyem", callback_data="menu_bakiye")
    
    if user_id == ADMIN_ID:
        btn_admin = types.InlineKeyboardButton("👑 Admin Paneli", callback_data="menu_admin")
        markup.add(btn_kumar, btn_market)
        markup.add(btn_admin, btn_yardim)
        markup.add(btn_bakiye)
    else:
        markup.add(btn_kumar, btn_market)
        markup.add(btn_yardim, btn_bakiye)
        
    return markup

def get_back_inline_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_ana"))
    return markup

# ---------------------------------------------------------
# START VE INLINE MENÜ DÖNGÜSÜ
# ---------------------------------------------------------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    if is_banned(message.from_user.id):
        bot.send_message(message.chat.id, "🚫 **Sistemden engellendiniz!** Botu kullanamazsınız.", parse_mode="Markdown")
        return

    register_user(message.from_user)
    admin_states.pop(message.from_user.id, None)
    
    start_text = (
        f"👋 Merhaba {message.from_user.first_name}!\n\n"
        "👑 Bu Bot 𝑫𝒆𝒏𝒊𝒛 𝑨𝒌𝒔𝒐𝒚 Tarafından Yapılmıştır.\n\n"
        "Aşağıdaki panelden istediğin işlemi seçebilirsin:"
    )
    
    bot.send_message(
        message.chat.id,
        start_text,
        reply_markup=get_main_inline_keyboard(message.from_user.id)
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id

    if is_banned(user_id):
        bot.answer_callback_query(call.id, "🚫 Engellendiğiniz için bu butonu kullanamazsınız!", show_alert=True)
        return

    register_user(call.from_user)
    
    if call.data == "menu_ana":
        admin_states.pop(user_id, None)
        bot.edit_message_text(
            "Ana menüye dönüldü. Seçiminizi yapın:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=get_main_inline_keyboard(user_id)
        )
        
    elif call.data == "menu_kumar":
        text = (
            "🎰 **KUMAR SALONU** 🎰\n\n"
            "Oyun oynamak için sohbet kutusuna komutları yazabilirsin:\n\n"
            "🎲 **Zar Oyunu:** `/zar <miktar>`\n"
            "🎰 **Slot Oyunu:** `/slot <miktar>`\n"
            "🪙 **Yazı Tura:** `/yazitura <yazi/tura> <miktar>`\n\n"
            "📌 *Örnek:* `/slot 100` veya `/yazitura yazi 50`"
        )
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=get_back_inline_keyboard()
        )

    elif call.data == "menu_market":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("1000 Bakiye - ⭐ 15 Yıldız", callback_data="buy_star"),
            types.InlineKeyboardButton("5000 Bakiye - ⭐ 50 Yıldız", callback_data="buy_star"),
            types.InlineKeyboardButton("500.000 Bakiye - ⭐ 100 Yıldız", callback_data="buy_star"),
            types.InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")
        )
        bot.edit_message_text(
            "🛒 **MARKET MENÜSÜ**\n\nSatın almak istediğin miktarı seç:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    elif call.data == "buy_star":
        bot.answer_callback_query(call.id, "⭐ Yıldız ile yükleme yapmak için Kurucu ile iletişime geçin.", show_alert=True)

    elif call.data == "menu_yardim":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👑 Kurucu", url=KURUCU_LINK),
            types.InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")
        )
        text = (
            "🆘 **YARDIM PANELSİ**\n\n"
            "Bir sorun veya yardım için aşağıdaki butondan kurucuya ulaşabilirsin."
        )
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="Markdown",
            reply_markup=markup
        )

    elif call.data == "menu_bakiye":
        bal = users[user_id]["balance"]
        bot.answer_callback_query(call.id, f"💵 Mevcut Bakiyeniz: {bal} Çip", show_alert=True)

    # ADMİN MENÜSÜ
    elif call.data == "menu_admin" and user_id == ADMIN_ID:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📢 Duyuru Gönder", callback_data="admin_duyuru"),
            types.InlineKeyboardButton("👥 Kullanıcılar", callback_data="admin_users"),
            types.InlineKeyboardButton("➕ Bakiye Ver", callback_data="admin_bakiye_ver"),
            types.InlineKeyboardButton("➖ Bakiye Al", callback_data="admin_bakiye_al"),
            types.InlineKeyboardButton("🚫 Kullanıcı Banla", callback_data="admin_ban"),
            types.InlineKeyboardButton("🟢 Ban Kaldır", callback_data="admin_unban"),
            types.InlineKeyboardButton("🔙 Geri", callback_data="menu_ana")
        )
        bot.edit_message_text(
            "👑 **ADMİN PANELİ**\nYapmak istediğin işlemi seç:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=markup
        )

    elif call.data == "admin_users" and user_id == ADMIN_ID:
        text = "👥 **Kayıtlı Kullanıcılar:**\n\n"
        for uid, data in users.items():
            durum = "🚫 Banlı" if uid in banned_users else "🟢 Aktif"
            text += f"👤 **İsim:** {data['first_name']}\n🆔 **ID:** `{uid}`\n🏷 **Kullanıcı Adı:** @{data['username']}\n💵 **Bakiye:** {data['balance']}\n📌 **Durum:** {durum}\n-------------------\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown", reply_markup=get_back_inline_keyboard())

    elif call.data == "admin_duyuru" and user_id == ADMIN_ID:
        admin_states[user_id] = "WAITING_ANNOUNCEMENT"
        bot.send_message(call.message.chat.id, "📢 Göndermek istediğin duyuru mesajını yaz:", reply_markup=get_back_inline_keyboard())

    elif call.data == "admin_bakiye_ver" and user_id == ADMIN_ID:
        admin_states[user_id] = "WAITING_ADD_BALANCE"
        bot.send_message(
            call.message.chat.id, 
            "➕ Eklemek istediğin miktarı ve Kullanıcı ID veya Kullanıcı Adını yazın:\n\nÖrnek: `5000 123456789` veya `5000 @ahmet`", 
            parse_mode="Markdown",
            reply_markup=get_back_inline_keyboard()
        )

    elif call.data == "admin_bakiye_al" and user_id == ADMIN_ID:
        admin_states[user_id] = "WAITING_REMOVE_BALANCE"
        bot.send_message(
            call.message.chat.id, 
            "➖ Kesmek istediğin miktarı ve Kullanıcı ID veya Kullanıcı Adını yazın:\n\nÖrnek: `2000 123456789` veya `2000 @ahmet`", 
            parse_mode="Markdown",
            reply_markup=get_back_inline_keyboard()
        )

    elif call.data == "admin_ban" and user_id == ADMIN_ID:
        admin_states[user_id] = "WAITING_BAN_INPUT"
        bot.send_message(
            call.message.chat.id, 
            "🚫 Banlamak istediğin Kullanıcı ID veya Kullanıcı Adını yazın:\n\nÖrnek: `123456789` veya `@ahmet`", 
            parse_mode="Markdown",
            reply_markup=get_back_inline_keyboard()
        )

    elif call.data == "admin_unban" and user_id == ADMIN_ID:
        admin_states[user_id] = "WAITING_UNBAN_INPUT"
        bot.send_message(
            call.message.chat.id, 
            "🟢 Banını kaldırmak istediğin Kullanıcı ID veya Kullanıcı Adını yazın:\n\nÖrnek: `123456789` veya `@ahmet`", 
            parse_mode="Markdown",
            reply_markup=get_back_inline_keyboard()
        )

# ---------------------------------------------------------
# OYUNLAR (EFEKTLİ/ANİMASYONLU)
# ---------------------------------------------------------
@bot.message_handler(commands=['slot'])
def play_slot(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Banlı olduğunuz için oyun oynayamazsınız.")
        return

    register_user(message.from_user)
    user = users[message.from_user.id]
    args = message.text.split()
    
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Geçersiz kullanım! Örnek: `/slot 100`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    if bet <= 0 or bet > user['balance']:
        bot.reply_to(message, "❌ Yetersiz bakiye!")
        return

    wait_msg = bot.reply_to(message, "🎰 **Slot çevriliyor...**", parse_mode="Markdown")
    time.sleep(1.5)

    emojis = ['🎰', '🍋', '🍒', '🔔', '💎', '7️⃣']
    s1, s2, s3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)
    
    res_text = f"🎰 **SLOT ÇEVRİLDİ!**\n\n[ {s1} | {s2} | {s3} ]\n\n"
    
    if s1 == s2 == s3:
        win = bet * 5
        user['balance'] += win
        res_text += f"🔥 **JACKPOT!** 3 sembol aynı!\n🎉 **+{win} Çip**"
    elif s1 == s2 or s2 == s3 or s1 == s3:
        win = bet * 2
        user['balance'] += win
        res_text += f"✨ 2 sembol eşleşti!\n🎉 **+{win} Çip**"
    else:
        user['balance'] -= bet
        res_text += f"❌ Kaybettin! **-{bet} Çip**"
        
    res_text += f"\n💵 **Yeni Bakiye:** {user['balance']}"
    bot.edit_message_text(res_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['zar'])
def play_dice(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Banlı olduğunuz için oyun oynayamazsınız.")
        return

    register_user(message.from_user)
    user = users[message.from_user.id]
    args = message.text.split()
    
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "❌ Geçersiz kullanım! Örnek: `/zar 100`", parse_mode="Markdown")
        return
        
    bet = int(args[1])
    if bet <= 0 or bet > user['balance']:
        bot.reply_to(message, "❌ Yetersiz bakiye!")
        return

    dice_msg = bot.send_dice(message.chat.id, emoji='🎲')
    score = dice_msg.dice.value
    time.sleep(2)

    if score >= 4:
        user['balance'] += bet
        bot.reply_to(message, f"🎲 Zar: **{score}** geldi!\n🎉 Kazandın! **+{bet} Çip**\n💵 Yeni Bakiye: {user['balance']}", parse_mode="Markdown")
    else:
        user['balance'] -= bet
        bot.reply_to(message, f"🎲 Zar: **{score}** geldi!\n❌ Kaybettin! **-{bet} Çip**\n💵 Yeni Bakiye: {user['balance']}", parse_mode="Markdown")

@bot.message_handler(commands=['yazitura'])
def play_coin(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Banlı olduğunuz için oyun oynayamazsınız.")
        return

    register_user(message.from_user)
    user = users[message.from_user.id]
    args = message.text.split()
    
    if len(args) < 3 or args[1].lower() not in ['yazi', 'tura'] or not args[2].isdigit():
        bot.reply_to(message, "❌ Geçersiz kullanım! Örnek: `/yazitura yazi 100`", parse_mode="Markdown")
        return
        
    choice = args[1].lower()
    bet = int(args[2])
    
    if bet <= 0 or bet > user['balance']:
        bot.reply_to(message, "❌ Yetersiz bakiye!")
        return

    wait_msg = bot.reply_to(message, "🪙 **Para havaya atılıyor...**", parse_mode="Markdown")
    time.sleep(1.5)

    result = random.choice(['yazi', 'tura'])
    if choice == result:
        user['balance'] += bet
        res_text = f"🪙 Sonuç: **{result.upper()}**!\n🎉 Doğru tahmin! **+{bet} Çip**\n💵 Yeni Bakiye: {user['balance']}"
    else:
        user['balance'] -= bet
        res_text = f"🪙 Sonuç: **{result.upper()}**!\n❌ Yanlış tahmin! **-{bet} Çip**\n💵 Yeni Bakiye: {user['balance']}"

    bot.edit_message_text(res_text, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode="Markdown")

# ---------------------------------------------------------
# ADMİN GİRDİLERİ VE İŞLEMLERİ
# ---------------------------------------------------------
@bot.message_handler(func=lambda msg: msg.from_user.id in admin_states)
def handle_admin_inputs(message):
    state = admin_states.get(message.from_user.id)
    
    # DUYURU
    if state == "WAITING_ANNOUNCEMENT":
        success, failed = 0, 0
        for uid in users.keys():
            try:
                bot.send_message(uid, f"📢 **DUYURU**\n\n{message.text}", parse_mode="Markdown")
                success += 1
            except:
                failed += 1
        bot.send_message(message.chat.id, f"✅ Duyuru Gönderildi!\n Başarılı: {success}\n❌ Başarısız: {failed}")
        admin_states.pop(message.from_user.id, None)
        
    # BAKİYE VERME
    elif state == "WAITING_ADD_BALANCE":
        args = message.text.split()
        if len(args) != 2 or not args[0].isdigit():
            bot.send_message(message.chat.id, "❌ Hatalı format! Örnek: `5000 123456789` veya `5000 @ahmet`", parse_mode="Markdown")
            return
            
        amount = int(args[0])
        target_input = args[1].replace("@", "").lower()
        target_id = find_user_id(target_input)
        
        if not target_id:
            bot.send_message(message.chat.id, "❌ **Hata:** Bu kullanıcı botu henüz başlatmamış veya kayıtlı değil!")
        else:
            users[target_id]["balance"] += amount
            bot.send_message(message.chat.id, f"✅ `{target_id}` ID'li kullanıcıya **+{amount} Çip** eklendi!\nYeni Bakiyesi: {users[target_id]['balance']}", parse_mode="Markdown")
            try:
                bot.send_message(target_id, f"🎉 Hesabınıza Admin tarafından **+{amount} Çip** eklendi!")
            except:
                pass
        admin_states.pop(message.from_user.id, None)

    # BAKİYE ALMA
    elif state == "WAITING_REMOVE_BALANCE":
        args = message.text.split()
        if len(args) != 2 or not args[0].isdigit():
            bot.send_message(message.chat.id, "❌ Hatalı format! Örnek: `2000 123456789` veya `2000 @ahmet`", parse_mode="Markdown")
            return
            
        amount = int(args[0])
        target_input = args[1].replace("@", "").lower()
        target_id = find_user_id(target_input)
        
        if not target_id:
            bot.send_message(message.chat.id, "❌ **Hata:** Bu kullanıcı kayıtlı değil!")
        else:
            users[target_id]["balance"] = max(0, users[target_id]["balance"] - amount)
            bot.send_message(message.chat.id, f"✅ `{target_id}` ID'li kullanıcıdan **-{amount} Çip** kesildi!\nYeni Bakiyesi: {users[target_id]['balance']}", parse_mode="Markdown")
            try:
                bot.send_message(target_id, f"⚠️ Hesabınızdan Admin tarafından **-{amount} Çip** kesildi!")
            except:
                pass
        admin_states.pop(message.from_user.id, None)

    # KULLANICI BANLAMA
    elif state == "WAITING_BAN_INPUT":
        target_input = message.text.replace("@", "").lower()
        target_id = find_user_id(target_input)

        if not target_id:
            bot.send_message(message.chat.id, "❌ **Hata:** Kullanıcı bulunamadı!")
        elif target_id == ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Kendinizi banlayamazsınız!")
        else:
            banned_users.add(target_id)
            bot.send_message(message.chat.id, f"🚫 `{target_id}` ID'li kullanıcı başarıyla **banlandı**!", parse_mode="Markdown")
            try:
                bot.send_message(target_id, "🚫 Bot erişiminiz Admin tarafından engellendi.")
            except:
                pass
        admin_states.pop(message.from_user.id, None)

    # BAN KALDIRMA
    elif state == "WAITING_UNBAN_INPUT":
        target_input = message.text.replace("@", "").lower()
        target_id = find_user_id(target_input)

        if not target_id or target_id not in banned_users:
            bot.send_message(message.chat.id, "❌ **Hata:** Bu kullanıcı banlı değil veya bulunamadı!")
        else:
            banned_users.remove(target_id)
            bot.send_message(message.chat.id, f"🟢 `{target_id}` ID'li kullanıcının banı **kaldırıldı**!", parse_mode="Markdown")
            try:
                bot.send_message(target_id, "🟢 Banınız kaldırıldı, botu tekrar kullanabilirsiniz!")
            except:
                pass
        admin_states.pop(message.from_user.id, None)

def find_user_id(target_input):
    """ID veya Username üzerinden kullanıcı arar."""
    if target_input.isdigit() and int(target_input) in users:
        return int(target_input)
    for uid, data in users.items():
        if data["username"] == target_input:
            return uid
    return None

# ---------------------------------------------------------
# SUNUCUYU VE BOTU BAŞLATMA
# ---------------------------------------------------------
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot 7/24 Kesintisiz Başlatıldı...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
