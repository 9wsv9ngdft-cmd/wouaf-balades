import sys; sys.path.insert(0, __import__("os").path.dirname(__file__))
from e2e_common import *
errs = []
with sync_playwright() as pw:
    b, ctx, page = new_phone(pw, errors=errs)
    page.on("console", lambda m: print("console:", m.type, m.text[:200]) if m.type == "error" else None)
    open_app(page, 3000)
    print("title:", page.title(), "| errors:", errs)
    print("appVer:", page.evaluate("document.querySelector('#appVer').textContent"))
    print("modal open:", page.evaluate("document.querySelector('#modal').classList.contains('open')"))
    page.screenshot(path="/tmp/smoke.png")
    b.close()
