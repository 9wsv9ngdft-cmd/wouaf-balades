"""Écran « Nouveau dans la version » (un seul écran, une fois) et tuto court de 3 écrans (le complet reste dans le menu)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
txt = lambda p: p.evaluate("document.querySelector('#sheet').innerText")
local_api("GET", "/__wipe")
errs = []
with sync_playwright() as pw:
    # téléphone déjà utilisé, version précédente vue = 33
    b, c, A = new_phone(pw, errors=errs, init="if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','33');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}")
    open_app(A, 3500)
    t = txt(A)
    check("mise à jour : « Nouveau dans la version » dans la fenêtre unique", "Nouveau dans la version" in t and A.locator("#dgNext").count() == 1, t[:150])
    check("une seule fenêtre, pas de cartes à faire défiler", A.locator("#dg").count() == 0)
    A.click("#dgNext"); A.wait_for_timeout(600)
    A.reload(); A.wait_for_timeout(3500)
    check("une seule fois par téléphone", "Nouveau dans la version" not in (txt(A) if A.evaluate("document.querySelector('#modal').classList.contains('open')") else ""))
    # téléphone neuf : tuto court
    b2, c2, B = new_phone(pw, errors=errs, init="localStorage.setItem('wouaf-init','1');")
    open_app(B, 2500)
    check("1er lancement : tuto court qui commence par « Voici Roxy »", "Voici Roxy" in txt(B), txt(B)[:80])
    n = B.evaluate("document.querySelector('.dotsT').textContent.length")
    check("tuto court = 3 écrans", n == 3, n)
    B.click("#tutoSkip"); B.wait_for_timeout(800)
    if B.locator("#wName").count(): B.fill("#wName", "Tom"); B.click("#whoForm button[type=submit]"); B.wait_for_timeout(800)
    B.evaluate("__wouaf.openMenu()"); B.click("#muTuto"); B.wait_for_timeout(500)
    n = B.evaluate("document.querySelector('.dotsT').textContent.length")
    check("menu ☰ › Tuto : tuto complet (8 écrans)", n == 8, n)
    # 📈 choix des statistiques au démarrage, avec le rappel de ce qui reste privé
    b3, c3, Cc = new_phone(pw, errors=errs, init="if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','37');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Zoé'}));}")
    open_app(Cc, 4000); t = txt(Cc)
    check("démarrage : choix des statistiques + rappel « privé »", "améliorer l'app" in t and "reste privé" in t and Cc.locator("[data-st]").count() == 2, t[:300])
    check("démarrage : carte « Sors Roxy en un seul geste » avec « Je l'installe »", "un seul geste" in t and Cc.locator("[data-go='sc']").count() == 1, t[:400])
    Cc.click("[data-st='0']"); Cc.wait_for_timeout(300)
    check("Non merci : rien n'est compté", Cc.evaluate("localStorage.getItem('wouaf-stats-ok')") == "false" and Cc.evaluate("JSON.stringify(JSON.parse(localStorage.getItem('wouaf-usage')||'{}'))") == "{}")
    Cc.click("#dgNext"); Cc.wait_for_timeout(300); Cc.evaluate("__wouaf.openMenu()"); Cc.wait_for_timeout(200)
    check("menu : 🔒 Vie privée pour changer d'avis", "Vie privée" in txt(Cc))
    # v2.2 : accueil et menu sur un seul écran d'iPhone (393 × 760 utiles, mode sombre)
    Cc.evaluate("__wouaf.closeSheet ? __wouaf.closeSheet() : document.querySelector('#sheetX').click()"); Cc.wait_for_timeout(400)
    Cc.emulate_media(color_scheme="dark"); Cc.set_viewport_size({"width": 393, "height": 760}); Cc.wait_for_timeout(300)
    h = Cc.evaluate("[document.documentElement.scrollHeight, innerHeight]")
    check("accueil sans défilement (393 × 760)", h[0] <= h[1], h)
    check("gros lots en 3 tuiles", Cc.locator(".ltiles .lt").count() == 3)
    # v2.3 : Roxy parle et se laisse caresser
    say = lambda: Cc.evaluate("document.querySelector('#sayBtn') ? document.querySelector('#sayBtn').textContent : ''")
    s1 = say()
    check("bulle de Roxy : accueil « première balade » (aucune sortie)", "première balade" in s1, s1)
    Cc.click("#sayBtn"); Cc.wait_for_timeout(200)
    check("toucher la bulle : autre phrase", say() and say() != s1, say())
    r = Cc.locator("#heroDog").bounding_box(); x = r["x"] + r["width"] / 2; y = r["y"] + r["height"] / 2
    Cc.mouse.move(x - 15, y); Cc.mouse.down()
    for i in range(10): Cc.mouse.move(x - 15 + (i % 2) * 30, y + (i % 3) * 4); Cc.wait_for_timeout(40)
    nh = Cc.locator(".heart").count(); Cc.mouse.up(); Cc.wait_for_timeout(300)
    check("caresse : des cœurs, Roxy remue, une phrase contente", nh >= 2 and Cc.evaluate("document.querySelector('#heroDog').classList.contains('petted')"), nh)
    check("caresse : n'ouvre pas la fiche de Roxy", not Cc.evaluate("document.querySelector('#modal').classList.contains('open')"))
    import json as _j, time as _t
    e = int(_t.time()) - 3600
    local_api("POST", "/walk", _j.dumps({"walker": "Tom", "walk": {"s": e - 1800, "e": e, "min": 30, "m": 2000, "cs": 10}, "sum": {}}).encode())
    Cc.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); Cc.wait_for_timeout(1500); Cc.evaluate("__wouaf.renderHome && __wouaf.renderHome()"); Cc.wait_for_timeout(200)
    check("retour dans l'app : « Tom m'a sortie tout à l'heure »", "Tom m'a sortie" in say(), say())
    h = Cc.evaluate("[document.documentElement.scrollHeight, innerHeight]")
    check("accueil toujours sans défilement avec la bulle", h[0] <= h[1], h)
    Cc.evaluate("__wouaf.openMenu()"); Cc.wait_for_timeout(300)
    m = Cc.evaluate("(()=>{const s=document.querySelector('#sheet .sbody');return [s.scrollHeight,s.clientHeight]})()")
    check("menu sans défilement", m[0] <= m[1], m)
    check("menu : 4 tuiles, À propos", Cc.locator(".mgrid button").count() == 4 and "À propos" in txt(Cc))
    Cc.click("#muAbout"); Cc.wait_for_timeout(400)
    check("À propos : version et crédits OpenStreetMap", "Wouaf Balades, version" in txt(Cc) and "OpenStreetMap" in txt(Cc), txt(Cc)[:200])
    check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
