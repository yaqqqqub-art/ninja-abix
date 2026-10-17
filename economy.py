"""
economy.py - Abix Ninja er taka (Tk), dollar, diamond ar Special Tools.

  123 Tk  = 1 Dollar
  2000 Tk = 1 Diamond
  Chapter er 20 number level (boss) prothom bar shesh korle  +20 DIAMOND.
  Level er taka / jinish ekbar nile replay te ar pawa jay na (save["taken"] - ager moto).

Save e: money (Tk), dollars, diamonds, special {star, code, electric}, bonus20 [5]
"""
TK_PER_DOLLAR = 123
TK_PER_DIAMOND = 2000
CHAPTER_DIAMONDS = 20

# ---- NINJA SKIN (30 ta) -------------------------------------------
NINJA_COUNT = 30
NINJA_FIRST_PRICE = 300      # 2 number ninja = 300 diamond
NINJA_STEP = 50              # tarpor protita +50 diamond (30 number = 1700)


def ninja_price(i):
    """0 number ninja FREE. 1 = 300 diamond, 2 = 350, 3 = 400 ... """
    return 0 if i <= 0 else NINJA_FIRST_PRICE + (i - 1) * NINJA_STEP


# Special Tools - 9 ta slot. price_tk = taka dam, price_dia = diamond dam (2000 Tk = 1 diamond).
SPECIAL = [
    {"id": "star", "name": "t_star", "desc": "d_star", "price_tk": 40000, "price_dia": 20},
    {"id": "code", "name": "t_code", "desc": "d_code", "price_tk": 20000, "price_dia": 10},
    {"id": "electric", "name": "t_electric", "desc": "d_electric", "price_tk": 30000, "price_dia": 15},
] + [{"id": None} for _ in range(6)]


def ensure(save):
    """Save e notun field gulo bosiye dey (purono save o thik thake)."""
    save["money"] = max(0, int(save.get("money", 0)))
    save["dollars"] = max(0, int(save.get("dollars", 0)))
    save["diamonds"] = max(0, int(save.get("diamonds", 0)))
    sp = save.get("special")
    if not isinstance(sp, dict):
        sp = {}
    save["special"] = {k: bool(sp.get(k, False)) for k in ("star", "code", "electric")}
    b = save.get("bonus20")
    if not (isinstance(b, list) and len(b) == 5):
        b = [False] * 5
    save["bonus20"] = [bool(x) for x in b]
    nj = save.get("ninja")
    if not isinstance(nj, dict):
        nj = {}
    owned = sorted({int(i) for i in nj.get("owned", []) if isinstance(i, (int, float)) and 0 <= int(i) < NINJA_COUNT} | {0})
    sel = nj.get("sel", 0)
    sel = int(sel) if isinstance(sel, (int, float)) and int(sel) in owned else 0
    save["ninja"] = {"owned": owned, "sel": sel}
    st = save.get("settings")
    if not isinstance(st, dict):
        st = {}
    st["lang"] = st.get("lang") if st.get("lang") in ("en", "bn", "zh", "ja", "es") else "en"
    st["control"] = st.get("control") if st.get("control") in ("keyboard", "controller", "touch") else ("touch" if "ANDROID_ARGUMENT" in __import__("os").environ else "keyboard")
    save["settings"] = st
    return save


def exchange(save, kind, count=1):
    """kind: 'dollar' | 'diamond'.  Tk theke count ta dollar / diamond kine. True = holo."""
    cost = (TK_PER_DOLLAR if kind == "dollar" else TK_PER_DIAMOND) * count
    if save["money"] < cost:
        return False
    save["money"] -= cost
    save["dollars" if kind == "dollar" else "diamonds"] += count
    return True


def buy(save, tool_id, with_diamonds):
    """'ok' | 'owned' | 'poor' | 'none'"""
    item = next((s for s in SPECIAL if s["id"] == tool_id), None)
    if not item:
        return "none"
    if save["special"].get(tool_id):
        return "owned"
    if with_diamonds:
        if save["diamonds"] < item["price_dia"]:
            return "poor"
        save["diamonds"] -= item["price_dia"]
    else:
        if save["money"] < item["price_tk"]:
            return "poor"
        save["money"] -= item["price_tk"]
    save["special"][tool_id] = True
    return "ok"


def award_chapter(save, ch):
    """Chapter er level 20 prothom bar shesh hole +20 diamond. Return: koto pelo (0 = ager e peyeche)."""
    if not save["bonus20"][ch]:
        save["bonus20"][ch] = True
        save["diamonds"] += CHAPTER_DIAMONDS
        return CHAPTER_DIAMONDS
    return 0


def buy_ninja(save, i):
    """'ok' | 'owned' | 'poor' | 'none'   (diamond diye kena)"""
    if not 0 <= i < NINJA_COUNT:
        return "none"
    if i in save["ninja"]["owned"]:
        return "owned"
    price = ninja_price(i)
    if save["diamonds"] < price:
        return "poor"
    save["diamonds"] -= price
    save["ninja"]["owned"] = sorted(save["ninja"]["owned"] + [i])
    return "ok"


def select_ninja(save, i):
    if i in save["ninja"]["owned"]:
        save["ninja"]["sel"] = i
        return True
    return False
