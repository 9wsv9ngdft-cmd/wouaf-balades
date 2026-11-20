// 👤 v4.4 : comptes (identifiant fixe, prénom affiché modifiable, code haché, superviseur, inscriptions ouvertes / fermées)
import test from "node:test";
import assert from "node:assert/strict";
import { loadWorker, makeEnv, client } from "./load-worker.mjs";

const setup = async () => { const worker = await loadWorker(), env = makeEnv(); return { worker, env, api: client(worker, env) }; };
const walk = (e, extra) => Object.assign({ s: e - 1800, e, min: 30, m: 2500, cs: 40 }, extra);

test("inscription d'un promeneur d'avant : la clé reste son prénom, le code n'est jamais gardé en clair", async () => {
  const { api, env } = await setup();
  const r = await api.post("/acc-signup", { login: "leo2010", name: "Léo", code: "1234", key: "Léo" });
  assert.equal(r.status, 200); assert.equal(r.j.acc.key, "Léo"); assert.equal(r.j.acc.name, "Léo"); assert.ok(r.j.token.length >= 16);
  const raw = await env.WOUAF.get("acc:leo2010");
  assert.ok(raw && !raw.includes("1234"));                                       // code haché
  const p = await api.get("/pause");
  assert.equal(p.j.names["léo"].n, "Léo"); assert.equal(p.j.signup, true);
  assert.ok(!JSON.stringify(p.j.names).includes("leo2010"));                      // l'identifiant n'est pas public
  // identifiant, clé et prénom déjà pris
  assert.equal((await api.post("/acc-signup", { login: "LEO2010", name: "Zoé", code: "9999", key: "Zoé" })).status, 409);
  assert.equal((await api.post("/acc-signup", { login: "autre", name: "Zoé", code: "9999", key: "Léo" })).status, 409);
  assert.equal((await api.post("/acc-signup", { login: "autre", name: "leo", code: "9999", key: "Zoé" })).status, 409);
  // mauvais formats, Éric réservé
  assert.equal((await api.post("/acc-signup", { login: "x", name: "Zoé", code: "1234" })).status, 400);
  assert.equal((await api.post("/acc-signup", { login: "zoe", name: "Zoé", code: "12" })).status, 400);
  assert.equal((await api.post("/acc-signup", { login: "eric", name: "Zoé", code: "1234" })).status, 403);
  // nouveau promeneur : clé = identifiant, mot de passe accepté
  const z = await api.post("/acc-signup", { login: "zoe", name: "Zoé", code: "motdepasse" });
  assert.equal(z.status, 200); assert.equal(z.j.acc.key, "zoe");
});

test("connexion : bon code, mauvais code, 10 essais par jour", async () => {
  const { api } = await setup();
  await api.post("/acc-signup", { login: "leo", name: "Léo", code: "1234", key: "Léo" });
  const ok = await api.post("/acc-login", { login: "Leo", code: "1234" });
  assert.equal(ok.status, 200); assert.equal(ok.j.acc.key, "Léo"); assert.equal(ok.j.supToken, undefined);
  assert.equal((await api.post("/acc-login", { login: "leo", code: "0000" })).status, 403);
  assert.equal((await api.post("/acc-login", { login: "inconnu", code: "0000" })).status, 403);
  for (let i = 0; i < 9; i++) await api.post("/acc-login", { login: "leo", code: "0000" });
  assert.equal((await api.post("/acc-login", { login: "leo", code: "1234" })).status, 429);
});

test("changer de prénom : seul l'affichage change, plus de doublon côté serveur", async () => {
  const { api, env } = await setup();
  const r = await api.post("/acc-signup", { login: "leo", name: "Léo", code: "1234", key: "Léo" });
  await api.post("/acc-signup", { login: "zoe", name: "Zoé", code: "1234", key: "Zoé" });
  const now = Math.floor(Date.now() / 1000);
  await api.post("/walk", { walker: "Léo", walk: walk(now - 7200) });
  assert.equal((await api.post("/acc-rename", { login: "leo", token: "faux-jeton-0123456789", name: "Tom" })).status, 403);
  assert.equal((await api.post("/acc-rename", { login: "leo", token: r.j.token, name: "zoe" })).status, 409);   // prénom de quelqu'un d'autre
  assert.equal((await api.post("/acc-rename", { login: "leo", token: r.j.token, name: "Éric" })).status, 403);
  const rn = await api.post("/acc-rename", { login: "leo", token: r.j.token, name: "Tom" });
  assert.equal(rn.status, 200); assert.equal(rn.j.acc.key, "Léo"); assert.equal(rn.j.acc.name, "Tom");
  await api.post("/walk", { walker: "Léo", walk: walk(now - 600) });                                           // le téléphone envoie toujours la clé
  const keys = (await env.WOUAF.list({ prefix: "d:" })).keys.map(k => k.name);
  assert.deepEqual(keys, ["d:léo"]);                                                                            // une seule fiche
  assert.equal((await api.get("/pause")).j.names["léo"].n, "Tom");
});

test("code oublié : le superviseur le remet à zéro, le promeneur en choisit un nouveau", async () => {
  const { api } = await setup();
  const tok = (await api.post("/claim", { walker: "Éric" })).j.token;
  await api.post("/acc-signup", { login: "leo", name: "Léo", code: "1234", key: "Léo" });
  assert.equal((await api.post("/acc-reset", { token: "faux-jeton-0123456789", login: "leo" })).status, 403);
  assert.equal((await api.post("/acc-reset", { token: tok, login: "leo" })).status, 200);
  assert.equal((await api.post("/acc-login", { login: "leo", code: "1234" })).j.needCode, true);
  assert.equal((await api.post("/acc-login", { login: "leo", newCode: "12" })).status, 400);
  const n = await api.post("/acc-login", { login: "leo", newCode: "5678" });
  assert.equal(n.status, 200);
  assert.equal((await api.post("/acc-login", { login: "leo", code: "5678" })).status, 200);
  // changer de code soi-même
  assert.equal((await api.post("/acc-code", { login: "leo", token: n.j.token, old: "0000", code: "4321" })).status, 403);
  assert.equal((await api.post("/acc-code", { login: "leo", token: n.j.token, old: "5678", code: "4321" })).status, 200);
  assert.equal((await api.post("/acc-login", { login: "leo", code: "4321" })).status, 200);
  // liste des comptes pour le superviseur
  const l = await api.post("/acc-list", { token: tok });
  assert.equal(l.j.accounts.length, 1); assert.equal(l.j.accounts[0].login, "leo"); assert.equal(l.j.open, true);
});

test("inscriptions fermées : plus de nouveaux comptes, mais les promeneurs qui ont déjà des balades peuvent créer le leur", async () => {
  const { api } = await setup();
  const tok = (await api.post("/claim", { walker: "Éric" })).j.token;
  await api.post("/walk", { walker: "Léo", walk: walk(Math.floor(Date.now() / 1000) - 600) });
  assert.equal((await api.post("/acc-open", { token: tok, open: false })).j.open, false);
  assert.equal((await api.get("/pause")).j.signup, false);
  assert.equal((await api.post("/acc-signup", { login: "intrus", name: "Intrus", code: "1234" })).status, 403);
  assert.equal((await api.post("/acc-signup", { login: "zoe", name: "Zoé", code: "1234", key: "Zoé" })).status, 403);   // pas de balade
  assert.equal((await api.post("/acc-signup", { login: "leo", name: "Léo", code: "1234", key: "Léo" })).status, 200);
  await api.post("/acc-open", { token: tok, open: true });
  assert.equal((await api.post("/acc-signup", { login: "zoe", name: "Zoé", code: "1234" })).status, 200);
});

test("bascule superviseur : compte créé depuis le téléphone superviseur, l'ancien code ne marche plus, connexion ailleurs = jeton superviseur en plus", async () => {
  const { api } = await setup();
  const tok = (await api.post("/claim", { walker: "Éric" })).j.token;
  assert.equal((await api.post("/dash", { code: "1234" })).status, 200);                                 // ancien code : encore valable
  assert.equal((await api.post("/acc-sup-create", { code: "1234", login: "chef", name: "Le Chef", code2: "x" })).status, 403);   // il faut le téléphone superviseur
  const c = await api.post("/acc-sup-create", { token: tok, login: "chef", name: "Le Chef", code: "2468" });
  assert.equal(c.status, 200); assert.equal(c.j.acc.key, "Éric"); assert.equal(c.j.acc.sup, 1);
  assert.equal((await api.post("/acc-sup-create", { token: tok, login: "chef2", name: "X", code: "2468" })).status, 409);   // un seul
  assert.equal((await api.post("/dash", { code: "1234" })).status, 403);                                 // l'ancien code ne marche plus
  assert.equal((await api.post("/claim", { walker: "Éric", code: "1234" })).status, 403);
  assert.equal((await api.post("/dash", { token: tok })).status, 200);                                   // le téléphone superviseur reste connecté
  const l = await api.post("/acc-login", { login: "chef", code: "2468" });                              // 2e téléphone
  assert.equal(l.status, 200); assert.ok(l.j.supToken); assert.equal(l.j.acc.key, "Éric");
  assert.equal((await api.post("/dash", { token: l.j.supToken })).status, 200);
  assert.equal((await api.post("/sup-phones", { token: tok })).j.phones, 2);
  const me = await api.post("/acc-sup-me", { token: l.j.supToken });
  assert.equal(me.j.acc.login, "chef");
  assert.equal((await api.post("/acc-reset", { token: tok, login: "chef" })).status, 403);              // le code superviseur ne se remet pas à zéro
  assert.equal((await api.get("/pause")).j.names["éric"].n, "Le Chef");
});

test("sauvegarde : un promeneur la récupère lui-même avec son compte (nouveau téléphone)", async () => {
  const { api } = await setup();
  const r = await api.post("/acc-signup", { login: "leo", name: "Léo", code: "1234", key: "Léo" });
  assert.equal((await api.post("/acc-backup", { login: "leo", token: r.j.token })).status, 404);
  await api.post("/backup", { walker: "Léo", data: { jeu: { total: 5 }, carnet: [] } });
  const l = await api.post("/acc-login", { login: "leo", code: "1234" });
  const b = await api.post("/acc-backup", { login: "leo", token: l.j.token });
  assert.equal(b.status, 200); assert.equal(b.j.backup.data.jeu.total, 5);
  assert.equal((await api.post("/acc-backup", { login: "leo", token: "faux-jeton-0123456789" })).status, 403);
});
