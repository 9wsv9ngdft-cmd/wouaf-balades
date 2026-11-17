"""v47 (vraie carte Leaflet : lancer d'abord tests/build-leaflet.sh) : toucher Roxy = journal de bord (chiffres de la famille via /journal,
qui sort Roxy, mes balades) ; toucher une de mes balades = revoir le trajet (carte, repères, détail) ; depuis le carnet, les dernières sorties
et les paies des semaines."""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2e_common as E
from playwright.sync_api import sync_playwright

REAL = open("/tmp/leaflet-real.js").read()
CSS = open("/tmp/lf/dist/leaflet.css").read() if os.path.exists("/tmp/lf/dist/leaflet.css") else ""
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)

def phone(pw, init, errs):
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width":393,"height":760}, geolocation={"latitude":48.8566,"longitude":2.3522}, permissions=["geolocation"], has_touch=True, is_mobile=True)
    def cdn(route):
        u = route.request.url
        if "leaflet.min.js" in u: route.fulfill(body=REAL, content_type="application/javascript")
        elif "leaflet.min.css" in u: route.fulfill(body=CSS, content_type="text/css")
        else: route.abort()
    ctx.route("**/cdnjs.cloudflare.com/**", cdn)
    for pat in ("**/fonts.googleapis.com/**","**/fonts.gstatic.com/**","**/*tile*/**","**/overpass-api.de/**"): ctx.route(pat, lambda r: r.abort())
    ctx.route("**/photon.komoot.io/**", lambda r: r.fulfill(body='{"features":[]}', content_type="application/json"))
    ctx.route("**/api.open-meteo.com/**", lambda r: r.fulfill(body='{}', content_type="application/json"))
    def api(route):
        req = route.request; st, data = E.local_api(req.method, req.url[len(E.API_HOST):], req.post_data_buffer)
        route.fulfill(status=st, body=data, headers={"content-type":"application/json","access-control-allow-origin":"*"})
    ctx.route(E.API_HOST + "/**", api)
    ctx.add_init_script(init)
    p = ctx.new_page(); p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    return b, p

NOW = int(time.time() * 1000)
ID = NOW - 2 * 3600 * 1000
LINE = [[48.8566 + i * 0.0004, 2.3522 + (i % 3) * 0.0003] for i in range(20)]
LOG = [{"id": ID, "date": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(ID / 1000)), "title": "Balade libre", "cat": "free", "icon": "🚶", "min": 32, "plannedMin": 30,
        "m": 2600, "routeM": 2600, "walker": "Léa", "recap": {"eu": 0.47, "pp": 1}, "line": LINE}]
TRACES = [{"d": 1, "s": "", "w": "Léa", "t": ID + 2000, "p": [{"k": "p", "a": 48.8586, "o": 2.3525}, {"k": "d", "a": 48.8596, "o": 2.3528}]}]
INIT = ("if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','47');"
        "localStorage.setItem('wouaf-stats-ok','true');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-welcome2','0');"
        "localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));"
        f"localStorage.setItem('wouaf-carnet', JSON.stringify({json.dumps(LOG)}));localStorage.setItem('wouaf-traces', JSON.stringify({json.dumps(TRACES)}));"
        "localStorage.setItem('wouaf-jeu', JSON.stringify({pts:0,total:300,money:{},bonus:{},streak:{day:'',n:0},seen:{},claims:[],home:{lat:48.8566,lon:2.3522},chests:[],firstUse:Date.now()-30*86400000,weeks:{}}));}")

E.local_api("GET", "/__wipe")
e = int(time.time())
for w, extra in (("Léa", {"pp": 1}), ("Tom", {"cc": 1}), ("Tom", {})):
    e -= 3000
    E.local_api("POST", "/walk", json.dumps({"walker": w, "walk": dict({"s": e - 1800, "e": e, "min": 30, "m": 2500, "cs": 40}, **extra), "sum": {}}).encode())
E.local_api("POST", "/walk", json.dumps({"walker": "Léa", "walk": {"s": ID // 1000 - 1920, "e": ID // 1000, "min": 32, "m": 2600, "cs": 47, "pp": 1}, "sum": {}}).encode())

errs = []
with sync_playwright() as pw:
    b, P = phone(pw, INIT, errs)
    P.goto(E.SITE); P.wait_for_function("window.__wouaf !== undefined", timeout=15000); P.wait_for_timeout(3500)
    if P.evaluate("document.querySelector('#modal').classList.contains('open')"): P.evaluate("__wouaf.renderHome && 0"); P.click("#sheetX"); P.wait_for_timeout(400)
    # 1. toucher Roxy = journal
    P.click("#heroDog"); P.wait_for_timeout(2000)
    t = P.inner_text("#sheet")
    check("toucher Roxy ouvre son journal de bord", "Le journal de" in t, t[:200])
    check("Roxy parle en haut du journal", P.locator("#sheet .jsay").count() == 1)
    check("totaux de la famille (4 balades)", "4\nbalades" in t or "4 balades" in t.replace("\n", " "), t[:500])
    check("« Qui sort Roxy ? » avec Toi et Tom", "qui sort" in t.lower() and "Toi" in t and "Tom" in t, t[:800])
    check("pipis et cacas comptés", "💧 2 pipis" in t and "💩 1 caca" in t, t)
    check("mes balades à revoir", P.locator("#sheet [data-wk]").count() == 1)
    # 2. revoir une balade
    P.click("#sheet [data-wk]"); P.wait_for_timeout(1500)
    t = P.inner_text("#sheet")
    check("revoir : carte du trajet affichée", P.locator("#wkmap.leaflet-container, #wkmap .leaflet-container").count() >= 1)
    check("revoir : trajet dessiné", P.locator("#wkmap path.leaflet-interactive").count() >= 1)
    pins = P.locator("#wkmap .hpin").all_inner_texts()
    check("revoir : départ, arrivée et repères (💧, 🐕)", "🟢" in pins and "🏁" in pins and "💧" in pins and "🐕" in pins, pins)
    check("revoir : durée, distance, vitesse, clebsous", "32 min" in t and "2,6 km" in t and "km/h" in t and "+47" in t, t)
    check("revoir : boutons refaire, renvoyer, retour", P.locator("#wkRedo").count() == 1 and P.locator("#wkSend").count() == 1 and "Retour" in P.inner_text("#wkBack"))
    P.click("#wkBack"); P.wait_for_timeout(1500)
    check("← Retour revient au journal", "Le journal de" in P.inner_text("#sheet"))
    P.click("#sheetX"); P.wait_for_timeout(400)
    # 3. dernières sorties : ma balade cliquable, celles de Tom non
    P.evaluate("__wouaf.sheetOuts()"); P.wait_for_timeout(1500)
    check("dernières sorties : ma balade est cliquable, pas celles de Tom", P.locator("#sheet [data-wk]").count() == 1)
    P.click("#sheet [data-wk]"); P.wait_for_timeout(1200)
    check("… et ouvre la balade", P.locator("#wkmap").count() == 1)
    P.click("#sheetX"); P.wait_for_timeout(400)
    # 4. paies des semaines → balades de la semaine
    wk = P.evaluate(f"(() => {{ const g = __wouaf.getGame(); const d = new Date({ID} - 4*3600000); d.setHours(0,0,0,0); d.setDate(d.getDate() - (d.getDay() + 6) % 7); const t = new Date(d.getTime() + 5*3600000); return t.getFullYear() + '-' + (t.getMonth()+1) + '-' + t.getDate(); }})()")
    P.evaluate(f"__wouaf.sheetWeekWalks('{wk}')"); P.wait_for_timeout(600)
    check("semaine : la balade de la semaine est listée", P.locator("#sheet [data-wk]").count() == 1, P.inner_text("#sheet")[:200])
    P.screenshot(path="/tmp/v47-week.png")
    b.close()
real = [x for x in errs if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
