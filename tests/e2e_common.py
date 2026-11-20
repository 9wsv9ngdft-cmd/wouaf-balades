"""Aides pour les tests dans le navigateur : vraie page index.html, faux Leaflet, VRAI code du Worker (serve-worker.mjs)."""
import json, os, urllib.request
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "http://127.0.0.1:8000/index.html"
API_HOST = "https://wouaf-notifs.6fgbcr2vtp.workers.dev"
LOCAL_API = "http://127.0.0.1:8787"
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def local_api(method, path, body=None):
    req = urllib.request.Request(LOCAL_API + path, data=body, method=method)
    try:
        with _opener.open(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

def kv():
    return dict(json.loads(_opener.open(LOCAL_API + "/__kv").read()))

# v4.0 : le pop-up du jour s'affiche une fois par jour ; les anciens tests le marquent « déjà vu » (pop=True pour le tester)
NO_POP = "try{ if (!window.__wantPop){ const d = new Date(Date.now() - 4*3600000), p = n => String(n).padStart(2, '0'); localStorage.setItem('wouaf-pop', JSON.stringify(d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()))); } }catch(e){}"

# v4.4 : l'écran d'entrée (comptes) s'affiche une fois par téléphone ; les anciens tests le passent (acc=True pour le tester)
NO_ACC = "try{ localStorage.setItem('wouaf-acc-skip', '1'); }catch(e){}"

def new_phone(pw, name=None, errors=None, init=None, pop=False, acc=False):
    """Un « téléphone » = un contexte de navigateur isolé (son propre localStorage / IndexedDB)."""
    b = pw.chromium.launch()
    ctx = b.new_context(viewport={"width": 390, "height": 800}, geolocation={"latitude": 48.8566, "longitude": 2.3522}, permissions=["geolocation"])
    stub = open(os.path.join(HERE, "leaflet-stub.js"), encoding="utf-8").read()
    def route_cdn(route):
        u = route.request.url
        if "leaflet.min.js" in u: route.fulfill(body=stub, content_type="application/javascript")
        elif "leaflet.min.css" in u: route.fulfill(body="", content_type="text/css")
        else: route.abort()
    ctx.route("**/cdnjs.cloudflare.com/**", route_cdn)
    ctx.route("**/fonts.googleapis.com/**", lambda r: r.abort())
    ctx.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    ctx.route("**/*tile*/**", lambda r: r.abort())
    ctx.route("**/photon.komoot.io/**", lambda r: r.fulfill(body='{"features":[]}', content_type="application/json"))
    ctx.route("**/api.open-meteo.com/**", lambda r: r.fulfill(body='{}', content_type="application/json"))
    def route_api(route):
        req = route.request
        st, data = local_api(req.method, req.url[len(API_HOST):], req.post_data_buffer)
        route.fulfill(status=st, body=data, headers={"content-type": "application/json", "access-control-allow-origin": "*"})
    ctx.route(API_HOST + "/**", route_api)
    page = ctx.new_page()
    if errors is not None:
        page.on("pageerror", lambda e: errors.append(str(e)))
    if init: ctx.add_init_script(init)
    ctx.add_init_script("window.__wantPop = true;" if pop else NO_POP)
    if not acc: ctx.add_init_script(NO_ACC)
    return b, ctx, page

def open_app(page, wait=2200):
    page.goto(SITE)
    page.wait_for_function("window.__wouaf !== undefined", timeout=15000)
    page.wait_for_timeout(wait)
