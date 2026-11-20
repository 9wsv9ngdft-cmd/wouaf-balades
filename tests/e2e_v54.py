"""v4.4 : comptes. Écran d'entrée (Je m'inscris / J'ai déjà un compte), identifiant fixe, prénom affiché modifiable,
nouveau téléphone, bascule du compte superviseur, Superviseur › Comptes (inscriptions fermées, code oublié)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from e2e_common import *
FAILS = []
def check(n, c, x=""):
    print(("PASS " if c else "FAIL ") + n + ((" → " + str(x)) if (x != "" and not c) else ""))
    if not c: FAILS.append(n)
def base(name=None):
    p = f"localStorage.setItem('wouaf-profil', JSON.stringify({{walker:'{name}'}}));" if name else ""
    return ("if(!localStorage.getItem('wouaf-init')){localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','57');"
            "localStorage.setItem('wouaf-welcome2','0');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-sc-tip','1');localStorage.setItem('wouaf-hon-vu','2099-01');" + p + "}")
sheet = lambda P: P.evaluate("document.querySelector('#sheet').innerText")
post = lambda path, body: local_api("POST", path, json.dumps(body).encode())
local_api("GET", "/__wipe")
errs = []
with sync_playwright() as pw:
    # 1) Léa, téléphone d'avant : l'écran d'entrée s'ouvre, sans croix
    bA, cA, A = new_phone(pw, errors=errs, init=base("Léa"), acc=True); A.on("dialog", lambda d: d.accept()); open_app(A, 3500)
    t = sheet(A)
    check("écran d'entrée à l'ouverture (Léa)", "Salut Léa" in t and "Je m'inscris" in t and "J'ai déjà un compte" in t, t[:200])
    check("pas de croix pour fermer l'écran d'entrée", A.evaluate("getComputedStyle(document.querySelector('#sheetX')).display") == 'none')
    A.click("#agNew"); A.wait_for_timeout(300)
    check("identifiant proposé (sans accent) et prénom déjà rempli", A.input_value("#aLogin") == "lea" and A.input_value("#aName") == "Léa", (A.input_value("#aLogin"), A.input_value("#aName")))
    check("avertissement « Retiens bien ton identifiant »", "Retiens bien ton identifiant" in sheet(A))
    A.fill("#aCode", "1234"); A.fill("#aCode2", "1235"); A.click("#agForm button[type=submit]"); A.wait_for_timeout(300)
    check("deux codes différents : refusé", "pas pareils" in sheet(A))
    A.fill("#aCode2", "1234"); A.click("#agForm button[type=submit]"); A.wait_for_timeout(1200)
    t = sheet(A)
    check("compte créé : identifiant affiché", "Ton compte est créé" in t and "lea" in t, t[:200])
    A.click("#agOk"); A.wait_for_timeout(900)
    acc = A.evaluate("__wouaf.getAcc()")
    check("le téléphone garde le compte, la clé reste « Léa »", acc and acc["login"] == "lea" and acc["key"] == "Léa", acc)
    check("le code n'est pas gardé en clair sur le serveur", "1234" not in json.dumps(kv().get("acc:lea", "")))
    # 2) changer de prénom : seul l'affichage change
    A.evaluate("__wouaf.askProfile()"); A.wait_for_timeout(300)
    check("☰ › 👤 = Mon compte (identifiant visible)", "Mon compte" in sheet(A) and "lea" in sheet(A))
    A.fill("#acName", "Lilou"); A.click("#acForm button[type=submit]"); A.wait_for_timeout(1000)
    check("prénom changé en Lilou", "Lilou" in sheet(A) and A.evaluate("document.querySelector('#whoText').textContent") == "Salut Lilou")
    check("la clé envoyée au serveur ne bouge pas", A.evaluate("JSON.parse(localStorage.getItem('wouaf-profil')).walker") == "Léa")
    names = json.loads(local_api("GET", "/pause")[1])["names"]
    check("le serveur affiche Lilou pour la clé Léa", names.get("léa", {}).get("n") == "Lilou", names)
    A.evaluate("__wouaf.backupNow && __wouaf.backupNow(true)"); A.wait_for_timeout(800)
    # 3) nouveau téléphone : « J'ai déjà un compte » → mêmes données
    bB, cB, B = new_phone(pw, errors=errs, init=base(), acc=True); B.on("dialog", lambda d: d.accept()); open_app(B, 3500)
    check("nouveau téléphone : écran d'entrée", "Bienvenue" in sheet(B))
    B.click("#agLog"); B.fill("#aLogin", "lea"); B.fill("#aPass", "0000"); B.click("#agForm button[type=submit]"); B.wait_for_timeout(900)
    check("mauvais code : refusé", "incorrect" in sheet(B))
    B.fill("#aPass", "1234"); B.click("#agForm button[type=submit]"); B.wait_for_timeout(3500)
    open_app(B, 2500) if B.evaluate("!window.__wouaf") else None
    check("connecté : clé Léa, prénom Lilou", B.evaluate("JSON.parse(localStorage.getItem('wouaf-profil')).walker") == "Léa" and B.evaluate("__wouaf.myName()") == "Lilou")
    # 4) superviseur : bascule
    tok = json.loads(post("/claim", {"walker": "Éric"})[1])["token"]
    check("avant la bascule, l'ancien code marche", post("/dash", {"code": "1234"})[0] == 200)
    sup_init = base("Éric") + f"if(!localStorage.getItem('wouaf-sup')) localStorage.setItem('wouaf-sup', JSON.stringify('{tok}'));"
    bS, cS, S = new_phone(pw, errors=errs, init=sup_init, acc=True); open_app(S, 3500)
    check("téléphone superviseur : écran « Créer le compte superviseur »", "Créer le compte superviseur" in sheet(S), sheet(S)[:150])
    S.fill("#aLogin", "chef"); S.fill("#aName", "Le Chef"); S.fill("#aCode", "2468"); S.fill("#aCode2", "2468")
    S.click("#scGo"); S.wait_for_timeout(200)
    check("il faut confirmer (l'ancien code s'arrête)", "Sûr" in S.inner_text("#scGo"))
    S.click("#scGo"); S.wait_for_timeout(1200)
    check("compte superviseur créé", "Compte superviseur créé" in sheet(S) and S.evaluate("__wouaf.getAcc().sup") == 1)
    check("l'ancien code ne marche plus", post("/dash", {"code": "1234"})[0] == 403)
    check("le téléphone superviseur garde ses pouvoirs", S.evaluate("__wouaf.isTester()"))
    # 5) Superviseur › Comptes : liste, inscriptions fermées
    S.click("#scOk"); S.wait_for_timeout(300)
    S.evaluate("__wouaf.sheetAccounts()"); S.wait_for_timeout(900)
    t = sheet(S)
    check("Comptes : Lilou (avant « Léa ») et Le Chef", "Lilou" in t and "Le Chef" in t and "Inscriptions ouvertes" in t, t[:300])
    S.click("#caOpen"); S.wait_for_timeout(1000)
    check("inscriptions fermées", "Inscriptions fermées" in sheet(S))
    S.click("[data-car='lea']"); S.click("[data-car='lea']"); S.wait_for_timeout(900)
    check("code de Lilou remis à zéro", "nouveau code à choisir" in sheet(S))
    # 6) 3e téléphone : inscriptions fermées ; connexion au compte superviseur
    bC, cC, C = new_phone(pw, errors=errs, init=base(), acc=True); C.on("dialog", lambda d: d.accept()); open_app(C, 3500)
    check("inscriptions fermées : « Je m'inscris » grisé", C.evaluate("document.querySelector('#agNew').disabled") and "fermées" in sheet(C))
    C.click("#agLog"); C.fill("#aLogin", "chef"); C.fill("#aPass", "2468"); C.click("#agForm button[type=submit]"); C.wait_for_timeout(2000)
    check("connexion au compte superviseur depuis un autre téléphone", bool(C.evaluate("__wouaf.supToken()")) and C.evaluate("__wouaf.isTester()") and C.evaluate("__wouaf.myName()") == "Le Chef")
    check("2 téléphones superviseur connectés", json.loads(post("/sup-phones", {"token": tok})[1])["phones"] == 2)
    # 7) code oublié : Lilou choisit un nouveau code
    bD, cD, D = new_phone(pw, errors=errs, init=base(), acc=True); D.on("dialog", lambda d: d.accept()); open_app(D, 3500)
    D.click("#agLog"); D.fill("#aLogin", "lea"); D.fill("#aPass", "1234"); D.click("#agForm button[type=submit]"); D.wait_for_timeout(900)
    check("code remis à zéro : on en choisit un nouveau", "Nouveau code" in sheet(D))
    D.fill("#aCode", "9876"); D.fill("#aCode2", "9876"); D.click("#agForm button[type=submit]"); D.wait_for_timeout(3500)
    open_app(D, 2500) if D.evaluate("!window.__wouaf") else None
    check("reconnectée avec le nouveau code", D.evaluate("__wouaf.myName()") == "Lilou")
    check("aucune erreur JavaScript", not errs, errs)
print("\n%d échec(s)" % len(FAILS) if FAILS else "\nTout est vert ✅"); sys.exit(1 if FAILS else 0)
