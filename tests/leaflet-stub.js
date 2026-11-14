// Faux Leaflet pour les tests (le vrai vient d'un CDN bloqué ici) : tout est chaînable et ne fait rien.
(function(){
  const mk = () => {
    const f = function(){};
    const p = new Proxy(f, {
      get(t, k){
        if (k === Symbol.toPrimitive) return () => 0;
        if (k === "prototype") return t.prototype;
        if (k === "then") return undefined;
        if (k === "extend") return () => mk();
        if (k === "getZoom") return () => 16;
        if (k === "getCenter") return () => ({ lat:48.85, lng:2.35 });
        if (k === "getBounds") return () => ({ getNorth:()=>49, getSouth:()=>48, getEast:()=>3, getWest:()=>2, contains:()=>true });
        if (k === "getSize") return () => ({ x:400, y:700 });
        if (k === "getPane") return () => document.createElement("div");
        if (k === "createPane") return () => document.createElement("div");
        if (k === "options") return {};
        return mk();
      },
      apply(){ return mk(); },
      construct(){ return mk(); },
      set(){ return true; }
    });
    return p;
  };
  window.L = mk();
})();
