"""v58 (4.5) : nouvel accueil (maquette B) et nouveau départ : une seule question, « Propose-moi » sur la carte, classement en direct, couronne qui se vole."""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','59');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-hon-vu','2099-01');localStorage.setItem('wouaf-wa-sent','[]');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
EV = lambda P, js: P.evaluate(js)
is_open = lambda P: P.evaluate("document.querySelector('#modal').classList.contains('open')")
sheet = lambda P: P.inner_text("#sheet") if is_open(P) else ""
body = lambda P: P.evaluate("document.body.className")
FAKE = """(() => { const S = __wouaf.state, c = { lat: 48.8566, lon: 2.3522 };
  const mk = (n, k, dlat, dlon, min) => ({ type:'loop', cat:'nature', via:[{ name:n, kind:'park', pt:{ lat:c.lat + dlat, lon:c.lon + dlon } }, { name:n + ' bis', kind:'park', pt:{ lat:c.lat + dlat, lon:c.lon - dlon } }],
    line:[c, { lat:c.lat + dlat, lon:c.lon + dlon }, { lat:c.lat + dlat, lon:c.lon - dlon }, c], m: min * 75, min, newPct: 40 });
  S.results = [mk('Parc A', 'park', .004, .004, 31), mk('Parc B', 'park', -.004, .005, 33)]; S.cat = 'all'; S.pi = null;
  __wouaf.propShow(0); })()"""
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.emulate_media(color_scheme="dark")
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 2500)
    P.screenshot(path="/tmp/v58-accueil.png")
    check("accueil sombre (réglage du téléphone)", "nuit" in body(P))
    h = P.evaluate("[document.documentElement.scrollHeight, innerHeight]")
    check("accueil sans défilement", h[0] <= h[1], h)
    P.set_viewport_size({"width": 393, "height": 852}); P.wait_for_timeout(500)
    g = EV(P, "[document.querySelector('#miniMap').offsetHeight, innerHeight - document.querySelector('#homeFoot').getBoundingClientRect().bottom, document.documentElement.scrollHeight - innerHeight]")
    check("v4.5.1 (iPhone 393 × 852) : la carte remplit, plus de vide en bas, pas de défilement", g[0] > 420 and g[1] < 30 and g[2] <= 0, g)
    # ---- v4.5.2 : accueil fixe ----
    check("v4.5.2 : l'accueil est fixe (classe homefix)", EV(P, "document.documentElement.classList.contains('homefix')"))
    EV(P, "window.scrollTo(0, 300)"); P.wait_for_timeout(200)
    check("v4.5.2 : impossible de faire glisser l'accueil", EV(P, "window.scrollY") == 0, EV(P, "window.scrollY"))
    P.mouse.move(200, 400); P.mouse.wheel(0, 600); P.wait_for_timeout(300)
    check("v4.5.2 : même à la molette / au doigt", EV(P, "window.scrollY") == 0, EV(P, "window.scrollY"))
    EV(P, "__wouaf.openMenu()"); P.wait_for_timeout(400)
    check("v4.5.2 : une fiche ouverte : l'accueil n'est plus « fixe » (la fiche défile)", not EV(P, "document.documentElement.classList.contains('homefix')"))
    EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(500)
    check("v4.5.2 : fiche fermée : de nouveau fixe", EV(P, "document.documentElement.classList.contains('homefix')"))
    P.set_viewport_size({"width": 393, "height": 760}); P.wait_for_timeout(400)
    check("3 tuiles collées en bas", P.locator(".btiles .bt").count() == 3)
    check("« Ta semaine » sous la carte", "Ta semaine" in P.inner_text("#weekBar"), P.inner_text("#weekBar"))
    # ---- mode clair ----
    P.emulate_media(color_scheme="light"); P.wait_for_timeout(400)
    check("mode clair : l'accueil suit le téléphone", "nuit" not in body(P))
    P.screenshot(path="/tmp/v58-clair.png")
    P.emulate_media(color_scheme="dark"); P.wait_for_timeout(300)
    # ---- toucher la carte = une seule question ----
    P.click("#miniMap"); P.wait_for_timeout(500)
    t = sheet(P)
    check("toucher la carte : une seule question", "Tu gères ta balade, ou je te propose un parcours" in t, t[:200])
    check("deux réponses + la balade express en petit lien", P.locator("#chFree").count() == 1 and P.locator("#chRoute").count() == 1 and P.locator("#chExpress.linkish").count() == 1)
    P.screenshot(path="/tmp/v58-question.png")
    # ---- Propose-moi : sur la carte, plein écran ----
    P.click("#chRoute"); P.wait_for_timeout(1500)
    check("Propose-moi : la carte en plein écran", "propose" in body(P) and P.locator("#propCard").is_visible() and P.locator("#propX").is_visible())
    EV(P, FAKE); P.wait_for_timeout(300)
    check("un parcours affiché : titre, durée, gain", "Parc A" in P.inner_text("#propTitle") and "jusqu'à" in P.inner_text("#propSub"), P.inner_text("#propCard"))
    check("J'y vais · Suivant · Choisis pour moi", P.locator("#propGo").is_visible() and P.locator("#propNext").is_visible() and P.locator("#propDice").is_visible())
    P.screenshot(path="/tmp/v58-propose.png")
    P.click("#propNext"); P.wait_for_timeout(200)
    check("Suivant : l'autre parcours (2/2)", "Parc B" in P.inner_text("#propTitle") and "2/2" in P.inner_text("#propIdx"), P.inner_text("#propCard"))
    P.click("#propNext"); P.wait_for_timeout(200)
    check("Suivant encore : on revient au premier", "1/2" in P.inner_text("#propIdx"))
    P.click("#propX"); P.wait_for_timeout(500)
    check("✕ : retour à l'accueil (on peut revenir en arrière)", "propose" not in body(P) and "hasmap" not in body(P) and P.locator("#miniMap").is_visible())
    # ---- v4.5.1 : ✕ avant que la position arrive : on reste sur l'accueil, pas de liste en dessous ----
    EV(P, "window.__geoSlow = navigator.geolocation.getCurrentPosition; navigator.geolocation.getCurrentPosition = (ok) => setTimeout(() => ok({ coords: { latitude: 48.8566, longitude: 2.3522, accuracy: 10 } }), 1500); 0")
    P.click("#miniMap"); P.wait_for_timeout(400); P.click("#chRoute"); P.wait_for_timeout(400)
    P.click("#propX"); P.wait_for_timeout(2500)
    check("v4.5.1 : ✕ avant la position : toujours l'accueil (pas de carte qui revient)", "hasmap" not in body(P) and "propose" not in body(P) and P.locator("#miniMap").is_visible(), body(P))
    check("v4.5.1 : ✕ : plus de liste de parcours sous l'accueil", EV(P, "document.querySelector('#props').innerHTML.trim() === ''") and not P.locator("#props .prop").count())
    EV(P, "navigator.geolocation.getCurrentPosition = window.__geoSlow; 0")
    # ---- J'y vais ----
    P.click("#miniMap"); P.wait_for_timeout(400); P.click("#chRoute"); P.wait_for_timeout(800); EV(P, FAKE); P.wait_for_timeout(200)
    P.click("#propGo"); P.wait_for_timeout(800)
    check("J'y vais : la balade démarre avec ce parcours", "walking" in body(P) and "propose" not in body(P) and EV(P, "__wouaf.state.walk && __wouaf.state.walk.line.length > 0"))
    EV(P, "__wouaf.cancelWalk ? __wouaf.cancelWalk() : 0"); P.wait_for_timeout(800)
    if is_open(P): EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(300)
    # ---- Choisis pour moi ----
    EV(P, "__wouaf.proposeRoutes(30)"); P.wait_for_timeout(600); EV(P, FAKE); P.wait_for_timeout(200)
    P.click("#propDice"); P.wait_for_timeout(300)
    check("🎲 : Roxy choisit", "Roxy a choisi" in P.inner_text("#propTitle"), P.inner_text("#propTitle"))
    P.wait_for_timeout(1600)
    check("🎲 : puis la balade démarre toute seule", "walking" in body(P))
    EV(P, "__wouaf.cancelWalk ? __wouaf.cancelWalk() : 0"); P.wait_for_timeout(800)
    if is_open(P): EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(300)
    # ---- Je gère ----
    P.click("#miniMap"); P.wait_for_timeout(400); P.click("#chFree"); P.wait_for_timeout(800)
    check("Je gère : balade libre tout de suite", "walking" in body(P) and EV(P, "__wouaf.state.walk && __wouaf.state.walk.line.length === 0"))
    EV(P, "__wouaf.cancelWalk ? __wouaf.cancelWalk() : 0"); P.wait_for_timeout(800)
    if is_open(P): EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(300)
    # ---- ☁️ exploration ----
    EV(P, "__wouaf.renderHome()"); P.wait_for_timeout(300)
    check("bouton ☁️ dans un coin de la mini-carte", P.locator("#miniExplo").is_visible())
    # ---- durée proposée : un peu plus que d'habitude ----
    log = [{"id": 1000 + i, "date": (datetime.datetime.now() - datetime.timedelta(days=i + 1)).isoformat(), "min": 40, "m": 3000, "walker": "Léa"} for i in range(4)]
    EV(P, "localStorage.setItem('wouaf-carnet', " + json.dumps(json.dumps(log)) + ")")
    d = EV(P, "__wouaf.propDur()")
    check("durée proposée : un peu plus que d'habitude (40 min → 60)", d == 60, d)
    # ---- classement ----
    EV(P, "localStorage.setItem('wouaf-explo', JSON.stringify({ wk:'2026-11-16', rank:[{ w:'Tom', r:1 }, { w:'Léa', r:2 }, { w:'Zoé', r:3 }], prev:{ rank:[] } }))")
    EV(P, "__wouaf.renderHome()"); P.wait_for_timeout(300)
    rt = P.inner_text("[data-lot='rank']")
    check("tuile classement : ⚔️ DÉFIER (plus « en direct »), Toi en 2e, couronne au 1er", "DÉFIER" in rt and "EN DIRECT" not in rt and "Toi" in rt and "Tom" in rt and P.locator("[data-lot='rank'] .r.c1 .cr").count() == 1 and P.locator("[data-lot='rank'] .r.me").count() == 1, rt)
    P.click("[data-lot='rank']"); P.wait_for_timeout(900)
    t = sheet(P)
    check("fiche du classement : podium + Défier", "Le classement" in t and P.locator("#sheet .podium").count() == 1 and P.locator("#rkDuel").count() == 1, t[:200])
    tabs = P.locator("#sheet [data-rt]").all_inner_texts()
    check("v4.5.5 : onglets Semaine · Mois · Année · Rigolo (plus de Saison ni de 🎄)", tabs == ["Semaine", "Mois", "Année", "😂 Rigolo"], tabs)
    for k in ["month", "year", "fun", "week"]:
        P.click(f"#sheet [data-rt='{k}']"); P.wait_for_timeout(400)
    check("tous les onglets s'ouvrent", "Le classement" in sheet(P))
    EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(300)
    P.click("[data-lot='bills']"); P.wait_for_timeout(400)
    check("tuile argent : les billets (cadeau argenté + coffre)", "Cadeau argenté" in sheet(P) and "Coffre" in sheet(P))
    EV(P, "document.querySelector('#sheetX').click()"); P.wait_for_timeout(300)
    # ---- la couronne se vole ----
    EV(P, "localStorage.setItem('wouaf-explo', JSON.stringify({ wk:'2026-11-16', rank:[{ w:'Léa', r:1 }, { w:'Tom', r:2 }], prev:{ rank:[] } })); __wouaf.crownWatch(); __wouaf.renderHome()")
    P.wait_for_timeout(300)
    check("1re en direct : la vraie couronne sur Roxy", EV(P, "__wouaf.wearCrown()") and EV(P, "!document.querySelector('#crownBtn').hidden"))
    EV(P, "localStorage.setItem('wouaf-explo', JSON.stringify({ wk:'2026-11-16', rank:[{ w:'Tom', r:1 }, { w:'Léa', r:2 }], prev:{ rank:[] } })); __wouaf.crownWatch()")
    P.wait_for_timeout(1800)
    tt = EV(P, "document.body.innerText")
    check("Tom passe devant : « 😱 Tom m'a piqué la couronne ! »", "piqué la couronne" in tt)
    check("plus de couronne sur Roxy", not EV(P, "__wouaf.wearCrown()"))
    check("aucune erreur JavaScript", not errs, errs[:3])
    b.close()
print("\n" + ("Tout est vert ✅" if not FAILS else f"{len(FAILS)} échec(s)"))
sys.exit(1 if FAILS else 0)
