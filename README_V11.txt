ABIX NINJA - v11  (LEVEL 11 : POLICE HEADQUARTERS)
===================================================

Chapter 1 / Level 11 khulbe Level 10 shesh korle.   Lokkho: Police HQ theke "EVIDENCE DRIVE" churi kore
pichoner gali r GETAWAY VAN e palano.

ELITE POLICE  (notun, shob shomoy ashe - level er majh theke)
  - 5 HP.   KNIFE (J) = 1 HP -> 5 knife.     SUPER PUNCH (K) = 2 HP -> 3 punch e KO.
  - GOD MODE:  police er SHAMNE (je dike mukh kore ache) theke knife / punch KAJ KORE NA ("GOD MODE!" likha ashe).
      -> police er opor diye lafao, pichone giye mar.  Police ghurte 0.45 sec shomoy nei, tokhon e mar.
      -> mar khele police 0.65 sec atke thake - tokhon abar mar.
  - KO hole 10 sec por 3 HP niye uthe.   Speed 200 (tomar 250) - dour dile bachbe.   Door / laser police ke atkay.
  - CATCH BAR:  police dhorle tomar matha r upor bar bhore.  SPACE / W (jump) mere bar komao, ba dour dao.
      Bar bhorle  "CAUGHT 1 / 3"  (upore ARREST meter e handcuff lal hoy).  3 bar dhora porle:
  - 3D ARREST ANIMATION:  camera ghure ghure dekhay, police tomake handcuff pore jail cell e niye jay,
      lohar dorja khole ninja ke dhukay, tarpor dorja bondho hoy ("LOCKED UP!").  Tarpor jail screen (bail / 5 din)
      ar checkpoint theke abar shuru.
  - 22 sec dhora na porle 1 ta CAUGHT mafe.

Level e ki ki:  keycard door (HQ ENTRANCE) -> PAGE e EVIDENCE ROOM er code -> CODE LOCK door -> laser grid ->
THERMITE vault -> EVIDENCE DRIVE -> getaway van.   Reward 4500 Tk, bail 900 Tk.

Dam / balance bodlate:  level11.py -> World11.ELITE_POLICE   ("hp", "knife", "punch", "catch_time", "catch_max",
"max" (ek shathe koyjon), "spawn_every", "speed", "turn", "from" (kon x theke shuru)).
Police bondho:  save settings -> "police": false.

NOTUN FILE:  level11.py, bust3d.py       BODLANO:  police.py, main_game.py

NOTE: ei update ta pygame chalaye test kora hoyni (developer machine e pygame chilo na) - logic test kora hoyeche,
ar compile check.  Kono bug paile (crash / draw) amake error ta pathao.
