"""v51 (3.9, avec la 3.8) : cadeau argenté (un seul gagnant), coffre à 100 orange-rouge, pluie de billets, objets selon la cagnotte, trophées du mois et palmarès."""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
_e = int(datetime.datetime.now().timestamp()) - 3 * 3600   # un record du mois très long (Zoé) pour que les balades de test ne touchent pas le +50
local_api("POST", "/walk", json.dumps({"walker": "Zoé", "walk": {"s": _e - 14400, "e": _e, "min": 240, "m": 15000, "cs": 0}, "sum": {}}).encode())
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','51');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-hon-vu','2099-01');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'%s'}));}"
EV = lambda P, js: P.evaluate(js)
post = lambda path, body: json.loads(local_api("POST", path, json.dumps(body).encode())[1] or b"{}")
get = lambda path: json.loads(local_api("GET", path)[1] or b"{}")

LAT, LON = 48.8566, 2.3522
START = """async ({minutes, rain}) => {
  const W = window.__wouaf, now = Date.now(), t0 = now - minutes*60000, track = [];
  for (let i = 0; i <= 60; i++) track.push({ lat: 48.8566, lon: 2.3522 + i*0.00004, t: t0 + i*(minutes*60000)/60 });
  const gw = { needs:{p:0,c:0}, items:[], got:{b:0,t:0,f:0,s:0}, itemPts:0, cells:[], newCells:0, acc:0, next:99999, treasure:true, last:null, chest:false, hunt:0, rain, rainChecked:true };
  await W.startWalk({ type:'free', line:[], m:0, min:minutes, cat:'free', via:[], _title:'Balade libre', _icon:'🚶' },
    { t0, track, walked:2400, home:{lat:48.8566,lon:2.3522}, maxAway:0, gw, saved: now, pausedMs:0 });
}"""
errs = []
with sync_playwright() as pw:
    # Éric superviseur (jeton) : il pose le cadeau argenté
    tok = post("/claim", {"walker": "Éric"})["token"]
    sv = post("/silver-set", {"token": tok, "lat": LAT + 0.002, "lon": LON})["silver"]
    check("Éric pose le cadeau argenté (Worker)", bool(sv and sv["id"]), sv)
    bL, cL, L = new_phone(pw, errors=errs, init=INIT % "Léa"); bT, cT, T = new_phone(pw, errors=errs, init=INIT % "Tom")
    for P in (L, T):
        P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 2500)
        if P.locator("#dgNext").count(): P.click("#dgNext")
        EV(P, "(() => { const g = __wouaf.getGame(); __wouaf.ensureGame(); g.home = {lat:48.8566, lon:2.3522}; g.firstUse = Date.now() - 40*86400000; })()")
        EV(P, "__wouaf.loadPauses()"); P.wait_for_timeout(800); EV(P, "__wouaf.renderHome()"); P.wait_for_timeout(300)
    # ---- cadeau argenté : tuile, fiche, un seul gagnant
    t = L.locator("[data-lot='bills']")
    check("v4.5 : tuile argent « Billets » 250 · coffre sur l'accueil de Léa", t.count() == 1 and "250" in t.inner_text(), t.all_inner_texts() if t.count() else "")
    t.click(); L.wait_for_timeout(400); L.click("#blSilver"); L.wait_for_timeout(500)
    check("fiche du cadeau argenté", "Cadeau argenté" in L.inner_text("#sheet") and "Un seul gagnant" in L.inner_text("#sheet").replace("un seul", "Un seul") and L.locator("#svGo").count() == 1, L.inner_text("#sheet")[:160])
    L.click("#svX"); L.wait_for_timeout(300)
    check("nuage argenté dans les zones de la carte", EV(L, "(() => { try { return !!__wouaf.silverLive(); } catch(e) { return false; } })()"))
    L.evaluate(START, {"minutes": 35, "rain": False}); L.wait_for_timeout(400)
    EV(L, f"__wouaf.silverCheck({{lat:{LAT + 0.0021}, lon:{LON}}})"); L.wait_for_timeout(1200)
    check("Léa trouve le cadeau : 250 dans la balade, serveur = Léa", EV(L, "__wouaf.getGw().silver") == 250 and EV(L, "__wouaf.getGame().silver.found > 0") and get("/pause")["silver"]["by"] == "Léa", get("/pause")["silver"])
    check("loin du cadeau : rien", EV(T, "__wouaf.silverLive() !== null"))
    EV(T, "__wouaf.loadPauses()"); T.wait_for_timeout(800)
    check("Tom : le cadeau a disparu de l'accueil", EV(T, "__wouaf.silverLive()") is None)
    EV(L, "__wouaf.stopWalk()"); L.wait_for_timeout(1500)
    if L.locator("#sheetX").count() and EV(L, "document.querySelector('#modal').classList.contains('open')"): L.click("#sheetX"); L.wait_for_timeout(300)
    g = EV(L, "__wouaf.getGame()"); k = EV(L, "(()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')})()")
    check("Léa : +250 clebsous hors plafond (2,50 € de bonus)", abs((g["bonus"].get(k, 0)) - 2.5) < 0.001, g.get("bonus"))
    ent = EV(L, "__wouaf.getLog()[0]")
    check("la balade garde le gain du cadeau (gx.sv) pour pouvoir l'annuler", ent and ent.get("gx", {}).get("sv") == 250, ent and ent.get("gx"))
    # ---- coffre à 100
    check("coffre à 100 clebsous", abs(EV(L, "__wouaf.chestValue()") - 1) < 0.001)
    # ---- objets selon la cagnotte
    EV(L, f"__wouaf.getGame().money['{k}'] = 0")
    check("cagnotte normale : ⭐ vaut 5, 🦴 vaut 1", EV(L, "__wouaf.objVal(5)") == 5 and EV(L, "__wouaf.objVal(1)") == 1)
    EV(L, f"__wouaf.getGame().money['{k}'] = 15")
    check("en avance sur le rythme : ⭐ vaut 3, 🍖 2, 🦴 reste 1", EV(L, "__wouaf.objVal(5)") == 3 and EV(L, "__wouaf.objVal(3)") == 2 and EV(L, "__wouaf.objVal(1)") == 1, [EV(L, "__wouaf.objVal(5)"), EV(L, "__wouaf.objVal(3)")])
    EV(L, f"__wouaf.getGame().money['{k}'] = Math.ceil(__wouaf.paceAllowed())")
    add = EV(L, "__wouaf.addMoney(1, 0.4)")
    check("addMoney : la part des objets n'est pas coupée deux fois (0,6 ÷ 2 + 0,4)", abs(add - 0.7) < 0.011, add)
    EV(L, f"__wouaf.getGame().money['{k}'] = 0")
    # ---- il pleut des billets
    L.evaluate(START, {"minutes": 35, "rain": True}); L.wait_for_timeout(400)
    for i in range(12):
        EV(L, f"__wouaf.gameFix({{ lat: {LAT} + {i}*0.00027, lon: {LON}, t: Date.now() + {i}*30000, a: 8 }}, {{lat:{LAT}, lon:{LON}}})")
    gw = EV(L, "__wouaf.getGw()")
    check("sous la pluie, des billets sont tombés", len(gw.get("bills", [])) >= 1 and gw.get("billN", 0) >= 1, {k: gw.get(k) for k in ("bills", "billN", "nextBill", "acc")})
    b0 = gw["bills"][0]; pts0 = gw["itemPts"]
    EV(L, f"__wouaf.gameFix({{ lat: {b0['lat']}, lon: {b0['lon']}, t: Date.now() + 999999, a: 8 }}, {{lat:{LAT}, lon:{LON}}})")
    gw = EV(L, "__wouaf.getGw()")
    check("un billet ramassé = +4 clebsous", gw.get("billGot") == 1 and gw["itemPts"] - pts0 == 4, {"got": gw.get("billGot"), "pts": gw["itemPts"] - pts0})
    check("jamais plus de 8 billets par balade", all(True for _ in [0]) and EV(L, "(() => { const g = __wouaf.getGw(); return (g.billN || 0) <= 8; })()"))
    EV(L, "__wouaf.stopWalk()"); L.wait_for_timeout(1800)
    ent = EV(L, "__wouaf.getLog()[0]")
    check("récap : plus de ×1,5, mais les billets", ent and "billet" in json.dumps(ent.get("recap", ""), ensure_ascii=False) + EV(L, "document.body.innerText") and "×1,5" not in EV(L, "document.body.innerText"), "")
    L.wait_for_timeout(600)
    d = get("/__kv") if False else kv()
    ws = json.loads(d.get("d:léa", "{}") or "{}").get("walks", [])
    check("le serveur sait qu'il pleuvait (rn) pour le trophée Courageux", ws and ws[0].get("rn") == 1, ws[:1])
    # ---- trophées du mois dernier
    today = datetime.date.today(); first = today.replace(day=1); prev = (first - datetime.timedelta(days=1)); pm = prev.strftime("%Y-%m")
    def at(day, hour): return int(datetime.datetime(prev.year, prev.month, day, hour - 1, 0, tzinfo=datetime.timezone.utc).timestamp())
    for who, day, hour, extra in (("Léa", 3, 7, {"cc": 4, "pp": 2, "nc": 9, "m": 4000, "rn": 1}), ("Léa", 5, 14, {"cc": 2, "pp": 1, "nc": 4, "m": 3000}), ("Tom", 4, 14, {"cc": 3, "pp": 7, "nc": 3, "m": 9000, "du": 1})):
        e = at(day, hour); w = {"s": e - 2400, "e": e, "min": 40, "m": 2500, "cs": 30}; w.update(extra)
        post("/walk", {"walker": who, "walk": w, "sum": {}})
    EV(L, "localStorage.setItem('wouaf-hon-vu', '')")
    card = EV(L, "__wouaf.honorsCard().then(c => c ? { party: c.party, html: c.html } : null)")
    check("le 1er du mois : la carte des trophées apparaît (confettis)", card and card["party"] and "Roi du Caca" in card["html"] and "Maître Arroseur" in card["html"], (card or {}).get("html", "")[:200])
    check("Roi du Caca : Léa (6 cacas), Maître Arroseur : Tom (7 pipis)", card and "Roi du Caca : Toi" in card["html"] and "Maître Arroseur : Tom" in card["html"], (card or {}).get("html", "")[:400])
    check("résumé drôle : kilomètres, cacas, pipis", card and "km à vous tous" in card["html"] and "cacas" in card["html"] and "pipis" in card["html"], (card or {}).get("html", "")[-400:])
    check("la carte ne revient pas deux fois", EV(L, "__wouaf.honorsCard()") is None and json.loads(EV(L, "localStorage.getItem('wouaf-hon-vu')")) == pm)
    EV(L, "__wouaf.sheetPalmares()"); L.wait_for_timeout(1500)
    t = L.inner_text("#sheet")
    check("palmarès : tableau d'honneur de l'année et mois par mois", "palmarès" in t.lower() and str(prev.year) in t and "mois par mois" in t.lower() and "trophée" in t, t[:300])
    L.screenshot(path="/tmp/palmares.png")
    L.click("#palX"); L.wait_for_timeout(300)
    # menu
    EV(L, "__wouaf.openMenu()"); L.wait_for_timeout(400)
    check("v4.5.5 : menu sans Palmarès (il est dans le classement)", L.locator("#muHon").count() == 0)
    check("menu : toujours sans défilement", EV(L, "(() => { const s = document.querySelector('#sheet'); return s.scrollHeight <= s.clientHeight + 2; })()"))
    L.screenshot(path="/tmp/menu39.png")
    for b in (bL, bT): b.close()
print("aucune erreur JavaScript" if not errs else errs)
check("aucune erreur JavaScript", not errs, errs[:3])
print("\nTout est vert ✅" if not FAILS else "\nÉCHECS : " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
