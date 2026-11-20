"""Éric déjà choisi AVANT la 2.0 (pas de jeton) : le téléphone réclame Éric tout seul, sans code.
Autre téléphone (ou Safari au lieu de l'icône) : bouton « C'est mon téléphone » avec le code une fois."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','42');localStorage.setItem('wouaf-welcome2','0');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Éric'}));}"
local_api("GET", "/__wipe")
errs = []
with sync_playwright() as pw:
    bA, cA, A = new_phone(pw, errors=errs, init=INIT); open_app(A, 7000)
    check("Éric choisi avant la 2.0 : jeton récupéré tout seul à l'ouverture", bool(A.evaluate("__wouaf.supToken()")))
    A.evaluate("__wouaf.openMenu()"); A.click("#muSupAll"); A.wait_for_timeout(300); t = A.evaluate("document.querySelector('#sheet').innerText")
    check("menu superviseur complet, sans code", "Tableau de bord" in t and "Tout remettre à zéro" in t, t[:200])
    bB, cB, B = new_phone(pw, errors=errs, init=INIT); open_app(B, 7000)
    check("2e téléphone « Éric » : pas de jeton", not B.evaluate("__wouaf.supToken()"))
    B.evaluate("__wouaf.openMenu()"); B.click("#muSup"); B.wait_for_timeout(1200)
    check("2e téléphone : bouton « C'est mon téléphone »", B.locator("#supMine").count() == 1)
    B.fill("#supCode", "0000"); B.click("#supMine"); B.wait_for_timeout(800)
    check("mauvais code refusé", "incorrect" in B.evaluate("document.querySelector('#supMsg').textContent"))
    B.fill("#supCode", "1234"); B.click("#supMine"); B.wait_for_timeout(1200)
    check("bon code : ce téléphone devient le superviseur", bool(B.evaluate("__wouaf.supToken()")) and "Superviseur" in B.evaluate("document.querySelector('#sheet').innerText"))
    r = local_api("POST", "/dash", json.dumps({"token": A.evaluate("__wouaf.supToken()")}).encode())
    check("v4.4 : l'ancien téléphone reste connecté", r[0] == 200 if isinstance(r, tuple) else True, r)
    # 📱 Superviseur › Téléphones connectés : 2 téléphones, puis « déconnecter les autres » depuis B
    B.evaluate("document.querySelector('#sheetX') && document.querySelector('#sheetX').click()"); B.wait_for_timeout(300)
    B.evaluate("__wouaf.sheetSupMenu()"); B.wait_for_timeout(300)
    check("menu superviseur : entrée Téléphones connectés", B.evaluate("!!document.querySelector('#muSupF')"))
    B.click("#muSupF"); B.wait_for_timeout(1000)
    if True:
        check("fiche : 2 téléphones connectés", "2 téléphones" in B.evaluate("document.querySelector('#sheet').innerText"))
        B.click("#spOnly"); B.click("#spOnly"); B.wait_for_timeout(800)
        check("fiche : seul ce téléphone reste", "Seul" in B.evaluate("document.querySelector('#sheet').innerText"))
        r = local_api("POST", "/dash", json.dumps({"token": A.evaluate("__wouaf.supToken()")}).encode())
        check("l'autre téléphone est déconnecté", r[0] == 403 if isinstance(r, tuple) else True, r)
    # 3e téléphone : tape « Éric » → refusé → champ code dans la même fiche
    bC, cC, C = new_phone(pw, errors=errs, init="localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','42');")
    C.emulate_media(color_scheme="dark"); open_app(C, 2000)
    C.evaluate("__wouaf.askProfile()"); C.fill("#wName", "Éric")
    col = C.evaluate("(()=>{const s=getComputedStyle(document.querySelector('#wName'));return [s.color,s.backgroundColor]})()")
    check("mode sombre : le prénom se voit (texte clair sur fond foncé)", col[0] != col[1] and col[1] != "rgb(255, 255, 255)", col)
    C.click("#whoForm button[type=submit]"); C.wait_for_timeout(1000)
    check("prénom Éric pris : le champ code apparaît", C.evaluate("!document.querySelector('#whoSup').hidden"))
    C.fill("#wCode", "1234"); C.click("#wCodeGo"); C.wait_for_timeout(1200)
    check("bon code : ce téléphone devient Éric superviseur", bool(C.evaluate("__wouaf.supToken()")) and C.evaluate("JSON.parse(localStorage.getItem('wouaf-profil')).walker") == "Éric")
    check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
