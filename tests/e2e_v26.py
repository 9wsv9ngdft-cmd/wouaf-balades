"""v2.6 « Croquette » : rappels de soin, copains, repères pipi/caca, carte de chaleur, sons, paie à la semaine, nuages, heures de cours, chiffres, lisibilité."""
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
sheet = lambda p: p.evaluate("document.querySelector('#sheet').innerText")
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")
    # --- balade de 50 min : pipi, copain pendant la balade, fin
    P.evaluate(WALK, 50); P.wait_for_timeout(600)
    P.evaluate("__wouaf.openRoxyMenu()"); P.wait_for_timeout(200)
    check("menu de Roxy : bouton 🐕 Copain", "Copain" in P.evaluate("document.querySelector('#roxyMenu').innerText"))
    P.click("#rmP"); P.wait_for_timeout(200)
    P.evaluate("__wouaf.openRoxyMenu()"); P.wait_for_timeout(200); P.click("#rmD"); P.wait_for_timeout(300)
    P.fill("#copN", "Filou"); P.click("#copF button[type=submit]"); P.wait_for_timeout(300)
    check("copain ajouté pendant la balade", any(x["n"] == "Filou" and x["c"] == 1 for x in P.evaluate("__wouaf.copains()")))
    check("repères gardés avec la position (pipi + copain)", [x["k"] for x in P.evaluate("__wouaf.getGw().pins")] == ["p", "d"], P.evaluate("__wouaf.getGw().pins"))
    P.evaluate("__wouaf.setWx({ at: Date.now(), t: 28, p: 0, code: 0, day: 1 })")
    P.evaluate("__wouaf.stopWalk()"); P.wait_for_timeout(1500)
    t = sheet(P)
    check("récap : 🥣 rappel d'eau (chaleur : 28°)", "28°" in t and "eau" in t, t[:600])
    check("récap : 🦴 friandise après 45 min", "friandise" in t)
    check("récap : territoires marqués", "marqué 1 territoire" in t)
    check("récap : « Tu as croisé un copain ? » avec Filou", "croisé un copain" in t and "Filou" in t)
    P.click("#sheet .care button"); P.wait_for_timeout(100)
    check("toucher le rappel le coche", "✓" in P.evaluate("document.querySelector('#sheet .care button').innerText"))
    P.fill("#copN2", "Rex"); P.click("#copA2"); P.wait_for_timeout(200)
    check("copain ajouté depuis le récap (compté une fois)", any(x["n"] == "Rex" and x["c"] == 1 for x in P.evaluate("__wouaf.copains()")))
    tr = P.evaluate("JSON.parse(localStorage.getItem('wouaf-traces'))")
    check("le chemin garde le prénom et les repères (sur le téléphone)", tr and tr[-1].get("w") == "Léa" and len(tr[-1].get("p", [])) == 2, tr[-1] if tr else None)
    check("rien de tout ça n'est envoyé au serveur", "Filou" not in json.dumps(kv(), ensure_ascii=False) and "\"p\": [" not in json.dumps(kv()))
    P.evaluate("document.querySelector('#closeRecap') && document.querySelector('#closeRecap').click()"); P.wait_for_timeout(400)
    # --- carte de chaleur
    P.evaluate("__wouaf.sheetHeat()"); P.wait_for_timeout(500); t = sheet(P)
    check("carte de chaleur : calques, période, territoire en km²", all(x in t for x in ("Chemins", "Pipi", "Copains", "7 jours", "km²")), t[:400])
    d = P.evaluate("__wouaf.heatData('all')")
    check("carte de chaleur : 1 balade, 2 repères", d["n"] == 1 and len(d["pins"]) == 2, d)
    P.click("[data-h='lay:p']"); P.wait_for_timeout(300)
    check("un calque se coupe", "on" not in (P.evaluate("document.querySelector(\"[data-h='lay:p']\").className")))
    # --- copains (menu)
    P.evaluate("__wouaf.sheetCopains()"); P.wait_for_timeout(300)
    check("fiche des copains", "Filou" in sheet(P) and "Rex" in sheet(P) and "rencontre" in sheet(P))
    # --- sons
    P.evaluate("__wouaf.openMenu()"); P.wait_for_timeout(300)
    check("menu : bouton Sons", P.locator("#muSon").count() == 1)
    P.click("#muSon"); P.wait_for_timeout(300)
    check("sons coupés et mémorisés", P.evaluate("__wouaf.soundOn()") is False and "Sons coupés" in sheet(P))
    m = P.evaluate("(()=>{const s=document.querySelector('#sheet .sbody');return [s.scrollHeight,s.clientHeight]})()")
    check("menu toujours sans défilement", m[0] <= m[1], m)
    check("titre du menu lisible (pas ivoire sur blanc)", P.evaluate("getComputedStyle(document.querySelector('#sheet h2')).color") != "rgb(243, 239, 230)")
    P.click("#muSon"); P.wait_for_timeout(200)
    # --- 📊 chiffres
    n = P.evaluate("__wouaf.roxyNumbers()")
    check("Roxy en chiffres : km, pas de chien, heure préférée", "km" in n and "pas de chien" in n and "heure préférée" in n, n[:300])
    # --- ☁️ nuages
    h = P.evaluate("(() => { const g = __wouaf.getGame(); const h = __wouaf.weekHunt(); const z = __wouaf.huntCloud(h); const R = 6371000, toR = Math.PI/180; const dl = (z.lat-h.lat)*toR*R, dn = (z.lon-h.lon)*toR*R*Math.cos(h.lat*toR); return Math.hypot(dl, dn); })()")
    check("nuage doré : le trésor est dedans, pas au centre (150–450 m)", 140 < h < 460, h)
    P.evaluate("(() => { const g = __wouaf.getGame(); g.chests = []; g.firstUse = Date.now() - 40*86400000; })()")
    # --- 💶 paie à la semaine
    r = P.evaluate("(() => { const g = __wouaf.getGame(); g.wkBase = { wk: '2020-01-06', cum: __wouaf.moneyAll() - 0.5 }; return __wouaf.paydayCardData(); })()")
    check("lundi : carte « Jour de paie » de la semaine avec la révélation", r and "Jour de paie" in r["html"] and "100 clebsous = 1 €" in r["html"] and ">50 " in r["html"] and "Invalid" not in r["html"], r and r["html"][:300])
    check("pas deux fois la même semaine", P.evaluate("__wouaf.paydayCardData()") is None)
    P.wait_for_timeout(800)
    pays = kv().get("pays")
    check("la paie part au serveur pour le tableau de bord", pays and "Léa" in pays and "0.5" in pays, pays)
    st, body = local_api("POST", "/dash", json.dumps({"code": "1234"}).encode())
    j = json.loads(body)
    check("tableau de bord : paies à verser", st == 200 and any(x["walker"] == "Léa" for x in j.get("pays", [])), body[:200])
    wk = list(json.loads(pays)["léa"]["w"].keys())[0]
    st, _ = local_api("POST", "/pay-mark", json.dumps({"code": "1234", "walker": "Léa", "wk": wk}).encode())
    st2, body2 = local_api("GET", "/pause")
    check("« Versé ✓ » : le téléphone le saura via /pause", st == 200 and wk in json.loads(body2).get("paid", {}).get("léa", {}), body2[:300])
    st3, _ = local_api("POST", "/pay-mark", json.dumps({"code": "0000", "walker": "Léa", "wk": wk}).encode())
    check("« Versé ✓ » refusé sans le bon code", st3 == 403)
    # --- 🎒 heures de cours (réglage)
    P.evaluate("__wouaf.openRappels()"); P.wait_for_timeout(300)
    if P.locator("input[data-c='1'][data-s='0']").count():
        P.fill("input[data-c='1'][data-s='0']", "08:00"); P.fill("input[data-c='1'][data-s='1']", "16:30"); P.check("#rapVac"); P.click("#rapOn"); P.wait_for_timeout(300)
        rp = P.evaluate("JSON.parse(localStorage.getItem('wouaf-rappels'))")
        check("heures de cours et vacances enregistrées", rp["cours"][1] == ["08:00", "16:30"] and rp["vac"] is True, rp.get("cours"))
    else:
        check("réglage des heures de cours visible", "cours" in sheet(P).lower() or "écran d'accueil" in sheet(P), sheet(P)[:200])
    # --- zoom de la page bloqué
    check("la page ne se zoome plus (viewport)", "user-scalable=no" in P.evaluate("document.querySelector('meta[name=viewport]').content"))
    check("version 3.3 · CROQUETTE", "3.3" in P.evaluate("document.querySelector('#homeFoot').innerText") and "CROQUETTE" in P.evaluate("document.querySelector('#homeFoot').innerText"))
    b.close()
check("aucune erreur JavaScript", not errs, errs[:3])
print("\n" + ("✅ TOUT EST BON" if not FAILS else f"❌ {len(FAILS)} échec(s) : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
