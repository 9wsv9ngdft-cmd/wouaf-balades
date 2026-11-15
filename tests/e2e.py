"""Tests de bout en bout de Wouaf Balades 2.0 : vraie page, vrai code du Worker (serve-worker.mjs), faux Leaflet.
Lancer : node tests/serve-worker.mjs &  python3 -m http.server 8000 --bind 127.0.0.1 &  python3 tests/e2e.py"""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *

FAILS = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + ((" → " + str(extra)) if (extra != "" and not cond) else ""))
    if not cond: FAILS.append(name)

INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','39');}"
NOW = datetime.datetime(2026, 11, 17, 12, 0, 0)     # mardi 17/11 : les amendes ont commencé le 16/11

local_api("GET", "/__wipe") if False else None

def phone(pw, errors):
    b, ctx, page = new_phone(pw, errors=errors, init=INIT)
    page.clock.set_system_time(NOW)
    return b, ctx, page

def set_name(page, name):
    page.evaluate("__wouaf.askProfile()")
    page.fill("#wName", name)
    page.click("#whoForm button[type=submit]")
    page.wait_for_timeout(700)

def ev(page, js, arg=None):
    return page.evaluate(js, arg) if arg is not None else page.evaluate(js)

def game(page): return ev(page, "JSON.parse(localStorage.getItem('wouaf-jeu')||'{}')")
def log(page): return ev(page, "JSON.parse(localStorage.getItem('wouaf-carnet')||'[]')")
def month(page): return ev(page, "(()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')})()")
def sheet_text(page): return ev(page, "document.querySelector('#sheet').innerText")
def modal_open(page): return ev(page, "document.querySelector('#modal').classList.contains('open')")

WALK_JS = """async ({minutes, chest, hunt}) => {
  const W = window.__wouaf, now = Date.now(), t0 = now - minutes*60000, track = [];
  for (let i = 0; i <= 60; i++) track.push({ lat: 48.8566 + i*0.0004, lon: 2.3522, t: t0 + i*(minutes*60000)/60 });
  const gw = { needs:{p:1,c:0}, items:[], got:{b:2,t:1,f:0,s:0}, itemPts:4, cells:[], newCells:3, acc:0, next:9999, treasure:false, last:null, chest, hunt };
  await W.startWalk({ type:'free', line:[], m:0, min:minutes, cat:'free', via:[], _title:'Balade libre', _icon:'🚶' },
    { t0, track, walked:2400, home:{lat:48.8566,lon:2.3522}, maxAway:0, gw, saved: now, pausedMs:0 });
}"""
def start_walk(page, minutes=35, chest=False, hunt=0):
    page.evaluate(WALK_JS, {"minutes": minutes, "chest": chest, "hunt": hunt}); page.wait_for_timeout(400)
def stop_walk(page):
    page.evaluate("__wouaf.stopWalk()"); page.wait_for_timeout(900)
def close_sheet(page):
    if modal_open(page): page.click("#sheetX"); page.wait_for_timeout(700)

local_api("GET", "/__wipe")
# un record du mois très long (Zoé, 4 h) pour que les balades de test ne battent pas le record (+50 testé dans e2e_duels.py)
_e = int(__import__("time").time()) - 3 * 3600
local_api("POST", "/walk", json.dumps({"walker": "Zoé", "walk": {"s": _e - 14400, "e": _e, "min": 240, "m": 15000, "cs": 0}, "sum": {}}).encode())
errs = []
with sync_playwright() as pw:
    bA, cA, A = phone(pw, errs)   # Éric (superviseur / testeur)
    bB, cB, B = phone(pw, errs)   # Léa
    bC, cC, C = phone(pw, errs)   # Tom
    for p in (A, B, C): open_app(p, 2000)

    # ---------- 1. Éric ----------
    set_name(A, "Éric")
    check("Éric : le 1er téléphone devient superviseur (jeton gardé)", bool(ev(A, "__wouaf.supToken()")) and ev(A, "__wouaf.isTester()"))
    set_name(B, " ERIC ")
    check("Éric : refusé sur un autre téléphone (accents/majuscules ignorés)", "déjà pris" in ev(B, "document.querySelector('#whoMsg').textContent") and not ev(B, "__wouaf.supToken()"))
    set_name(B, "Léa"); set_name(C, "Tom")
    check("prénoms normaux acceptés", ev(B, "JSON.parse(localStorage.getItem('wouaf-profil')).walker") == "Léa")
    check("pas de jeton sur le téléphone de Léa", not ev(B, "__wouaf.supToken()") and not ev(B, "__wouaf.isTester()"))

    # ---------- 2. menus ----------
    ev(A, "__wouaf.openMenu()"); check("menu d\'Éric : une seule entrée 🔑 Superviseur", "Superviseur" in sheet_text(A) and "Tout remettre à zéro" not in sheet_text(A)); A.click("#muSupAll"); A.wait_for_timeout(300); tA = sheet_text(A)
    check("menu d'Éric : Pause, tableau de bord, corriger, restaurer, annuler, remise à zéro", all(x in tA for x in ["Pause", "Tableau de bord", "Corriger une tirelire", "Restaurer un promeneur", "Annuler une balade", "Tout remettre à zéro"]), tA)
    check("menu d'Éric : pas de rappels (testeur)", "Mes rappels" not in tA)
    close_sheet(A)
    ev(B, "__wouaf.openMenu()"); tB = sheet_text(B)
    check("menu de Léa : rappels, lien discret « Superviseur », rien de plus", "Rappels" in tB and "Superviseur" in tB and "Tout remettre à zéro" not in tB and "Annuler une balade" not in tB, tB)
    close_sheet(B)

    # ---------- 3. balades ----------
    start_walk(B, 35, chest=True, hunt=500); stop_walk(B); close_sheet(B)
    gB = game(B); mk = month(B)
    check("Léa : balade payée (tirelire > 0)", gB["money"].get(mk, 0) > 0, gB.get("money"))
    check("Léa : coffre 5 € + trésor 5 € hors plafond (bonus = 10)", abs(gB["bonus"].get(mk, 0) - 10) < 0.001, gB.get("bonus"))
    eB = log(B)[0]
    check("Léa : la balade garde ce qu'elle a rapporté (gx)", eB["gx"]["c"] == 5 and eB["gx"]["h"] == 500 and eB["gx"]["w"] == 1, eB.get("gx"))
    start_walk(C, 25); stop_walk(C); close_sheet(C)
    start_walk(A, 35, chest=True, hunt=500); stop_walk(A)
    check("Éric : l'écran de fin indique le mode testeur", "test" in sheet_text(A).lower() and "Mode testeur" in sheet_text(A))
    close_sheet(A)
    gA = game(A)
    check("Éric : pas de tirelire, pas de coffre, pas de trésor payés", not gA.get("money", {}).get(mk) and not gA.get("bonus", {}).get(mk) and not gA.get("chests"), (gA.get("money"), gA.get("bonus")))
    check("Éric : jamais d'amende", ev(A, "__wouaf.processMalus().length") == 0)
    B.wait_for_timeout(800)
    d = kv()
    check("serveur : balades de Léa, Tom et Éric reçues (Éric à 0 clebsou, marqué testeur)", all(k in d for k in ["d:léa", "d:tom", "d:éric"]) and json.loads(d["d:éric"])["walks"][0]["cs"] == 0 and json.loads(d["d:éric"])["sum"]["test"] == 1, [k for k in d if k.startswith("d:")])
    check("serveur : les sorties d'Éric comptent pour l'humeur de Roxy (last)", json.loads(d["last"])["walker"] in ("Éric", "Léa", "Tom"))
    check("serveur : Éric n'est pas inscrit aux rappels", not any(k.startswith("u:") for k in d))

    # ---------- 4. annuler la balade de Léa ----------
    ev(A, "__wouaf.openDash({ token: __wouaf.supToken() }, true)"); A.wait_for_timeout(900)
    check("tableau de bord : boutons ❌ Annuler présents", A.locator("[data-void]").count() >= 2)
    A.locator("[data-void][data-w='Léa']").first.click(); A.wait_for_timeout(300)
    A.click("#vdGo"); A.wait_for_timeout(200)
    check("annuler sans motif refusé", "motif" in A.inner_text("#vdMsg").lower())
    A.fill("#vdWhy", "balade faite en voiture"); A.click("#vdGo"); A.wait_for_timeout(900)
    check("annulation envoyée", "Balade annulée" in sheet_text(A), sheet_text(A))
    A.click("#vdBack"); A.wait_for_timeout(900)
    check("tableau de bord : la balade apparaît barrée avec le motif", "annulée (balade faite en voiture)" in sheet_text(A) and A.locator(".dwalk.void s").count() == 1)
    close_sheet(A)
    d = kv(); check("serveur : correction « void » rangée pour Léa", any(a.get("type") == "void" for a in json.loads(d["a:léa"])))
    ev(B, "__wouaf.startupDigest()"); B.wait_for_timeout(2500)
    tB = sheet_text(B)
    check("Léa : message « Balade annulée » avec motif, gains retirés et amende", "Balade annulée" in tB and "balade faite en voiture" in tB and "amende" in tB, tB)
    gB = game(B)
    check("Léa : tirelire, coffre et trésor retirés", gB["money"].get(mk, 0) == 0 and gB["bonus"].get(mk, 0) == 0 and gB["chests"] == [], (gB["money"], gB["bonus"]))
    check("Léa : niveau / total remis comme avant", gB["total"] == 0, gB["total"])
    check("Léa : plus de série", gB["streak"]["n"] == 0 and gB["streak"]["day"] == "", gB["streak"])
    check("Léa : seule balade du jour annulée → amende −30 sans joker", gB.get("noJoker") or any(m["k"] == "void" for m in gB.get("malus", [])), (gB.get("noJoker"), gB.get("malus")))
    check("Léa : balade marquée annulée dans le carnet", log(B)[0].get("void", {}).get("why") == "balade faite en voiture")
    ev(B, "document.querySelector('#modal').classList.remove('open')")
    ev(B, "__wouaf.renderLog()"); ev(B, "__wouaf.sheetOuts()"); B.wait_for_timeout(900)
    check("Léa : « annulée » dans les dernières sorties", "annulée" in sheet_text(B))
    close_sheet(B)
    check("la balade annulée ne compte plus (série / semaine)", ev(B, "__wouaf.weekStats(Date.now()).n") == 0)
    d = kv(); check("serveur : Roxy retrouve sa dernière vraie sortie (pas la balade annulée)", json.loads(d["last"])["walker"] != "Léa")

    # ---------- 5. trésor : un seul gagnant ----------
    HUNT = """() => { const g = __wouaf.getGame(), wk = (()=>{ const f = __wouaf.weekKeyNow; return f ? f() : null; })();
      const lat = 48.8566, lon = 2.3522; g.home = { lat, lon };
      const d = new Date(Date.now() - 4*3600000); d.setHours(0,0,0,0); d.setDate(d.getDate() - (d.getDay() + 6) % 7);
      const t = new Date(d.getTime() + 5*3600000), key = t.getFullYear() + '-' + (t.getMonth()+1) + '-' + t.getDate();
      g.hunt = { wk: key, lat, lon, zlat: lat, zlon: lon, found:false, snapped:true }; }"""
    for p in (A, B, C): ev(p, HUNT)
    start_walk(B, 35); start_walk(C, 30); start_walk(A, 30)
    ev(B, "__wouaf.huntCheck({lat:48.8566, lon:2.3522})"); B.wait_for_timeout(1000)
    check("trésor : Léa (la 1re) le trouve, 500 clebsous", ev(B, "__wouaf.getGw().hunt") == 500 and ev(B, "__wouaf.getGame().hunt.found") > 0)
    ev(C, "__wouaf.huntCheck({lat:48.8566, lon:2.3522})"); C.wait_for_timeout(1000)
    check("trésor : Tom arrive trop tard, rien reçu, le trésor disparaît", not ev(C, "__wouaf.getGw().hunt") and ev(C, "__wouaf.getGame().hunt.gone") == "Léa")
    ev(A, "__wouaf.huntCheck({lat:48.8566, lon:2.3522})"); A.wait_for_timeout(800)
    check("trésor : Éric (testeur) ne prend jamais le trésor", ev(A, "__wouaf.getGw().hunt") == 0 and "Léa" == kv()["t:" + ev(B, "__wouaf.getGame().hunt.wk")])
    ms = ev(C, "__wouaf.missions().find(m => m.ic === '🏴‍☠️')")
    check("trésor : Tom voit « Léa a trouvé le trésor ! »", ms and "Léa a trouvé le trésor" in ms["t"], ms)
    stop_walk(B); close_sheet(B)
    gB = game(B)
    check("trésor : +5 € hors plafond pour Léa (comme un coffre)", abs(gB["bonus"].get(mk, 0) - 5) < 0.001, gB["bonus"])
    stop_walk(C); close_sheet(C); stop_walk(A); close_sheet(A)
    check("trésor : Tom n'a rien touché en bonus", not game(C).get("bonus", {}).get(mk))

    # ---------- 5b. trésor trouvé puis balade annulée : alerte pour Éric ----------
    start_walk(B, 10); ev(B, "__wouaf.getGw().hunt = 500"); ev(B, "__wouaf.cancelWalk()"); B.wait_for_timeout(900)
    ev(A, "__wouaf.openDash({ token: __wouaf.supToken() })"); A.wait_for_timeout(900)
    check("alerte : Éric voit « Léa a trouvé le trésor puis annulé »", "Léa" in sheet_text(A) and "annulé sa balade" in sheet_text(A), sheet_text(A)[:200])
    A.locator("[data-al][data-give]").first.click(); A.wait_for_timeout(1200)
    check("alerte : « Redonner 500 » envoie la correction à Léa et efface l'alerte", "annulé sa balade" not in sheet_text(A) and any(a.get("cs") == 500 for a in json.loads(kv()["a:léa"])))
    close_sheet(A)

    # ---------- 6. remise à zéro ----------
    ev(B, "localStorage.setItem('wouaf-avatar','data:image/jpeg;base64,AAAA')")
    ev(B, "localStorage.setItem('wouaf-envois', JSON.stringify([{walker:'Léa'}]))")
    ev(B, """(async () => { const c = document.createElement('canvas'); c.width = c.height = 10; const b = await new Promise(r => c.toBlob(r, 'image/jpeg')); await __wouaf.savePhoto(new File([b], 'a.jpg', { type:'image/jpeg' })); })()""")
    B.wait_for_timeout(500)
    rap = ev(B, "localStorage.getItem('wouaf-rappels')")
    ev(A, "__wouaf.openReset(__wouaf.supToken() ? { token: __wouaf.supToken() } : {})"); A.wait_for_timeout(300)
    check("remise à zéro : 1re confirmation", "Tout remettre à zéro" in sheet_text(A))
    A.click("#rsGo1"); A.wait_for_timeout(300)
    check("remise à zéro : 2e confirmation distincte", "Dernière confirmation" in sheet_text(A))
    # Léa est en balade au moment où la remise à zéro arrive : elle doit attendre
    start_walk(B, 22)
    A.click("#rsGo2"); A.wait_for_timeout(2500)
    d = kv()
    check("serveur : tout effacé (d:, b:, a:, t:, last), admin et pauses gardés", not any(k.startswith(("d:", "b:", "a:", "t:")) for k in d) and "last" not in d and "admin" in d and "reset" in d, [k for k in d])
    check("Éric : son téléphone repart de zéro aussi (écran « tout repart de zéro »)", "tout repart de zéro" in sheet_text(A), sheet_text(A)[:120])
    gA = game(A); fu = gA.get("firstUse", 0)
    check("Éric : jeton et prénom gardés", bool(ev(A, "__wouaf.supToken()")) and ev(A, "JSON.parse(localStorage.getItem('wouaf-profil')).walker") == "Éric")
    ev(B, "__wouaf.loadPauses().then(() => __wouaf.applyReset())"); B.wait_for_timeout(1200)
    check("Léa en balade : la remise à zéro attend", len(log(B)) >= 1 and ev(B, "__wouaf.getGw() !== null"))
    stop_walk(B)
    check("Léa : l'écran de fin de balade reste ouvert pendant l'attente", modal_open(B))
    B.click("#sheetX"); B.wait_for_timeout(2500)
    B.wait_for_function("window.__wouaf !== undefined"); B.wait_for_timeout(2200)
    gB = game(B)
    check("Léa : jeu, tirelire, carnet remis à zéro", gB.get("total", 0) == 0 and not gB.get("money", {}).get(mk) and log(B) == [] , (gB.get("total"), log(B)[:1]))
    check("Léa : prénom, rappels et photo de Roxy gardés", ev(B, "JSON.parse(localStorage.getItem('wouaf-profil')).walker") == "Léa" and ev(B, "localStorage.getItem('wouaf-rappels')") == rap and ev(B, "localStorage.getItem('wouaf-avatar')") is not None)
    check("Léa : envois en attente, traces, carnet effacés", ev(B, "localStorage.getItem('wouaf-envois')") is None and ev(B, "localStorage.getItem('wouaf-traces')") is None)
    n = ev(B, "new Promise(r => { const q = indexedDB.open('wouaf-photos', 1); q.onsuccess = () => { const t = q.result.transaction('p'); const c = t.objectStore('p').count(); c.onsuccess = () => r(c.result); }; })")
    check("Léa : album photo vidé", n == 0, n)
    check("Léa : écran « Wouaf Balades 2.0, tout repart de zéro ! »", "tout repart de zéro" in sheet_text(B), sheet_text(B)[:100])
    day = 86400000
    fuB = gB.get("firstUse", 0); now_ms = ev(B, "Date.now()")
    check("Léa : amendes repartent demain (premier jour = lendemain)", 0.9 * day < fuB - now_ms < 1.1 * day, fuB - now_ms)
    B.click("#w2Ok"); B.wait_for_timeout(900)
    check("puis le tuto", "Voici Roxy" in sheet_text(B), sheet_text(B)[:100])
    ev(C, "__wouaf.loadPauses().then(() => __wouaf.applyReset())"); C.wait_for_timeout(3500)
    check("Tom : remis à zéro aussi", game(C).get("total", 0) == 0 and log(C) == [])
    # téléphone neuf après la remise à zéro : pas d'écran « tout repart », juste le tuto normal
    bD, cD, D = new_phone(pw, errors=errs, init="localStorage.setItem('wouaf-init','1');")
    D.clock.set_system_time(NOW); open_app(D, 2500)
    check("téléphone neuf après la remise à zéro : tuto normal, pas d'écran « tout repart »", "Voici Roxy" in sheet_text(D) and "tout repart" not in sheet_text(D), sheet_text(D)[:80])

    check("aucune erreur JavaScript pendant les tests", not errs, errs)
    for b in (bA, bB, bC, bD): b.close()

print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅")
sys.exit(1 if FAILS else 0)
