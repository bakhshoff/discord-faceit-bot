"""Calestify FACEIT — AZ / TR lokalizasiya modulu."""

STRINGS = {
    # ── AZƏRBAYCANCA ──────────────────────────────────────────────────────────
    'az': {
        # Xəbərdarlıq / Ban / Unban DM
        'warn_dm':          "⚠️ **Calestify FACEIT** — Xəbərdarlıq #{count}\n**Səbəb:** {reason}",
        'ban_perm_dm':      "🔴 **Calestify FACEIT** — DAİMİ banlandınız.\n**Səbəb:** {reason}",
        'ban_temp_dm':      "🔴 **Calestify FACEIT** — {label} banlandınız.\n**Səbəb:** {reason}\n**Bitmə:** {exp}",
        'unban_dm':         "✅ **Calestify FACEIT** — Banınız açıldı, yenidən qoşula bilərsiniz.",

        # Matç bildirişləri
        'match_start_dm':   "🎮 **Matç No{num}** başladı!\n**Komandanız:** {team}\n**Kanal:** {channel}\n\nTez qoşulun!",
        'match_win_dm':     "🏆 **Matç No{num}** — Qalibsiniz!\n**+{elo} ELO** qazandınız. Yeni ELO: **{new_elo}**",
        'match_loss_dm':    "💔 **Matç No{num}** — Məğlub oldunuz.\n**-{elo} ELO**. Yeni ELO: **{new_elo}**",
        'match_cancel_dm':  "🚫 **Matç No{num}** ləğv edildi.",

        # Növbə (queue)
        'queue_joined':     "✅ Sıraya əlavə olundunuz. Mövqeyiniz: **{pos}/10**",
        'queue_left':       "❌ Sıradan çıxdınız.",
        'queue_full':       "🔔 Sıra doldu! Matç tezliklə başlayacaq.",

        # Gündəlik bonus
        'daily_bonus':      "🎁 Gündəlik bonus: **+{coins} coin**" ,
        'daily_streak':     " (Giriş seriyası: {streak}🔥)",

        # Qeydiyyat
        'register_success': "✅ Qeydiyyat tamamlandı! Xoş gəldiniz, **{nick}**!\n`/profile` ilə profilinizə baxa bilərsiniz.",
        'already_reg':      "❌ Siz artıq qeydiyyatdan keçmisiniz!",

        # Parametrlər
        'settings_title':   "⚙️ Parametrlər",
        'settings_desc':    "Aşağıdan dil seçin. Seçim profilinizə saxlanılır.",
        'lang_set_az':      "✅ Dil **Azərbaycanca** olaraq təyin edildi.",
        'lang_set_tr':      "✅ Dil **Türkcə** olaraq təyin edildi.",
        'current_lang':     "Hazırkı dil: 🇦🇿 Azərbaycanca",

        # Coin
        'coin_transfer_ok': "✅ **{recv} coin** <@{to}>-yə göndərildi. (Komissiya: {comm} coin)",
        'coin_no_balance':  "❌ Kifayət qədər coin yoxdur.",

        # Ümumi
        'not_registered':   "❌ Qeydiyyatdan keçməmisən. `/register` istifadə et.",
        'error_generic':    "❌ Xəta baş verdi. Yenidən cəhd edin.",
    },

    # ── TÜRKCƏ ────────────────────────────────────────────────────────────────
    'tr': {
        # Uyarı / Ban / Unban DM
        'warn_dm':          "⚠️ **Calestify FACEIT** — Uyarı #{count}\n**Sebep:** {reason}",
        'ban_perm_dm':      "🔴 **Calestify FACEIT** — KALİCİ olarak yasaklandınız.\n**Sebep:** {reason}",
        'ban_temp_dm':      "🔴 **Calestify FACEIT** — {label} yasaklandınız.\n**Sebep:** {reason}\n**Bitiş:** {exp}",
        'unban_dm':         "✅ **Calestify FACEIT** — Yasağınız kaldırıldı, tekrar katılabilirsiniz.",

        # Maç bildirimleri
        'match_start_dm':   "🎮 **Maç No{num}** başladı!\n**Takımınız:** {team}\n**Kanal:** {channel}\n\nHemen katılın!",
        'match_win_dm':     "🏆 **Maç No{num}** — Kazandınız!\n**+{elo} ELO** kazandınız. Yeni ELO: **{new_elo}**",
        'match_loss_dm':    "💔 **Maç No{num}** — Kaybettiniz.\n**-{elo} ELO**. Yeni ELO: **{new_elo}**",
        'match_cancel_dm':  "🚫 **Maç No{num}** iptal edildi.",

        # Kuyruk (queue)
        'queue_joined':     "✅ Sıraya eklendiniz. Sıranız: **{pos}/10**",
        'queue_left':       "❌ Sıradan çıktınız.",
        'queue_full':       "🔔 Sıra doldu! Maç yakında başlayacak.",

        # Günlük bonus
        'daily_bonus':      "🎁 Günlük bonus: **+{coins} coin**",
        'daily_streak':     " (Giriş serisi: {streak}🔥)",

        # Kayıt
        'register_success': "✅ Kayıt tamamlandı! Hoş geldiniz, **{nick}**!\n`/profile` ile profilinizi görüntüleyebilirsiniz.",
        'already_reg':      "❌ Zaten kayıtlısınız!",

        # Ayarlar
        'settings_title':   "⚙️ Ayarlar",
        'settings_desc':    "Aşağıdan dil seçin. Seçiminiz profilinize kaydedilir.",
        'lang_set_az':      "✅ Dil **Azerbaycanca** olarak ayarlandı.",
        'lang_set_tr':      "✅ Dil **Türkçe** olarak ayarlandı.",
        'current_lang':     "Mevcut dil: 🇹🇷 Türkçe",

        # Coin
        'coin_transfer_ok': "✅ **{recv} coin** <@{to}>'e gönderildi. (Komisyon: {comm} coin)",
        'coin_no_balance':  "❌ Yeterli coin yok.",

        # Genel
        'not_registered':   "❌ Kayıtlı değilsin. `/register` kullan.",
        'error_generic':    "❌ Bir hata oluştu. Tekrar deneyin.",
    },
}


def t(discord_id_or_lang, key: str, **kwargs) -> str:
    """Get localized string for a user (by discord_id) or explicit lang code."""
    if isinstance(discord_id_or_lang, str):
        lang = discord_id_or_lang if discord_id_or_lang in STRINGS else 'az'
    else:
        try:
            from database import get_lang
            lang = get_lang(discord_id_or_lang)
        except Exception:
            lang = 'az'

    text = STRINGS.get(lang, STRINGS['az']).get(key)
    if text is None:
        text = STRINGS['az'].get(key, key)
    return text.format(**kwargs) if kwargs else text
