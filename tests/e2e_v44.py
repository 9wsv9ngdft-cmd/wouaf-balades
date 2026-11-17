"""v44 (vraie carte Leaflet : lancer d'abord tests/build-leaflet.sh) : Éric supervise SANS balade (exploration, carte du superviseur),
maison de la famille arrondie reprise par tous, trésor unique publié par le téléphone d'Éric, nuages argentés des ados sur sa carte,
fiches trésor et coffre sur l'accueil."""
import sys, os, json, re, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2e_common as E
from playwright.sync_api import sync_playwright

REAL = open("/tmp/leaflet-real.js").read()
CSS = open("/tmp/lf/dist/leaflet.css").read() if os.path.exists("/tmp/lf/dist/leaflet.css") else ""
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)

def overpass(route):
    d = urllib.parse.unquote(route.request.url.split("data=", 1)[1])
    m = re.search(r"around:(\d+),([-\d.]+),([-\d.]+)", d); lat, lon = float(m.group(2)), float(m.group(3))
    dl = 30 / 111320
    route.fulfill(body=json.dumps({"elements": [{"type": "way", "geometry": [{"lat": lat + dl, "lon": lon - 0.002}, {"lat": lat + dl, "lon": lon + 0.002}]}]}), content_type="application/json")

def phone(pw, init, errs, geo=(48.8566, 2.3522)):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width":393,"height":760}, geolocation={"latitude":geo[0],"longitude":geo[1]}, permissions=["geolocation"], has_touch=True, is_mobile=True)
    def cdn(route):
        u = route.request.url
        if "leaflet.min.js" in u: route.fulfill(body=REAL, content_type="application/javascript")
        elif "leaflet.min.css" in u: route.fulfill(body=CSS, content_type="text/css")
        else: route.abort()
    ctx.route("**/cdnjs.cloudflare.com/**", cdn)
    for pat in ("**/fonts.googleapis.com/**","**/fonts.gstatic.com/**","**/*tile*/**"): ctx.route(pat, lambda r: r.abort())
    ctx.route("**/photon.komoot.io/**", lambda r: r.fulfill(body='{"features":[]}', content_type="application/json"))
    ctx.route("**/api.open-meteo.com/**", lambda r: r.fulfill(body='{}', content_type="application/json"))
    ctx.route("**/overpass-api.de/**", overpass)
    def api(route):
        req = route.request; st, data = E.local_api(req.method, req.url[len(E.API_HOST):], req.post_data_buffer)
        route.fulfill(status=st, body=data, headers={"content-type":"application/json","access-control-allow-origin":"*"})
    ctx.route(E.API_HOST + "/**", api)
    ctx.add_init_script(init)
    p = ctx.new_page(); p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    return b, p

BASE = "localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','44');localStorage.setItem('wouaf-stats-ok','true');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-welcome2','0');"
ERIC = "if(!localStorage.getItem('wouaf-init')){" + BASE + "localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Éric'}));}"
# Léa : sa propre maison (ailleurs), sortie 5 des 7 derniers jours (coffre chaud), dernier coffre il y a longtemps
LEA = "if(!localStorage.getItem('wouaf-init')){" + BASE + """localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));
const now=Date.now(), log=[1,2,3,4,5].map(i=>({date:new Date(now-i*86400000).toISOString(),min:30,m:2500}));
localStorage.setItem('wouaf-carnet', JSON.stringify(log));
localStorage.setItem('wouaf-jeu', JSON.stringify({pts:0,total:300,money:{},bonus:{},streak:{day:'',n:0},seen:{},claims:[],home:{lat:48.87,lon:2.30},chests:[],firstUse:now-60*86400000}));}"""

E.local_api("GET", "/__wipe")
errs, errs2 = [], []
with sync_playwright() as pw:
    # ---------- 1. Éric, aucune balade ----------
    b, e = phone(pw, ERIC, errs)
    e.goto(E.SITE); e.wait_for_function("window.__wouaf !== undefined", timeout=15000); e.wait_for_timeout(7000)
    check("Éric superviseur (jeton)", bool(e.evaluate("__wouaf.supToken()")))
    e.evaluate("__wouaf.openExplore()"); e.wait_for_timeout(600)
    check("exploration ouverte sans balade pour le superviseur", e.evaluate("document.body.classList.contains('explore')"))
    e.evaluate("document.querySelector('#exploreBar button') && document.body.classList.remove('explore')")
    e.evaluate("__wouaf.openMenu()"); e.wait_for_timeout(400); e.click("#muSupAll"); e.wait_for_timeout(400)
    check("menu : « Carte du superviseur »", "Carte du superviseur" in e.inner_text("#muSupT"))
    e.click("#muSupT"); e.wait_for_timeout(1800)
    check("carte affichée sans maison ni balade", e.locator("#tmap.leaflet-container, #tmap .leaflet-container").count() >= 1)
    check("message : pas encore de maison de la famille", "Pas encore de maison" in e.inner_text("#sheet"))
    e.click("#tmHere"); e.wait_for_timeout(3500)
    st, raw = E.local_api("GET", "/pause"); pz = json.loads(raw)
    check("maison de la famille enregistrée ARRONDIE", pz.get("home") and abs(pz["home"]["lat"] - 48.856) < 1e-9 and abs(pz["home"]["lon"] - 2.352) < 1e-9, pz.get("home"))
    check("trésor publié tout seul par le téléphone d'Éric (auto)", pz.get("hpos") and pz["hpos"].get("auto") == 1, pz.get("hpos"))
    check("la carte montre maintenant maison et trésor", e.locator("#tmap .hpin").count() >= 2, e.locator("#tmap .hpin").count())
    hpos = pz.get("hpos") or {}
    e.evaluate("__wouaf.openMenu()"); e.wait_for_timeout(200)   # (téléphone d'Éric gardé ouvert pour l'étape 3)

    # ---------- 2. Léa (sa maison à elle, ailleurs) ----------
    b2, l = phone(pw, LEA, errs2, geo=(48.87, 2.30))
    l.goto(E.SITE); l.wait_for_function("window.__wouaf !== undefined", timeout=15000); l.wait_for_timeout(4000)
    g = l.evaluate("__wouaf.getGame()")
    check("Léa prend la maison de la famille", abs(g["home"]["lat"] - 48.856) < 1e-9 and abs(g["home"]["lon"] - 2.352) < 1e-9, g.get("home"))
    check("Léa a exactement le trésor publié par Éric", abs(g["hunt"]["lat"] - hpos.get("lat", 0)) < 1e-7 and abs(g["hunt"]["lon"] - hpos.get("lon", 0)) < 1e-7, (g.get("hunt"), hpos))
    check("coffre chaud chez Léa", l.evaluate("__wouaf.chestChance()") > 0)
    l.wait_for_timeout(800)
    st, raw = E.local_api("POST", "/clouds", json.dumps({"code": "1234"}).encode()); cl = json.loads(raw).get("clouds", [])
    check("nuage argenté de Léa envoyé au serveur", any(c["w"] == "Léa" for c in cl), cl)
    # fiches de l'accueil
    l.evaluate("__wouaf.renderHome && __wouaf.renderHome()"); l.wait_for_timeout(300)
    l.evaluate("document.querySelector('[data-lot=\"hunt\"]').click()"); l.wait_for_timeout(500)
    t = l.inner_text("#sheet")
    check("tuile trésor → fiche trésor (plus la liste des bonus)", "Trésor de la semaine" in t and "Un seul gagnant" in t and "avant qu'il disparaisse" in t, t[:300])
    check("fiche trésor : boutons « J'y vais » et « nuage doré »", l.locator("#tzGo").count() == 1 and l.locator("#tzMap").count() == 1)
    l.click("#tzX"); l.wait_for_timeout(400)
    l.evaluate("document.querySelector('[data-lot=\"chest\"]').click()"); l.wait_for_timeout(500)
    t = l.inner_text("#sheet")
    check("tuile coffre → fiche coffre (chaud, chances, rues neuves)", "Le coffre est chaud" in t and "rue neuve" in t, t[:300])
    check("fiche coffre : lien vers les bonus (os, balle…)", l.locator("#cfBonus").count() == 1)
    l.click("#cfBonus"); l.wait_for_timeout(600)
    check("« Ce que vaut chaque bonus » ouvre la liste des bonus", "🦴" in l.inner_text("#sheet"))
    b2.close()

    # ---------- 3. Éric voit le nuage de Léa ----------
    e.reload(); e.wait_for_function("window.__wouaf !== undefined", timeout=15000); e.wait_for_timeout(5000)
    e.evaluate("__wouaf.openHuntAdmin()"); e.wait_for_timeout(3000)
    t = e.inner_text("#sheet")
    check("carte du superviseur : « Coffre chaud aujourd'hui : Léa »", "Coffre chaud aujourd'hui : Léa" in t, t[:300])
    check("étiquette 💰 Léa sur la carte", "💰 Léa" in e.inner_text("#tmap"))
    b.close()

real = [x for x in errs + errs2 if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
