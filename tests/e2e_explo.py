"""🧭 Classement des explorateurs (v2.3) : carte sur l'accueil, fiche podium, annonce du lundi, couronne 👑 chez le premier de la semaine passée."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
now = int(time.time())
def walk(w, e, nc, ob, mn=30):
    local_api("POST", "/walk", json.dumps({"walker": w, "walk": {"s": e - mn * 60, "e": e, "min": mn, "m": 2000, "cs": 50, "nc": nc, "ob": ob}, "sum": {"cs": 100}}).encode())
walk("Tom", now - 3600, 8, 6); walk("Léa", now - 7200, 5, 4); walk("Zoé", now - 9000, 2, 1)
walk("Léa", now - 8 * 86400, 9, 9); walk("Tom", now - 8 * 86400 - 3600, 3, 2)
INIT = lambda w: "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','41');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'%s'}));}" % w
txt = lambda p: p.evaluate("document.querySelector('#sheet').innerText")
errs = []
with sync_playwright() as pw:
    b, c, L = new_phone(pw, errors=errs, init=INIT("Léa"))
    L.emulate_media(color_scheme="dark"); L.set_viewport_size({"width": 393, "height": 760})
    open_app(L, 3500)
    t = txt(L)
    check("Léa (1re la semaine passée) : « Tu es l'explorateur de la semaine ! »", "Tu es l'explorateur de la semaine" in t, t[:300])
    L.click("#dgNext"); L.wait_for_timeout(500)
    check("Léa : la couronne 👑 sur Roxy", "👑" in L.evaluate("document.querySelector('#heroDog').innerHTML"))
    check("accueil : la vraie couronne (pas fantôme) sur la photo", L.evaluate("document.querySelector('#crownBtn').classList.contains('real')"))
    check("Léa 2e cette semaine : la 👑 pulse dans le bouton", not L.evaluate("document.querySelector('#goCrown').hidden"))
    check("accueil sans défilement", L.evaluate("document.documentElement.scrollHeight <= innerHeight"))
    L.click("#crownBtn"); L.wait_for_timeout(400); t = txt(L)
    check("toucher la couronne : podium Tom, Toi, Zoé sans chiffres", "Tom" in t and "Toi" in t and "Zoé" in t, t[:300])
    check("fiche : podium, la couronne pour le 1er, tout repart le lundi", "Les explorateurs" in t and "couronne" in t and "lundi" in t and L.locator(".podium .step").count() == 3, t[:300])
    L.reload(); L.wait_for_timeout(3000)
    check("l'annonce du lundi ne revient pas", "explorateur de la semaine" not in (txt(L) if L.evaluate("document.querySelector('#modal').classList.contains('open')") else ""))
    b2, c2, T = new_phone(pw, errors=errs, init=INIT("Tom"))
    T.set_viewport_size({"width": 393, "height": 760}); open_app(T, 3500); t = txt(T)
    check("Tom : « Léa est l'explorateur de la semaine ! » avec sa place", "Léa est l'explorateur" in t and "🥈" in t, t[:300])
    T.click("#dgNext"); T.wait_for_timeout(400)
    check("Tom : pas de couronne", "👑" not in T.evaluate("document.querySelector('#heroDog').innerHTML"))
    check("Tom : couronne fantôme ; 1er cette semaine donc pas de 👑 qui pulse", T.evaluate("document.querySelector('#crownBtn').classList.contains('ghost') && document.querySelector('#goCrown').hidden"))
    T.evaluate("__wouaf.openMenu()"); T.wait_for_timeout(300); T.click("#muToday"); T.wait_for_timeout(300)
    check("menu : 📋 Missions du jour", "Aujourd" in txt(T), txt(T)[:100])
    check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
