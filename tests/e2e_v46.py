"""v46 : anti-oubli. Immobile depuis 12 min → « La balade est finie ? » ; terminer coupe la balade au moment où on s'est arrêté ;
« Je continue » laisse tranquille ; balade reprise après une longue absence → question tout de suite ; promeneur qui marche → aucune question."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','46');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Mamie'}));}"
# move = minutes de marche (en ligne droite), still = minutes immobile ensuite (petits mouvements de GPS sur place)
WALK = """async ({move, still, saved}) => {
  const W = window.__wouaf, now = Date.now(), t0 = now - (move + still + (saved || 0)) * 60000, track = [];
  const g = W.getGame(); g.home = {lat:48.8566, lon:2.3522};
  for (let i = 0; i <= move; i++) track.push({ lat: 48.8566 + i*0.0007, lon: 2.3522, t: t0 + i*60000, a: 10 });
  const end = track[track.length - 1];
  for (let i = 1; i <= still; i++) track.push({ lat: end.lat + (i % 2 ? 0.0002 : -0.0001), lon: end.lon + (i % 3 ? 0.0001 : 0), t: end.t + i*60000, a: 15 });
  const gw = { needs:{p:0,c:0}, items:[], got:{b:0,t:0,f:0,s:0}, itemPts:0, cells:[], newCells:0, acc:0, next:9999, treasure:false, last:null, validTold:true };
  await W.startWalk({ type:'free', line:[], m:0, min:30, cat:'free', via:[], _title:'Balade libre', _icon:'🚶' },
    { t0, track, walked: move*75, home:{lat:48.8566,lon:2.3522}, maxAway:0, gw, saved: saved ? now - saved*60000 : now, pausedMs:0 });
}"""
banner = lambda P: (not P.evaluate("document.querySelector('#walkBanner').hidden")) and P.evaluate("document.querySelector('#wbText').innerText") or ""
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")

    # 1. on marche encore : aucune question
    P.evaluate(WALK, {"move": 25, "still": 2, "saved": 0}); P.wait_for_timeout(800)
    P.evaluate("__wouaf.checkForgot()"); P.wait_for_timeout(300)
    check("on marche : pas de question « balade finie ? »", "bouges plus" not in banner(P), banner(P))
    P.evaluate("__wouaf.cancelWalk()"); P.wait_for_timeout(500)

    # 2. 20 min de marche puis 15 min immobile (à la maison) : question, puis « Oui, terminer » coupe la balade
    P.evaluate(WALK, {"move": 20, "still": 15, "saved": 0}); P.wait_for_timeout(800)
    P.evaluate("__wouaf.checkForgot()"); P.wait_for_timeout(300)
    t = banner(P)
    check("immobile 15 min : « Tu ne bouges plus… La balade est finie ? »", "bouges plus" in t and "finie" in t, t)
    check("compte à rebours avant l'arrêt automatique", "Fin dans 3 min" in t, t)
    check("boutons « Oui, terminer » / « Je continue »", "terminer" in P.inner_text("#wbA") and "continue" in P.inner_text("#wbB"))
    P.click("#wbA"); P.wait_for_timeout(1500)
    log = P.evaluate("__wouaf.getLog()")
    m = log[0]["min"] if log else None
    check("balade coupée quand on s'est arrêté (~21 min, pas 35)", m is not None and 19 <= m <= 23, m)
    check("message : le temps immobile ne compte pas", "temps immobile ne compte pas" in P.evaluate("document.body.innerText"))
    if P.evaluate("document.querySelector('#modal').classList.contains('open')"): P.click("#sheetX"); P.wait_for_timeout(400)

    # 3. « Je continue » : plus de question tout de suite
    P.evaluate(WALK, {"move": 20, "still": 15, "saved": 0}); P.wait_for_timeout(800)
    P.evaluate("__wouaf.checkForgot()"); P.wait_for_timeout(300)
    P.click("#wbB"); P.wait_for_timeout(300)
    P.evaluate("__wouaf.checkForgot()"); P.wait_for_timeout(300)
    check("« Je continue » : la balade continue, plus de question", P.evaluate("!!__wouaf.state.walk") and P.evaluate("document.querySelector('#walkBanner').hidden"))
    P.evaluate("__wouaf.cancelWalk()"); P.wait_for_timeout(500)

    # 4. balade relancée puis oubliée : l'app est rouverte 1 h plus tard → question dès la reprise
    P.evaluate(WALK, {"move": 3, "still": 0, "saved": 60}); P.wait_for_timeout(1000)
    t = banner(P)
    check("reprise après 1 h sans bouger : question dès l'ouverture", "bouges plus" in t, t)
    P.click("#wbA"); P.wait_for_timeout(1500)
    log = P.evaluate("__wouaf.getLog()")
    check("balade oubliée : pas notée comme une balade d'1 h (trop courte)", log and log[0]["min"] < 10, [x.get("min") for x in log])
    b.close()
real = [x for x in errs if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
