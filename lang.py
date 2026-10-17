"""
lang.py - Abix Ninja er 5 ta bhasha: English, Bangla, Chinese, Japanese, Spanish.

  lang.tr("play")          -> ekhon select kora bhashay lekha
  lang.set_lang("bn")      -> bhasha bodlao
  lang.font(size, bold)    -> oi bhasha-r akkhor dekhabe emon font (animation.get_font eta use kore)
  lang.speak_text(text)    -> (kotha, gTTS_code)  guard er kotha oi bhasha-y bolar jonno

Note: menu / settings / shop / PC er shob lekha 5 bhasha-y. Level er vitore choto HUD hint (jemon
"[E] ENTER CODE") ekhono English. Guard er kotha (voice) bhasha onujayi bole.
"""
import pygame

LANGS = [
    ("en", "English"),
    ("bn", "বাংলা"),
    ("zh", "中文"),
    ("ja", "日本語"),
    ("es", "Español"),
]
CODES = [c for c, _ in LANGS]

TTS_CODE = {"en": "en", "bn": "bn", "zh": "zh-CN", "ja": "ja", "es": "es"}
# pyttsx3 e oi bhasha-r gola khujar shobdo
VOICE_HINT = {"bn": ("bangla", "bengali"), "zh": ("chinese", "huihui", "zh-", "mandarin"),
              "ja": ("japanese", "haruka", "ja-"), "es": ("spanish", "helena", "es-", "sabina")}

_cur = {"code": "en"}

# (en, bn, zh, ja, es)
S = {
    "play": ("PLAY", "খেলুন", "开始游戏", "プレイ", "JUGAR"),
    "settings": ("SETTINGS", "সেটিংস", "设置", "設定", "AJUSTES"),
    "abix_tools": ("ABIX TOOLS", "আবিক্স টুলস", "ABIX 工具", "ABIX ツール", "HERRAMIENTAS ABIX"),
    "special_tools": ("SPECIAL TOOLS", "বিশেষ টুলস", "特殊工具", "スペシャルツール", "HERRAMIENTAS ESPECIALES"),
    "gaming_pc": ("GAMING PC", "গেমিং পিসি", "游戏电脑", "ゲーミングPC", "PC GAMER"),
    "language": ("LANGUAGE", "ভাষা", "语言", "言語", "IDIOMA"),
    "control_mode": ("CONTROL MODE", "কন্ট্রোল মোড", "控制模式", "操作モード", "MODO DE CONTROL"),
    "keyboard": ("KEYBOARD", "কীবোর্ড", "键盘", "キーボード", "TECLADO"),
    "controller": ("CONTROLLER", "কন্ট্রোলার", "手柄", "コントローラー", "MANDO"),
    "touch": ("MOBILE", "মোবাইল", "触屏", "タッチ", "MÓVIL"),
    "volume": ("VOLUME", "ভলিউম", "音量", "音量", "VOLUMEN"),
    "about": ("ABOUT", "সম্পর্কে", "关于", "このゲームについて", "ACERCA DE"),
    "privacy": ("PRIVACY POLICY", "গোপনীয়তা নীতি", "隐私政策", "プライバシーポリシー", "POLÍTICA DE PRIVACIDAD"),
    "back": ("BACK", "ফিরে যান", "返回", "戻る", "VOLVER"),
    "esc_back": ("ESC = back", "ESC = ফিরে যান", "ESC = 返回", "ESC = 戻る", "ESC = volver"),
    "ctrl_none": ("No controller found - plug one in", "কোনো কন্ট্রোলার পাওয়া যায়নি - লাগান",
                  "未检测到手柄 - 请插入", "コントローラーが見つかりません", "No se encontró mando - conéctalo"),
    "ctrl_ok": ("Controller connected", "কন্ট্রোলার যুক্ত আছে", "手柄已连接", "コントローラー接続済み", "Mando conectado"),
    "c_move": ("Left stick = move", "বাম স্টিক = চলা", "左摇杆 = 移动", "左スティック = 移動", "Palanca izq. = mover"),
    "c_jump": ("RB = jump", "RB = লাফ", "RB = 跳跃", "RB = ジャンプ", "RB = saltar"),
    "c_knife": ("X = knife", "X = ছুরি", "X = 小刀", "X = ナイフ", "X = cuchillo"),
    "c_punch": ("Y = super punch", "Y = সুপার পাঞ্চ", "Y = 超级重拳", "Y = スーパーパンチ", "Y = súper puñetazo"),
    "c_hide": ("B = hide (hold)", "B = লুকানো (ধরে রাখুন)", "B = 躲藏(按住)", "B = 隠れる(長押し)", "B = esconderse (mantener)"),
    "c_star": ("A = ninja star (if unlocked)", "A = নিনজা স্টার (আনলক থাকলে)", "A = 忍者星(已解锁)",
               "A = 手裏剣(解放済み)", "A = estrella ninja (si está desbloqueada)"),
    "c_use": ("LB = use tool", "LB = টুল ব্যবহার", "LB = 使用工具", "LB = ツール使用", "LB = usar herramienta"),
    "c_wheel": ("BACK = tool wheel (stick = move, A = pick)", "BACK = টুল হুইল (স্টিক = সরান, A = বাছুন)",
                "BACK = 工具轮盘(摇杆选择, A确定)", "BACK = ツールホイール(スティック=選択, A=決定)",
                "ATRÁS = rueda de herramientas (palanca = mover, A = elegir)"),
    "c_pause": ("START = pause", "START = বিরতি", "START = 暂停", "START = ポーズ", "START = pausa"),
    "c_laptop": ("L3 = laptop", "L3 = ল্যাপটপ", "L3 = 笔记本", "L3 = ノートPC", "L3 = portátil"),
    "c_special": ("R3 = code writer on/off,  LT = electric", "R3 = কোড রাইটার অন/অফ,  LT = ইলেকট্রিক",
                  "R3 = 代码器 开/关,  LT = 电击", "R3 = コード入力 オン/オフ,  LT = 電撃",
                  "R3 = escritor de código on/off,  LT = eléctrico"),
    "about_1": ("ABIX NINJA  -  a stealth heist game", "ABIX NINJA  -  একটি স্টেলথ হেইস্ট গেম",
                "ABIX NINJA  -  潜行盗窃游戏", "ABIX NINJA  -  ステルス強盗ゲーム", "ABIX NINJA  -  juego de robos de sigilo"),
    "about_2": ("Made by Abix Games", "তৈরি: Abix Games", "制作: Abix Games", "制作: Abix Games", "Creado por Abix Games"),
    "about_3": ("Made with Python and Pygame", "Python ও Pygame দিয়ে তৈরি", "使用 Python 和 Pygame 制作",
                "Python と Pygame で作成", "Hecho con Python y Pygame"),
    "priv_1": ("Your progress is saved only on your", "আপনার অগ্রগতি শুধু আপনার কম্পিউটারে",
               "你的进度只保存在你的电脑上", "進行状況はあなたのPCにのみ保存されます", "Tu progreso se guarda solo en tu"),
    "priv_2": ("computer (abix_save.json).", "সেভ হয় (abix_save.json)।", "(abix_save.json)。",
               "(abix_save.json)。", "ordenador (abix_save.json)."),
    "priv_3": ("Nothing is sent to anyone.", "কাউকে কিছু পাঠানো হয় না।", "不会向任何人发送数据。",
               "データは誰にも送信されません。", "No se envía nada a nadie."),
    "priv_4": ("Guard voices may use Google text-to-speech", "গার্ডের কণ্ঠে Google টেক্সট-টু-স্পিচ লাগতে পারে",
               "守卫语音可能使用 Google 文字转语音", "ガードの音声は Google 音声合成を使う場合があります",
               "Las voces pueden usar el texto a voz de Google"),
    "priv_5": ("(needs internet) only if no offline voice exists.", "(ইন্টারনেট লাগে) অফলাইন ভয়েস না থাকলে।",
               "(需要网络) 仅在没有离线语音时。", "(ネット接続が必要) オフライン音声が無い場合のみ。",
               "(requiere internet) solo si no hay voz sin conexión."),
    "sp_title": ("SPECIAL TOOLS", "বিশেষ টুলস", "特殊工具", "スペシャルツール", "HERRAMIENTAS ESPECIALES"),
    "exchange": ("EXCHANGE", "মুদ্রা বদল", "兑换", "両替", "CAMBIO"),
    "ex_title": ("CURRENCY EXCHANGE", "মুদ্রা বিনিময়", "货币兑换", "通貨両替", "CAMBIO DE MONEDA"),
    "ex_rate1": ("123 Tk = 1 Dollar", "১২৩ টাকা = ১ ডলার", "123 塔卡 = 1 美元", "123 タカ = 1 ドル", "123 Tk = 1 dólar"),
    "ex_rate2": ("2000 Tk = 1 Diamond", "২০০০ টাকা = ১ ডায়মন্ড", "2000 塔卡 = 1 钻石", "2000 タカ = 1 ダイヤ", "2000 Tk = 1 diamante"),
    "tk": ("Tk", "টাকা", "塔卡", "タカ", "Tk"),
    "dollar": ("DOLLARS", "ডলার", "美元", "ドル", "DÓLARES"),
    "diamond": ("DIAMONDS", "ডায়মন্ড", "钻石", "ダイヤ", "DIAMANTES"),
    "get": ("GET", "নিন", "兑换", "交換", "OBTENER"),
    "exchanged": ("EXCHANGED!", "বদল হয়েছে!", "兑换成功!", "両替しました!", "¡CAMBIADO!"),
    "buy_tk": ("BUY with Tk", "টাকায় কিনুন", "用塔卡购买", "タカで購入", "COMPRAR con Tk"),
    "buy_dia": ("BUY with diamonds", "ডায়মন্ডে কিনুন", "用钻石购买", "ダイヤで購入", "COMPRAR con diamantes"),
    "owned": ("OWNED", "কেনা হয়েছে", "已拥有", "所持", "COMPRADO"),
    "locked": ("LOCKED", "লক করা", "未解锁", "ロック中", "BLOQUEADO"),
    "soon": ("COMING SOON", "শীঘ্রই আসছে", "即将推出", "近日公開", "PRÓXIMAMENTE"),
    "need_more": ("NOT ENOUGH MONEY", "যথেষ্ট টাকা নেই", "钱不够", "お金が足りません", "DINERO INSUFICIENTE"),
    "bought": ("PURCHASED!", "কেনা হয়েছে!", "购买成功!", "購入しました!", "¡COMPRADO!"),
    "t_star": ("NINJA STAR", "নিনজা স্টার", "忍者飞镖", "手裏剣", "ESTRELLA NINJA"),
    "t_code": ("MINI CODE WRITER", "মিনি কোড রাইটার", "迷你代码器", "ミニコードライター", "MINI ESCRITOR DE CÓDIGO"),
    "t_electric": ("ELECTRIC", "ইলেকট্রিক", "电击", "エレクトリック", "ELÉCTRICO"),
    "d_star": ("Throw a star (T / A button).|Kills a guard in its path.", "তারা ছুড়ুন (T / A বোতাম)।|পথে থাকা গার্ড মরবে।",
               "投掷飞镖 (T / A 键)。|击杀路径上的守卫。", "手裏剣を投げる (T / A)。|進路上のガードを倒す。",
               "Lanza una estrella (T / botón A).|Elimina a un guardia."),
    "d_code": ("Types the code for you.|Press C (R3) to turn on / off.", "কোড নিজে নিজে লিখে দেয়।|C (R3) চেপে অন/অফ।",
               "自动输入代码。|按 C (R3) 开/关。", "コードを自動で入力する。|C (R3) でオン/オフ。",
               "Escribe el código por ti.|Pulsa C (R3) para activar."),
    "d_electric": ("Press Q (LT): all guards are|frozen for 5 seconds.", "Q (LT) চাপুন: ৫ সেকেন্ড সব গার্ড|থেমে থাকবে।",
                   "按 Q (LT): 所有守卫|冻结 5 秒。", "Q (LT): 5秒間すべてのガードが|動けなくなる。",
                   "Pulsa Q (LT): todos los guardias|se congelan 5 segundos."),
    "bonus20": ("CHAPTER COMPLETE!  +20 DIAMONDS", "চ্যাপ্টার শেষ!  +২০ ডায়মন্ড", "章节完成!  +20 钻石",
                "チャプタークリア!  +20 ダイヤ", "¡CAPÍTULO COMPLETO!  +20 DIAMANTES"),
    "pc_title": ("MY GAMING PC", "আমার গেমিং পিসি", "我的游戏电脑", "マイ ゲーミングPC", "MI PC GAMER"),
    "pc_game": ("Ninja Run", "নিনজা রান", "忍者跑酷", "忍者ラン", "Ninja Run"),
    "pc_score": ("SCORE", "স্কোর", "分数", "スコア", "PUNTOS"),
    "pc_best": ("BEST", "সেরা", "最高", "ベスト", "MEJOR"),
    "pc_over": ("GAME OVER  -  press SPACE", "গেম শেষ  -  SPACE চাপুন", "游戏结束  -  按空格", "ゲームオーバー  -  SPACE", "FIN DEL JUEGO  -  pulsa ESPACIO"),
    "pc_tip": ("SPACE / W / click = jump", "SPACE / W / ক্লিক = লাফ", "空格 / W / 点击 = 跳跃", "SPACE / W / クリック = ジャンプ", "ESPACIO / W / clic = saltar"),
    "god_on": ("GOD MODE ON", "গড মোড চালু", "上帝模式开启", "ゴッドモード オン", "MODO DIOS ACTIVADO"),
    "god_off": ("GOD MODE OFF", "গড মোড বন্ধ", "上帝模式关闭", "ゴッドモード オフ", "MODO DIOS DESACTIVADO"),
}

# guard er kotha (voice) - category onujayi
_ALERT_WORDS = ("freeze", "halt", "hands up", "stop right", "intruder", "thief", "security", "sound the alarm",
                "kill the", "cyber breach", "not a vip")
SPEECH = {
    "alert": ("Stop! Thief! Hands up!", "থামো! চোর! হাত তোলো!", "站住!小偷!举起手来!", "止まれ!泥棒!手を上げろ!", "¡Alto! ¡Ladrón! ¡Manos arriba!"),
    "cctv": ("I have camera footage of you!", "আমার কাছে তোমার ক্যামেরা ফুটেজ আছে!", "我有你的监控录像!",
             "お前の監視カメラ映像がある!", "¡Tengo tus imágenes de cámara!"),
    "god": ("God mode on", "গড মোড চালু", "上帝模式开启", "ゴッドモード オン", "Modo dios activado"),
}


def set_lang(code):
    if code in CODES:
        _cur["code"] = code
        _fonts.clear()


def get_lang():
    return _cur["code"]


def lang_name(code=None):
    code = code or _cur["code"]
    return dict(LANGS).get(code, code)


def tr(key):
    v = S.get(key)
    if not v:
        return key
    i = CODES.index(_cur["code"])
    return v[i] if i < len(v) and v[i] else v[0]


def tr_lines(key):
    """'a|b' dhoroner lekha ke line e bhag kore."""
    return tr(key).split("|")


def speak_text(text):
    """(kotha, gTTS_code): oi bhasha-y anubad thakle seta, na thakle English."""
    code = _cur["code"]
    if code == "en":
        return text, "en"
    low = text.lower()
    cat = None
    if "god summoned" in low:
        cat = "god"
    elif "cctv" in low:
        cat = "cctv"
    elif any(w in low for w in _ALERT_WORDS):
        cat = "alert"
    if cat:
        return SPEECH[cat][CODES.index(code)], TTS_CODE[code]
    return text, "en"


# ------------------------------------------------------------------
# Font: bhasha onujayi
# ------------------------------------------------------------------
_FONT_NAMES = {
    "bn": ("nirmalaui", "nirmala ui", "vrinda", "shonarbangla", "notosansbengali", "lohitbengali", "arialunicodems"),
    "zh": ("microsoftyahei", "simhei", "simsun", "notosanscjksc", "pingfangsc", "wenquanyimicrohei", "arialunicodems"),
    "ja": ("yugothic", "meiryo", "msgothic", "notosanscjkjp", "hiraginosans", "takaopgothic", "arialunicodems"),
}
_fonts = {}


def font(size, bold=True):
    code = _cur["code"]
    key = (code, size, bold)
    f = _fonts.get(key)
    if f is not None:
        return f
    f = None
    if code in _FONT_NAMES:
        for name in _FONT_NAMES[code]:
            try:
                path = pygame.font.match_font(name)
            except Exception:
                path = None
            if path:
                try:
                    f = pygame.font.Font(path, size)
                    f.set_bold(bool(bold) and code != "bn")
                    break
                except Exception:
                    f = None
    if f is None:
        f = pygame.font.SysFont("arialblack,arial,verdana", size, bold=bold)
    _fonts[key] = f
    return f
