import React, { useState, useMemo } from "react";

/* Official FTO2 retouching code sheet — 123 sub-codes.
   CDVE collapsed from 19 duplicate codes into a single toggle.
   Severity / RPN / Priority carried from the sheet's FMEA ratings. */
const NATURES = [{"code": "Q01","label": "Verrouillage","hint": "Contact non verrouillé / faux contact","isTest": false,"objects": [{"sub": "Q01-001","label": "Contact","detail": "Copper, aluminum, fiber optic","sev": 7,"rpn": 245,"cdve": "Q01-003"},{"sub": "Q01-002","label": "False contact","detail": "Not locked","sev": 3,"rpn": 120,"cdve": null}]},{"code": "Q03","label": "Élément manquant","hint": "Quelque chose n'est pas là","isTest": false,"objects": [{"sub": "Q03-001","label": "Shutter/obturateur","detail": "Circular, rectangular, VT module, ventilation hole","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q03-002","label": "Heat shrink tubing","detail": "Low temp, high temp","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q03-003","label": "Mechanical element","detail": "Screw, washer, nut, spacer","sev": 4,"rpn": 96,"cdve": null},{"sub": "Q03-004","label": "Electrical element","detail": "Cable, contact, diode, resistor, connector, VG module, rear connector","sev": 4,"rpn": 64,"cdve": null},{"sub": "Q03-005","label": "Braking/freinage","detail": "Brake wire, glue, frangible paint line","sev": 3,"rpn": 48,"cdve": null},{"sub": "Q03-006","label": "Collar/collier","detail": "routing, plastic shrink, string shrink, V-support, plastic, metal","sev": 3,"rpn": 108,"cdve": null},{"sub": "Q03-007","label": "Protective caps","detail": "Ventilation hole, open hole","sev": 3,"rpn": 60,"cdve": null},{"sub": "Q03-008","label": "End protection","detail": "Socket plug, plastic bag","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q03-009","label": "Tamper-evident label","detail": "Furniture door lock, cut-off socket","sev": 3,"rpn": 36,"cdve": null},{"sub": "Q03-010","label": "Sheathing/gaine","detail": "Textile, corrugated, EMI, spare","sev": 4,"rpn": 72,"cdve": null},{"sub": "Q03-011","label": "Identification plate/sleeve/flag","detail": "END, route, cable number, clamp, ramp","sev": 3,"rpn": 48,"cdve": null},{"sub": "Q03-012","label": "Identification label","detail": "FIN, MSN","sev": 3,"rpn": 60,"cdve": null}]},{"code": "Q04","label": "Erreur de montage","hint": "Mauvaise réf, mauvais sens, mauvaise taille","isTest": false,"objects": [{"sub": "Q04-001","label": "Shutter","detail": "Reference, mounting direction","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q04-002","label": "Heat shrink tubing","detail": "Reference, size","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q04-003","label": "Mechanical","detail": "Screw, washer, nut, spacer, V-bracket, structure, VT bar - ref/size/orientation","sev": 4,"rpn": 128,"cdve": null},{"sub": "Q04-004","label": "Contact","detail": "Reference, copper, aluminum","sev": 9,"rpn": 216,"cdve": null},{"sub": "Q04-005","label": "Resistor, connector, circuit breaker, relay, switch, rear connection","detail": "Ref, mounting, orientation","sev": 3,"rpn": 63,"cdve": null},{"sub": "Q04-006","label": "Lock wire","detail": "Reference","sev": 3,"rpn": 54,"cdve": null},{"sub": "Q04-007","label": "Plastic routing collar","detail": "Reference, size, orientation","sev": 3,"rpn": 75,"cdve": null},{"sub": "Q04-008","label": "Metal routing collar","detail": "Reference, size, orientation","sev": 3,"rpn": 45,"cdve": null},{"sub": "Q04-009","label": "Error correction/detrompage","detail": "Coding key, ARINC plug pin, polarization key","sev": 4,"rpn": 80,"cdve": null},{"sub": "Q04-010","label": "Ventilation hole protective caps","detail": "Reference","sev": 3,"rpn": 36,"cdve": null},{"sub": "Q04-011","label": "Electrical element","detail": "Ground braid, terminal, indicator light - ref/orientation/charging","sev": 4,"rpn": 96,"cdve": null},{"sub": "Q04-012","label": "Socket protective cap","detail": "Reference, size","sev": 3,"rpn": 36,"cdve": null},{"sub": "Q04-013","label": "Identification plate","detail": "plate, function label, adhesive END, flame, sleeve - ref/identification/reversal","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q04-014","label": "Frettage","detail": "Reference plastic fret collar, reference string fret","sev": 3,"rpn": 60,"cdve": null}]},{"code": "Q05","label": "Serrage","hint": "Trop serré, pas assez, desserré","isTest": false,"objects": [{"sub": "Q05-001","label": "Electrical element","detail": "Rear connection, connector, VG module, terminal, circuit breaker - over/under/loose","sev": 8,"rpn": 480,"cdve": null},{"sub": "Q05-002","label": "Mechanical","detail": "screws, safety wire, frangible paint, clamp, diode block, BAND-IT, VT bar, standoff, sleeve, light, switch, re","sev": 4,"rpn": 160,"cdve": null},{"sub": "Q05-003","label": "Rope collar","detail": "Over/under/loose screws","sev": 4,"rpn": 240,"cdve": null},{"sub": "Q05-004","label": "Frettage","detail": "Plastic collar, string fret","sev": 4,"rpn": 120,"cdve": null}]},{"code": "Q06","label": "Mise en œuvre câblage","hint": "Cheminement, gainage, contact/clash","isTest": false,"objects": [{"sub": "Q06-001","label": "Harness","detail": "Routing, cable management, under/overlength, wrong destination, not in collar, V-support, pinched","sev": 4,"rpn": 96,"cdve": null},{"sub": "Q06-002","label": "Poor sheathing installation","detail": "Visible line, incorrect twist, branch, sock","sev": 4,"rpn": 96,"cdve": null},{"sub": "Q06-003","label": "Combining tape/amalgamant","detail": "Overlap, permitted overlap","sev": 3,"rpn": 75,"cdve": null},{"sub": "Q06-004","label": "Cable in contact with structural element","detail": "Clash with plate, ramp, pipe, screw, connecting rod","sev": 5,"rpn": 120,"cdve": null},{"sub": "Q06-005","label": "Cable in contact with electrical component","detail": "Clash with VG, connector","sev": 5,"rpn": 80,"cdve": null},{"sub": "Q06-006","label": "Incorrect positioning of shrink ring","detail": "Plastic collar, string","sev": 3,"rpn": 60,"cdve": null},{"sub": "Q06-007","label": "Fringing on rear connection","detail": "Sheath not secured, sheath too short","sev": 3,"rpn": 90,"cdve": null},{"sub": "Q06-008","label": "Sheathing","detail": "Too short, in contact with grommet, not secured to rear connector","sev": 4,"rpn": 96,"cdve": null},{"sub": "Q06-009","label": "Route not resumed after test","detail": "Cabling not completed","sev": 3,"rpn": 60,"cdve": null},{"sub": "Q06-010","label": "Identification","detail": "Positioning flame, plate, sleeve - offset, not specified, too short/long, illegible","sev": 4,"rpn": 80,"cdve": null},{"sub": "Q06-011","label": "Frettage implementation","detail": "double capstan knot, fret length cut, ferrule clamp","sev": 3,"rpn": 90,"cdve": null},{"sub": "Q06-012","label": "Implementation of connections in Band-it collar","detail": "","sev": 5,"rpn": 60,"cdve": null}]},{"code": "Q07","label": "Sertissage standard","hint": "Contacts et cosses cuivre/alu","isTest": false,"objects": [{"sub": "Q07-001","label": "Aluminum contact","detail": "Stripping, Crimping","sev": 9,"rpn": 135,"cdve": "Q07-006"},{"sub": "Q07-002","label": "Copper contact","detail": "Stripping, Crimping","sev": 9,"rpn": 180,"cdve": "Q07-007"},{"sub": "Q07-003","label": "Self-welding sleeve","detail": "Deformation, overheating","sev": 9,"rpn": 180,"cdve": "Q07-008"},{"sub": "Q07-004","label": "Copper lug","detail": "Stripping, Crimping","sev": 9,"rpn": 135,"cdve": "Q07-009"},{"sub": "Q07-005","label": "Aluminum lug","detail": "Stripping, Crimping","sev": 9,"rpn": 135,"cdve": "Q07-010"}]},{"code": "Q08","label": "Sertissage spécifique","hint": "Quadrax, twinax, coax, fibre, brasure","isTest": false,"objects": [{"sub": "Q08-001","label": "QUADRAX contact","detail": "Stripping, Crimping","sev": 9,"rpn": 27,"cdve": null},{"sub": "Q08-002","label": "TWINAX contact","detail": "Stripping, Crimping","sev": 9,"rpn": 27,"cdve": null},{"sub": "Q08-003","label": "TRIAXIAL contact","detail": "Stripping, Crimping","sev": 9,"rpn": 27,"cdve": null},{"sub": "Q08-004","label": "BUSCAN contact","detail": "Stripping, Crimping","sev": 9,"rpn": 27,"cdve": null},{"sub": "Q08-005","label": "Coax contact","detail": "Stripping, Crimping","sev": 9,"rpn": 27,"cdve": null},{"sub": "Q08-006","label": "Optical fiber contact","detail": "Stripping, gluing","sev": 6,"rpn": 18,"cdve": null},{"sub": "Q08-007","label": "Brazing","detail": "Non-compliant weld","sev": 9,"rpn": 135,"cdve": null}]},{"code": "Q09","label": "Métallisation / bonding","hint": "Protection, point de masse","isTest": false,"objects": [{"sub": "Q09-001","label": "Protection not applied","detail": "Petroleum jelly, protective paint","sev": 6,"rpn": 42,"cdve": "Q09-004"},{"sub": "Q09-002","label": "Application of protection","detail": "Partially applied, metallization visible","sev": 6,"rpn": 42,"cdve": "Q09-005"},{"sub": "Q09-003","label": "Ground point","detail": "Oxidation, non-compliant brush diameter, non-compliant measurement","sev": 6,"rpn": 42,"cdve": "Q09-006"}]},{"code": "Q10","label": "Dommage structure","hint": "Plaque, structure, main courante, tuyauterie","isTest": false,"objects": [{"sub": "Q10-001","label": "Damaged plate","detail": "Impact, scratch, bent, soiling","sev": 4,"rpn": 120,"cdve": null},{"sub": "Q10-002","label": "Damaged structure","detail": "Impact, scratch, soiling","sev": 4,"rpn": 120,"cdve": null},{"sub": "Q10-003","label": "Damaged handrail","detail": "Impact, scratch, bent, soiled","sev": 4,"rpn": 100,"cdve": null},{"sub": "Q10-004","label": "Column","detail": "Impact, scratch, soiling","sev": 4,"rpn": 80,"cdve": null},{"sub": "Q10-005","label": "Damaged piping","detail": "Impact, scratch, soiling","sev": 4,"rpn": 80,"cdve": null},{"sub": "Q10-006","label": "Mechanism","detail": "Insert, screws - damaged threads, broken screws inside","sev": 4,"rpn": 160,"cdve": null}]},{"code": "Q11","label": "Dommage élément élec.","hint": "Câble, composant, cosse, contact abîmés","isTest": false,"objects": [{"sub": "Q11-001","label": "Cable cut","detail": "","sev": 8,"rpn": 48,"cdve": null},{"sub": "Q11-014","label": "Scratched, damaged cable","detail": "","sev": 8,"rpn": 480,"cdve": null},{"sub": "Q11-002","label": "Identification","detail": "Wave, label, sleeve - torn, soiled","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q11-003","label": "Component","detail": "VG module, circuit breaker, VT strip module, connector, rear fitting, lighting plate","sev": 4,"rpn": 168,"cdve": "Q11-016"},{"sub": "Q11-004","label": "Protective sheath","detail": "Textile, corrugated, EMI","sev": 4,"rpn": 96,"cdve": null},{"sub": "Q11-005","label": "Lug","detail": "copper, aluminum","sev": 4,"rpn": 140,"cdve": "Q11-018"},{"sub": "Q11-006","label": "Contact","detail": "Copper, aluminum","sev": 9,"rpn": 189,"cdve": "Q11-019"},{"sub": "Q11-007","label": "Amalgamating tape","detail": "Torn, soiled","sev": 3,"rpn": 45,"cdve": null},{"sub": "Q11-008","label": "Heat shrink tubing","detail": "Torn, soiled","sev": 3,"rpn": 45,"cdve": null},{"sub": "Q11-009","label": "Ground braid metallization","detail": "Broken strands","sev": 4,"rpn": 60,"cdve": "Q11-022"},{"sub": "Q11-010","label": "Cable collar","detail": "Plastic, metal, V-bracket","sev": 3,"rpn": 60,"cdve": null},{"sub": "Q11-011","label": "BAND-IT clamp","detail": "Metal clamp, PTFE tape","sev": 5,"rpn": 40,"cdve": null},{"sub": "Q11-012","label": "VT strip","detail": "Damaged module, deformed rail","sev": 3,"rpn": 60,"cdve": null},{"sub": "Q11-013","label": "Damaged sealing sleeves","detail": "","sev": 4,"rpn": 112,"cdve": "Q11-026"}]},{"code": "Q12","label": "Impression / marquage","hint": "Jauge, type, longueur, identification câble","isTest": false,"objects": [{"sub": "Q12-001","label": "Cable gauge error","detail": "G20, G18","sev": 4,"rpn": 80,"cdve": "Q12-007"},{"sub": "Q12-002","label": "Cable type error","detail": "DR, AD","sev": 4,"rpn": 120,"cdve": "Q12-008"},{"sub": "Q12-003","label": "Cable length error","detail": "Too short, too long","sev": 4,"rpn": 60,"cdve": null},{"sub": "Q12-004","label": "Cable identification","detail": "Readability, ID number error, marking characteristics","sev": 4,"rpn": 80,"cdve": null},{"sub": "Q12-005","label": "Identification","detail": "Sleeve, plate, label - legibility, incorrect reference, color","sev": 3,"rpn": 45,"cdve": null},{"sub": "Q12-006","label": "VT bar","detail": "Module identification error, module reference, rail size","sev": 3,"rpn": 63,"cdve": null}]},{"code": "Q13","label": "Dossier de fabrication","hint": "Opération, tampon, traçabilité, doc","isTest": false,"objects": [{"sub": "Q13-001","label": "Operation","detail": "Not badged, order of operations not respected","sev": 3,"rpn": 72,"cdve": null},{"sub": "Q13-002","label": "Stamp","detail": "Not affixed to tracking sheet, partially visible","sev": 3,"rpn": 36,"cdve": null},{"sub": "Q13-003","label": "Traceability label","detail": "CT176 not completed, CT129D not completed","sev": 4,"rpn": 64,"cdve": null},{"sub": "Q13-004","label": "Documentation","detail": "Missing, non-compliant","sev": 4,"rpn": 80,"cdve": null},{"sub": "Q13-005","label": "Tool entry","detail": "Not performed, tool kit error","sev": 4,"rpn": 48,"cdve": null}]},{"code": "Q16","label": "FOD","hint": "Corps étranger","isTest": false,"objects": [{"sub": "Q16-001","label": "Tools","detail": "Flashlight, mirror, wrench, screwdriver, Allen key","sev": 8,"rpn": 96,"cdve": null},{"sub": "Q16-002","label": "Fasteners and aircraft parts","detail": "Bolts, washers, nuts","sev": 8,"rpn": 96,"cdve": null},{"sub": "Q16-003","label": "Personal effects","detail": "ID badge, glasses, phone, laptop, tablet","sev": 8,"rpn": 96,"cdve": null},{"sub": "Q16-004","label": "Industrial debris","detail": "Silver filings, dust, insulation, metal chips","sev": 8,"rpn": 128,"cdve": null},{"sub": "Q16-005","label": "Additional items","detail": "Consumables, caps, plugs, work order","sev": 8,"rpn": 128,"cdve": null},{"sub": "Q16-006","label": "Maintenance","detail": "Item left in work area, workshop, workstation, corridor","sev": 4,"rpn": 48,"cdve": null}]},{"code": "T01","label": "Câble manquant (test)","hint": "","isTest": true,"objects": [{"sub": "T01","label": "Missing cable","detail": "Copper, aluminum, fiber optic","sev": 8,"rpn": 80,"cdve": null}]},{"code": "T02","label": "Erreur de branchement (test)","hint": "","isTest": true,"objects": [{"sub": "T02","label": "Connection error","detail": "Copper, aluminum, fiber optic","sev": 8,"rpn": 96,"cdve": null}]},{"code": "T03","label": "Shunt manquant (test)","hint": "","isTest": true,"objects": [{"sub": "T03","label": "Missing shunt","detail": "Electrical, Mechanical","sev": 8,"rpn": 96,"cdve": null}]},{"code": "T04","label": "Inversion de branchement (test)","hint": "","isTest": true,"objects": [{"sub": "T04","label": "Connection reversal","detail": "Copper, Aluminum, Fiber optic","sev": 8,"rpn": 96,"cdve": null}]},{"code": "T05","label": "Câble non connecté (test)","hint": "","isTest": true,"objects": [{"sub": "T05","label": "Unconnected cable","detail": "Copper, aluminum, fiber optic","sev": 8,"rpn": 200,"cdve": null}]},{"code": "T06","label": "Perte optique NC (test)","hint": "","isTest": true,"objects": [{"sub": "T06","label": "Insertion loss measurement on non-compliant optical links","detail": "","sev": 6,"rpn": 72,"cdve": null}]},{"code": "T07","label": "Résistance métallisation NC (test)","hint": "","isTest": true,"objects": [{"sub": "T07","label": "Resistance measurement on non-conforming metallization","detail": "VN, VG, VH","sev": 6,"rpn": 36,"cdve": "T07-CDVE"}]},{"code": "T08","label": "Résistance linéique NC (test)","hint": "","isTest": true,"objects": [{"sub": "T08","label": "Non-compliant linear resistance measurement","detail": "EMI sheath, overbraiding","sev": 6,"rpn": 36,"cdve": "T08-CDVE"}]}];

const PRODUITS = ["MIP A350", "740VU", "PTVU", "300VU", "OHP"];
const DETECTIONS = ["Poste", "Test", "Contrôle Final", "Réception", "Client"];
// frequency-ranked shortcuts, measured on 2 346 real defects
const SHORTCUTS_TEST = ["T04", "T02", "T01", "T05", "T03"];
const SHORTCUTS_INSP = ["Q03", "Q11", "Q04", "Q01", "Q05"];
const FIN_SUGGEST = ["3RN3B","3RN1A","3RN1B","3RN2A","3RN3A","1WK22A","1WK53A","300VT101","300VT400","9KS","115VMB","1608VC070A"];

function priorityOf(rpn, sev) {
  if (rpn == null) return { label: "Non coté", color: "#8C8C8C" };
  if (rpn >= 480 || sev === 10) return { label: "Priorité haute", color: "#A32B2B" };
  if (rpn <= 55) return { label: "Priorité basse", color: "#5B7089" };
  return { label: "Priorité moyenne", color: "#8A6D00" };
}
const sevLabel = (s) => (s >= 8 ? "MAJEURE" : "MINEURE");

export default function NCTool() {
  const [screen, setScreen] = useState("header");
  const [header, setHeader] = useState({ msn: "", produit: "", detection: "", station: "V42RA1" });
  const [locked, setLocked] = useState(false);
  const [defects, setDefects] = useState([]);
  const [nature, setNature] = useState(null);
  const [obj, setObj] = useState(null);
  const [cdve, setCdve] = useState(false);
  const [loc, setLoc] = useState("");
  const [qty, setQty] = useState(1);
  const [sevOverride, setSevOverride] = useState(null);
  const [comment, setComment] = useState("");
  const [detail, setDetail] = useState("");
  const [query, setQuery] = useState("");
  const [err, setErr] = useState(null);
  const [blocked, setBlocked] = useState(false);
  const [editIdx, setEditIdx] = useState(null);

  const isTest = header.detection === "Test";
  const headerOk = header.msn.trim() && header.produit && header.detection && header.station.trim();

  /* search across code, nature label, object label, detail text */
  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    const out = [];
    NATURES.forEach((n) =>
      n.objects.forEach((o) => {
        const hay = (n.code + " " + n.label + " " + o.label + " " + o.detail + " " + o.sub).toLowerCase();
        if (hay.includes(q)) out.push({ n, o });
      })
    );
    return out.slice(0, 12);
  }, [query]);

  const orderedNatures = useMemo(() => {
    const arr = [...NATURES];
    arr.sort((a, b) => {
      const pa = isTest ? (a.isTest ? 0 : 1) : (a.isTest ? 1 : 0);
      const pb = isTest ? (b.isTest ? 0 : 1) : (b.isTest ? 1 : 0);
      return pa - pb;
    });
    return arr;
  }, [isTest]);

  const shortcuts = (isTest ? SHORTCUTS_TEST : SHORTCUTS_INSP)
    .map((c) => NATURES.find((n) => n.code === c))
    .filter(Boolean);

  function pickNature(n) { setNature(n); setObj(null); setCdve(false); setScreen("object"); }
  function pickObject(n, o) {
    setNature(n); setObj(o); setCdve(false); setLoc(""); setQty(1);
    setSevOverride(null); setComment(""); setDetail(""); setErr(null); setScreen("detail");
  }

  const effSub = obj ? (cdve && obj.cdve ? obj.cdve : obj.sub) : null;
  const effSev = obj ? (cdve && obj.cdve ? 10 : obj.sev) : null;
  const sev = sevOverride || (effSev != null ? sevLabel(effSev) : "MINEURE");

  function genLine(seq, d) {
    const bits = [d.loc || "-", d.objLabel];
    if (d.detail) bits.push(d.detail);
    return `DEF ${seq} - ${d.sub}${d.qty > 1 ? ` - QTE ${d.qty}` : ""} : ${bits.join(" — ")}`;
  }

  function save() {
    if (!loc.trim()) { setErr("Localisation requise (FIN, zone, ou « - »)"); return; }
    const entry = {
      code: nature.code, natureLabel: nature.label, sub: effSub, objLabel: obj.label,
      detail, loc, qty, sev, comment, rpn: obj.rpn, sevNum: effSev, cdve,
    };
    entry.line = genLine(editIdx !== null ? editIdx + 1 : defects.length + 1, entry);
    if (editIdx !== null) setDefects((d) => d.map((x, i) => (i === editIdx ? entry : x)));
    else { setDefects((d) => [...d, entry]); setLocked(true); }
    setEditIdx(null); setQuery(""); setScreen("list");
  }

  function duplicateLast() {
    const l = defects[defects.length - 1];
    if (!l) return setScreen("nature");
    const n = NATURES.find((x) => x.code === l.code);
    const o = n.objects.find((x) => x.sub === l.sub || x.cdve === l.sub);
    setNature(n); setObj(o); setCdve(l.cdve); setLoc(l.loc);
    setQty(1); setComment(""); setDetail(""); setErr(null); setEditIdx(null); setScreen("detail");
  }

  const S = {
    page: { minHeight: "100%", background: "#EEF1F5", fontFamily: "'IBM Plex Sans',system-ui,sans-serif", color: "#16202E" },
    bar: { background: "#00205B", color: "#fff", padding: "12px 18px", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 6 },
    body: { maxWidth: 760, margin: "0 auto", padding: "18px 14px 110px" },
    card: { background: "#fff", borderRadius: 10, padding: 16, marginBottom: 12, boxShadow: "0 1px 3px rgba(0,0,0,.09)" },
    h1: { fontSize: 19, fontWeight: 700, color: "#00205B", margin: "0 0 4px" },
    sub: { fontSize: 13, color: "#5B7089", margin: "0 0 14px" },
    lab: { display: "block", fontSize: 11.5, fontWeight: 700, color: "#3A4658", marginBottom: 4, letterSpacing: .4, textTransform: "uppercase" },
    inp: { width: "100%", padding: "10px 11px", fontSize: 15, border: "1.5px solid #D2D9E3", borderRadius: 7, boxSizing: "border-box", background: "#fff" },
    row: { marginBottom: 14 },
    tile: { border: "1.5px solid #E1E6EE", borderRadius: 9, padding: "12px 13px", background: "#fff", cursor: "pointer", textAlign: "left", width: "100%" },
    btn: { background: "#00205B", color: "#fff", border: "none", padding: "12px 20px", borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: "pointer" },
    btnG: { background: "#fff", color: "#00205B", border: "1.5px solid #00205B", padding: "10px 16px", borderRadius: 8, fontWeight: 600, fontSize: 13.5, cursor: "pointer" },
    btnGold: { background: "#E0A800", color: "#16202E", border: "none", padding: "12px 20px", borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: "pointer" },
    off: { background: "#C7CDD8", color: "#fff", border: "none", padding: "12px 20px", borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: "not-allowed" },
    foot: { position: "fixed", left: 0, right: 0, bottom: 0, background: "#fff", borderTop: "1px solid #E1E6EE", padding: "10px 14px", display: "flex", gap: 8, justifyContent: "center", flexWrap: "wrap" },
    mono: { fontFamily: "'IBM Plex Mono',monospace", fontSize: 12, background: "#0B1F3F", color: "#B9D4FF", padding: "10px 12px", borderRadius: 7, lineHeight: 1.65, whiteSpace: "pre-wrap", overflowX: "auto" },
    chip: { display: "inline-block", fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 5, color: "#fff", marginLeft: 6 },
    code: { fontFamily: "monospace", fontSize: 11.5, color: "#8A93A3" },
  };

  return (
    <div style={S.page}>
      <div style={S.bar}>
        <div style={{ fontWeight: 800, fontSize: 14.5 }}>
          NC · Saisie structurée <span style={{ ...S.chip, background: "#E0A800", color: "#16202E" }}>CODES OFFICIELS</span>
        </div>
        {screen !== "header" && (
          <div style={{ fontSize: 12, opacity: .85 }}>MSN {header.msn} · {header.produit} · {header.detection}</div>
        )}
      </div>

      {blocked && (
        <div style={{ position: "fixed", top: 60, left: "50%", transform: "translateX(-50%)", background: "#A32B2B", color: "#fff", padding: "9px 16px", borderRadius: 8, fontSize: 13, fontWeight: 600, zIndex: 40, maxWidth: 420, textAlign: "center" }}>
          Produit / détection verrouillés dès le 1er défaut. Créez une nouvelle NC.
        </div>
      )}

      <div style={S.body}>
        {/* ---------- HEADER ---------- */}
        {screen === "header" && (
          <div style={S.card}>
            <h1 style={S.h1}>Nouvelle NC</h1>
            <p style={S.sub}>Saisi une fois. La détection filtre ensuite les codes proposés (T = test, Q = inspection).</p>
            <div style={S.row}><label style={S.lab}>MSN</label>
              <input style={S.inp} placeholder="ex. 2160" value={header.msn} onChange={(e) => setHeader({ ...header, msn: e.target.value })} /></div>
            <div style={S.row}><label style={S.lab}>Produit</label>
              <select style={S.inp} value={header.produit} onChange={(e) => setHeader({ ...header, produit: e.target.value })}>
                <option value="">— choisir —</option>{PRODUITS.map((p) => <option key={p}>{p}</option>)}</select></div>
            <div style={S.row}><label style={S.lab}>Détection</label>
              <select style={S.inp} value={header.detection} onChange={(e) => setHeader({ ...header, detection: e.target.value })}>
                <option value="">— choisir —</option>{DETECTIONS.map((p) => <option key={p}>{p}</option>)}</select></div>
            <div style={S.row}><label style={S.lab}>Station</label>
              <input style={S.inp} value={header.station} onChange={(e) => setHeader({ ...header, station: e.target.value })} /></div>
            <button style={headerOk ? S.btn : S.off} disabled={!headerOk} onClick={() => setScreen("list")}>Continuer →</button>
          </div>
        )}

        {/* ---------- LIST ---------- */}
        {screen === "list" && (
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <h1 style={S.h1}>Défauts de la NC</h1>
              <button style={{ background: "none", border: "none", fontSize: 11.5, fontWeight: 600, color: locked ? "#AEB6C2" : "#00205B", cursor: locked ? "default" : "pointer" }}
                onClick={() => { if (locked) { setBlocked(true); setTimeout(() => setBlocked(false), 2500); } else setScreen("header"); }}>
                {locked ? "🔒 En-tête verrouillé" : "Modifier l'en-tête"}
              </button>
            </div>
            <p style={S.sub}>{defects.length ? `${defects.length} défaut(s) — total ${defects.reduce((s, d) => s + d.qty, 0)}` : "Aucun défaut enregistré."}</p>
            {!defects.length && <div style={{ ...S.card, textAlign: "center", color: "#8A93A3", padding: 28 }}>Cliquez « Ajouter un défaut ».</div>}
            {defects.map((d, i) => {
              const p = priorityOf(d.rpn, d.sevNum);
              return (
                <div key={i} style={{ ...S.card, padding: 12, display: "flex", justifyContent: "space-between", gap: 8 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12.5, fontWeight: 700, color: "#00205B" }}>
                      Défaut {i + 1} · {d.natureLabel}
                      <span style={{ ...S.chip, background: d.sev === "MAJEURE" ? "#A32B2B" : "#8A6D00" }}>{d.sev}</span>
                      {d.cdve && <span style={{ ...S.chip, background: "#5B4A8A" }}>CDVE</span>}
                      {d.qty > 1 && <span style={{ ...S.chip, background: "#5B7089" }}>×{d.qty}</span>}
                    </div>
                    <div style={{ fontFamily: "monospace", fontSize: 11, color: "#5B7089", marginTop: 3 }}>{d.line}</div>
                    <div style={{ fontSize: 10.5, color: p.color, fontWeight: 700, marginTop: 3 }}>{p.label}{d.rpn ? ` · RPN ${d.rpn}` : ""}</div>
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                    <button style={{ ...S.btnG, padding: "4px 8px", fontSize: 11 }} onClick={() => {
                      const n = NATURES.find((x) => x.code === d.code);
                      const o = n.objects.find((x) => x.sub === d.sub || x.cdve === d.sub);
                      setNature(n); setObj(o); setCdve(d.cdve); setLoc(d.loc); setQty(d.qty);
                      setSevOverride(d.sev); setComment(d.comment); setDetail(d.detail); setEditIdx(i); setScreen("detail");
                    }}>Modifier</button>
                    <button style={{ ...S.btnG, padding: "4px 8px", fontSize: 11, color: "#A32B2B", borderColor: "#A32B2B" }}
                      onClick={() => setDefects((x) => x.filter((_, j) => j !== i))}>✕</button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ---------- NATURE (step 1) ---------- */}
        {screen === "nature" && (
          <div>
            <h1 style={S.h1}>Étape 1 — Nature du défaut</h1>
            <p style={S.sub}>Cherchez directement, ou choisissez la nature. {isTest ? "Codes T (test) en tête." : "Codes Q en tête."}</p>

            <div style={S.row}>
              <input style={{ ...S.inp, fontSize: 16 }} placeholder="🔎 Chercher : « contact », « obturateur », « T04 »…"
                value={query} onChange={(e) => setQuery(e.target.value)} />
            </div>

            {results.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <label style={S.lab}>{results.length} résultat(s)</label>
                {results.map((r, i) => (
                  <div key={i} style={{ ...S.tile, marginBottom: 5, padding: "9px 12px" }} onClick={() => pickObject(r.n, r.o)}>
                    <div style={{ fontSize: 13.5, fontWeight: 600 }}>{r.o.label} <span style={S.code}>{r.o.sub}</span></div>
                    <div style={{ fontSize: 11, color: "#8A93A3" }}>{r.n.label}{r.o.detail ? " · " + r.o.detail : ""}</div>
                  </div>
                ))}
              </div>
            )}

            {!query && (
              <div style={{ marginBottom: 16 }}>
                <label style={S.lab}>Les plus fréquents {isTest ? "au test" : "en inspection"}</label>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {shortcuts.map((n) => (
                    <button key={n.code} style={{ ...S.btnG, borderColor: "#E0A800", background: "#FFFBF0" }} onClick={() => pickNature(n)}>
                      {n.label} <span style={S.code}>{n.code}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            <label style={S.lab}>Toutes les natures ({NATURES.length})</label>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(215px,1fr))", gap: 7 }}>
              {orderedNatures.map((n) => (
                <div key={n.code} style={{ ...S.tile, borderColor: n.isTest ? "#B5482A33" : "#E1E6EE" }} onClick={() => pickNature(n)}>
                  <div style={{ fontSize: 13.5, fontWeight: 700 }}>{n.label} <span style={S.code}>{n.code}</span></div>
                  <div style={{ fontSize: 11, color: "#8A93A3", marginTop: 2 }}>{n.hint || `${n.objects.length} élément(s)`}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ---------- OBJECT (step 2) ---------- */}
        {screen === "object" && nature && (
          <div>
            <button style={{ ...S.btnG, marginBottom: 12, padding: "6px 11px", fontSize: 12 }} onClick={() => setScreen("nature")}>← Nature</button>
            <h1 style={S.h1}>Étape 2 — Sur quel élément ?</h1>
            <p style={S.sub}>{nature.label} <span style={S.code}>{nature.code}</span> · {nature.objects.length} élément(s)</p>
            {nature.objects.map((o) => {
              const p = priorityOf(o.rpn, o.sev);
              return (
                <div key={o.sub} style={{ ...S.tile, marginBottom: 6 }} onClick={() => pickObject(nature, o)}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600 }}>{o.label}</div>
                      {o.detail && <div style={{ fontSize: 11, color: "#8A93A3", marginTop: 2 }}>{o.detail}</div>}
                    </div>
                    <div style={{ textAlign: "right", flexShrink: 0 }}>
                      <div style={S.code}>{o.sub}</div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: p.color }}>{o.rpn ? `RPN ${o.rpn}` : "non coté"}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ---------- DETAIL (step 3) ---------- */}
        {screen === "detail" && obj && nature && (
          <div>
            <button style={{ ...S.btnG, marginBottom: 12, padding: "6px 11px", fontSize: 12 }} onClick={() => setScreen(editIdx !== null ? "list" : "object")}>
              ← {editIdx !== null ? "Annuler" : "Élément"}
            </button>
            <div style={S.card}>
              <h1 style={S.h1}>{obj.label}
                <span style={{ ...S.chip, background: sev === "MAJEURE" ? "#A32B2B" : "#8A6D00" }}>{sev}</span>
              </h1>
              <p style={S.sub}>{nature.label} · code <b style={{ fontFamily: "monospace", color: "#00205B" }}>{effSub}</b>
                {obj.rpn ? ` · RPN ${obj.rpn} · ${priorityOf(obj.rpn, effSev).label}` : " · non coté"}</p>

              {obj.cdve && (
                <div style={{ ...S.row, background: "#F5F2FB", border: "1.5px solid #5B4A8A44", borderRadius: 8, padding: "10px 12px" }}>
                  <label style={{ display: "flex", alignItems: "center", gap: 9, cursor: "pointer", fontSize: 14 }}>
                    <input type="checkbox" checked={cdve} onChange={(e) => { setCdve(e.target.checked); setSevOverride(null); }} style={{ width: 17, height: 17 }} />
                    <span><b>Circuit CDVE</b> (commandes de vol) — bascule le code vers <span style={{ fontFamily: "monospace" }}>{obj.cdve}</span></span>
                  </label>
                </div>
              )}

              <div style={S.row}>
                <label style={S.lab}>Localisation (FIN, zone, ou « - »)</label>
                <input style={{ ...S.inp, ...(err ? { borderColor: "#A32B2B", background: "#FDF2F1" } : {}) }} list="fins"
                  placeholder="ex. 3RN3B" value={loc} onChange={(e) => { setLoc(e.target.value); setErr(null); }} />
                <datalist id="fins">{FIN_SUGGEST.map((f) => <option key={f} value={f} />)}</datalist>
                {err && <div style={{ color: "#A32B2B", fontSize: 12, fontWeight: 600, marginTop: 4 }}>{err}</div>}
              </div>

              <div style={S.row}>
                <label style={S.lab}>Précision (optionnel)</label>
                <input style={S.inp} placeholder={obj.detail ? `ex. ${obj.detail.split(",")[0]}` : "ex. bornes J <-> H"}
                  value={detail} onChange={(e) => setDetail(e.target.value)} />
              </div>

              <div style={{ display: "flex", gap: 10 }}>
                <div style={{ ...S.row, flex: "0 0 110px" }}>
                  <label style={S.lab}>Quantité</label>
                  <input type="number" min={1} style={S.inp} value={qty} onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))} />
                </div>
                <div style={{ ...S.row, flex: 1 }}>
                  <label style={S.lab}>Sévérité <span style={{ textTransform: "none", fontWeight: 400, color: "#8A93A3" }}>(auto : sév. {effSev ?? "?"}/10)</span></label>
                  <select style={S.inp} value={sev} onChange={(e) => setSevOverride(e.target.value)}>
                    <option value="MINEURE">Mineure</option><option value="MAJEURE">Majeure</option>
                  </select>
                </div>
              </div>

              <div style={S.row}>
                <label style={S.lab}>Complément libre (optionnel)</label>
                <textarea style={{ ...S.inp, minHeight: 54, fontFamily: "inherit" }} maxLength={200} value={comment}
                  onChange={(e) => setComment(e.target.value)} placeholder="Nuance non capturée ci-dessus…" />
              </div>

              <div style={{ fontSize: 11.5, color: "#5B7089", marginBottom: 5 }}>Aperçu :</div>
              <div style={S.mono}>{genLine(editIdx !== null ? editIdx + 1 : defects.length + 1, { sub: effSub, objLabel: obj.label, detail, loc, qty })}</div>
            </div>
          </div>
        )}

        {/* ---------- REVIEW ---------- */}
        {screen === "review" && (
          <div>
            <button style={{ ...S.btnG, marginBottom: 12, padding: "6px 11px", fontSize: 12 }} onClick={() => setScreen("list")}>← Liste</button>
            <div style={S.card}>
              <h1 style={S.h1}>Texte généré (SAP)</h1>
              <p style={S.sub}>Écrit automatiquement dans la description longue. Codes officiels, comptage exact.</p>
              <div style={S.mono}>{`### DEFAUTS v1 | MSN: ${header.msn} | PRODUIT: ${header.produit} | DETECTION: ${header.detection.toUpperCase()}\n`}
                {defects.map((d) => d.line).join("\n")}
                {`\n### TOTAL: ${defects.reduce((s, d) => s + d.qty, 0)}`}</div>
            </div>
            <div style={{ ...S.card, background: "#EFF6F1" }}>
              <div style={{ fontWeight: 700, color: "#1E8449", marginBottom: 5 }}>✓ Prêt</div>
              <div style={{ fontSize: 13 }}>
                {defects.length} défaut(s) · {defects.filter((d) => d.sev === "MAJEURE").length} majeur(s) ·
                RPN cumulé {defects.reduce((s, d) => s + (d.rpn || 0) * d.qty, 0)}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ---------- FOOTERS ---------- */}
      {screen === "list" && (
        <div style={S.foot}>
          <button style={S.btnG} onClick={duplicateLast} disabled={!defects.length}>⧉ Dupliquer le dernier</button>
          <button style={S.btn} onClick={() => { setQuery(""); setScreen("nature"); }}>+ Ajouter un défaut</button>
          <button style={defects.length ? S.btnGold : S.off} disabled={!defects.length} onClick={() => setScreen("review")}>Terminer →</button>
        </div>
      )}
      {screen === "detail" && (
        <div style={S.foot}>
          <button style={S.btnG} onClick={() => setScreen(editIdx !== null ? "list" : "object")}>Annuler</button>
          <button style={S.btn} onClick={save}>{editIdx !== null ? "Enregistrer la modification" : "Enregistrer ce défaut"}</button>
        </div>
      )}
      {screen === "review" && (
        <div style={S.foot}>
          <button style={S.btnG} onClick={() => setScreen("list")}>← Modifier</button>
          <button style={S.btn} onClick={() => { alert("NC soumise (simulation)."); setScreen("header"); setDefects([]); setLocked(false); setHeader({ msn: "", produit: "", detection: "", station: "V42RA1" }); }}>Soumettre la NC</button>
        </div>
      )}
    </div>
  );
}
