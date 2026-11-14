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
    check("mise à jour : écran « Nouveau dans la version »", "Nouveau dans la version" in t and A.locator("#nwOk").count() == 1, t[:150])
    check("écran seul (pas de cartes à faire défiler)", A.locator("#dg").count() == 0)
    A.click("#nwOk"); A.wait_for_timeout(600)
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
    check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
