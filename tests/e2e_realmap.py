"""v2.7 avec la VRAIE carte Leaflet (lancer d'abord tests/build-leaflet.sh) : mini-carte, exploration visible, nuages, Roxy, Fini en appui long."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e2e_common as E
from playwright.sync_api import sync_playwright
REAL = open("/tmp/leaflet-real.js").read()
CSS = open("/tmp/lf/dist/leaflet.css").read() if os.path.exists("/tmp/lf/dist/leaflet.css") else open("/tmp/lf/src/../leaflet.css").read() if os.path.exists("/tmp/lf/leaflet.css") else ""
def phone(pw, init, errs):
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
    ctx.add_init_script(init)
    p = ctx.new_page(); p.on("pageerror", lambda e: errs.append(str(e)))
    p.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    return b, p
INIT = """if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','42');localStorage.setItem('wouaf-stats-ok','true');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));
localStorage.setItem('wouaf-jeu', JSON.stringify({pts:0,total:300,money:{},bonus:{},streak:{day:'',n:0},seen:{'54285:1809':1,'54286:1809':1},claims:[],home:{lat:48.8566,lon:2.3522},chests:[],firstUse:Date.now()-30*86400000}));}"""

FAILS=[]
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
E.local_api("GET", "/__wipe")
TR = "localStorage.setItem('wouaf-traces', JSON.stringify([{d: Math.floor(Date.now()/86400000) - 30, s: ''}]));"
errs=[]
with sync_playwright() as pw:
    b, p = phone(pw, INIT, errs)
    p.goto(E.SITE); p.wait_for_function("window.__wouaf !== undefined", timeout=15000); p.wait_for_timeout(4000)
    # vieux chemin (40 jours) le long d'une rue
    p.evaluate("(() => { const pts=[]; for(let i=0;i<30;i++) pts.push({lat:48.8566+i*0.0002, lon:2.3522}); __wouaf.saveTrace(pts); })()")
    if p.locator("#dgNext").count(): p.click("#dgNext"); p.wait_for_timeout(800)
    box = p.locator("#miniMap").bounding_box()
    p.touchscreen.tap(box["x"]+box["width"]/2, box["y"]+box["height"]/3); p.wait_for_timeout(800)
    t = p.evaluate("document.querySelector('#sheet').innerText")
    check("toucher la mini-carte = « Encore une ? » : balade libre, parcours, carte d'exploration", "Balade libre" in t and "Choisir un parcours" in t and "Carte d'exploration" in t, t[:200])
    p.click("#chExplo"); p.wait_for_timeout(2500)
    st = p.evaluate("({explore: document.body.classList.contains('explore'), walking: document.body.classList.contains('walking'), disp: getComputedStyle(document.querySelector('#map')).display, h: document.querySelector('#map').getBoundingClientRect().height})")
    check("3e choix : la carte d'exploration s'ouvre (pas la balade)", st["explore"] and not st["walking"], st)
    check("la carte d'exploration est visible (plus d'écran vide)", st["disp"] != "none" and st["h"] > 500, st)
    p.screenshot(path="/tmp/explore27.png")
    # pixels du nuage : blanc loin, doré sur le trésor
    px = p.evaluate("""(() => { const cv=[...document.querySelectorAll('.leaflet-fog-pane canvas, .leaflet-pane canvas')].find(c=>c.width>0); if(!cv) return null;
       const ctx=cv.getContext('2d'), r=cv.getBoundingClientRect(); const at=(x,y)=>Array.from(ctx.getImageData(Math.round((x-r.left)*cv.width/r.width),Math.round((y-r.top)*cv.height/r.height),1,1).data);
       const m=__wouaf.map, c=m.latLngToContainerPoint([48.8566+15*0.0002,2.3522]), mr=document.querySelector('#map').getBoundingClientRect();
       return { far: at(mr.left+20, mr.top+20), path: at(mr.left+c.x, mr.top+c.y) }; })()""")
    check("nuage blanc partout (avec motif très pâle)", px and px["far"][0] > 215 and px["far"][3] > 240, px)
    check("le vieux chemin (40 jours) reste visible", px and px["path"][3] < 60, px)
    p.click("#exploreClose"); p.wait_for_timeout(600)
    # trésor : nuage doré dans la carte
    p.evaluate("__wouaf.openExplore(true)"); p.wait_for_timeout(2500)
    gp = p.evaluate("""(() => { const h=__wouaf.weekHunt(), z=__wouaf.huntCloud(h); const cv=[...document.querySelectorAll('.leaflet-pane canvas')].find(c=>c.width>0); const ctx=cv.getContext('2d'), r=cv.getBoundingClientRect();
       const pt=__wouaf.map.latLngToContainerPoint([z.lat,z.lon]), mr=document.querySelector('#map').getBoundingClientRect(); const x=mr.left+pt.x, y=mr.top+pt.y;
       return Array.from(ctx.getImageData(Math.round((x-r.left)*cv.width/r.width),Math.round((y-r.top)*cv.height/r.height),1,1).data); })()""")
    check("nuage doré sur la zone du trésor", gp and gp[0] > 200 and gp[2] < 140, gp)
    p.screenshot(path="/tmp/hunt27.png")
    p.click("#exploreClose"); p.wait_for_timeout(600)
    # tuile trésor -> carte sur le nuage
    p.click("[data-lot='hunt']"); p.wait_for_timeout(1500)
    check("tuile trésor : ouvre la carte sur le nuage doré", p.evaluate("document.body.classList.contains('explore') && getComputedStyle(document.querySelector('#map')).display !== 'none'"))
    p.click("#exploreClose"); p.wait_for_timeout(600)
    # chien
    p.click("#heroDog"); p.wait_for_timeout(600)
    check("toucher Roxy ne lance pas la balade", not p.evaluate("document.body.classList.contains('walking')"))
    real = [e for e in errs if "Failed to load resource" not in e]
    check("aucune erreur JavaScript (vraie carte)", not real, real[:3])
    b.close()

WALK = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "e2e_v26.py")).read().split('WALK = """')[1].split('"""')[0]
errs=[]
with sync_playwright() as pw:
    b, p = phone(pw, INIT, errs)
    p.goto(E.SITE); p.wait_for_function("window.__wouaf !== undefined", timeout=15000); p.wait_for_timeout(4000)
    if p.locator("#dgNext").count(): p.click("#dgNext"); p.wait_for_timeout(800)
    p.evaluate(WALK, 25); p.wait_for_timeout(2500)
    for i in range(6): p.evaluate(f"__wouaf.onFix({{ coords:{{ latitude: 48.8626 + {i}*0.0003, longitude: 2.3522, accuracy: 8 }} }})"); p.wait_for_timeout(300)
    p.wait_for_timeout(1500)
    p.screenshot(path="/tmp/walk27.png")
    print("paws", p.evaluate("document.querySelectorAll('.pawm').length"))
    box = p.locator("#stop").bounding_box(); x, y = box["x"]+box["width"]/2, box["y"]+box["height"]/2
    p.mouse.move(x, y); p.mouse.down(); p.wait_for_timeout(1300)
    check("appui long sur Fini : balade finie, sélection bloquée", p.evaluate("document.body.classList.contains('nosel')") and not p.evaluate("document.body.classList.contains('walking')")); print("nosel during hold:", p.evaluate("document.body.classList.contains('nosel')"), "walking:", p.evaluate("document.body.classList.contains('walking')"))
    p.mouse.up(); p.wait_for_timeout(1200)
    check("après le doigt levé : aucun texte sélectionné", p.evaluate("String(getSelection())") == ""); print("nosel after release:", p.evaluate("document.body.classList.contains('nosel')"), "selection:", repr(p.evaluate("String(getSelection())")))
    p.screenshot(path="/tmp/recap27.png")
    print([e for e in errs if "Failed to load" not in e][:3])

print("\n" + ("✅ TOUT EST BON" if not FAILS else "❌ " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
