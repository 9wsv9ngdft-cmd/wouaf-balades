"""v58 (4.5) : surprises : arcade d'habitude, Noël en décembre ; ouverture, retour de balade, pop-up bien lu (+10), pop-up zappé (« Ah non… t'es sûr ? »)."""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','63');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-hon-vu','2099-01');localStorage.setItem('wouaf-wa-sent','[]');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
EV = lambda P, js: P.evaluate(js)
on = lambda P: EV(P, "document.querySelector('#surp').classList.contains('on')")
txt = lambda P: EV(P, "document.querySelector('#surp').innerText")
sc = lambda P: EV(P, "(document.querySelector('#surp .sc') || {}).dataset ? document.querySelector('#surp .sc').dataset.sc : ''")
CTX = "{ min: 52, m: 3400, nc: 5, pp: 3, cs: 120, streak: 3 }"
T = lambda m, d, h=10: datetime.datetime(2026, m, d, h, 0, 0)
errs = []
with sync_playwright() as pw:
    for month, day, theme in [(11, 25, "arcade"), (12, 3, "xmas")]:
        st, body = local_api("POST", "/opts-set", json.dumps({"code": "1234", "opts": {"surp": True, "jabPen": True, "jabAmt": 1}}).encode())   # v4.7 : surprises éteintes par défaut, allumées par le superviseur
        check("v4.7 : Superviseur › Options enregistrées sur le serveur", st == 200 and json.loads(body)["opts"]["surp"] is True, body[:120])
        b, c, P = new_phone(pw, errors=errs, init=INIT)
        P.clock.install(time=T(month, day)); P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 2500)
        P.clock.run_for(4000)
        if EV(P, "document.querySelector('#modal').classList.contains('open')"): EV(P, "document.querySelector('#sheetX').click()")
        P.clock.run_for(4500)   # (fermer le pop-up du jour tout de suite = « zappé » : on laisse passer le « Ah non… »)
        EV(P, "localStorage.removeItem('wouaf-surp')")
        check(f"{theme} : le thème du jour", EV(P, "__wouaf.surpTheme()") == theme)
        EV(P, "window.__surpForce = 0.99")
        check(f"{theme} : ouverture, rare : pas cette fois", EV(P, "__wouaf.surpOpenMaybe()") is False and not on(P))
        EV(P, "window.__surpForce = 0")
        check(f"{theme} : ouverture : ça déboule", EV(P, "__wouaf.surpOpenMaybe()") and on(P))
        t1 = txt(P); P.clock.run_for(900); t2 = txt(P)
        if theme == "arcade":
            check("arcade : v4.7 « ON Y VA ? » puis « WOUAF !! » (unisexe)", "ON Y VA ?" in t1 and "WOUAF" in t2, (t1, t2))
        else:
            check("Noël : « HO HO HO… » puis « JOYEUX WOUAF ! » sous la neige", "HO HO HO" in t1 and "JOYEUX" in t2 and EV(P, "document.querySelectorAll('#surp .snow').length") > 10, (t1, t2))
        P.clock.run_for(2000)
        check(f"{theme} : court, puis ça disparaît", not on(P))
        check(f"{theme} : une seule fois par jour", EV(P, "__wouaf.surpOpenMaybe()") is False)
        # ---- retour de balade ----
        check(f"{theme} : balade de moins de 20 min : rien", EV(P, "__wouaf.surpBackMaybe({ min: 12, m: 900, cs: 0, streak: 1 })") is False)
        check(f"{theme} : balade express : rien", EV(P, "__wouaf.surpBackMaybe({ min: 25, m: 1500, cs: 0, streak: 1, express: true })") is False)
        check(f"{theme} : retour de balade : le grand spectacle", EV(P, f"__wouaf.surpBackMaybe({CTX})") and on(P))
        seen = []
        for _ in range(12):
            s, t = sc(P), txt(P)
            if s and (not seen or seen[-1][0] != s): seen.append((s, t))
            if not on(P): break
            P.clock.run_for(1500)
        ids = [x[0] for x in seen]; alltxt = " ".join(x[1] for x in seen)
        check(f"{theme} : enchaînement K.O. → résultats → combo → gain → demain", ids == ["ko", "res", "combo", "gain", "tease"], ids)
        check(f"{theme} : les vrais chiffres (3,4 km, 52 min, 5 rues, ×3, +120)", "3,4 KM" in alltxt and "52 MIN" in alltxt and "×3" in alltxt and "+120" in alltxt, alltxt[:300])
        if theme == "arcade":
            check("arcade : K.O. et COMBO ×4 ? pour demain", "K.O." in alltxt and "COMBO ×4" in alltxt, alltxt[:300])
        else:
            check("Noël : HO HO HO !, la hotte, la guirlande, les cadeaux sous le sapin, la case 4 demain", "HO HO HO !" in alltxt and "TA HOTTE" in alltxt and "GUIRLANDE" in alltxt and "SOUS LE SAPIN" in alltxt and "LA CASE 4" in alltxt, alltxt[:400])
        EV(P, f"__wouaf.surpBackMaybe({CTX})"); P.clock.run_for(500)
        EV(P, "document.querySelector('#surp .skip').click()")
        check(f"{theme} : un toucher et c'est passé", not on(P))
        # ---- pop-up du jour zappé ----
        jt0 = EV(P, "__wouaf.getGame().total || 0")
        EV(P, "localStorage.removeItem('wouaf-surp'); __wouaf.dailyPop()"); P.clock.run_for(1500)
        EV(P, "document.querySelector('#sheetX').click()"); P.clock.run_for(900)
        check(f"{theme} : v4.7 pop-up zappé : « Ah non… vraiment ? » et −1", "Ah non… vraiment ?" in txt(P) and "C'est pour Roxy." in txt(P) and "−1" in txt(P), txt(P))
        P.clock.run_for(3500)
        check(f"{theme} : v4.7 le clebsou du zappé est vraiment retiré", EV(P, "__wouaf.getGame().total || 0") == max(0, jt0 - 1), (jt0, EV(P, "__wouaf.getGame().total")))
        # ---- pop-up du jour bien lu ----
        tot0 = EV(P, "__wouaf.getGame().total || 0")
        EV(P, "__wouaf.dailyPop()")
        for _ in range(2):
            P.clock.run_for(4000); EV(P, "document.querySelector('#popNext').click()")
        P.clock.run_for(4000); EV(P, "document.querySelector('#popNext').click()"); P.clock.run_for(900)
        t = txt(P)
        if theme == "arcade":
            check("arcade : pop-up bien lu : « BIEN LU ! » sans pièce", "BIEN" in t and "LU !" in t and "+10" not in t, t)
        else:
            check("Noël : pop-up bien lu : « LUTIN MODÈLE ! » sans pièce", "LUTIN" in t and "MODÈLE" in t and "+10" not in t, t)
        check(f"{theme} : v4.7 bien lu = 0 clebsou", EV(P, "__wouaf.getGame().total || 0") == tot0, (tot0, EV(P, "__wouaf.getGame().total")))
        b.close()
    # ---- v4.5.4 : Superviseur › Voir les surprises ----
    b, c, P = new_phone(pw, errors=errs, init=INIT); P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 2500)
    P.wait_for_timeout(3000)
    EV(P, "__wouaf.sheetSurprises()"); P.wait_for_timeout(400)
    check("v4.5.4 : fiche « Voir les surprises » : 8 boutons (arcade + Noël)", P.locator("#sheet [data-sp]").count() == 8)
    tot0 = EV(P, "__wouaf.getGame().total || 0")
    P.click("#sheet [data-sp='back'][data-th='xmas']"); P.wait_for_timeout(1200)
    check("v4.5.4 : le retour de balade de Noël se joue", on(P) and "HO HO HO" in txt(P), txt(P))
    EV(P, "document.querySelector('#surp .skip').click()"); P.wait_for_timeout(700)
    check("v4.5.4 : à la fin, on revient à la fiche des surprises", "Les surprises" in EV(P, "document.querySelector('#sheet').innerText"))
    P.click("#sheet [data-sp='read'][data-th='arcade']"); P.wait_for_timeout(900)
    check("v4.5.4 : « BIEN LU ! » en aperçu", "BIEN" in txt(P))
    EV(P, "document.querySelector('#surp .skip').click()"); P.wait_for_timeout(600)
    check("v4.5.4 : l'aperçu ne donne pas de clebsous", EV(P, "__wouaf.getGame().total || 0") == tot0)
    b.close()
    check("aucune erreur JavaScript", not errs, errs[:3])
print("\n" + ("Tout est vert ✅" if not FAILS else f"{len(FAILS)} échec(s)"))
sys.exit(1 if FAILS else 0)
