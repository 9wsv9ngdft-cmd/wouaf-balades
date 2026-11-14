// Petite KV Cloudflare simulée (en mémoire), avec une liste paginée (3 clés par page) pour tester les curseurs.
export class FakeKV {
  constructor(){ this.m = new Map(); }
  async get(k, type){ const v = this.m.get(k); if (v == null) return null; return type === "json" ? JSON.parse(v) : v; }
  async put(k, v){ this.m.set(k, String(v)); }
  async delete(k){ this.m.delete(k); }
  async list({ prefix = "", cursor } = {}){
    const all = [...this.m.keys()].filter(k => k.startsWith(prefix)).sort();
    const start = cursor ? +cursor : 0, page = all.slice(start, start + 3);
    const done = start + 3 >= all.length;
    return { keys: page.map(name => ({ name })), list_complete: done, cursor: done ? undefined : String(start + 3) };
  }
}
