"""v52 (3.9.1) : rappel quand on oublie d'envoyer le récap au groupe WhatsApp « Roxy »."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
import datetime
_e = int(datetime.datetime.now().timestamp()) - 3 * 3600   # record du mois très long (Zoé) : pas de fenêtre « Nouveau record » pendant le test
local_api("POST", "/walk", json.dumps({"walker": "Zoé", "walk": {"s": _e - 14400, "e": _e, "min": 240, "m": 15000, "cs": 0}, "sum": {}}).encode())
# une vieille balade déjà au carnet (avant la mise à jour) : ne doit jamais déclencher de rappel
OLD = "[{id:1,date:new Date(Date.now()-3600e3*20).toISOString(),title:'Balade libre',min:30,m:2000,walker:'Léa',recap:{d:'hier',w:'Léa',s:Math.round(Date.now()/1000)-3600*21,e:Math.round(Date.now()/1000)-3600*20,m:2000}}]"
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','52');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-hon-vu','2099-01');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));localStorage.setItem('wouaf-carnet', JSON.stringify(" + OLD + "));}" \
       + "navigator.share = async (d) => { window.__shared = (window.__shared||0) + 1; window.__lastShare = d; };"
EV = lambda P, js: P.evaluate(js)
START = """async () => {
  const W = window.__wouaf, now = Date.now(), t0 = now - 30*60000, track = [];
  for (let i = 0; i <= 60; i++) track.push({ lat: 48.8566, lon: 2.3522 + i*0.00004, t: t0 + i*30000 });
  const gw = { needs:{p:0,c:0}, items:[], got:{b:0,t:0,f:0,s:0}, itemPts:0, cells:[], newCells:0, acc:0, next:99999, treasure:true, last:null, chest:false, hunt:0, rainChecked:true };
  await W.startWalk({ type:'free', line:[], m:0, min:30, cat:'free', via:[], _title:'Balade libre', _icon:'🚶' },
    { t0, track, walked:2400, home:{lat:48.8566,lon:2.3522}, maxAway:0, gw, saved: now, pausedMs:0 });
}"""
errs = []
open_ = lambda P: P.evaluate("document.querySelector('#modal').classList.contains('open')")
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 2500)
    check("carnet : la vieille balade est là", "wouaf-carnet" and EV(P, "__wouaf.getLog().length") >= 1, EV(P, "__wouaf.getLog().length"))
    check("pas de rappel pour les balades d'avant la mise à jour", EV(P, "__wouaf.unsentRecaps().length") == 0 and "Récap pas envoyé" not in (P.inner_text("#sheet") if open_(P) else ""))
    if open_(P) and P.locator("#dgNext").count(): P.click("#dgNext"); P.wait_for_timeout(300)
    # balade finie, on ferme le récap sans l'envoyer
    P.evaluate(START); P.wait_for_timeout(400); EV(P, "__wouaf.stopWalk()"); P.wait_for_timeout(1800)
    check("le récap est affiché", open_(P) and P.locator("#sendRecap").count() == 1)
    P.click("#closeRecap"); P.wait_for_timeout(900)
    t = P.inner_text("#sheet") if open_(P) else ""
    check("en fermant sans envoyer : « Tu as oublié le récap ! »", "oublié le récap" in t and P.locator("#nuSend").count() == 1, t[:120])
    P.click("#nuLater"); P.wait_for_timeout(700)
    check("« Plus tard » : la fenêtre ne revient pas tout de suite", not open_(P), P.inner_html("#sheet")[:600])
    check("la balade reste à rappeler", EV(P, "__wouaf.unsentRecaps().length") == 1)
    # réouverture de l'app : carte dans le « Quoi de neuf »
    EV(P, "__wouaf.startupDigest()"); P.wait_for_timeout(1500)
    t = P.inner_text("#sheet") if open_(P) else ""
    check("à l'ouverture : carte « Récap pas envoyé » avec un bouton Envoyer", "Récap pas envoyé" in t and P.locator("#sheet [data-us='0']").count() == 1, t[:200])
    P.click("#sheet [data-us='0']"); P.wait_for_timeout(800)
    check("Envoyer : le menu Partager s'ouvre avec le récap et le lien", EV(P, "window.__shared") == 1 and "#r=" in EV(P, "window.__lastShare.text"))
    check("le bouton passe à « ✓ Envoyé »", "Envoyé" in P.inner_text("#sheet [data-us='0']"))
    check("plus rien à rappeler", EV(P, "__wouaf.unsentRecaps().length") == 0)
    P.click("#dgNext"); P.wait_for_timeout(300)
    # 2e balade : envoyée directement depuis le récap → aucun rappel
    P.evaluate(START); P.wait_for_timeout(400); EV(P, "__wouaf.stopWalk()"); P.wait_for_timeout(1800)
    P.click("#sendRecap"); P.wait_for_timeout(600); P.click("#closeRecap"); P.wait_for_timeout(900)
    check("récap envoyé puis fermé : pas de rappel", not open_(P) and EV(P, "__wouaf.unsentRecaps().length") == 0)
    # 3e balade : « Pas besoin »
    P.evaluate(START); P.wait_for_timeout(400); EV(P, "__wouaf.stopWalk()"); P.wait_for_timeout(1800)
    P.click("#closeRecap"); P.wait_for_timeout(900); P.click("#nuLater"); P.wait_for_timeout(500)
    EV(P, "__wouaf.startupDigest()"); P.wait_for_timeout(1500)
    P.click("#sheet [data-us='no']"); P.wait_for_timeout(300)
    check("« Pas besoin » : plus de rappel", EV(P, "__wouaf.unsentRecaps().length") == 0)
    # 4e balade : une autre fenêtre s'ouvre juste après le récap → le rappel attend qu'elle se ferme
    P.evaluate(START); P.wait_for_timeout(400); EV(P, "__wouaf.stopWalk()"); P.wait_for_timeout(1800)
    P.click("#closeRecap"); P.evaluate("setTimeout(() => document.querySelector('#tabbar [data-t=moi]').click(), 50)"); P.wait_for_timeout(1200)
    check("une autre fenêtre est ouverte : pas de rappel par-dessus", "oublié le récap" not in P.inner_text("#sheet"))
    P.click("#sheetX"); P.wait_for_timeout(2200)
    check("elle se ferme : le rappel arrive", open_(P) and "oublié le récap" in P.inner_text("#sheet"), P.inner_text("#sheet")[:100] if open_(P) else "fermé")
    P.screenshot(path="/tmp/recap-oublie.png")
    b.close()
check("aucune erreur JavaScript", not errs, errs[:3])
print("\nTout est vert ✅" if not FAILS else "\nÉCHECS : " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
