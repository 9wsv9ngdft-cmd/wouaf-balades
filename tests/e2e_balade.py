"""v2.4 : écran de balade « la carte d'abord » (missions, trésor au bord, Roxy cliquable, flair, Fini en appui long, barre discrète)."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','42');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
WALK = """async (minutes) => {
  const W = window.__wouaf, now = Date.now(), t0 = now - minutes*60000, track = [];
  const g = W.getGame(); g.home = {lat:48.8566, lon:2.3522};
  for (let i = 0; i <= 20; i++) track.push({ lat: 48.8566 + i*0.0003, lon: 2.3522, t: t0 + i*(minutes*60000)/20 });
  try{ W.weekHunt(); }catch(e){}
  const gw = { needs:{p:0,c:0}, items:[], got:{b:1,t:0,f:0,s:0}, itemPts:1, cells:[], newCells:1, acc:0, next:9999, treasure:true, last:null, validTold: minutes >= 20 };
  await W.startWalk({ type:'free', line:[], m:0, min:45, cat:'free', via:[], _title:'Balade libre', _icon:'🚶' },
    { t0, track, walked:1200, home:{lat:48.8566,lon:2.3522}, maxAway:0, gw, saved: now, pausedMs:0 });
  W.onFix({ coords:{ latitude: 48.8566 + 20*0.0003, longitude: 2.3522, accuracy: 8 } });
}"""
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")
    P.evaluate(WALK, 12); P.wait_for_timeout(600)
    ch = P.evaluate("document.querySelector('#wChips').innerText")
    check("missions en haut : objets, rues neuves, photo", "objets" in ch and "rues neuves" in ch and "photo" in ch, ch)
    check("plus de compte à rebours « minimum dans »", "minimum dans" not in P.evaluate("document.querySelector('#walkbar').innerText"))
    check("gros chiffres : clebsous et temps", "+" in P.evaluate("document.querySelector('#wGain').innerText") and "12 min" in P.evaluate("document.querySelector('#wTime').innerText"))
    check("gros boutons visibles : Photo, Poche et Fini", P.locator("#camBtn").is_visible() and P.locator("#pocketBtn").is_visible() and P.locator("#stop").is_visible() and not P.locator("#photoBtn").is_visible() and not P.locator("#needP").is_visible())
    check("flèche du trésor au bord de l'écran", not P.evaluate("document.querySelector('#wTreasure').hidden") and "km" in P.evaluate("document.querySelector('#wTreasure').innerText"), P.evaluate("document.querySelector('#wTreasure').innerText"))
    P.evaluate("__wouaf.openRoxyMenu()"); P.wait_for_timeout(200)
    check("toucher Roxy : Pipi, Caca, Photo, Plus", P.locator("#roxyMenu").is_visible() and "Pipi" in P.evaluate("document.querySelector('#roxyMenu').innerText"))
    P.click("#rmP"); P.wait_for_timeout(200)
    check("pipi noté depuis la bulle de Roxy", P.evaluate("__wouaf.getGw().needs.p") == 1)
    check("le serveur sait seulement que la balade est en cours (heure, pas de position)", "léa" in str(kv().get("live", "")) and "lat" not in str(kv().get("live", "")), kv().get("live"))
    # flair
    P.evaluate("__wouaf.spawnTrail()"); P.wait_for_timeout(1200)
    check("flair : bandeau violet avec le temps restant", "piste fraîche" in P.evaluate("document.querySelector('#wFlair').innerText") and not P.evaluate("document.querySelector('#wFlair').hidden"))
    tr = P.evaluate("__wouaf.getGw().trail")
    pts0 = P.evaluate("__wouaf.getGw().itemPts")
    P.evaluate("t => __wouaf.onFix({ coords:{ latitude: t.lat, longitude: t.lon, accuracy: 8 } })", tr); P.wait_for_timeout(300)
    check("piste attrapée : +5", P.evaluate("__wouaf.getGw().itemPts") - pts0 >= 5 and P.evaluate("__wouaf.getGw().trail") is None)
    check("le bandeau disparaît", P.evaluate("document.querySelector('#wFlair').hidden"))
    P.evaluate("__wouaf.spawnTrail(); __wouaf.getGw().trail.until = Date.now() - 1; __wouaf.flairTick()"); P.wait_for_timeout(300)
    check("piste ratée : elle s'envole", P.evaluate("__wouaf.getGw().trail") is None)
    # barre discrète
    P.wait_for_timeout(10600)
    banner = not P.evaluate("document.querySelector('#walkBanner').hidden")
    check("après 10 s sans toucher, la barre se réduit", banner or P.evaluate("document.querySelector('#walkbar').classList.contains('mini')"))
    P.evaluate("document.querySelector('#walkbar').dispatchEvent(new PointerEvent('pointerdown', {bubbles:true}))"); P.wait_for_timeout(100)
    check("un toucher la rouvre", not P.evaluate("document.querySelector('#walkbar').classList.contains('mini')"))
    # Fini en appui long
    box = P.locator("#stop").bounding_box(); x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    P.mouse.move(x, y); P.mouse.down(); P.wait_for_timeout(300); P.mouse.up(); P.wait_for_timeout(300)
    check("appui court sur Fini : la balade continue + bulle d'aide", P.evaluate("document.body.classList.contains('walking')") and "Garde le doigt" in P.evaluate("document.querySelector('#coach').innerText"))
    P.mouse.move(x, y); P.mouse.down(); P.wait_for_timeout(1300); P.mouse.up(); P.wait_for_timeout(900)
    check("appui long sur Fini : la balade se termine", not P.evaluate("document.body.classList.contains('walking')"))
    check("le serveur ne garde pas la balade « en cours »", "léa" not in str(kv().get("live", "")), kv().get("live"))
    # balade trop courte : pas de « Bravo »
    if P.evaluate("document.querySelector('#modal').classList.contains('open')"): P.click("#sheetX"); P.wait_for_timeout(500)
    P.evaluate(WALK, 1); P.wait_for_timeout(400)
    P.evaluate("__wouaf.stopWalk()"); P.wait_for_timeout(800)
    check("balade de 1 min : pas de « Bravo » en bas de l'accueil", "Bravo" not in P.evaluate("document.querySelector('#status').innerText"))
    check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
