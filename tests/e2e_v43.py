"""v43 (vraie carte Leaflet : lancer d'abord tests/build-leaflet.sh) : trésor à 0,8–1,5 km posé sur une rue ouverte (Overpass simulé),
carte du trésor du superviseur, déplacement à la main repris par un autre téléphone, retour au placement automatique."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2e_common as E
REAL = open("/tmp/leaflet-real.js").read()
CSS = open("/tmp/lf/dist/leaflet.css").read() if os.path.exists("/tmp/lf/dist/leaflet.css") else ""

def phone(pw, init, errs, extra=None):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width":393,"height":760}, geolocation={"latitude":48.8566,"longitude":2.3522}, permissions=["geolocation"], has_touch=True, is_mobile=True)
    def cdn(route):
        u = route.request.url
        if "leaflet.min.js" in u: route.fulfill(body=REAL, content_type="application/javascript")
        elif "leaflet.min.css" in u: route.fulfill(body=CSS, content_type="text/css")
        else: route.abort()
    ctx.route("**/cdnjs.cloudflare.com/**", cdn)
    for pat in ("**/fonts.googleapis.com/**","**/fonts.gstatic.com/**","**/*tile*/**"): ctx.route(pat, lambda r: r.abort())
    ctx.route("**/photon.komoot.io/**", lambda r: r.fulfill(body='{"features":[]}', content_type="application/json"))
    ctx.route("**/api.open-meteo.com/**", lambda r: r.fulfill(body='{}', content_type="application/json"))
    def api(route):
        req = route.request; st, data = E.local_api(req.method, req.url[len(E.API_HOST):], req.post_data_buffer)
        route.fulfill(status=st, body=data, headers={"content-type":"application/json","access-control-allow-origin":"*"})
    ctx.route(E.API_HOST + "/**", api)
    if extra: extra(ctx)
    ctx.add_init_script(init)
    p = ctx.new_page(); p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    return b, p
from playwright.sync_api import sync_playwright

FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)

def init(name):
    return """if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','43');localStorage.setItem('wouaf-stats-ok','true');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-welcome2','0');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'%s'}));
localStorage.setItem('wouaf-jeu', JSON.stringify({pts:0,total:300,money:{},bonus:{},streak:{day:'',n:0},seen:{},claims:[],home:{lat:48.8566,lon:2.3522},chests:[],firstUse:Date.now()-30*86400000,hunt:{wk:'2000-01-03',lat:0,lon:0}}));}""" % name

# Overpass simulé : une seule rue ouverte, horizontale, qui passe à ~30 m au nord du point demandé
SEEN = []
def overpass(route):
    q = route.request.url
    import urllib.parse, re
    d = urllib.parse.unquote(q.split("data=", 1)[1])
    SEEN.append(d)
    m = re.search(r"around:(\d+),([-\d.]+),([-\d.]+)", d); lat, lon = float(m.group(2)), float(m.group(3))
    dl = 30 / 111320
    body = {"elements": [{"type": "way", "geometry": [{"lat": lat + dl, "lon": lon - 0.002}, {"lat": lat + dl, "lon": lon + 0.002}]}]}
    route.fulfill(body=json.dumps(body), content_type="application/json")

E.local_api("GET", "/__wipe")
errs = []
with sync_playwright() as pw:
    b, p = phone(pw, init("Léa"), errs, extra=lambda ctx: ctx.route("**/overpass-api.de/**", overpass))
    p.goto(E.SITE); p.wait_for_function("window.__wouaf !== undefined", timeout=15000); p.wait_for_timeout(3500)
    hu = p.evaluate("(() => { const g = JSON.parse(localStorage.getItem('wouaf-jeu')); return g.hunt; })()")
    from math import cos, radians, hypot
    dkm = hypot((hu["lat"] - 48.8566) * 111.32, (hu["lon"] - 2.3522) * 111.32 * cos(radians(48.8566)))
    check("trésor de la nouvelle version (v2) recalculé", hu.get("v") == 2, hu)
    check("trésor entre 0,8 et 1,5 km (+ recalage sur la rue)", 0.75 <= dkm <= 1.55, dkm)
    check("recalé sur une rue ouverte (Overpass)", hu.get("snapped") is True and len(SEEN) >= 1, hu)
    check("requête : pas de voies privées ni de service", SEEN and 'access!~"^(private' in SEEN[0] and "service" not in SEEN[0], SEEN[:1])
    b.close()

    # Éric : carte du trésor, déplacement à la main
    errs2 = []
    b2, e = phone(pw, init("Éric"), errs2, extra=lambda ctx: ctx.route("**/overpass-api.de/**", overpass))
    e.goto(E.SITE); e.wait_for_function("window.__wouaf !== undefined", timeout=15000); e.wait_for_timeout(7000)
    tok = e.evaluate("__wouaf.supToken()")
    check("Éric a son jeton superviseur", bool(tok), tok)
    e.evaluate("__wouaf.openMenu()"); e.wait_for_timeout(500)
    e.click("#muSupAll"); e.wait_for_timeout(600)
    check("entrée « Carte du trésor » dans le menu superviseur", e.locator("#muSupT").count() == 1)
    e.click("#muSupT"); e.wait_for_timeout(1200)
    check("carte affichée", e.locator("#tmap .leaflet-container, #tmap.leaflet-container").count() >= 1)
    check("trésor et maison sur la carte", e.locator("#tmap .hpin").count() >= 2, e.locator("#tmap .hpin").count())
    check("bouton grisé tant qu'on n'a rien choisi", e.locator("#tmOk").is_disabled())
    box = e.locator("#tmap").bounding_box()
    e.mouse.click(box["x"] + box["width"] * 0.3, box["y"] + box["height"] * 0.4); e.wait_for_timeout(400)
    check("toucher la carte active le bouton", not e.locator("#tmOk").is_disabled())
    e.click("#tmOk"); e.wait_for_timeout(1200)
    st, raw = E.local_api("GET", "/pause"); hp = json.loads(raw).get("hpos")
    check("position enregistrée sur le serveur", hp and hp.get("lat") is not None, hp)
    check("Éric voit « placé à la main » et le bouton automatique", e.locator("#tmAuto").count() == 1)
    b2.close()

    # Un autre téléphone reprend la position d'Éric telle quelle (pas recalée)
    errs3 = []
    b3, l = phone(pw, init("Léa"), errs3, extra=lambda ctx: ctx.route("**/overpass-api.de/**", overpass))
    l.goto(E.SITE); l.wait_for_function("window.__wouaf !== undefined", timeout=15000); l.wait_for_timeout(3500)
    hu = l.evaluate("JSON.parse(localStorage.getItem('wouaf-jeu')).hunt")
    check("autre téléphone : trésor exactement à l'endroit choisi par Éric", hp and abs(hu["lat"] - hp["lat"]) < 1e-7 and abs(hu["lon"] - hp["lon"]) < 1e-7 and hu.get("moved") == hp.get("at"), (hu, hp))
    # Éric remet le placement automatique → le téléphone recalcule à la prochaine synchro
    E.local_api("POST", "/hunt-move", json.dumps({"code": "1234", "clear": 1}).encode())
    l.evaluate("window.__wouaf && window.__wouaf.loadPauses ? window.__wouaf.loadPauses() : null"); l.reload(); l.wait_for_function("window.__wouaf !== undefined", timeout=15000); l.wait_for_timeout(3500)
    hu2 = l.evaluate("JSON.parse(localStorage.getItem('wouaf-jeu')).hunt")
    check("placement automatique : plus de position à la main", not hu2.get("moved"), hu2)
    b3.close()

real = [x for x in errs + errs2 + errs3 if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
