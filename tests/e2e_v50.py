"""v50 (3.6) : GPS surveillé. Position refusée ou GPS muet → bandeau rouge ; « Fini » sur une longue balade à 0 m → avertissement."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','50');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
# faux GPS piloté par window.__geo.mode : 'deny' (refusé), 'silent' (rien), 'ok'
GEO = """(() => {
  window.__geo = { mode: 'deny' }; let id = 0; const W = {};
  const pos = () => ({ coords: { latitude: 48.8566 + Math.random() * 1e-4, longitude: 2.3522, accuracy: 10 } });
  const fire = () => { for (const k in W){ const w = W[k];
    if (__geo.mode === 'deny'){ if (w.e) w.e({ code: 1, message: 'denied' }); }
    else if (__geo.mode === 'ok') w.s(pos()); } };
  const g = navigator.geolocation;
  Object.defineProperty(g, 'watchPosition', { value: (s, e) => { const k = ++id; W[k] = { s, e }; setTimeout(fire, 50); return k; } });
  Object.defineProperty(g, 'clearWatch', { value: k => { delete W[k]; } });
  Object.defineProperty(g, 'getCurrentPosition', { value: (s, e) => setTimeout(() => { if (__geo.mode === 'ok') s(pos()); else if (e) e({ code: 1 }); }, 50) });
  window.__geoFire = fire;
  window.__shift = ms => { const d = Date.now.bind(Date), o = window.__off || 0; window.__off = o + ms; Date.now = () => d() + ms; };
})();"""
errs = []
banner = lambda P: P.evaluate("(() => { const b = document.querySelector('#walkBanner'); return b.hidden ? '' : b.dataset.kind + '|' + b.textContent; })()")
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT + GEO)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")
    check("version 3.6 (APP_NUM 50)", P.evaluate("document.querySelector('#homeFoot').textContent").find("3.6") >= 0, P.evaluate("document.querySelector('#homeFoot').textContent"))
    # 1) position refusée au départ
    P.click("#freeWalk"); P.wait_for_timeout(300); P.click("#chFree"); P.wait_for_timeout(800)
    bn = banner(P)
    check("position refusée : bandeau rouge tout de suite", bn.startswith("gps|") and "refusée" in bn, bn)
    check("bandeau rouge bien rouge", "gps" in P.get_attribute("#walkBanner", "class"))
    P.screenshot(path="/tmp/gps_denied.png")
    P.click("#wbB"); P.wait_for_timeout(400)
    t = P.inner_text("#sheet")
    check("« Comment faire » explique Autoriser / rouvrir l'app", "Autoriser" in t and "rouvre" in t, t[:200])
    P.screenshot(path="/tmp/gps_help.png")
    # 2) on autorise puis Réessayer : le bandeau part
    P.evaluate("__geo.mode = 'ok'"); P.click("#gpsRetry"); P.wait_for_timeout(600)
    check("après Autoriser + Réessayer : bandeau parti", banner(P) == "", banner(P))
    check("message « Roxy te voit »", "te voit" in P.evaluate("document.body.innerText"))
    # 3) le GPS se tait 2 min : bandeau « ne te voit plus »
    P.evaluate("__geo.mode = 'silent'; __shift(120000); __wouaf.gpsCheck()"); P.wait_for_timeout(200)
    bn = banner(P)
    check("GPS muet 2 min : bandeau « ne te voit plus »", bn.startswith("gps|") and "ne te voit plus" in bn, bn)
    # 4) un point revient : bandeau parti
    P.evaluate("__geo.mode = 'ok'; __geoFire()"); P.wait_for_timeout(300)
    check("le GPS revient : bandeau parti", banner(P) == "", banner(P))
    P.evaluate("__wouaf.cancelWalk()"); P.wait_for_timeout(500)
    # 5) longue balade sans aucune position : « Fini » prévient
    P.evaluate("__geo.mode = 'deny'"); P.click("#freeWalk"); P.wait_for_timeout(300); P.click("#chFree"); P.wait_for_timeout(800)
    P.evaluate("__shift(15 * 60000); __wouaf.finishWalk()"); P.wait_for_timeout(400)
    t = P.inner_text("#sheet")
    check("Fini à 0 m après 15 min : avertissement", "pas vu bouger" in t and "Terminer quand même" in t, t[:200])
    check("la balade continue tant qu'on n'a pas confirmé", P.evaluate("!!__wouaf.state.walk"))
    P.screenshot(path="/tmp/gps_finish.png")
    P.click("#fwStop"); P.wait_for_timeout(1200)
    check("« Terminer quand même » termine la balade", not P.evaluate("!!__wouaf.state.walk"))
    b.close()
    # 6) balade normale (GPS OK) : Fini termine sans question
    b2, c2, Q = new_phone(pw, errors=errs, init=INIT + GEO)
    Q.set_viewport_size({"width": 393, "height": 760}); open_app(Q, 3000)
    if Q.locator("#dgNext").count(): Q.click("#dgNext")
    Q.evaluate("__geo.mode = 'ok'"); Q.click("#freeWalk"); Q.wait_for_timeout(300); Q.click("#chFree"); Q.wait_for_timeout(800)
    check("GPS OK : pas de bandeau rouge", not banner(Q).startswith("gps"), banner(Q))
    Q.evaluate("__wouaf.gpsCheck()")
    check("GPS OK : gpsCheck ne dit rien", not banner(Q).startswith("gps"), banner(Q))
    Q.evaluate("__wouaf.finishWalk()"); Q.wait_for_timeout(1200)
    check("balade courte : Fini termine sans question", not Q.evaluate("!!__wouaf.state.walk"))
    b2.close()
real = [x for x in errs if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
