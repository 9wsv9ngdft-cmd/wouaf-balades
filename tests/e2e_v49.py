"""v49 : ☰ › Signaler un bug (icône coccinelle), liste des bugs côté superviseur avec « Réglé ✓ »."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','49');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")
    P.evaluate("__wouaf.openMenu()"); P.wait_for_timeout(300)
    check("le menu propose « Signaler un bug » avec l'icône dessinée", P.locator("#muBug svg.bugic").count() == 1)
    P.screenshot(path="/tmp/menu_bug.png")
    P.click("#muBug"); P.wait_for_timeout(500)
    P.click("#bugGo"); check("texte vide : message, rien d'envoyé", "quelques mots" in P.inner_text("#bugS"))
    P.fill("#bugT", "Le bouton Photo ne répond pas"); P.screenshot(path="/tmp/bug_form.png"); P.click("#bugGo"); P.wait_for_timeout(1000)
    check("envoyé : fiche fermée", not P.evaluate("document.querySelector('#modal').classList.contains('open')"))
    st, body = local_api("POST", "/bugs", json.dumps({"code": "1234"}).encode())
    l = json.loads(body).get("bugs", [])
    check("le serveur a reçu le bug de Léa", st == 200 and len(l) == 1 and l[0]["walker"] == "Léa" and l[0]["v"] == "3.5", body[:200])
    # Éric : liste + Réglé
    bE, cE, E = new_phone(pw, errors=errs, init=INIT.replace("'Léa'", "'Éric'")); E.set_viewport_size({"width": 393, "height": 760}); open_app(E, 6000)
    E.evaluate("__wouaf.openMenu()"); E.click("#muSupAll"); E.wait_for_timeout(300); E.click("#muSupB"); E.wait_for_timeout(1200)
    t = E.inner_text("#sheet")
    check("Éric voit le bug de Léa", "Léa" in t and "bouton Photo" in t and "1 à regarder" in t, t[:200])
    E.screenshot(path="/tmp/bug_list.png")
    E.click("[data-done]"); E.wait_for_timeout(800)
    check("Réglé ✓ : passe en « réglé »", "0 à regarder" in E.inner_text("#sheet"), E.inner_text("#sheet")[:120])
    b.close(); bE.close()
real = [x for x in errs if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
