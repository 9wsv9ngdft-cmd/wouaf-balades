"""v4.5.5 (lot 1, Éric le 20/11 au soir) : classement qui s'ouvre tout de suite, tuile « Défier », onglets allégés, menu allégé, diagnostic d'écran du superviseur."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
def init(who): return ("if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','58');"
    "localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-hon-vu','2099-01');localStorage.setItem('wouaf-wa-sent','[]');"
    "localStorage.setItem('wouaf-welcome2','0');localStorage.setItem('wouaf-surp', JSON.stringify({ o:'2099-01-01' }));localStorage.setItem('wouaf-profil', JSON.stringify({walker:'%s'}));}" % who)
EV = lambda P, js: P.evaluate(js)
is_open = lambda P: P.evaluate("document.querySelector('#modal').classList.contains('open')")
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=init("Léa"))
    c.route(API_HOST + "/honors", lambda r: None)   # le serveur ne répond pas (réseau lent) : la fiche doit s'ouvrir quand même
    P.emulate_media(color_scheme="dark"); P.set_viewport_size({"width": 393, "height": 852}); open_app(P, 2500)
    rt = P.inner_text("[data-lot='rank']")
    check("tuile classement : « ⚔️ DÉFIER », plus « EN DIRECT »", "DÉFIER" in rt and "EN DIRECT" not in rt, rt)
    P.click("[data-lot='rank']"); P.wait_for_timeout(400)
    check("toucher le classement : la fiche s'ouvre tout de suite, même si le serveur ne répond pas", is_open(P) and "Le classement" in P.inner_text("#sheet"), P.inner_text("#sheet")[:100] if is_open(P) else "fermée")
    tabs = P.locator("#sheet [data-rt]").all_inner_texts()
    check("onglets : Semaine · Mois · Année · Rigolo", tabs == ["Semaine", "Mois", "Année", "😂 Rigolo"], tabs)
    for k in ["month", "year", "fun"]:
        P.click(f"#sheet [data-rt='{k}']"); P.wait_for_timeout(250)
    check("les onglets s'ouvrent sans réponse du serveur", "Le classement" in P.inner_text("#sheet"))
    EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(300)
    EV(P, "__wouaf.openMenu()"); P.wait_for_timeout(400)
    m = P.inner_text("#sheet")
    check("menu : plus de Tirelire, Duels, Exploration ni Palmarès", all(P.locator(x).count() == 0 for x in ("#muMoney", "#muDuel", "#muFog", "#muHon")), m[:300])
    check("menu : on garde Progrès, Dernières sorties, Carnet, Album, Événements, Bug", all(P.locator(x).count() == 1 for x in ("#muProg", "#muOuts", "#muLog", "#muAlbum", "#muEvt", "#muBug")))
    check("menu : Réglages en bas (Sons, Raccourci, Compte)", all(P.locator(x).count() == 1 for x in ("#muSon", "#muShort", "#muWho")))
    P.click("#muProg"); P.wait_for_timeout(400)
    check("menu › Progrès s'ouvre", "page" in EV(P, "document.body.className"))
    check("pas de diagnostic d'écran pour un promeneur", P.locator("#scrDiag").count() == 0)
    P.screenshot(path="/tmp/lot1-lea.png")
    b.close()
    # ---- Éric : le diagnostic d'écran ----
    import json
    tok = json.loads(local_api("POST", "/claim", json.dumps({"walker": "Éric"}).encode())[1])["token"]
    b, c, E = new_phone(pw, errors=errs, init=init("Éric") + f"if(!localStorage.getItem('wouaf-sup')) localStorage.setItem('wouaf-sup', JSON.stringify('{tok}'));")
    E.set_viewport_size({"width": 393, "height": 852}); open_app(E, 2500)
    check("Éric : jeton superviseur", bool(EV(E, "__wouaf.supToken()")))
    EV(E, "__wouaf.screenDiag()"); E.wait_for_timeout(600)
    d = E.inner_text("#scrDiag") if E.locator("#scrDiag").count() else ""
    check("Éric : diagnostic visible (hauteurs, zones sûres, carte)", "inner" in d and "zones sûres" in d and "carte" in d, d)
    check("le diagnostic ne bloque pas les touchers", EV(E, "getComputedStyle(document.querySelector('#scrDiag')).pointerEvents") == "none")
    E.set_viewport_size({"width": 393, "height": 800}); E.wait_for_timeout(700)
    check("le diagnostic note quand l'écran change", "a changé à" in E.inner_text("#scrDiag"), E.inner_text("#scrDiag"))
    E.screenshot(path="/tmp/lot1-eric.png")
    EV(E, "__wouaf.sheetSupMenu()"); E.wait_for_timeout(300)
    check("Superviseur › 📏 Diagnostic de l'écran", "Diagnostic de l'écran" in E.inner_text("#sheet"))
    E.click("#muSupH"); E.wait_for_timeout(300)
    check("on peut le couper", not EV(E, "__wouaf.diagOn()"))
    b.close()
check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
