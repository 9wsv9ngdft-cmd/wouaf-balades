import sys; sys.path.insert(0, "/home/claude/wouaf-balades/tests")
from e2e_common import *
errs=[]
with sync_playwright() as pw:
    b, c, p = new_phone(pw, errors=errs, init="localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','37');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));")
    p.goto("http://127.0.0.1:8000/index.html#go"); p.wait_for_timeout(5000)
    print("walk started:", p.evaluate("!!__wouaf.state.walk"), "| hash:", p.evaluate("location.hash"), "| walking class:", p.evaluate("document.body.classList.contains('walking')"))
    b2, c2, q = new_phone(pw, errors=errs, init="localStorage.setItem('wouaf-init','1');localStorage.setItem('wouaf-tuto','1');localStorage.setItem('wouaf-vu','37');localStorage.setItem('wouaf-stats-ok','false');localStorage.setItem('wouaf-profil', JSON.stringify({walker:'Léa'}));")
    open_app(q, 3000)
    if q.evaluate("document.querySelector('#modal').classList.contains('open')"): q.evaluate("document.querySelector('#sheetX').click()")
    q.evaluate("__wouaf.openMenu()"); q.click("#muShort"); q.wait_for_timeout(400)
    t = q.evaluate("document.querySelector('#sheet').innerText"); print("sheet ok:", "Télécharger le raccourci" in t and "3 gestes" in t)
print("errs", errs); sys.exit(1 if errs else 0)
