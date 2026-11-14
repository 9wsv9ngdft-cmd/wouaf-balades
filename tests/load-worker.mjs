import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FakeKV } from "./fake-kv.mjs";
const here = path.dirname(fileURLToPath(import.meta.url));
// le Worker est un module ES dans un .js : on le charge par une URL « data: » pour ne pas dépendre d'un package.json
export async function loadWorker(){
  const src = fs.readFileSync(path.join(here, "..", "worker", "wouaf-rappels.js"), "utf8");
  return (await import("data:text/javascript;base64," + Buffer.from(src).toString("base64"))).default;
}
export function makeEnv(code = "1234"){ return { WOUAF: new FakeKV(), SUPERVISOR_CODE: code }; }
export function client(worker, env){
  const call = async (method, p, body) => {
    const res = await worker.fetch(new Request("https://w.test" + p, { method, body: body ? JSON.stringify(body) : undefined }), env, {});
    return { status: res.status, ok: res.ok, j: await res.json() };
  };
  return { get: p => call("GET", p), post: (p, b) => call("POST", p, b) };
}
