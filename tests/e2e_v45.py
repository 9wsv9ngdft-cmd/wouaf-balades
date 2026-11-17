"""v45 : 📷 Photo bien visible en bas pendant la balade, mode poche « glisse la patte » (plus de double toucher),
consigne « groupe WhatsApp Roxy » au moment d'envoyer le récap."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','45');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
WALK = """async (minutes) => {
  const W = window.__wouaf, now = Date.now(), t0 = now - minutes*60000, track = [];
  const g = W.getGame(); g.home = {lat:48.8566, lon:2.3522};
  for (let i = 0; i <= 20; i++) track.push({ lat: 48.8566 + i*0.0003, lon: 2.3522, t: t0 + i*(minutes*60000)/20 });
  const gw = { needs:{p:0,c:0}, items:[], got:{b:1,t:0,f:0,s:0}, itemPts:1, cells:[], newCells:1, acc:0, next:9999, treasure:false, last:null, validTold: minutes >= 20 };
  await W.startWalk({ type:'free', line:[], m:0, min:45, cat:'free', via:[], _title:'Balade libre', _icon:'🚶' },
    { t0, track, walked:1200, home:{lat:48.8566,lon:2.3522}, maxAway:0, gw, saved: now, pausedMs:0 });
  W.onFix({ coords:{ latitude: 48.8566 + 20*0.0003, longitude: 2.3522, accuracy: 8 } });
}"""
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")
    P.evaluate(WALK, 25); P.wait_for_timeout(600)
    # 📷
    check("3 gros boutons en bas : Photo, Poche, Fini", all(P.locator(x).is_visible() for x in ("#camBtn", "#pocketBtn", "#stop")))
    bx = [P.locator(x).bounding_box() for x in ("#camBtn", "#pocketBtn", "#stop")]
    check("les 3 boutons tiennent sur une ligne, assez grands (≥ 90 px)", all(abs(x["y"] - bx[0]["y"]) < 2 and x["width"] >= 90 for x in bx), bx)
    with P.expect_file_chooser(timeout=3000) as fc:
        P.click("#camBtn")
    check("📷 Photo ouvre l'appareil photo", fc.value is not None)
    # 🌙
    P.click("#pocketBtn"); P.wait_for_timeout(300)
    check("mode poche ouvert", P.locator("#pocket").is_visible())
    P.mouse.click(200, 300); P.wait_for_timeout(100); P.mouse.click(200, 300); P.wait_for_timeout(100); P.mouse.click(200, 300); P.wait_for_timeout(500)
    check("des touchers (double, triple) ne font plus sortir du mode poche", P.locator("#pocket").is_visible())
    k = P.locator("#pkKnob").bounding_box(); tr = P.locator("#pkSlide").bounding_box()
    P.mouse.move(k["x"] + 20, k["y"] + 20); P.mouse.down(); P.mouse.move(k["x"] + 80, k["y"] + 20, steps=5); P.mouse.up(); P.wait_for_timeout(400)
    check("glisser à moitié : on reste en mode poche (la patte revient)", P.locator("#pocket").is_visible())
    P.mouse.move(k["x"] + 20, k["y"] + 20); P.mouse.down(); P.mouse.move(tr["x"] + tr["width"] + 10, k["y"] + 20, steps=10); P.mouse.up(); P.wait_for_timeout(400)
    check("glisser la patte jusqu'au bout : retour à la balade", not P.locator("#pocket").is_visible())
    check("la balade continue", P.evaluate("!!__wouaf.state.walk"))
    # 📲
    P.evaluate("__wouaf.stopWalk()"); P.wait_for_timeout(1500)
    t = P.evaluate("document.querySelector('#sheet').innerText")
    check("récap : consigne « choisis le groupe Roxy »", "choisis le groupe" in t and "« Roxy »" in t, t[-300:])
    check("bouton « Envoyer au groupe « Roxy » »", "groupe « Roxy »" in P.inner_text("#sendRecap"))
    hint = P.locator(".waHint").bounding_box(); btn = P.locator("#sendRecap").bounding_box()
    check("la consigne est juste au-dessus du bouton, bien visible", hint and btn and 0 <= btn["y"] - (hint["y"] + hint["height"]) < 30 and hint["y"] > 0, (hint, btn))
    P.screenshot(path="/tmp/v45-recap.png")
    b.close()
real = [x for x in errs if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
