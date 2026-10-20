// NC FTO2 · Saisie structurée: the Streamlit app (reference/app_streamlit.py) rebuilt for a Slate
// Code Sandbox widget. Paste this file in the widget's JavaScript tab, nc_writer.css in the CSS tab
// and nc_writer.html in the HTML tab. No library and no network call: the sandbox allows neither.
// Outside Slate (nc_writer_standalone.html) the same code runs and only shows / downloads the NC.
(function (root) {
"use strict";

// What Slate sees on "Soumettre": the widget state gets {submission: row}, then the event fires.
// The Slate event handler reads <widget>.state.submission.<column> and writes the row (README).
// Never type two opening curly braces in this file: Slate would read them as a Handlebars template.
var CONFIG = { stateKey: "submission", eventName: "submit" };

// --- TAXONOMY: the official code sheet, copied from app_streamlit.py (tests/check_parity.py checks it) ---
// <DATA>
var NATURES = [
  { code: "Q01", label: "Verrouillage", hint: "Contact non verrouillé / faux contact", isTest: false, objects: [
    { sub: "Q01-001", label: "Contact", detail: "Cuivre, aluminium, fibre optique", sev: 7, rpn: 245, cdve: "Q01-003" },
    { sub: "Q01-002", label: "Faux contact", detail: "Non verrouillé", sev: 3, rpn: 120, cdve: null }
  ] },
  { code: "Q03", label: "Élément manquant", hint: "Quelque chose n'est pas là", isTest: false, objects: [
    { sub: "Q03-001", label: "Obturateur", detail: "Circulaire, rectangulaire, module VT, trou de ventilation", sev: 3, rpn: 72, cdve: null },
    { sub: "Q03-002", label: "Gaine thermorétractable", detail: "Basse temp, haute temp", sev: 3, rpn: 72, cdve: null },
    { sub: "Q03-003", label: "Élément mécanique", detail: "Vis, rondelle, écrou, entretoise", sev: 4, rpn: 96, cdve: null },
    { sub: "Q03-004", label: "Élément électrique", detail: "Câble, contact, diode, résistance, connecteur, module VG, raccordement arrière", sev: 4, rpn: 64, cdve: null },
    { sub: "Q03-005", label: "Freinage", detail: "Fil de frein, colle, vernis frangible", sev: 3, rpn: 48, cdve: null },
    { sub: "Q03-006", label: "Collier", detail: "Cheminement, frette plastique, frette ficelle, support en V, plastique, métal", sev: 3, rpn: 108, cdve: null },
    { sub: "Q03-007", label: "Bouchons de protection", detail: "Trou de ventilation, trou ouvert", sev: 3, rpn: 60, cdve: null },
    { sub: "Q03-008", label: "Protection d'extrémité", detail: "Bouchon de prise, sac plastique", sev: 3, rpn: 72, cdve: null },
    { sub: "Q03-009", label: "Étiquette d'inviolabilité", detail: "Serrure de porte, prise coupée", sev: 3, rpn: 36, cdve: null },
    { sub: "Q03-010", label: "Gainage", detail: "Textile, annelée, EMI, réserve", sev: 4, rpn: 72, cdve: null },
    { sub: "Q03-011", label: "Plaque/manchon/drapeau d'identification", detail: "Bout, route, numéro de câble, collier, rampe", sev: 3, rpn: 48, cdve: null },
    { sub: "Q03-012", label: "Étiquette d'identification", detail: "FIN, MSN", sev: 3, rpn: 60, cdve: null }
  ] },
  { code: "Q04", label: "Erreur de montage", hint: "Mauvaise réf, mauvais sens, mauvaise taille", isTest: false, objects: [
    { sub: "Q04-001", label: "Obturateur", detail: "Référence, sens de montage", sev: 3, rpn: 72, cdve: null },
    { sub: "Q04-002", label: "Gaine thermorétractable", detail: "Référence, taille", sev: 3, rpn: 72, cdve: null },
    { sub: "Q04-003", label: "Mécanique", detail: "Vis, rondelle, écrou, entretoise, support en V, structure, barre VT", sev: 4, rpn: 128, cdve: null },
    { sub: "Q04-004", label: "Contact", detail: "Référence, cuivre, aluminium", sev: 9, rpn: 216, cdve: null },
    { sub: "Q04-005", label: "Électrique (Résistance, connecteur, relais...)", detail: "Réf, montage, orientation", sev: 3, rpn: 63, cdve: null },
    { sub: "Q04-006", label: "Fil de freinage", detail: "Référence", sev: 3, rpn: 54, cdve: null },
    { sub: "Q04-007", label: "Collier de cheminement plastique", detail: "Référence, taille, orientation", sev: 3, rpn: 75, cdve: null },
    { sub: "Q04-008", label: "Collier de cheminement métallique", detail: "Référence, taille, orientation", sev: 3, rpn: 45, cdve: null },
    { sub: "Q04-009", label: "Détrompage", detail: "Clé de codage, broche de prise ARINC, clé de polarisation", sev: 4, rpn: 80, cdve: null },
    { sub: "Q04-010", label: "Bouchon de protection ventilation", detail: "Référence", sev: 3, rpn: 36, cdve: null },
    { sub: "Q04-011", label: "Élément électrique", detail: "Tresse de masse, cosse, voyant lumineux", sev: 4, rpn: 96, cdve: null },
    { sub: "Q04-012", label: "Capuchon de protection de prise", detail: "Référence, taille", sev: 3, rpn: 36, cdve: null },
    { sub: "Q04-013", label: "Plaque d'identification", detail: "Plaque, étiquette de fonction, adhésif de bout, manchon", sev: 3, rpn: 72, cdve: null },
    { sub: "Q04-014", label: "Frettage", detail: "Référence frette plastique, référence frette ficelle", sev: 3, rpn: 60, cdve: null }
  ] },
  { code: "Q05", label: "Serrage", hint: "Trop serré, pas assez, desserré", isTest: false, objects: [
    { sub: "Q05-001", label: "Élément électrique", detail: "Raccordement arrière, connecteur, module VG, cosse, disjoncteur", sev: 8, rpn: 480, cdve: null },
    { sub: "Q05-002", label: "Mécanique", detail: "Vis, fil de freinage, vernis frangible, pince, bloc diode, BAND-IT, barre VT", sev: 4, rpn: 160, cdve: null },
    { sub: "Q05-003", label: "Collier corde", detail: "Sur-serré / sous-serré / vis desserrée", sev: 4, rpn: 240, cdve: null },
    { sub: "Q05-004", label: "Frettage", detail: "Collier plastique, frette ficelle", sev: 4, rpn: 120, cdve: null }
  ] },
  { code: "Q06", label: "Mise en œuvre câblage", hint: "Cheminement, gainage, contact/clash", isTest: false, objects: [
    { sub: "Q06-001", label: "Harnais", detail: "Cheminement, gestion de câble, sur/sous-longueur, mauvaise destination", sev: 4, rpn: 96, cdve: null },
    { sub: "Q06-002", label: "Mauvaise installation de gaine", detail: "Ligne visible, mauvaise torsion, branche, chaussette", sev: 4, rpn: 96, cdve: null },
    { sub: "Q06-003", label: "Ruban amalgamant", detail: "Chevauchement, chevauchement permis", sev: 3, rpn: 75, cdve: null },
    { sub: "Q06-004", label: "Câble en contact avec élément structurel", detail: "Clash avec plaque, rampe, tuyau, vis, bielle", sev: 5, rpn: 120, cdve: null },
    { sub: "Q06-005", label: "Câble en contact avec composant électrique", detail: "Clash avec VG, connecteur", sev: 5, rpn: 80, cdve: null },
    { sub: "Q06-006", label: "Mauvais positionnement d'anneau thermo", detail: "Collier plastique, ficelle", sev: 3, rpn: 60, cdve: null },
    { sub: "Q06-007", label: "Frange sur raccordement arrière", detail: "Gaine non sécurisée, gaine trop courte", sev: 3, rpn: 90, cdve: null },
    { sub: "Q06-008", label: "Gainage", detail: "Trop court, en contact avec passe-fil, non sécurisé au connecteur", sev: 4, rpn: 96, cdve: null },
    { sub: "Q06-009", label: "Route non reprise après test", detail: "Câblage non terminé", sev: 3, rpn: 60, cdve: null },
    { sub: "Q06-010", label: "Identification", detail: "Positionnement flamme, plaque, manchon - décalé, non spécifié", sev: 4, rpn: 80, cdve: null },
    { sub: "Q06-011", label: "Implémentation frettage", detail: "Nœud cabestan double, longueur de frette coupée", sev: 3, rpn: 90, cdve: null },
    { sub: "Q06-012", label: "Connexions dans collier Band-it", detail: "", sev: 5, rpn: 60, cdve: null }
  ] },
  { code: "Q07", label: "Sertissage standard", hint: "Contacts et cosses cuivre/alu", isTest: false, objects: [
    { sub: "Q07-001", label: "Contact aluminium", detail: "Dénudage, Sertissage", sev: 9, rpn: 135, cdve: "Q07-006" },
    { sub: "Q07-002", label: "Contact cuivre", detail: "Dénudage, Sertissage", sev: 9, rpn: 180, cdve: "Q07-007" },
    { sub: "Q07-003", label: "Manchon auto-soudeur", detail: "Déformation, surchauffe", sev: 9, rpn: 180, cdve: "Q07-008" },
    { sub: "Q07-004", label: "Cosse cuivre", detail: "Dénudage, Sertissage", sev: 9, rpn: 135, cdve: "Q07-009" },
    { sub: "Q07-005", label: "Cosse aluminium", detail: "Dénudage, Sertissage", sev: 9, rpn: 135, cdve: "Q07-010" }
  ] },
  { code: "Q08", label: "Sertissage spécifique", hint: "Quadrax, twinax, coax, fibre, brasure", isTest: false, objects: [
    { sub: "Q08-001", label: "Contact QUADRAX", detail: "Dénudage, Sertissage", sev: 9, rpn: 27, cdve: null },
    { sub: "Q08-002", label: "Contact TWINAX", detail: "Dénudage, Sertissage", sev: 9, rpn: 27, cdve: null },
    { sub: "Q08-003", label: "Contact TRIAXIAL", detail: "Dénudage, Sertissage", sev: 9, rpn: 27, cdve: null },
    { sub: "Q08-004", label: "Contact BUSCAN", detail: "Dénudage, Sertissage", sev: 9, rpn: 27, cdve: null },
    { sub: "Q08-005", label: "Contact Coax", detail: "Dénudage, Sertissage", sev: 9, rpn: 27, cdve: null },
    { sub: "Q08-006", label: "Contact fibre optique", detail: "Dénudage, Collage", sev: 6, rpn: 18, cdve: null },
    { sub: "Q08-007", label: "Brasure", detail: "Soudure non conforme", sev: 9, rpn: 135, cdve: null }
  ] },
  { code: "Q09", label: "Métallisation / bonding", hint: "Protection, point de masse", isTest: false, objects: [
    { sub: "Q09-001", label: "Protection non appliquée", detail: "Vaseline, peinture de protection", sev: 6, rpn: 42, cdve: "Q09-004" },
    { sub: "Q09-002", label: "Application de protection", detail: "Partiellement appliquée, métallisation visible", sev: 6, rpn: 42, cdve: "Q09-005" },
    { sub: "Q09-003", label: "Point de masse", detail: "Oxydation, diamètre de brosse non conforme", sev: 6, rpn: 42, cdve: "Q09-006" }
  ] },
  { code: "Q10", label: "Dommage structure", hint: "Plaque, structure, main courante, tuyauterie", isTest: false, objects: [
    { sub: "Q10-001", label: "Plaque endommagée", detail: "Impact, rayure, plié, salissure", sev: 4, rpn: 120, cdve: null },
    { sub: "Q10-002", label: "Structure endommagée", detail: "Impact, rayure, salissure", sev: 4, rpn: 120, cdve: null },
    { sub: "Q10-003", label: "Main courante endommagée", detail: "Impact, rayure, plié, salie", sev: 4, rpn: 100, cdve: null },
    { sub: "Q10-004", label: "Colonne", detail: "Impact, rayure, salissure", sev: 4, rpn: 80, cdve: null },
    { sub: "Q10-005", label: "Tuyauterie endommagée", detail: "Impact, rayure, salissure", sev: 4, rpn: 80, cdve: null },
    { sub: "Q10-006", label: "Mécanisme", detail: "Insert, vis - filetages endommagés, vis cassées à l'intérieur", sev: 4, rpn: 160, cdve: null }
  ] },
  { code: "Q11", label: "Dommage élément élec.", hint: "Câble, composant, cosse, contact abîmés", isTest: false, objects: [
    { sub: "Q11-001", label: "Câble coupé", detail: "", sev: 8, rpn: 48, cdve: null },
    { sub: "Q11-014", label: "Câble rayé, endommagé", detail: "", sev: 8, rpn: 480, cdve: null },
    { sub: "Q11-002", label: "Identification", detail: "Onde, étiquette, manchon - déchiré, sali", sev: 3, rpn: 72, cdve: null },
    { sub: "Q11-003", label: "Composant", detail: "Module VG, disjoncteur, module barre VT, connecteur", sev: 4, rpn: 168, cdve: "Q11-016" },
    { sub: "Q11-004", label: "Gaine de protection", detail: "Textile, annelée, EMI", sev: 4, rpn: 96, cdve: null },
    { sub: "Q11-005", label: "Cosse", detail: "Cuivre, aluminium", sev: 4, rpn: 140, cdve: "Q11-018" },
    { sub: "Q11-006", label: "Contact", detail: "Cuivre, aluminium", sev: 9, rpn: 189, cdve: "Q11-019" },
    { sub: "Q11-007", label: "Ruban amalgamant", detail: "Déchiré, sali", sev: 3, rpn: 45, cdve: null },
    { sub: "Q11-008", label: "Gaine thermorétractable", detail: "Déchirée, salie", sev: 3, rpn: 45, cdve: null },
    { sub: "Q11-009", label: "Métallisation tresse de masse", detail: "Brins cassés", sev: 4, rpn: 60, cdve: "Q11-022" },
    { sub: "Q11-010", label: "Collier de câble", detail: "Plastique, métal, support en V", sev: 3, rpn: 60, cdve: null },
    { sub: "Q11-011", label: "Collier BAND-IT", detail: "Collier métal, bande PTFE", sev: 5, rpn: 40, cdve: null },
    { sub: "Q11-012", label: "Barre VT", detail: "Module endommagé, rail déformé", sev: 3, rpn: 60, cdve: null },
    { sub: "Q11-013", label: "Manchons d'étanchéité endommagés", detail: "", sev: 4, rpn: 112, cdve: "Q11-026" }
  ] },
  { code: "Q12", label: "Impression / marquage", hint: "Jauge, type, longueur, identification câble", isTest: false, objects: [
    { sub: "Q12-001", label: "Erreur de jauge câble", detail: "G20, G18", sev: 4, rpn: 80, cdve: "Q12-007" },
    { sub: "Q12-002", label: "Erreur type de câble", detail: "DR, AD", sev: 4, rpn: 120, cdve: "Q12-008" },
    { sub: "Q12-003", label: "Erreur longueur de câble", detail: "Trop court, trop long", sev: 4, rpn: 60, cdve: null },
    { sub: "Q12-004", label: "Identification de câble", detail: "Lisibilité, erreur numéro d'ID", sev: 4, rpn: 80, cdve: null },
    { sub: "Q12-005", label: "Identification", detail: "Manchon, plaque, étiquette - lisibilité", sev: 3, rpn: 45, cdve: null },
    { sub: "Q12-006", label: "Barre VT", detail: "Erreur d'identification de module, référence de module", sev: 3, rpn: 63, cdve: null }
  ] },
  { code: "Q13", label: "Dossier de fabrication", hint: "Opération, tampon, traçabilité, doc", isTest: false, objects: [
    { sub: "Q13-001", label: "Opération", detail: "Non badgé, ordre des opérations non respecté", sev: 3, rpn: 72, cdve: null },
    { sub: "Q13-002", label: "Tampon", detail: "Non apposé sur fiche suiveuse, partiellement visible", sev: 3, rpn: 36, cdve: null },
    { sub: "Q13-003", label: "Étiquette de traçabilité", detail: "CT176 non complété, CT129D non complété", sev: 4, rpn: 64, cdve: null },
    { sub: "Q13-004", label: "Documentation", detail: "Manquante, non conforme", sev: 4, rpn: 80, cdve: null },
    { sub: "Q13-005", label: "Entrée outillage", detail: "Non effectuée, erreur trousse à outils", sev: 4, rpn: 48, cdve: null }
  ] },
  { code: "Q16", label: "FOD", hint: "Corps étranger", isTest: false, objects: [
    { sub: "Q16-001", label: "Outils", detail: "Lampe torche, miroir, clé, tournevis", sev: 8, rpn: 96, cdve: null },
    { sub: "Q16-002", label: "Attaches et pièces avion", detail: "Boulons, rondelles, écrous", sev: 8, rpn: 96, cdve: null },
    { sub: "Q16-003", label: "Effets personnels", detail: "Badge, lunettes, téléphone, ordinateur", sev: 8, rpn: 96, cdve: null },
    { sub: "Q16-004", label: "Débris industriels", detail: "Copeaux, poussière, isolation", sev: 8, rpn: 128, cdve: null },
    { sub: "Q16-005", label: "Éléments supplémentaires", detail: "Consommables, bouchons, fiche d'instruction", sev: 8, rpn: 128, cdve: null },
    { sub: "Q16-006", label: "Maintenance", detail: "Objet laissé dans la zone, atelier, couloir", sev: 4, rpn: 48, cdve: null }
  ] },
  { code: "T01", label: "Câble manquant (test)", hint: "", isTest: true, objects: [
    { sub: "T01", label: "Câble manquant", detail: "Cuivre, aluminium, fibre optique", sev: 8, rpn: 80, cdve: null }
  ] },
  { code: "T02", label: "Erreur de branchement (test)", hint: "", isTest: true, objects: [
    { sub: "T02", label: "Erreur de connexion", detail: "Cuivre, aluminium, fibre optique", sev: 8, rpn: 96, cdve: null }
  ] },
  { code: "T03", label: "Shunt manquant (test)", hint: "", isTest: true, objects: [
    { sub: "T03", label: "Shunt manquant", detail: "Électrique, Mécanique", sev: 8, rpn: 96, cdve: null }
  ] },
  { code: "T04", label: "Inversion de branchement (test)", hint: "", isTest: true, objects: [
    { sub: "T04", label: "Inversion de connexion", detail: "Cuivre, Aluminium, Fibre optique", sev: 8, rpn: 96, cdve: null }
  ] },
  { code: "T05", label: "Câble non connecté (test)", hint: "", isTest: true, objects: [
    { sub: "T05", label: "Câble non connecté", detail: "Cuivre, aluminium, fibre optique", sev: 8, rpn: 200, cdve: null }
  ] },
  { code: "T06", label: "Perte optique NC (test)", hint: "", isTest: true, objects: [
    { sub: "T06", label: "Mesure de perte d'insertion sur liaisons optiques non conformes", detail: "", sev: 6, rpn: 72, cdve: null }
  ] },
  { code: "T07", label: "Résistance métallisation NC (test)", hint: "", isTest: true, objects: [
    { sub: "T07", label: "Mesure de résistance sur métallisation non conforme", detail: "VN, VG, VH", sev: 6, rpn: 36, cdve: "T07-CDVE" }
  ] },
  { code: "T08", label: "Résistance linéique NC (test)", hint: "", isTest: true, objects: [
    { sub: "T08", label: "Mesure de résistance linéique non conforme", detail: "Gaine EMI, surtressage", sev: 6, rpn: 36, cdve: "T08-CDVE" }
  ] }
];

var PRODUITS = ["MIP A350", "MIP 400M", "740VU", "PTVU", "300VU", "OHP", "E Rudder", "MFRL", "MDCD", "Autre"];
var DETECTIONS = ["Poste", "Test", "Contrôle Final", "Réception", "Client", "Autre"];
var FIN_GLOBAL_SUGGEST = ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A", "3RN3B", "51CV", "300VT301", "3CB"];
var FIN_MAPPING = {
  "Q01": ["100VG301", "300VT103", "100VG430", "300VG131", "300VG101", "300VT400"],
  "Q03": ["3CBB", "1608VC087A", "20TC2", "24XE", "4XC", "103PHD01"],
  "Q04": ["300VT400", "1608VC101A", "1608VC006A", "1610VC043", "10REA", "1610VC049"],
  "Q05": ["300VG105", "150RH", "740VU", "300VT101", "300VT400", "9KS"],
  "Q06": ["653VT", "1608VC082A", "703VT15", "740VU", "300VT101", "300VT400"],
  "Q07": ["115VMA", "1608VC097A", "300VT200", "1608VC019", "38JY", "302VMB"],
  "Q08": ["1610VC049", "1608VC076A", "3RN2B", "6TCB", "1608VC087A", "1WK03A"],
  "Q09": ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A"],
  "Q10": ["30CE", "3DB2", "430HC", "740VU", "300VT101", "300VT400"],
  "Q11": ["23FP", "1WK11A", "14PHB", "2WTA", "105SG1", "1DG1"],
  "Q12": ["729VN", "740VU", "300VT101", "300VT400", "9KS", "115VM"],
  "Q13": ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A"],
  "Q16": ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A"],
  "T01": ["18RN", "15RN", "19RN", "3RN2A", "37WE1", "260VT"],
  "T02": ["3RN3A", "3RN1A", "1WK22A", "3RN1B", "3RN2A", "3RN3B"],
  "T03": ["3RN1A", "3RN1", "8GD", "3WX", "651VT3", "29FPA"],
  "T04": ["300VT101", "1608VC070A", "3RN1B", "1608VC020A", "10FC1A", "1608VC097A"],
  "T05": ["3RN2B", "115VMB", "3RN2A", "115VMA", "1PH", "5QJ2"],
  "T06": ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A"],
  "T07": ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A"],
  "T08": ["740VU", "300VT101", "300VT400", "9KS", "115VM", "3RN1A"]
};
// </DATA>

var CTX_OPTIONS = [
  "",
  "Lors de l'inspection du montage",
  "Lors du contrôle final",
  "Lors du contrôle après test",
  "Sur la ligne de production, nous constatons"
];
var ACT_OPTIONS = [
  "",
  "Nous demandons la re-fabrication",
  "Merci de remettre en conformité",
  "Nous demandons le remplacement de l'équipement",
  "Veuillez s'il vous plait procéder à son remplacement"
];
var DEFAULT_HEADER = { msn: "", produit: "MIP A350", detection: "Poste" };
var COMMENT_MAX = 200;

// --- PURE HELPERS (same output as the Python app) ---

function genLine(seq, sub, qty, loc, objLabel, detail, comment) {
  var bits = [loc ? loc : "-", objLabel];
  if (detail) bits.push(detail);
  if (comment) bits.push(comment);
  var qtyStr = qty > 1 ? " - QTE " + qty : "";
  return "DEF " + seq + " - " + sub + qtyStr + " : " + bits.join(" — ");
}

function defectLine(d, i) {
  return genLine(i + 1, d.sub, d.qty, d.loc, d.objLabel, d.detail, d.comment);
}

function totalQty(defects) {
  return defects.reduce(function (s, d) { return s + d.qty; }, 0);
}

function buildSapText(header, ctxCombo, ctxText, defects, actCombo, actText) {
  var t = "### DEFAUTS v1 | PRODUIT: " + header.produit + " | DETECTION: " + header.detection.toUpperCase() + "\n\n";
  var ctx = (ctxCombo + " " + ctxText).trim();
  if (ctx) t += ctx + "\n\n";
  defects.forEach(function (d, i) { t += defectLine(d, i) + "\n"; });
  var act = (actCombo + " " + actText).trim();
  if (act) t += "\n" + act + "\n";
  return t + "\n### TOTAL: " + totalQty(defects);
}

function autoSeverity(sevNum) { return sevNum >= 8 ? "MAJEURE" : "MINEURE"; }

function findNature(code) {
  for (var i = 0; i < NATURES.length; i++) if (NATURES[i].code === code) return NATURES[i];
  return null;
}

function findObject(nature, sub) {
  for (var i = 0; i < nature.objects.length; i++) if (nature.objects[i].sub === sub) return nature.objects[i];
  return null;
}

// test natures first when the NC was found at test, as in the Python app (stable sort)
function sortedNatures(isTest) {
  return NATURES.map(function (n, i) { return { n: n, i: i }; })
    .sort(function (a, b) { return ((a.n.isTest === isTest ? 0 : 1) - (b.n.isTest === isTest ? 0 : 1)) || a.i - b.i; })
    .map(function (x) { return x.n; });
}

function fold(s) {
  return s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
}

// accents ignored, so "element" finds "Élément"
function searchObjects(query) {
  var q = fold(query.trim());
  if (q.length < 2) return null;
  var hits = [];
  NATURES.forEach(function (n) {
    n.objects.forEach(function (o) {
      if (fold(n.code + " " + n.label + " " + o.label + " " + o.detail + " " + o.sub).indexOf(q) !== -1) hits.push({ n: n, o: o });
    });
  });
  return hits;
}

function suggestedFins(code) {
  var list = (FIN_MAPPING[code] || FIN_GLOBAL_SUGGEST).slice();
  if (list.indexOf("Autre") === -1) list.push("Autre");
  return list;
}

function pad(n) { return (n < 10 ? "0" : "") + n; }

function formatTimestamp(d) {
  return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()) + " " +
    pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds());
}

function newId(d) {
  var stamp = formatTimestamp(d).replace(/\D/g, "");
  return "NCW-" + stamp + "-" + Math.random().toString(36).slice(2, 8).toUpperCase();
}

// one row per NC: the six columns of nc_writer_dataset, plus an id and the defects as JSON
function buildRow(header, ctxCombo, ctxText, defects, actCombo, actText, now) {
  return {
    submission_id: newId(now),
    timestamp: formatTimestamp(now),
    msn: header.msn,
    produit: header.produit,
    detection: header.detection,
    total_defauts: totalQty(defects),
    texte_sap: buildSapText(header, ctxCombo, ctxText, defects, actCombo, actText),
    defauts_json: JSON.stringify(defects.map(function (d, i) {
      return { seq: i + 1, code: d.code, sub: d.sub, cdve: d.cdve, loc: d.loc, objet: d.objLabel, precision: d.detail,
        qte: d.qty, severite: d.sev, sev_num: d.sevNum, complement: d.comment, ligne: defectLine(d, i) };
    }))
  };
}

function csvCell(v) {
  var s = String(v);
  return /[";\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
}

function rowToCsv(row) {
  var keys = Object.keys(row);
  return "﻿" + keys.join(";") + "\r\n" + keys.map(function (k) { return csvCell(row[k]); }).join(";") + "\r\n";
}

// --- SLATE BRIDGE: the only place that talks to Slate ---

function slateApi() {
  if (root.SlateFunctions) return root.SlateFunctions;
  /* global SlateFunctions */
  return typeof SlateFunctions !== "undefined" ? SlateFunctions : null;
}

function sendToSlate(row) {
  var sf = slateApi();
  if (!sf) return "standalone";
  if (typeof sf.setState !== "function" || typeof sf.triggerEvent !== "function")
    throw new Error("SlateFunctions.setState / triggerEvent introuvables dans ce widget.");
  var state = {};
  state[CONFIG.stateKey] = row;
  sf.setState(state);
  sf.triggerEvent(CONFIG.eventName);
  return "slate";
}

// --- STATE ---

var S;
function resetState() {
  S = {
    screen: "header",
    header: { msn: DEFAULT_HEADER.msn, produit: DEFAULT_HEADER.produit, detection: DEFAULT_HEADER.detection },
    hd: null,             // header form while on the header screen
    defects: [],
    ctxCombo: "", ctxText: "", actCombo: "", actText: "",
    natCode: null, objSub: null,
    editIdx: null, dupFrom: null,
    query: "",
    fd: null,             // defect form while on the detail screen
    sending: false, error: "",
    done: null            // {row, mode} after "Soumettre"
  };
}

function isTest() { return S.header.detection === "Test"; }

// --- RENDERING ---

var app = null;

function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  });
}

function svg(d) { return '<svg viewBox="0 0 24 24" aria-hidden="true">' + d + "</svg>"; }
var ICON = {
  edit: svg('<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>'),
  trash: svg('<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>'),
  copy: svg('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h10"/>'),
  plus: svg('<path d="M12 5v14M5 12h14"/>'),
  dup: svg('<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M4 16V5a1 1 0 0 1 1-1h11"/>'),
  search: svg('<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>'),
  back: svg('<path d="M15 6l-6 6 6 6"/>'),
  next: svg('<path d="M9 6l6 6-6 6"/>'),
  check: svg('<path d="M5 12.5l4.5 4.5L19 7.5"/>'),
  doc: svg('<path d="M7 3h7l5 5v13H7z"/><path d="M14 3v5h5M10 13h6M10 17h6"/>')
};

function options(list, selected, labels) {
  return list.map(function (v, i) {
    return '<option value="' + esc(v) + '"' + (v === selected ? " selected" : "") + ">" + esc(labels ? labels[i] : v) + "</option>";
  }).join("");
}

function btn(act, label, cls, extra) {
  return '<button type="button" class="btn ' + (cls || "") + '" data-act="' + act + '"' + (extra || "") + ">" + label + "</button>";
}

function iconBtn(act, icon, title, i, cls) {
  return '<button type="button" class="icon-btn ' + (cls || "") + '" data-act="' + act + '" data-i="' + i + '" title="' + title + '" aria-label="' + title + '">' + icon + "</button>";
}

function chips(act, list, selected) {
  return '<div class="chips">' + list.filter(Boolean).map(function (v) {
    return '<button type="button" class="chip" data-act="' + act + '" data-v="' + esc(v) + '" aria-pressed="' + (v === selected) + '">' + esc(v) + "</button>";
  }).join("") + "</div>";
}

function sevBadge(sev) {
  return '<span class="badge ' + (sev === "MAJEURE" ? "maj" : "min") + '">' + (sev === "MAJEURE" ? "Majeure" : "Mineure") + "</span>";
}

function cdveBadge(label) { return '<span class="badge cdve">' + (label || "CDVE") + "</span>"; }

function go(screen) {
  S.screen = screen;
  S.error = "";
  if (screen === "header") {
    var h = S.header;
    S.hd = {
      msn: h.msn,
      produitSel: PRODUITS.indexOf(h.produit) !== -1 ? h.produit : "Autre",
      produitCustom: PRODUITS.indexOf(h.produit) !== -1 ? "" : h.produit,
      detectionSel: DETECTIONS.indexOf(h.detection) !== -1 ? h.detection : "Autre",
      detectionCustom: DETECTIONS.indexOf(h.detection) !== -1 ? "" : h.detection
    };
  }
  if (screen === "nature") S.query = "";
  render();
  try { window.scrollTo(0, 0); } catch (e) { /* scrolling can be refused in a sandbox */ }
}

function headerValues() {
  var d = S.hd;
  return {
    msn: d.msn.trim(),
    produit: (d.produitSel === "Autre" ? d.produitCustom : d.produitSel).trim(),
    detection: (d.detectionSel === "Autre" ? d.detectionCustom : d.detectionSel).trim()
  };
}

function headerComplete() {
  var v = headerValues();
  return !!(v.msn && v.produit && v.detection);
}

function sapText() {
  return buildSapText(S.header, S.ctxCombo, S.ctxText, S.defects, S.actCombo, S.actText);
}

// top bar: title, and once the header is known, the NC's identity
function renderTop() {
  var h = S.header, s = S.screen;
  var ident = s !== "header" && s !== "done" ?
    '<div class="ident">' +
      '<div class="id"><span>MSN</span><b>' + esc(h.msn) + "</b></div>" +
      '<div class="id"><span>Produit</span><b>' + esc(h.produit) + "</b></div>" +
      '<div class="id"><span>Détection</span><b>' + esc(h.detection) + "</b></div>" +
      (s === "list" ? btn("edit-header", ICON.edit + "Modifier", "on-dark small") : "") +
    "</div>" : "";
  return '<header class="top"><div class="brand"><div class="logo">NC</div><div><h1>Saisie structurée de NC</h1>' +
    "<p>FTO2 · texte au format DEFAUTS v1</p></div></div>" + ident + "</header>";
}

function stepper(cur) {
  return '<ol class="steps">' + ["Nature", "Objet", "Détails"].map(function (s, i) {
    var n = i + 1, st = n < cur ? "done" : n === cur ? "cur" : "";
    return '<li class="' + st + '"><span class="dot">' + (n < cur ? ICON.check : n) + "</span>" + s + "</li>";
  }).join('<li class="sep" aria-hidden="true"></li>') + "</ol>";
}

function statsHtml() {
  var maj = S.defects.filter(function (d) { return d.sev === "MAJEURE"; }).length;
  return '<div><b>' + S.defects.length + "</b><span>défaut" + (S.defects.length > 1 ? "s" : "") + "</span></div>" +
    "<div><b>" + totalQty(S.defects) + "</b><span>quantité totale</span></div>" +
    '<div class="' + (maj ? "has-maj" : "") + '"><b>' + maj + "</b><span>majeure" + (maj > 1 ? "s" : "") + "</span></div>";
}

// right column: the SAP text as it builds up, and the way forward
function renderPanel() {
  var s = S.screen;
  if (s === "header") {
    return '<aside class="side"><div class="panel"><h3>Comment ça marche</h3><ol class="how">' +
      "<li><b>En-tête</b><span>MSN, produit et étape où le défaut a été vu.</span></li>" +
      "<li><b>Défauts</b><span>Une ligne par défaut, choisie dans la grille officielle des codes. Le texte se construit tout seul.</span></li>" +
      "<li><b>Vérification</b><span>Relecture du texte SAP, puis soumission de la NC.</span></li>" +
      "</ol></div></aside>";
  }
  var wizard = s === "nature" || s === "object" || s === "detail";
  var foot = "";
  if (s === "list") {
    foot = btn("finish", "Vérifier et soumettre" + ICON.next, "primary block", S.defects.length ? "" : " disabled") +
      (S.defects.length ? "" : '<p class="note">Ajoutez au moins un défaut pour continuer.</p>');
  } else if (s === "review") {
    foot = (S.error ? '<p class="error">' + esc(S.error) + "</p>" : "") +
      btn("submit", S.sending ? "Envoi…" : ICON.check + "Soumettre la NC", "primary block", S.sending ? " disabled" : "") +
      btn("back", ICON.back + "Retour aux défauts", "ghost block", ' data-to="list"');
  } else if (s === "done") {
    foot = btn("new-nc", ICON.plus + "Nouvelle NC", "primary block") +
      (S.done.mode === "slate" ? "" : btn("download", "Télécharger la ligne (CSV)", "secondary block"));
  } else if (wizard) {
    foot = '<p class="note">Enregistrez ou annulez le défaut en cours pour revenir à la liste.</p>';
  }
  return '<aside class="side"><div class="panel">' +
    '<div class="panel-head"><h3>' + ICON.doc + "Texte SAP</h3>" + btn("copy", ICON.copy + "Copier", "ghost small") + "</div>" +
    (s === "done" ? "" : '<div class="stats" id="ncw-stats">' + statsHtml() + "</div>") +
    '<pre class="sap" id="ncw-sap">' + esc(s === "done" ? S.done.row.texte_sap : sapText()) + "</pre>" + foot + "</div></aside>";
}

function renderHeader() {
  var d = S.hd;
  return '<section class="card"><div class="card-head"><div><h2>Nouvelle NC</h2>' +
    '<p class="sub">Ces informations ouvrent le texte SAP.</p></div></div>' +
    '<div class="grid2">' +
      '<label class="field"><span class="label">MSN</span><input type="text" class="big" data-field="hd.msn" value="' + esc(d.msn) + '" placeholder="ex. 2160" autocomplete="off"></label>' +
      '<div class="field"><label><span class="label">Produit</span><select class="big" data-field="hd.produitSel">' + options(PRODUITS, d.produitSel) + "</select></label>" +
        (d.produitSel === "Autre" ? '<input type="text" class="under" data-field="hd.produitCustom" value="' + esc(d.produitCustom) + '" placeholder="Préciser le produit" aria-label="Préciser le produit">' : "") +
      "</div>" +
    "</div>" +
    '<div class="field"><span class="label">Détection</span>' + chips("pick-detection", DETECTIONS, d.detectionSel) +
      (d.detectionSel === "Autre" ? '<input type="text" class="under narrow" data-field="hd.detectionCustom" value="' + esc(d.detectionCustom) + '" placeholder="Préciser la détection" aria-label="Préciser la détection">' : "") +
    "</div>" +
    '<div class="card-foot">' + btn("header-continue", "Continuer" + ICON.next, "primary", headerComplete() ? "" : " disabled") + "</div></section>";
}

function templateCard(title, sub, act, list, combo, field, text, placeholder) {
  return '<section class="card"><div class="card-head"><div><h2>' + title + '<span class="opt">optionnel</span></h2>' +
    '<p class="sub">' + sub + "</p></div></div>" + chips(act, list, combo) +
    '<textarea rows="2" data-field="' + field + '" placeholder="' + placeholder + '" aria-label="' + title + '">' + esc(text) + "</textarea></section>";
}

function renderDefect(d, i) {
  return '<article class="defect"><div class="num">' + (i + 1) + "</div>" +
    '<div class="defect-body">' +
      '<div class="defect-top"><span class="code">' + esc(d.sub) + "</span><strong>" + esc(d.objLabel) + '</strong><span class="muted">' + esc(d.natureLabel) + "</span></div>" +
      '<div class="defect-meta">' + sevBadge(d.sev) + (d.cdve ? cdveBadge() : "") +
        '<span class="meta">FIN <b>' + esc(d.loc || "—") + '</b></span><span class="meta">Qté <b>' + d.qty + "</b></span></div>" +
      '<pre class="line">' + esc(defectLine(d, i)) + "</pre>" +
    "</div>" +
    '<div class="defect-actions">' + iconBtn("edit-defect", ICON.edit, "Modifier", i) + iconBtn("delete-defect", ICON.trash, "Supprimer", i, "danger") + "</div></article>";
}

function renderList() {
  var n = S.defects.length;
  var h = templateCard("Contexte de découverte", "Choisissez un début de phrase, puis complétez si besoin.", "pick-ctx",
    CTX_OPTIONS, S.ctxCombo, "ctxText", S.ctxText, "Compléter la phrase…");
  h += '<section class="card"><div class="card-head"><div><h2>Défauts<span class="count">' + n + "</span></h2>" +
    '<p class="sub">Une ligne par défaut. L\'ordre est celui du texte SAP.</p></div>' +
    '<div class="head-actions">' + btn("duplicate-last", ICON.dup + "Dupliquer le dernier", "secondary", n ? "" : " disabled") +
    btn("add-defect", ICON.plus + "Ajouter un défaut", "primary") + "</div></div>";
  h += n ? '<div class="defects">' + S.defects.map(renderDefect).join("") + "</div>"
         : '<div class="empty">' + ICON.doc + "<b>Aucun défaut pour l'instant</b><span>Ajoutez le premier défaut constaté sur ce produit.</span></div>";
  h += "</section>";
  h += templateCard("Action demandée", "Ce qui est attendu pour solder la NC.", "pick-act",
    ACT_OPTIONS, S.actCombo, "actText", S.actText, "Compléter la demande…");
  return h;
}

function natureTile(n) {
  var hint = n.hint || n.objects[0].detail;
  return '<button type="button" class="tile" data-act="pick-nature" data-code="' + n.code + '">' +
    '<span class="tile-top"><span class="code tile-code">' + n.code + '</span><span class="muted small">' + n.objects.length + " objet" + (n.objects.length > 1 ? "s" : "") + "</span></span>" +
    "<strong>" + esc(n.label) + "</strong>" + (hint ? '<span class="muted">' + esc(hint) + "</span>" : "") + "</button>";
}

function renderNatureResults() {
  var hits = searchObjects(S.query);
  if (hits) {
    if (!hits.length) return '<div class="empty small">' + ICON.search + "<b>Aucun code ne correspond</b><span>Essayez un autre mot, ou parcourez les natures.</span></div>";
    return '<p class="muted small">' + hits.length + " résultat" + (hits.length > 1 ? "s" : "") + "</p>" +
      '<div class="rows">' + hits.map(function (x) {
        return '<button type="button" class="row" data-act="pick-object" data-code="' + x.n.code + '" data-sub="' + x.o.sub + '">' +
          '<span class="code">' + x.o.sub + "</span><span class=\"row-main\"><strong>" + esc(x.o.label) + "</strong>" +
          (x.o.detail ? '<span class="muted">' + esc(x.o.detail) + "</span>" : "") + "</span>" +
          '<span class="muted">' + esc(x.n.label) + "</span>" + ICON.next + "</button>";
      }).join("") + "</div>";
  }
  var groups = [[true, "Défauts constatés au test"], [false, "Défauts constatés à l'inspection"]];
  if (!isTest()) groups.reverse();
  return groups.map(function (g) {
    return '<h3 class="group">' + g[1] + '</h3><div class="tiles">' +
      NATURES.filter(function (n) { return n.isTest === g[0]; }).map(natureTile).join("") + "</div>";
  }).join("");
}

function renderNature() {
  return stepper(1) + '<section class="card"><div class="card-head"><div><h2>Nature du défaut</h2>' +
    '<p class="sub">Recherchez un mot ou un code, ou parcourez les familles.</p></div>' + btn("back", ICON.back + "Retour", "ghost", ' data-to="list"') + "</div>" +
    '<label class="search">' + ICON.search + '<input type="search" data-field="query" value="' + esc(S.query) +
    '" placeholder="contact, obturateur, T04, gaine…" autocomplete="off" aria-label="Recherche rapide"></label>' +
    '<div id="ncw-results">' + renderNatureResults() + "</div></section>";
}

function renderObject() {
  var n = findNature(S.natCode);
  return stepper(2) + '<section class="card"><div class="card-head"><div><h2><span class="code">' + n.code + "</span>" + esc(n.label) + "</h2>" +
    '<p class="sub">Choisissez l\'élément concerné.</p></div>' + btn("back", ICON.back + "Natures", "ghost", ' data-to="nature"') + "</div>" +
    '<div class="objects">' + n.objects.map(function (o) {
      return '<button type="button" class="pick" data-act="pick-object" data-code="' + n.code + '" data-sub="' + o.sub + '">' +
        '<span class="pick-top"><span class="code">' + o.sub + "</span>" + sevBadge(autoSeverity(o.sev)) + (o.cdve ? cdveBadge("CDVE possible") : "") + "</span>" +
        "<strong>" + esc(o.label) + "</strong>" + (o.detail ? '<span class="muted">' + esc(o.detail) + "</span>" : "") + "</button>";
    }).join("") + "</div></section>";
}

function detailContext() {
  var n = findNature(S.natCode), o = findObject(n, S.objSub), f = S.fd;
  var sevNum = f.cdve ? 10 : o.sev;
  var loc = f.locCustom.trim() || (f.locSel === "Autre" ? "" : f.locSel);
  var seq = S.editIdx !== null ? S.editIdx + 1 : S.defects.length + 1;
  var qty = /^\d+$/.test(String(f.qty).trim()) ? parseInt(f.qty, 10) : NaN;
  var errors = [];
  if (!(qty >= 1)) errors.push("La quantité doit être un nombre entier supérieur ou égal à 1.");
  if (f.locSel === "Autre" && !f.locCustom.trim()) errors.push("« Autre » choisi : saisir la localisation manuellement.");
  return {
    n: n, o: o, sevNum: sevNum, loc: loc, qty: qty, errors: errors,
    sub: f.cdve ? o.cdve : o.sub,
    line: genLine(seq, f.cdve ? o.cdve : o.sub, qty >= 1 ? qty : 1, loc, o.label, f.detail.trim(), f.comment.trim())
  };
}

function initDetailForm() {
  var n = findNature(S.natCode), o = findObject(n, S.objSub);
  var src = S.editIdx !== null ? S.defects[S.editIdx] : S.dupFrom !== null ? S.defects[S.dupFrom] : null;
  var fins = suggestedFins(n.code);
  var loc = src ? src.loc : "";
  S.fd = {
    cdve: src ? !!src.cdve && !!o.cdve : false,
    locSel: loc && fins.indexOf(loc) !== -1 ? loc : "",
    locCustom: loc && fins.indexOf(loc) === -1 ? loc : "",
    detail: src ? src.detail : "",
    qty: src ? String(src.qty) : "1",
    comment: src ? src.comment : "",
    sev: src ? src.sev : autoSeverity(o.sev),
    sevTouched: !!src
  };
}

function errorsHtml(errors) {
  return errors.map(function (e) { return "<li>" + esc(e) + "</li>"; }).join("");
}

function renderDetail() {
  var c = detailContext(), f = S.fd, o = c.o;
  var fins = suggestedFins(c.n.code);
  var h = stepper(3) + '<section class="card"><div class="card-head"><div><h2><span class="code" id="ncw-sub">' + c.sub + "</span>" + esc(o.label) + "</h2>" +
    '<p class="sub">' + esc(c.n.label) + (o.detail ? " · " + esc(o.detail) : "") + "</p></div>" +
    (S.editIdx !== null ? '<span class="tag">Modification du défaut ' + (S.editIdx + 1) + "</span>" : S.dupFrom !== null ? '<span class="tag">Copie du défaut ' + (S.dupFrom + 1) + "</span>" : "") + "</div>";
  if (o.cdve) {
    h += '<label class="switch-row"><input type="checkbox" class="switch" data-field="fd.cdve"' + (f.cdve ? " checked" : "") + ">" +
      "<span><b>Circuit Commandes de Vol (CDVE)</b><small>Le code devient " + o.cdve + " et la sévérité passe à majeure.</small></span></label>";
  }
  h += '<div class="grid2">' +
      '<div class="field"><label><span class="label">Localisation (FIN / zone)</span><select data-field="fd.locSel">' +
        options([""].concat(fins), f.locSel, ["— Choisir dans la liste —"].concat(fins)) + "</select></label>" +
        '<input type="text" class="under" data-field="fd.locCustom" value="' + esc(f.locCustom) + '" placeholder="ou saisir un autre FIN / une zone" aria-label="Saisir manuellement" autocomplete="off"></div>' +
      '<label class="field"><span class="label">Précision <span class="opt">optionnel</span></span><input type="text" data-field="fd.detail" value="' + esc(f.detail) + '" placeholder="' + esc(o.detail || "ex. bornes concernées") + '"></label>' +
    "</div>" +
    '<div class="grid2">' +
      '<label class="field"><span class="label">Quantité</span><input type="number" class="qty" min="1" step="1" data-field="fd.qty" value="' + esc(f.qty) + '"></label>' +
      '<div class="field"><span class="label">Sévérité</span><div class="seg" role="group" aria-label="Sévérité">' +
        ["MINEURE", "MAJEURE"].map(function (v) {
          return '<button type="button" class="' + (v === "MAJEURE" ? "maj" : "min") + '" data-act="set-sev" data-v="' + v + '" aria-pressed="' + (f.sev === v) + '">' + (v === "MAJEURE" ? "Majeure" : "Mineure") + "</button>";
        }).join("") + "</div></div>" +
    "</div>" +
    '<label class="field"><span class="label">Complément libre <span class="opt">optionnel</span><span class="counter" id="ncw-count">' + f.comment.length + " / " + COMMENT_MAX + "</span></span>" +
    '<textarea rows="2" maxlength="' + COMMENT_MAX + '" data-field="fd.comment">' + esc(f.comment) + "</textarea></label>" +
    '<div class="preview"><span class="label">Ligne générée</span><pre class="line big" id="ncw-preview">' + esc(c.line) + "</pre></div>" +
    '<ul class="errors" id="ncw-errors">' + errorsHtml(c.errors) + "</ul>" +
    '<div class="card-foot">' + btn("cancel-detail", "Annuler", "ghost") + btn("save-defect", ICON.check + "Enregistrer le défaut", "primary", c.errors.length ? " disabled" : "") + "</div></section>";
  return h;
}

function renderReview() {
  var ctx = (S.ctxCombo + " " + S.ctxText).trim(), act = (S.actCombo + " " + S.actText).trim();
  return '<section class="card"><div class="card-head"><div><h2>Vérification</h2>' +
    '<p class="sub">Relisez avant de soumettre. Le texte de droite est exactement celui qui sera envoyé.</p></div></div>' +
    '<dl class="facts"><div><dt>Contexte</dt><dd>' + (ctx ? esc(ctx) : '<span class="muted">—</span>') + "</dd></div>" +
    "<div><dt>Action demandée</dt><dd>" + (act ? esc(act) : '<span class="muted">—</span>') + "</dd></div></dl>" +
    '<table class="recap"><thead><tr><th>#</th><th>Code</th><th>Objet</th><th>FIN / zone</th><th class="r">Qté</th><th>Sévérité</th></tr></thead><tbody>' +
    S.defects.map(function (d, i) {
      return "<tr><td>" + (i + 1) + '</td><td><span class="code">' + esc(d.sub) + "</span></td><td>" + esc(d.objLabel) +
        (d.detail ? '<span class="muted"> · ' + esc(d.detail) + "</span>" : "") + "</td><td>" + esc(d.loc || "—") + '</td><td class="r">' + d.qty +
        "</td><td>" + sevBadge(d.sev) + (d.cdve ? " " + cdveBadge() : "") + "</td></tr>";
    }).join("") + "</tbody></table></section>";
}

function renderDone() {
  var r = S.done.row, slate = S.done.mode === "slate";
  return '<section class="card done-card"><div class="done-icon' + (slate ? "" : " warn-icon") + '">' + (slate ? ICON.check : ICON.doc) + "</div>" +
    (slate ? "<h2>NC soumise</h2><p class=\"ok\">NC transmise à Slate (" + esc(r.submission_id) + ").</p>"
           : "<h2>NC prête</h2><p class=\"warn\">Hors Slate : rien n'a été enregistré. Copiez le texte ou téléchargez la ligne.</p>") +
    '<dl class="facts"><div><dt>MSN</dt><dd>' + esc(r.msn) + "</dd></div><div><dt>Produit</dt><dd>" + esc(r.produit) + "</dd></div>" +
    "<div><dt>Détection</dt><dd>" + esc(r.detection) + "</dd></div><div><dt>Quantité totale</dt><dd>" + r.total_defauts + "</dd></div></dl></section>";
}

function render() {
  var s = S.screen, body;
  if (s === "header") body = renderHeader();
  else if (s === "list") body = renderList();
  else if (s === "nature") body = renderNature();
  else if (s === "object") body = renderObject();
  else if (s === "detail") body = renderDetail();
  else if (s === "review") body = renderReview();
  else body = renderDone();
  app.innerHTML = renderTop() + '<div class="layout"><main class="main">' + body + "</main>" + renderPanel() + "</div>" +
    '<div class="toast" id="ncw-toast" role="status"></div>';
  var first = app.querySelector("[data-field='query'], [data-field='hd.msn']");
  if (first && !first.value) try { first.focus(); } catch (e) { /* focus can be refused in an iframe */ }
}

// partial refreshes, so typing never loses the cursor
function refreshHeaderButton() {
  var b = app.querySelector("[data-act='header-continue']");
  if (b) b.disabled = !headerComplete();
}

function refreshPanel() {
  var pre = app.querySelector("#ncw-sap"), st = app.querySelector("#ncw-stats");
  if (pre && S.screen !== "done") pre.textContent = sapText();
  if (st) st.innerHTML = statsHtml();
}

function refreshDetail() {
  var c = detailContext();
  app.querySelector("#ncw-preview").textContent = c.line;
  app.querySelector("#ncw-count").textContent = S.fd.comment.length + " / " + COMMENT_MAX;
  app.querySelector("#ncw-errors").innerHTML = errorsHtml(c.errors);
  app.querySelector("[data-act='save-defect']").disabled = c.errors.length > 0;
}

function toast(msg) {
  var t = app.querySelector("#ncw-toast");
  if (!t) return;
  t.textContent = msg;
  t.className = "toast show";
  clearTimeout(toast.timer);
  toast.timer = setTimeout(function () { t.className = "toast"; }, 2200);
}

// --- ACTIONS ---

function saveDefect() {
  var c = detailContext(), f = S.fd;
  if (c.errors.length) return;
  var entry = {
    code: c.n.code, natureLabel: c.n.label, sub: c.sub, baseSub: c.o.sub, objLabel: c.o.label,
    detail: f.detail.trim(), loc: c.loc, qty: c.qty, sev: f.sev, comment: f.comment.trim(),
    sevNum: c.sevNum, cdve: f.cdve
  };
  var saved = S.editIdx !== null ? S.editIdx + 1 : S.defects.length + 1;
  if (S.editIdx !== null) S.defects[S.editIdx] = entry; else S.defects.push(entry);
  S.editIdx = null;
  S.dupFrom = null;
  go("list");
  toast("Défaut " + saved + " enregistré");
}

function openDetail(code, sub, editIdx, dupFrom) {
  S.natCode = code;
  S.objSub = sub;
  S.editIdx = editIdx;
  S.dupFrom = dupFrom;
  initDetailForm();
  go("detail");
}

function copyText(text) {
  function fallback() {
    var ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    if (ok) { toast("Texte copié"); return; }
    var pre = app.querySelector("#ncw-sap"), range = document.createRange();
    range.selectNodeContents(pre);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    toast("Texte sélectionné : Ctrl+C pour copier");
  }
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () { toast("Texte copié"); }, fallback);
      return;
    }
  } catch (e) { /* blocked in some sandboxes */ }
  fallback();
}

function download(row) {
  try {
    var blob = new Blob([rowToCsv(row)], { type: "text/csv;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "nc_" + row.submission_id + ".csv";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); document.body.removeChild(a); }, 0);
  } catch (e) {
    toast("Téléchargement impossible ici");
  }
}

function submit() {
  if (S.sending || !S.defects.length) return;
  var row = buildRow(S.header, S.ctxCombo, S.ctxText, S.defects, S.actCombo, S.actText, new Date());
  S.sending = true;
  S.error = "";
  try {
    var mode = sendToSlate(row);
    S.done = { row: row, mode: mode };
    S.sending = false;
    S.screen = "done";
  } catch (e) {
    S.sending = false;
    S.error = "Envoi impossible : " + (e && e.message ? e.message : e) + " La NC n'est pas perdue : copiez le texte ou réessayez.";
  }
  render();
}

function onClick(e) {
  var el = e.target.closest ? e.target.closest("[data-act]") : null;
  if (!el || el.disabled || !app.contains(el)) return;
  var act = el.getAttribute("data-act"), i = parseInt(el.getAttribute("data-i"), 10), v = el.getAttribute("data-v");
  if (act === "header-continue") {
    if (!headerComplete()) return;
    S.header = headerValues();
    go("list");
  } else if (act === "pick-detection") { S.hd.detectionSel = v; render(); }
  else if (act === "pick-ctx") { S.ctxCombo = S.ctxCombo === v ? "" : v; render(); }
  else if (act === "pick-act") { S.actCombo = S.actCombo === v ? "" : v; render(); }
  else if (act === "back") go(el.getAttribute("data-to"));
  else if (act === "edit-header") go("header");
  else if (act === "add-defect") { S.editIdx = null; S.dupFrom = null; go("nature"); }
  else if (act === "duplicate-last") {
    var last = S.defects[S.defects.length - 1];
    openDetail(last.code, last.baseSub, null, S.defects.length - 1);
  } else if (act === "edit-defect") openDetail(S.defects[i].code, S.defects[i].baseSub, i, null);
  else if (act === "delete-defect") { S.defects.splice(i, 1); render(); toast("Défaut " + (i + 1) + " supprimé"); }
  else if (act === "finish") go("review");
  else if (act === "pick-nature") { S.natCode = el.getAttribute("data-code"); go("object"); }
  else if (act === "pick-object") openDetail(el.getAttribute("data-code"), el.getAttribute("data-sub"), null, null);
  else if (act === "set-sev") { S.fd.sev = v; S.fd.sevTouched = true; render(); }
  else if (act === "cancel-detail") {
    var back = S.editIdx !== null || S.dupFrom !== null ? "list" : "object";
    S.editIdx = null;
    S.dupFrom = null;
    go(back);
  } else if (act === "save-defect") saveDefect();
  else if (act === "copy") copyText(S.screen === "done" ? S.done.row.texte_sap : sapText());
  else if (act === "submit") submit();
  else if (act === "download") download(S.done.row);
  else if (act === "new-nc") { resetState(); go("header"); }
}

function onInput(e) {
  var el = e.target, field = el.getAttribute && el.getAttribute("data-field");
  if (!field) return;
  var val = el.type === "checkbox" ? el.checked : el.value;
  var parts = field.split(".");
  if (parts.length === 2) S[parts[0]][parts[1]] = val; else S[field] = val;
  if (parts[0] === "hd") {
    if (field === "hd.produitSel") render(); else refreshHeaderButton();
  } else if (parts[0] === "fd") {
    if (field === "fd.cdve") {
      var o = findObject(findNature(S.natCode), S.objSub);
      if (!S.fd.sevTouched) S.fd.sev = autoSeverity(S.fd.cdve ? 10 : o.sev);
      render();
    } else refreshDetail();
  } else if (field === "query") {
    app.querySelector("#ncw-results").innerHTML = renderNatureResults();
  } else if (field === "ctxText" || field === "actText") {
    refreshPanel();
  }
}

function isChoice(el) { return el.tagName === "SELECT" || el.type === "checkbox"; }

function init() {
  app = document.getElementById("nc-writer");
  if (!app) {
    app = document.createElement("div");
    app.id = "nc-writer";
    document.body.appendChild(app);
  }
  app.className = "ncw";
  resetState();
  app.addEventListener("click", onClick);
  // text fields on "input", selects and checkboxes on "change" (some browsers fire both for a select)
  app.addEventListener("input", function (e) { if (!isChoice(e.target)) onInput(e); });
  app.addEventListener("change", function (e) { if (isChoice(e.target)) onInput(e); });
  go("header");
}

if (typeof module === "object" && module.exports) {
  module.exports = { NATURES: NATURES, PRODUITS: PRODUITS, DETECTIONS: DETECTIONS, FIN_MAPPING: FIN_MAPPING, FIN_GLOBAL_SUGGEST: FIN_GLOBAL_SUGGEST,
    CTX_OPTIONS: CTX_OPTIONS, ACT_OPTIONS: ACT_OPTIONS, CONFIG: CONFIG, genLine: genLine, buildSapText: buildSapText, buildRow: buildRow,
    searchObjects: searchObjects, sortedNatures: sortedNatures, suggestedFins: suggestedFins, rowToCsv: rowToCsv, formatTimestamp: formatTimestamp };
} else if (typeof document !== "undefined") {
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init); else init();
}
})(typeof window !== "undefined" ? window : this);
