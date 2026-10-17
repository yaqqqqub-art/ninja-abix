ABIX NINJA - V12 UPDATE
=======================

0. Install (PC):
      pip install pygame
      pip install ursina            <- REAL 3D "BUSTED" animation (optional)
      pip install imageio-ffmpeg    <- recorder MP4 (optional, ffmpeg thakle lagbe na)
   Ursina nei / phone / exe build  ->  game nijer pygame-3D (bust3d.py) use kore.  Bondho korte: ABIX_NO_URSINA=1

1. MOBILE BUTTON (touch.py)  - notun
   - Button boro + alada, overlap nei.  Kache jei button sei pay (angul ektu bahire porleo kaj kore).
   - JUMP = hold: chepe rakhle uchu lafay.   Slide LEFT <-> RIGHT thumb na tule.
   - RGB rainbow ring + glow, press e ripple + pop, JUMP breathing animation, pop-in start e.
   - REC button (upore) = recorder.   RGB bondho: touch.TOUCH.rgb = False

2. LEVEL 12 - CITY POLICE TOWER (level12.py)
   - ELITE SQUAD: ekshathe 4 jon, 5 HP.   KNIFE (J) = 1 HP -> 5 knife.   SUPER PUNCH (K) = 2 HP -> 3 punch e KO.
   - GOD MODE: police er SHAMNE theke mar kaj kore na.  Lafiye pichone giye mar.
   - CATCH BAR: dhorle matha r upor bar bhore, SPACE mere chharao.  3 bar dhora porle -> 3D animation e police tomake JAIL e niye jay.
   - Keycard door, PAGE e code, code lock, laser grid, thermite vault, getaway van.   Reward 6000, bail 1200.
   - Level 11 e o ELITE police ekhon thikmoto ashe (spawn bug fix: police.py _clear_path).

3. 3D JAIL ANIMATION (ursina_bust.py + bust_ursina.py)  - Ursina 3D: police ninja ke handcuff pore cell e niye jay,
   camera ghure, lohar dorja bondho, BUSTED! text.   ESC / SPACE = skip.

4. HD ANIMATION (hd_animation.py)
   - GOD MODE hex-shield dome (sweep line, rim glow, halo), samne mar dile ring + shards + "GOD MODE" RGB-split stamp,
     hit spark + slash, KO stars + "DOWN!", siren light cone, rainbow banner text.

5. RECORDER (recorder.py)
   - F9 = record shuru/shesh,  F10 = screenshot,  mobile: REC button.
   - Save:  %APPDATA%\AbixNinja\Recordings\abix_<date>.mp4   (sound record hoy na)

6. MOD CHECKER REMOVED (modloader.py / modsui.py)
   - Security server, code scan, block - shob bad.  Jekono mod folder (main.py) cholbe.  Full Python access.
   - Shudhu nijer trust kora mod chalao - mod ekhon tomar PC te jekono kaj korte pare.

NOTUN FILE:  level12.py, hd_animation.py, recorder.py, ursina_bust.py, bust_ursina.py, requirements.txt
BODLANO:     touch.py, police.py, level11.py, modloader.py, modsui.py, main_game.py
