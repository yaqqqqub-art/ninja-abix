ABIX NINJA - V14 MEGA UPDATE
============================
1. LEVEL 14 - NIGHT MUSEUM (level14.py)   Golden Mask churi.  Elite police 5 jon.  Reward 9000 Tk.
   LEVEL 15 - ROYAL FORTRESS (level15.py) Crown of Abix churi (FINALE).  Elite police 6 jon, 3 laser grid.  Reward 15000 Tk.
   - Keycard door, PAGE e code, code lock, laser grid, thermite vault, getaway van.
   - 3 bar dhora porle 3D arrest -> JAIL (nicher 3 option).
   - Level 14 khulbe Level 13 shesh korle, 15 khulbe 14 shesh korle (ba unlock code).

2. JAIL - 3 OPTION (jail.py)   [level 14, 15 ar 3D level e]
   1  PAY BAIL     10000 Tk dile sathe sathe free.
   2  WAIT         1 MINUTE dariye thako, tarpor free.
   3  BREAK OUT    3 ta CELL BAR + 2 ta WINDOW bhango.
        BREAK button (SPACE / ENTER / tap) chapo jokhon dagh ta SHOBUJ jaygay:
          GOOD (shobuj)   = boro bhanga  +55
          NORMAL (holud)  = chhoto bhanga +28
          BAD (lal)       = progress kome -30 ar GUARD shune phele.  3 bar BAD hole guard dhore -> 1 MIN wait.
        Protita stage 100 hole bhange.  Shob 5 ta bhangle ninja PALAY.
   Onno level e (1-13) ager moto bail / 5 din jail.   Onno level e 3 option chalu korte: World class e  JAIL3 = True.
   Dam bodlate:  jail.py -> PAY_COST, WAIT_TIME.

3. PLAY 3D NINJA (game3d.py)  - main menu te notun button (key 3)
   - 3 ta 3D level (BANK VAULT, MUSEUM NIGHT, POLICE FORTRESS).  Level 1 shuru te khola, porergulo ager ta shesh korle.
   - Lokkho: DIAMOND (nil) churi koro, tarpor EXIT (shobuj) e palao.
   - CCTV ghure ghure dekhe -> SPOT meter bhore -> ALARM -> shob police tomar dike ashe.
   - POLICE patrol kore, dekhle tare kore.  Dhorle CATCH BAR bhore, SPACE mere chharao.  3 bar dhora porle JAIL (3 option).
   - SNEAK (SHIFT / C / SNEAK button) = dhire hnete, dekhte pay kom.
   - Minimap (daan kone): holud = CCTV cone, lal/nil = police.
   - Keys: W S A D, <- ->, SHIFT, SPACE, ESC.   Phone: on-screen button.
   - Pure pygame raycaster - extra install lage na, phone e o cholbe.
   - Reward: 2000 / 3500 / 6000 Tk.   Balance: game3d.py -> LEVELS, REWARDS.

NOTUN FILE: level14.py, level15.py, jail.py, game3d.py
BODLANO:    level1.py (jail hook), level11.py, main_game.py (level 14/15 + PLAY 3D NINJA button)

NOTE: pygame na thakar karone ei update ta chalaye dekha jayni.  Logic (3D map, CCTV, police, catch, jail break) headless test kora hoyeche,
ar compile check.  Draw / look e kono bug paile error ta pathao.
