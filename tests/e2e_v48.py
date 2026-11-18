"""v48 : budget du mois réparti (gains divisés par 2 quand on est en avance), coffres plus fréquents et moins chers (plafond du mois),
rues « neuves » après 7 jours, balade express 10 min (sans jeu, sans clebsous, sans amende), paie le dimanche soir."""
import sys, os, json, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
local_api("GET", "/__wipe")
INIT = "if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','48');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));}"
EV = lambda P, js: P.evaluate(js)
errs = []
with sync_playwright() as pw:
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.clock.set_system_time(datetime.datetime(2026, 11, 18, 12, 0, 0))   # mercredi 18 novembre, midi (amendes actives depuis le 16/11)
    P.set_viewport_size({"width": 393, "height": 760}); open_app(P, 3000)
    if P.locator("#dgNext").count(): P.click("#dgNext")
    mk = "2026-11"
    # 1. budget réparti
    allowed = EV(P, "__wouaf.paceAllowed()")
    check("budget du 18/11 : 15 € × 18/30 + 2 = 11 €", abs(allowed - 11) < 0.01, allowed)
    EV(P, f"(() => {{ const g = __wouaf.getGame(); __wouaf.ensureGame(); g.money['{mk}'] = 6; }})()")
    check("en dessous du rythme : gain entier", abs(EV(P, "__wouaf.addMoney(1)") - 1) < 0.001)
    EV(P, f"__wouaf.getGame().money['{mk}'] = 12")
    check("en avance sur le rythme : gain divisé par 2 (jamais zéro)", abs(EV(P, "__wouaf.addMoney(1)") - 0.5) < 0.001)
    # 2. coffres
    check("coffre normal : 100 clebsous (v3.9)", abs(EV(P, "__wouaf.chestValue()") - 1) < 0.001)
    EV(P, f"__wouaf.getGame().chestM = {{ '{mk}': 6 }}")
    check("budget coffres du mois atteint : petits coffres de 50", abs(EV(P, "__wouaf.chestValue()") - 0.5) < 0.001)
    EV(P, "(() => { const g = __wouaf.getGame(); g.chestM = {}; g.chests = [new Date(Date.now() - 4*86400000).toISOString()]; localStorage.setItem('wouaf-carnet', JSON.stringify([1,2,3,4,5].map(i => ({ id:i, date:new Date(Date.now()-i*86400000).toISOString(), min:30, m:2500 })))); })()")
    ch = EV(P, "__wouaf.chestChance()")
    check("coffre de nouveau chaud 3 jours après le dernier (avant : 10)", ch > 0, ch)
    EV(P, "__wouaf.renderHome && __wouaf.renderHome()"); P.wait_for_timeout(300)
    check("tuile coffre : 100", "100" in (P.locator("[data-lot='chest']").inner_text() if P.locator("[data-lot='chest']").count() else ""), P.locator("[data-lot='chest']").all_inner_texts())
    # 3. express
    if P.evaluate("document.querySelector('#modal').classList.contains('open')"): P.click("#sheetX"); P.wait_for_timeout(300)
    P.click("#freeWalk"); P.wait_for_timeout(400)
    check("« On part comment ? » propose la balade express 10 min", P.locator("#chExpress").count() == 1 and "10 min" in P.inner_text("#chExpress"))
    EV(P, "(() => { const g = __wouaf.getGame(); localStorage.setItem('wouaf-carnet', JSON.stringify([1,2].map(i => ({ id:i, date:new Date(Date.now()-i*3600000).toISOString(), min:8, m:500 })))); g.malus = []; g.malusEur = {}; g.firstUse = Date.now() - 30*86400000; })()")
    P.click("#chExpress"); P.wait_for_timeout(800)
    check("express : balade démarrée, mode express", EV(P, "!!__wouaf.state.walk && __wouaf.state.walk.express === 1 && document.body.classList.contains('express')"))
    check("express : pas de missions ni de trésor à l'écran", not P.locator("#wChips").is_visible() and not P.locator("#wTreasure").is_visible())
    gw0 = EV(P, "JSON.stringify(__wouaf.getGw().got)")
    for i in range(12):
        EV(P, f"__wouaf.gameFix({{ lat: 48.8566 + {i}*0.0009, lon: 2.3522, t: Date.now() + {i}*30000, a: 8 }}, {{lat:48.8566, lon:2.3522}})")
    check("express : rien ramassé en marchant 1 km", EV(P, "JSON.stringify(__wouaf.getGw().got)") == gw0)
    P.clock.run_for(11 * 60 * 1000)
    EV(P, "__wouaf.stopWalk()"); P.wait_for_timeout(1500)
    log = EV(P, "__wouaf.getLog()")
    check("express : notée dans le carnet (express)", log and log[0].get("express") == 1 and log[0]["min"] >= 10, log[:1])
    check("express : 3e balade courte de la semaine, mais pas d'amende", not any(m.get("k") == "short" for m in EV(P, "__wouaf.getGame().malus || []")), EV(P, "__wouaf.getGame().malus"))
    check("express : la classe express est retirée à la fin", not EV(P, "document.body.classList.contains('express')"))
    if P.evaluate("document.querySelector('#modal').classList.contains('open')"): P.click("#sheetX"); P.wait_for_timeout(300)
    # contrôle : la même 3e balade courte, mais normale, prend bien l'amende
    EV(P, "(() => { const g = __wouaf.getGame(); g.firstUse = Date.now() - 30*86400000; localStorage.setItem('wouaf-carnet', JSON.stringify([1,2].map(i => ({ id:i, date:new Date(Date.now()-i*3600000).toISOString(), min:8, m:500 })))); g.malus = []; g.malusEur = {}; })()")
    check("contrôle : une balade normale de 8 min (3e courte) prend l'amende", EV(P, "__wouaf.shortMalus(8)") > 0, EV(P, "__wouaf.shortMalus(8)"))
    EV(P, "(() => { const g = __wouaf.getGame(); g.malus = []; g.malusEur = {}; })()")
    b.close()

    # 4. paie le dimanche soir
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.clock.set_system_time(datetime.datetime(2026, 11, 22, 19, 0, 0))   # dimanche 22/11, 19 h
    open_app(P, 2500)
    wk = EV(P, "(() => { const d = new Date(Date.now() - 4*3600000); d.setHours(0,0,0,0); d.setDate(d.getDate() - (d.getDay() + 6) % 7); const t = new Date(d.getTime() + 5*3600000); return t.getFullYear() + '-' + String(t.getMonth()+1).padStart(2,'0') + '-' + String(t.getDate()).padStart(2,'0'); })()")
    EV(P, f"(() => {{ const g = __wouaf.getGame(); __wouaf.ensureGame(); g.wkBase = {{ wk:'{wk}', cum:0 }}; g.money = {{ '2026-11': 3 }}; g.weeks = {{}}; }})()")
    r = EV(P, "__wouaf.weekPayRoll()")
    check("dimanche 19 h : la semaine en cours est payée (3 €)", r and r["wk"] == wk and abs(r["eur"] - 3) < 0.001, r)
    check("… une seule fois", EV(P, "__wouaf.weekPayRoll()") is None)
    EV(P, "__wouaf.getGame().money['2026-11'] = 4")   # balade du dimanche soir, après la paie
    P.clock.set_system_time(datetime.datetime(2026, 11, 23, 10, 0, 0))      # lundi
    check("lundi : rien de plus (déjà payé dimanche)", EV(P, "__wouaf.weekPayRoll()") is None)
    P.clock.set_system_time(datetime.datetime(2026, 11, 29, 18, 30, 0))     # dimanche suivant 18 h 30
    EV(P, "__wouaf.getGame().money['2026-11'] = 6")
    r = EV(P, "__wouaf.weekPayRoll()")
    check("dimanche suivant : paie = balade du dimanche soir d'avant + la semaine (3 €)", r and abs(r["eur"] - 3) < 0.001, r)
    b.close()

    # 5. pas ouvert dimanche : paie à l'ouverture suivante
    b, c, P = new_phone(pw, errors=errs, init=INIT)
    P.clock.set_system_time(datetime.datetime(2026, 11, 20, 12, 0, 0))   # vendredi
    open_app(P, 2500)
    wk = EV(P, "(() => { const d = new Date(Date.now() - 4*3600000); d.setHours(0,0,0,0); d.setDate(d.getDate() - (d.getDay() + 6) % 7); const t = new Date(d.getTime() + 5*3600000); return t.getFullYear() + '-' + String(t.getMonth()+1).padStart(2,'0') + '-' + String(t.getDate()).padStart(2,'0'); })()")
    EV(P, f"(() => {{ const g = __wouaf.getGame(); __wouaf.ensureGame(); g.wkBase = {{ wk:'{wk}', cum:0 }}; g.money = {{ '2026-11': 2 }}; g.weeks = {{}}; }})()")
    check("vendredi : pas encore de paie", EV(P, "__wouaf.weekPayRoll()") is None)
    P.clock.set_system_time(datetime.datetime(2026, 11, 24, 9, 0, 0))   # mardi suivant
    r = EV(P, "__wouaf.weekPayRoll()")
    check("pas ouvert dimanche : payé à l'ouverture suivante", r and r["wk"] == wk and abs(r["eur"] - 2) < 0.001, r)
    b.close()
real = [x for x in errs if "Failed to load resource" not in x and "ERR_FAILED" not in x]
check("aucune erreur JavaScript", not real, real[:5])
print("\n" + ("OK" if not FAILS else "ÉCHECS : " + ", ".join(FAILS)))
sys.exit(1 if FAILS else 0)
