import React, { useState, useRef, useEffect } from "react";

/* ---------------------------------------------------------------
   TAXONOMY — grounded in the spec (§4). Each type declares its own
   field set. Field.kind: 'select' | 'text' | 'number' | 'pair'
--------------------------------------------------------------- */
const TAXONOMY = {
  BRANCHEMENT: {
    label: "Branchement",
    hint: "Bonnes pièces, mauvaise logique",
    color: "#B5482A",
    types: {
      INVERSION: {
        label: "Inversion de bornes",
        code: "T04",
        severity: "MINEURE",
        fields: [
          { key: "fin", label: "FIN", kind: "text", required: true, placeholder: "ex. 3RN3B", autocomplete: ["3RN3B","3RN1A","3RN1B","3RN2A","3RN3A","1WK22A","300VT101","9KS"] },
          { key: "borneA", label: "Borne A", kind: "text", required: true, placeholder: "ex. J" },
          { key: "borneB", label: "Borne B", kind: "text", required: true, placeholder: "ex. H" },
          { key: "module", label: "Module / repère", kind: "text", required: false, placeholder: "optionnel" },
        ],
      },
      MAUVAISE_BORNE: {
        label: "Câble en mauvaise borne",
        code: "T02",
        severity: "MINEURE",
        fields: [
          { key: "fin", label: "FIN", kind: "text", required: true, placeholder: "ex. 1027VC", autocomplete: ["1027VC","1WK22A","4XBA","701VDA"] },
          { key: "borne", label: "Borne", kind: "pair", required: true, a: "Constatée", b: "Requise" },
          { key: "refCable", label: "Réf câble", kind: "text", required: false, placeholder: "optionnel" },
        ],
      },
      ERREUR_REF: {
        label: "Erreur de référence / plaquette",
        code: "Q04",
        severity: "MAJEURE",
        fields: [
          { key: "loc", label: "Emplacement (FIN ou zone)", kind: "text", required: true, placeholder: "ex. 115VMB" },
          { key: "element", label: "Élément", kind: "select", required: true, options: ["Prise","Plaquette","Disjoncteur","Composant","Autre"] },
          { key: "ref", label: "Référence", kind: "pair", required: true, a: "Constatée", b: "Requise" },
        ],
      },
      NON_CONNECTE: {
        label: "Non connecté",
        code: "T05",
        severity: "MINEURE",
        fields: [
          { key: "fin", label: "FIN", kind: "text", required: true, placeholder: "ex. 300VN359" },
          { key: "repere", label: "Borne / repère", kind: "text", required: false, placeholder: "optionnel" },
        ],
      },
    },
  },
  CONNEXION: {
    label: "Connexion",
    hint: "Bon point, geste non conforme",
    color: "#8A6D00",
    types: {
      DEVERROUILLAGE: {
        label: "Borne / contact déverrouillé",
        code: "Q01",
        severity: "MINEURE",
        fields: [
          { key: "fin", label: "FIN", kind: "text", required: true, placeholder: "ex. 300VG133" },
          { key: "bornes", label: "Borne(s)", kind: "text", required: false, placeholder: "optionnel" },
        ],
        hasQty: true,
      },
      GAINE: {
        label: "Gaine / backshell",
        code: "—",
        severity: "MINEURE",
        fields: [
          { key: "fin", label: "FIN", kind: "text", required: true, placeholder: "ex. 411VC005A" },
          { key: "elem", label: "Élément", kind: "select", required: true, options: ["Gaine","Backshell","Manchon","Amalgamant","Rétreint"] },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Non maintenu(e)","Mal rétreint(e)","Absent(e)","Mal positionné(e)","Autre"] },
        ],
      },
      FREINAGE: {
        label: "Freinage / frettes",
        code: "—",
        severity: "MINEURE",
        fields: [
          { key: "loc", label: "Localisation (FIN ou route)", kind: "select", required: true, options: ["1M","2M","1S","2S","1R","2R","Autre (FIN)"] },
          { key: "elem", label: "Élément", kind: "select", required: true, options: ["Frette","Frein","Tyrap","Collier"] },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Manquant","Desserré","Mal posé","Non conforme"] },
        ],
        hasQty: true,
      },
      SERRAGE: {
        label: "Serrage / couple",
        code: "—",
        severity: "MAJEURE",
        fields: [
          { key: "elem", label: "Élément", kind: "select", required: true, options: ["Vis","Écrou","Backshell","Connecteur","Autre"] },
          { key: "loc", label: "Localisation", kind: "text", required: true, placeholder: "FIN / zone" },
          { key: "constat", label: "Constat", kind: "select", required: true, options: ["Desserré","Couple non atteint","Non torqué","Torqueseal absent"] },
        ],
      },
    },
  },
  INTEGRITE: {
    label: "Intégrité",
    hint: "Dommage physique / panne",
    color: "#A32B2B",
    types: {
      CABLE_ENDOMMAGE: {
        label: "Câble endommagé",
        code: "—",
        severity: "MAJEURE",
        fields: [
          { key: "ref", label: "Réf câble", kind: "text", required: true, placeholder: "ex. 2424-0135" },
          { key: "loc", label: "Localisation (FIN ou zone)", kind: "text", required: false, placeholder: "optionnel" },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Coupé","Abîmé","Dénudé","Pincé","Écrasé","Rayé","Percé","Autre"] },
        ],
      },
      COMPOSANT_CASSE: {
        label: "Composant cassé",
        code: "Q11",
        severity: "MAJEURE",
        fields: [
          { key: "fin", label: "FIN / composant", kind: "text", required: true, placeholder: "ex. 54LEA" },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Cassé","Fissuré","Arraché","Tordu/déformé","Autre"] },
        ],
      },
      COMPOSANT_HS: {
        label: "Composant HS",
        code: "—",
        severity: "MAJEURE",
        fields: [
          { key: "fin", label: "FIN / composant", kind: "text", required: true, placeholder: "" },
          { key: "symptome", label: "Symptôme", kind: "select", required: true, options: ["Pas de continuité","Ne fonctionne pas","Défectueux","Autre"] },
        ],
      },
    },
  },
  MANQUANT: {
    label: "Manquant",
    hint: "Quelque chose n'est pas là",
    color: "#2E5C8A",
    types: {
      PIECE_MANQUANTE: {
        label: "Pièce manquante",
        code: "Q03",
        severity: "MINEURE",
        fields: [
          { key: "piece", label: "Pièce", kind: "select", required: true, options: ["Tyrap","Obturateur","Vis","Étiquette","Bouchon","Rondelle","Écrou","Switch guard","Capuchon","Autre (préciser)"] },
          { key: "loc", label: "Localisation (FIN ou zone)", kind: "text", required: true, placeholder: "ex. 411VC007A" },
        ],
        hasQty: true,
      },
      CABLE_MANQUANT: {
        label: "Câble manquant",
        code: "T01",
        severity: "MAJEURE",
        fields: [
          { key: "ref", label: "Réf câble", kind: "text", required: true, placeholder: "ex. 3161-0582" },
          { key: "statut", label: "Statut appro", kind: "select", required: false, options: ["Non reçu","Non livré","Introuvable","Inconnu"] },
        ],
      },
    },
  },
  AMONT: {
    label: "Amont Fabrication",
    hint: "Arrivé avec la pièce",
    color: "#5B4A8A",
    types: {
      LONGUEUR: {
        label: "Longueur non conforme",
        code: "—",
        severity: "MAJEURE",
        fields: [
          { key: "ref", label: "Réf câble", kind: "text", required: true, placeholder: "" },
          { key: "longueur", label: "Longueur", kind: "pair", required: true, a: "Constatée (mm)", b: "Requise (mm)" },
        ],
      },
      DEFAUT_RECU: {
        label: "Défaut à réception",
        code: "—",
        severity: "MAJEURE",
        fields: [
          { key: "ref", label: "Réf pièce/câble", kind: "text", required: true, placeholder: "" },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Reçu coupé","Reçu abîmé","Erreur d'impression","Non conforme plan","Autre"] },
        ],
      },
    },
  },
  INSTALLATION: {
    label: "Installation",
    hint: "Intégration mécanique",
    color: "#2E7D5B",
    types: {
      CHEMINEMENT: {
        label: "Cheminement / contrainte",
        code: "—",
        severity: "MINEURE",
        fields: [
          { key: "zone", label: "Zone / route", kind: "select", required: true, options: ["1M","2M","1S","2S","1R","2R","Autre"] },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["En contrainte","Clash / en contact","Frotte","En tension","Vrillé","Cheminement NC"] },
        ],
      },
      FIXATION: {
        label: "Fixation / visserie",
        code: "—",
        severity: "MINEURE",
        fields: [
          { key: "elem", label: "Élément", kind: "select", required: true, options: ["Clamp","Support","Vis","Rivet","Collier","Autre"] },
          { key: "loc", label: "Localisation", kind: "text", required: true, placeholder: "" },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Manquant","Desserré","Cassé","Mal monté"] },
        ],
        hasQty: true,
      },
    },
  },
  IDENTIFICATION: {
    label: "Identification",
    hint: "Étiquette / marquage",
    color: "#3A3A3A",
    types: {
      ETIQUETTE: {
        label: "Étiquette / marquage",
        code: "—",
        severity: "MINEURE",
        fields: [
          { key: "elem", label: "Élément / FIN", kind: "text", required: true, placeholder: "" },
          { key: "nature", label: "Nature", kind: "select", required: true, options: ["Manquante","Décollée","Erronée","Illisible"] },
        ],
      },
    },
  },
  AUTRE: {
    label: "Autre",
    hint: "Soupape — toujours disponible",
    color: "#8C8C8C",
    types: {
      AUTRE: {
        label: "Autre défaut",
        code: "AUT",
        severity: "MINEURE",
        fields: [
          { key: "desc", label: "Description", kind: "text", required: true, placeholder: "Décrire le défaut", multiline: true },
        ],
      },
    },
  },
};

const PRODUITS = ["MIP A350", "740VU", "PTVU", "300VU", "OHP"];
const DETECTIONS = ["Poste", "Test", "Contrôle Final", "Réception", "Client"];
const ZONE_OPTIONS = ["FIN précis", "Zone (planche sup.)", "Zone (planche inf.)", "Non applicable"];

/* --------------------------- helpers --------------------------- */
function genLine(seq, famKey, typeKey, values, qty, sev) {
  const def = TAXONOMY[famKey].types[typeKey];
  const code = def.code !== "—" ? def.code : famKey.slice(0, 3);
  const parts = [];
  if (typeKey === "INVERSION") {
    parts.push(`${values.fin || "?"} : inversion bornes ${values.borneA || "?"} <-> ${values.borneB || "?"}`);
  } else if (typeKey === "MAUVAISE_BORNE") {
    parts.push(`${values.fin || "?"} : câble en ${values.borne?.b || "?"} au lieu de ${values.borne?.a || "?"}`);
  } else if (def.fields.some((f) => f.kind === "pair")) {
    const pf = def.fields.find((f) => f.kind === "pair");
    parts.push(`${def.label} — ${values[pf.key]?.b || "?"} au lieu de ${values[pf.key]?.a || "?"}`);
  } else {
    const bits = def.fields.map((f) => values[f.key]).filter(Boolean);
    parts.push(`${def.label}${bits.length ? " : " + bits.join(", ") : ""}`);
  }
  const qtyStr = qty > 1 ? ` - QTE ${qty}` : "";
  return `DEF ${seq} - ${code}${qtyStr} : ${parts.join(" ")}`;
}

/* =========================== APP =========================== */
export default function NCWritingTool() {
  const [screen, setScreen] = useState("header"); // header | family | type | fields | list | review
  const [header, setHeader] = useState({ msn: "", produit: "", detection: "", station: "V42RA1" });
  const [locked, setLocked] = useState(false);
  const [defects, setDefects] = useState([]);
  const [famKey, setFamKey] = useState(null);
  const [typeKey, setTypeKey] = useState(null);
  const [values, setValues] = useState({});
  const [qty, setQty] = useState(1);
  const [sev, setSev] = useState("MINEURE");
  const [comment, setComment] = useState("");
  const [errors, setErrors] = useState({});
  const [warnConfirmed, setWarnConfirmed] = useState({});
  const [flash, setFlash] = useState(null);
  const [editingIdx, setEditingIdx] = useState(null);
  const [blockedNotice, setBlockedNotice] = useState(false);

  const recentTypes = useRef([]).current;

  useEffect(() => {
    if (flash) {
      const t = setTimeout(() => setFlash(null), 1800);
      return () => clearTimeout(t);
    }
  }, [flash]);

  const headerComplete = header.msn.trim() && header.produit && header.detection && header.station.trim();

  function startFamily() {
    setFamKey(null);
    setTypeKey(null);
    setValues({});
    setQty(1);
    setComment("");
    setErrors({});
    setWarnConfirmed({});
    setEditingIdx(null);
    setScreen("family");
  }

  function pickFamily(k) {
    setFamKey(k);
    const types = Object.keys(TAXONOMY[k].types);
    if (types.length === 1) {
      pickType(k, types[0]);
    } else {
      setScreen("type");
    }
  }

  function pickType(fk, tk) {
    setFamKey(fk);
    setTypeKey(tk);
    setSev(TAXONOMY[fk].types[tk].severity);
    setValues({});
    setQty(1);
    setErrors({});
    setScreen("fields");
  }

  function setField(key, val) {
    setValues((v) => ({ ...v, [key]: val }));
    setErrors((e) => ({ ...e, [key]: null }));
  }
  function setPairField(key, sub, val) {
    setValues((v) => ({ ...v, [key]: { ...(v[key] || {}), [sub]: val } }));
  }

  function validate() {
    const def = TAXONOMY[famKey].types[typeKey];
    const errs = {};
    def.fields.forEach((f) => {
      if (!f.required) return;
      if (f.kind === "pair") {
        if (!values[f.key]?.a || !values[f.key]?.b) errs[f.key] = "Requis";
      } else if (!values[f.key] || String(values[f.key]).trim() === "") {
        errs[f.key] = "Requis";
      }
    });
    if (typeKey === "INVERSION" && values.borneA && values.borneB && values.borneA === values.borneB) {
      errs.borneB = "Doit être différent de Borne A";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  function saveDefect() {
    if (!validate()) return;
    const seq = editingIdx !== null ? editingIdx + 1 : defects.length + 1;
    const line = genLine(seq, famKey, typeKey, values, qty, sev);
    const entry = { famKey, typeKey, values, qty, sev, comment, line };

    if (editingIdx !== null) {
      setDefects((d) => d.map((x, i) => (i === editingIdx ? entry : x)));
    } else {
      setDefects((d) => [...d, entry]);
      if (!locked) setLocked(true);
    }
    recentTypes.unshift({ famKey, typeKey });
    if (recentTypes.length > 4) recentTypes.pop();

    setFlash(editingIdx !== null ? "Défaut modifié" : `Défaut ${seq} enregistré`);
    setEditingIdx(null);
    setScreen("list");
  }

  function duplicateLast() {
    const last = defects[defects.length - 1];
    if (!last) return startFamily();
    setFamKey(last.famKey);
    setTypeKey(last.typeKey);
    setSev(last.sev);
    const carried = {};
    const def = TAXONOMY[last.famKey].types[last.typeKey];
    def.fields.forEach((f) => {
      if (f.key === "fin" || f.key === "loc" || f.key === "zone") carried[f.key] = last.values[f.key];
    });
    setValues(carried);
    setQty(1);
    setComment("");
    setErrors({});
    setScreen("fields");
  }

  function editDefect(i) {
    const d = defects[i];
    setFamKey(d.famKey);
    setTypeKey(d.typeKey);
    setValues(d.values);
    setQty(d.qty);
    setSev(d.sev);
    setComment(d.comment);
    setEditingIdx(i);
    setErrors({});
    setScreen("fields");
  }

  function removeDefect(i) {
    setDefects((d) => d.filter((_, idx) => idx !== i).map((x, idx2) => ({ ...x })));
  }

  function attemptChangeHeader() {
    if (locked) {
      setBlockedNotice(true);
      setTimeout(() => setBlockedNotice(false), 2600);
      return false;
    }
    return true;
  }

  function resetAll() {
    setScreen("header");
    setHeader({ msn: "", produit: "", detection: "", station: "V42RA1" });
    setLocked(false);
    setDefects([]);
    setFamKey(null);
    setTypeKey(null);
    setValues({});
    setEditingIdx(null);
  }

  /* ----------------------- shared styles ----------------------- */
  const S = {
    page: { minHeight: "100%", background: "#F0F2F5", fontFamily: "'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif", color: "#1A2333", display: "flex", flexDirection: "column" },
    topbar: { background: "#00205B", color: "#fff", padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 },
    topbarLeft: { display: "flex", alignItems: "center", gap: 12 },
    badge: { background: "#E0A800", color: "#1A2333", fontWeight: 700, fontSize: 11, padding: "3px 8px", borderRadius: 4, letterSpacing: 0.5 },
    body: { flex: 1, padding: "20px 16px 100px", maxWidth: 720, margin: "0 auto", width: "100%", boxSizing: "border-box" },
    card: { background: "#fff", borderRadius: 10, padding: 18, boxShadow: "0 1px 3px rgba(0,0,0,0.08)", marginBottom: 14 },
    h1: { fontSize: 20, fontWeight: 700, margin: "0 0 4px", color: "#00205B" },
    sub: { fontSize: 13.5, color: "#5B7089", margin: "0 0 18px" },
    label: { display: "block", fontSize: 12.5, fontWeight: 600, color: "#3A4658", marginBottom: 5, textTransform: "uppercase", letterSpacing: 0.3 },
    input: { width: "100%", padding: "11px 12px", fontSize: 15, border: "1.5px solid #D3D9E3", borderRadius: 7, boxSizing: "border-box", outline: "none", background: "#fff" },
    inputErr: { borderColor: "#C0392B", background: "#FDF1F0" },
    select: { width: "100%", padding: "11px 12px", fontSize: 15, border: "1.5px solid #D3D9E3", borderRadius: 7, boxSizing: "border-box", background: "#fff" },
    fieldWrap: { marginBottom: 16 },
    err: { color: "#C0392B", fontSize: 12, marginTop: 4, fontWeight: 600 },
    btnPrimary: { background: "#00205B", color: "#fff", border: "none", padding: "13px 22px", borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: "pointer" },
    btnGold: { background: "#E0A800", color: "#1A2333", border: "none", padding: "13px 22px", borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: "pointer" },
    btnGhost: { background: "#fff", color: "#00205B", border: "1.5px solid #00205B", padding: "11px 18px", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer" },
    btnDisabled: { background: "#C7CDD8", color: "#fff", border: "none", padding: "13px 22px", borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: "not-allowed" },
    footer: { position: "fixed", bottom: 0, left: 0, right: 0, background: "#fff", borderTop: "1px solid #E3E7EE", padding: "12px 16px", display: "flex", gap: 10, justifyContent: "center", boxShadow: "0 -2px 8px rgba(0,0,0,0.05)" },
    tile: { border: "2px solid #E3E7EE", borderRadius: 10, padding: "16px 12px", cursor: "pointer", textAlign: "left", background: "#fff", transition: "border-color .12s" },
    grid2: { display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 10 },
    mono: { fontFamily: "'IBM Plex Mono', 'Courier New', monospace", fontSize: 12.5, background: "#0B1F3F", color: "#B9D4FF", padding: "10px 12px", borderRadius: 7, lineHeight: 1.6, overflowX: "auto" },
    chip: { display: "inline-block", fontSize: 10.5, fontWeight: 700, padding: "2px 7px", borderRadius: 5, color: "#fff", marginLeft: 6, verticalAlign: "middle" },
    listItem: { display: "flex", alignItems: "flex-start", justifyContent: "space-between", padding: "12px 14px", background: "#fff", borderRadius: 8, marginBottom: 8, border: "1px solid #E9ECF2" },
    flash: { position: "fixed", top: 68, left: "50%", transform: "translateX(-50%)", background: "#1E8449", color: "#fff", padding: "9px 18px", borderRadius: 20, fontSize: 13.5, fontWeight: 600, boxShadow: "0 3px 10px rgba(0,0,0,0.2)", zIndex: 50 },
    noticeBlocked: { position: "fixed", top: 68, left: "50%", transform: "translateX(-50%)", background: "#C0392B", color: "#fff", padding: "10px 18px", borderRadius: 8, fontSize: 13.5, fontWeight: 600, boxShadow: "0 3px 10px rgba(0,0,0,0.2)", zIndex: 50, maxWidth: 400, textAlign: "center" },
  };

  const famList = Object.entries(TAXONOMY);

  /* ----------------------- render fields ----------------------- */
  function renderField(f) {
    const hasErr = !!errors[f.key];
    if (f.kind === "select") {
      return (
        <select style={{ ...S.select, ...(hasErr ? S.inputErr : {}) }} value={values[f.key] || ""} onChange={(e) => setField(f.key, e.target.value)}>
          <option value="">— choisir —</option>
          {f.options.map((o) => (
            <option key={o} value={o}>{o}</option>
          ))}
        </select>
      );
    }
    if (f.kind === "pair") {
      return (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div>
            <span style={{ fontSize: 11, color: "#8A93A3" }}>{f.a}</span>
            <input style={{ ...S.input, ...(hasErr ? S.inputErr : {}) }} value={values[f.key]?.a || ""} onChange={(e) => setPairField(f.key, "a", e.target.value)} />
          </div>
          <div>
            <span style={{ fontSize: 11, color: "#8A93A3" }}>{f.b}</span>
            <input style={{ ...S.input, ...(hasErr ? S.inputErr : {}) }} value={values[f.key]?.b || ""} onChange={(e) => setPairField(f.key, "b", e.target.value)} />
          </div>
        </div>
      );
    }
    if (f.key === "fin" && f.autocomplete) {
      return (
        <>
          <input
            style={{ ...S.input, ...(hasErr ? S.inputErr : {}) }}
            list={`ac-${f.key}`}
            placeholder={f.placeholder}
            value={values[f.key] || ""}
            onChange={(e) => setField(f.key, e.target.value)}
          />
          <datalist id={`ac-${f.key}`}>
            {f.autocomplete.map((o) => <option key={o} value={o} />)}
          </datalist>
        </>
      );
    }
    return (
      <input
        style={{ ...S.input, ...(hasErr ? S.inputErr : {}) }}
        placeholder={f.placeholder}
        value={values[f.key] || ""}
        onChange={(e) => setField(f.key, e.target.value)}
      />
    );
  }

  /* =========================== SCREENS =========================== */

  return (
    <div style={S.page}>
      <div style={S.topbar}>
        <div style={S.topbarLeft}>
          <div style={{ fontWeight: 800, fontSize: 15 }}>NC · Saisie Structurée</div>
          <span style={S.badge}>PROTOTYPE</span>
        </div>
        {screen !== "header" && (
          <div style={{ fontSize: 12.5, opacity: 0.85 }}>
            MSN {header.msn || "—"} · {header.produit || "—"} · {header.detection || "—"}
          </div>
        )}
      </div>

      {flash && <div style={S.flash}>{flash}</div>}
      {blockedNotice && (
        <div style={S.noticeBlocked}>
          Impossible : produit / détection verrouillés dès le 1er défaut enregistré. Créez une nouvelle NC.
        </div>
      )}

      <div style={S.body}>
        {/* ---------------- HEADER SCREEN ---------------- */}
        {screen === "header" && (
          <div style={S.card}>
            <h1 style={S.h1}>Nouvelle NC</h1>
            <p style={S.sub}>Renseigné une fois. Produit et Détection se verrouillent dès le premier défaut enregistré.</p>

            <div style={S.fieldWrap}>
              <label style={S.label}>MSN</label>
              <input style={S.input} placeholder="ex. 2160" value={header.msn} onChange={(e) => setHeader({ ...header, msn: e.target.value })} />
            </div>
            <div style={S.fieldWrap}>
              <label style={S.label}>Produit</label>
              <select style={S.select} value={header.produit} onChange={(e) => setHeader({ ...header, produit: e.target.value })}>
                <option value="">— choisir —</option>
                {PRODUITS.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
            <div style={S.fieldWrap}>
              <label style={S.label}>Détection</label>
              <select style={S.select} value={header.detection} onChange={(e) => setHeader({ ...header, detection: e.target.value })}>
                <option value="">— choisir —</option>
                {DETECTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div style={S.fieldWrap}>
              <label style={S.label}>Station</label>
              <input style={S.input} value={header.station} onChange={(e) => setHeader({ ...header, station: e.target.value })} />
            </div>

            <button
              style={headerComplete ? S.btnPrimary : S.btnDisabled}
              disabled={!headerComplete}
              onClick={() => setScreen("list")}
            >
              Continuer →
            </button>
          </div>
        )}

        {/* ---------------- FAMILY SCREEN ---------------- */}
        {screen === "family" && (
          <div>
            <h1 style={S.h1}>Étape 1 — Famille du défaut</h1>
            <p style={S.sub}>Choisissez la catégorie générale.</p>

            {recentTypes.length > 0 && (
              <div style={{ marginBottom: 18 }}>
                <label style={S.label}>Récemment utilisés</label>
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                  {recentTypes.map((r, i) => (
                    <button key={i} style={{ ...S.btnGhost, fontSize: 13 }} onClick={() => pickType(r.famKey, r.typeKey)}>
                      {TAXONOMY[r.famKey].types[r.typeKey].label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div style={S.grid2}>
              {famList.map(([k, f]) => (
                <div
                  key={k}
                  style={{ ...S.tile, borderColor: "#E3E7EE" }}
                  onClick={() => pickFamily(k)}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = f.color)}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = "#E3E7EE")}
                >
                  <div style={{ width: 10, height: 10, borderRadius: 3, background: f.color, marginBottom: 8 }} />
                  <div style={{ fontWeight: 700, fontSize: 14.5 }}>{f.label}</div>
                  <div style={{ fontSize: 11.5, color: "#8A93A3", marginTop: 2 }}>{f.hint}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ---------------- TYPE SCREEN ---------------- */}
        {screen === "type" && famKey && (
          <div>
            <button style={{ ...S.btnGhost, marginBottom: 14, fontSize: 12.5, padding: "7px 12px" }} onClick={() => setScreen("family")}>← Famille</button>
            <h1 style={S.h1}>Étape 2 — Type <span style={{ ...S.chip, background: TAXONOMY[famKey].color }}>{TAXONOMY[famKey].label}</span></h1>
            <p style={S.sub}>Choisissez le type précis de défaut.</p>
            <div>
              {Object.entries(TAXONOMY[famKey].types).map(([tk, t]) => (
                <div key={tk} style={{ ...S.tile, marginBottom: 8, display: "flex", justifyContent: "space-between", alignItems: "center" }} onClick={() => pickType(famKey, tk)}>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14.5 }}>{t.label}</div>
                    <div style={{ fontSize: 11.5, color: "#8A93A3" }}>{t.fields.length} champ{t.fields.length > 1 ? "s" : ""}</div>
                  </div>
                  {t.code !== "—" && <span style={{ fontFamily: "monospace", fontSize: 12, color: "#8A93A3" }}>{t.code}</span>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ---------------- FIELDS SCREEN ---------------- */}
        {screen === "fields" && famKey && typeKey && (
          <div>
            <button style={{ ...S.btnGhost, marginBottom: 14, fontSize: 12.5, padding: "7px 12px" }} onClick={() => setScreen(editingIdx !== null ? "list" : "type")}>
              ← {editingIdx !== null ? "Annuler modification" : "Type"}
            </button>
            <div style={S.card}>
              <h1 style={S.h1}>
                {TAXONOMY[famKey].types[typeKey].label}
                <span style={{ ...S.chip, background: sev === "MAJEURE" ? "#A32B2B" : "#8A6D00" }}>{sev}</span>
              </h1>
              <p style={S.sub}>{TAXONOMY[famKey].label} {TAXONOMY[famKey].types[typeKey].code !== "—" && `· code ${TAXONOMY[famKey].types[typeKey].code}`}</p>

              {TAXONOMY[famKey].types[typeKey].fields.map((f) => (
                <div key={f.key} style={S.fieldWrap}>
                  <label style={S.label}>{f.label}{f.required && <span style={{ color: "#C0392B" }}> *</span>}</label>
                  {renderField(f)}
                  {errors[f.key] && <div style={S.err}>{errors[f.key]}</div>}
                </div>
              ))}

              {TAXONOMY[famKey].types[typeKey].hasQty && (
                <div style={S.fieldWrap}>
                  <label style={S.label}>Quantité</label>
                  <input type="number" min={1} style={{ ...S.input, width: 100 }} value={qty} onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))} />
                </div>
              )}

              <div style={S.fieldWrap}>
                <label style={S.label}>Sévérité</label>
                <select style={S.select} value={sev} onChange={(e) => setSev(e.target.value)}>
                  <option value="MINEURE">Mineure</option>
                  <option value="MAJEURE">Majeure</option>
                </select>
              </div>

              <div style={S.fieldWrap}>
                <label style={S.label}>Complément libre (optionnel)</label>
                <textarea style={{ ...S.input, minHeight: 60, fontFamily: "inherit", resize: "vertical" }} maxLength={200} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Nuance non capturée par les champs ci-dessus…" />
              </div>

              <div style={{ background: "#F4F6FA", borderRadius: 7, padding: "10px 12px", fontSize: 12, color: "#5B7089", marginTop: 4 }}>
                Aperçu texte généré :
                <div style={{ ...S.mono, marginTop: 6 }}>{genLine(editingIdx !== null ? editingIdx + 1 : defects.length + 1, famKey, typeKey, values, qty, sev)}</div>
              </div>
            </div>
          </div>
        )}

        {/* ---------------- LIST SCREEN ---------------- */}
        {screen === "list" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 4 }}>
              <h1 style={S.h1}>Défauts de la NC</h1>
              <button
                style={{ background: "none", border: "none", color: locked ? "#C7CDD8" : "#00205B", fontSize: 12, fontWeight: 600, cursor: locked ? "default" : "pointer", textDecoration: locked ? "none" : "underline" }}
                onClick={() => attemptChangeHeader() && setScreen("header")}
              >
                {locked ? "🔒 Produit / Détection verrouillés" : "Modifier l'en-tête"}
              </button>
            </div>
            <p style={S.sub}>{defects.length === 0 ? "Aucun défaut enregistré pour l'instant." : `${defects.length} défaut${defects.length > 1 ? "s" : ""} — total ${defects.reduce((s, d) => s + d.qty, 0)}`}</p>

            {defects.length === 0 && (
              <div style={{ ...S.card, textAlign: "center", padding: 32, color: "#8A93A3" }}>
                Cliquez « Ajouter un défaut » pour commencer.
              </div>
            )}

            {defects.map((d, i) => (
              <div key={i} style={S.listItem}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: "#00205B" }}>
                    Défaut {i + 1} — {TAXONOMY[d.famKey].types[d.typeKey].label}
                    <span style={{ ...S.chip, background: d.sev === "MAJEURE" ? "#A32B2B" : "#8A6D00" }}>{d.sev}</span>
                    {d.qty > 1 && <span style={{ ...S.chip, background: "#5B7089" }}>×{d.qty}</span>}
                  </div>
                  <div style={{ fontFamily: "monospace", fontSize: 11.5, color: "#5B7089", marginTop: 4 }}>{d.line}</div>
                </div>
                <div style={{ display: "flex", gap: 6, flexShrink: 0, marginLeft: 10 }}>
                  <button style={{ ...S.btnGhost, padding: "6px 10px", fontSize: 12 }} onClick={() => editDefect(i)}>Modifier</button>
                  <button style={{ ...S.btnGhost, padding: "6px 10px", fontSize: 12, color: "#C0392B", borderColor: "#C0392B" }} onClick={() => removeDefect(i)}>✕</button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ---------------- REVIEW SCREEN ---------------- */}
        {screen === "review" && (
          <div>
            <button style={{ ...S.btnGhost, marginBottom: 14, fontSize: 12.5, padding: "7px 12px" }} onClick={() => setScreen("list")}>← Retour à la liste</button>
            <div style={S.card}>
              <h1 style={S.h1}>Aperçu — texte généré (SAP)</h1>
              <p style={S.sub}>Ce texte sera écrit automatiquement dans le champ description longue.</p>
              <div style={S.mono}>
                {`### DEFAUTS v1 | MSN: ${header.msn} | PRODUIT: ${header.produit} | DETECTION: ${header.detection.toUpperCase()}`}
                <br />
                {defects.map((d) => d.line).join("\n")}
                <br />
                {`### TOTAL: ${defects.reduce((s, d) => s + d.qty, 0)}`}
              </div>
            </div>
            <div style={{ ...S.card, background: "#EFF6F1" }}>
              <div style={{ fontWeight: 700, color: "#1E8449", marginBottom: 6 }}>✓ Prêt à soumettre</div>
              <div style={{ fontSize: 13, color: "#3A4658" }}>{defects.length} défaut(s) structuré(s) · comptage garanti exact par construction · aucune somme de contrôle nécessaire.</div>
            </div>
          </div>
        )}
      </div>

      {/* ---------------- STICKY FOOTER ---------------- */}
      {screen === "list" && (
        <div style={S.footer}>
          <button style={S.btnGhost} onClick={duplicateLast} disabled={defects.length === 0} title={defects.length === 0 ? "Aucun défaut à dupliquer" : ""}>
            ⧉ Dupliquer le dernier
          </button>
          <button style={S.btnPrimary} onClick={startFamily}>+ Ajouter un défaut</button>
          <button style={defects.length ? S.btnGold : S.btnDisabled} disabled={!defects.length} onClick={() => setScreen("review")}>
            Terminer →
          </button>
        </div>
      )}
      {screen === "fields" && (
        <div style={S.footer}>
          <button style={S.btnGhost} onClick={() => setScreen(editingIdx !== null ? "list" : "type")}>Annuler</button>
          <button style={S.btnPrimary} onClick={saveDefect}>
            {editingIdx !== null ? "Enregistrer la modification" : "Enregistrer ce défaut"}
          </button>
        </div>
      )}
      {screen === "review" && (
        <div style={S.footer}>
          <button style={S.btnGhost} onClick={() => setScreen("list")}>← Modifier</button>
          <button style={S.btnPrimary} onClick={() => { alert("NC soumise (simulation). Réinitialisation du prototype."); resetAll(); }}>
            Soumettre la NC
          </button>
        </div>
      )}
    </div>
  );
}
