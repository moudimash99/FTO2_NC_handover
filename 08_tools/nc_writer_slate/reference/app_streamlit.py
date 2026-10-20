from datetime import datetime
import csv
import os
from foundry.transforms import Dataset
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NC FTO2 · Saisie", layout="centered")


# --- CUSTOM CSS ---

st.markdown(
    """
<style>
    div[data-testid="InputInstructions"] {
        display: none !important;
    }

    /* Reduce vertical spacing between blocks */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
    }

    /* Make text areas more compact */
    div[data-testid="stTextArea"] textarea {
        min-height: 90px !important;
        border-radius: 10px !important;
    }

    /* Slightly smoother inputs/selects */
    div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        border-radius: 10px !important;
    }

    /* Reduce gap under subheaders a bit */
    h3 {
        margin-bottom: 0.3rem !important;
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- COMPLETE 123-CODE TAXONOMY (TRADUITE EN FRANÇAIS) ---

NATURES = [
    {
        "code": "Q01",
        "label": "Verrouillage",
        "hint": "Contact non verrouillé / faux contact",
        "isTest": False,
        "objects": [
            {
                "sub": "Q01-001",
                "label": "Contact",
                "detail": "Cuivre, aluminium, fibre optique",
                "sev": 7,
                "rpn": 245,
                "cdve": "Q01-003",
            },
            {
                "sub": "Q01-002",
                "label": "Faux contact",
                "detail": "Non verrouillé",
                "sev": 3,
                "rpn": 120,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q03",
        "label": "Élément manquant",
        "hint": "Quelque chose n'est pas là",
        "isTest": False,
        "objects": [
            {
                "sub": "Q03-001",
                "label": "Obturateur",
                "detail": (
                    "Circulaire, rectangulaire, module VT, trou de ventilation"
                ),
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q03-002",
                "label": "Gaine thermorétractable",
                "detail": "Basse temp, haute temp",
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q03-003",
                "label": "Élément mécanique",
                "detail": "Vis, rondelle, écrou, entretoise",
                "sev": 4,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q03-004",
                "label": "Élément électrique",
                "detail": (
                    "Câble, contact, diode, résistance, connecteur, module VG,"
                    " raccordement arrière"
                ),
                "sev": 4,
                "rpn": 64,
                "cdve": None,
            },
            {
                "sub": "Q03-005",
                "label": "Freinage",
                "detail": "Fil de frein, colle, vernis frangible",
                "sev": 3,
                "rpn": 48,
                "cdve": None,
            },
            {
                "sub": "Q03-006",
                "label": "Collier",
                "detail": (
                    "Cheminement, frette plastique, frette ficelle, support en"
                    " V, plastique, métal"
                ),
                "sev": 3,
                "rpn": 108,
                "cdve": None,
            },
            {
                "sub": "Q03-007",
                "label": "Bouchons de protection",
                "detail": "Trou de ventilation, trou ouvert",
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
            {
                "sub": "Q03-008",
                "label": "Protection d'extrémité",
                "detail": "Bouchon de prise, sac plastique",
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q03-009",
                "label": "Étiquette d'inviolabilité",
                "detail": "Serrure de porte, prise coupée",
                "sev": 3,
                "rpn": 36,
                "cdve": None,
            },
            {
                "sub": "Q03-010",
                "label": "Gainage",
                "detail": "Textile, annelée, EMI, réserve",
                "sev": 4,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q03-011",
                "label": "Plaque/manchon/drapeau d'identification",
                "detail": "Bout, route, numéro de câble, collier, rampe",
                "sev": 3,
                "rpn": 48,
                "cdve": None,
            },
            {
                "sub": "Q03-012",
                "label": "Étiquette d'identification",
                "detail": "FIN, MSN",
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q04",
        "label": "Erreur de montage",
        "hint": "Mauvaise réf, mauvais sens, mauvaise taille",
        "isTest": False,
        "objects": [
            {
                "sub": "Q04-001",
                "label": "Obturateur",
                "detail": "Référence, sens de montage",
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q04-002",
                "label": "Gaine thermorétractable",
                "detail": "Référence, taille",
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q04-003",
                "label": "Mécanique",
                "detail": (
                    "Vis, rondelle, écrou, entretoise, support en V, structure,"
                    " barre VT"
                ),
                "sev": 4,
                "rpn": 128,
                "cdve": None,
            },
            {
                "sub": "Q04-004",
                "label": "Contact",
                "detail": "Référence, cuivre, aluminium",
                "sev": 9,
                "rpn": 216,
                "cdve": None,
            },
            {
                "sub": "Q04-005",
                "label": "Électrique (Résistance, connecteur, relais...)",
                "detail": "Réf, montage, orientation",
                "sev": 3,
                "rpn": 63,
                "cdve": None,
            },
            {
                "sub": "Q04-006",
                "label": "Fil de freinage",
                "detail": "Référence",
                "sev": 3,
                "rpn": 54,
                "cdve": None,
            },
            {
                "sub": "Q04-007",
                "label": "Collier de cheminement plastique",
                "detail": "Référence, taille, orientation",
                "sev": 3,
                "rpn": 75,
                "cdve": None,
            },
            {
                "sub": "Q04-008",
                "label": "Collier de cheminement métallique",
                "detail": "Référence, taille, orientation",
                "sev": 3,
                "rpn": 45,
                "cdve": None,
            },
            {
                "sub": "Q04-009",
                "label": "Détrompage",
                "detail": (
                    "Clé de codage, broche de prise ARINC, clé de polarisation"
                ),
                "sev": 4,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q04-010",
                "label": "Bouchon de protection ventilation",
                "detail": "Référence",
                "sev": 3,
                "rpn": 36,
                "cdve": None,
            },
            {
                "sub": "Q04-011",
                "label": "Élément électrique",
                "detail": "Tresse de masse, cosse, voyant lumineux",
                "sev": 4,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q04-012",
                "label": "Capuchon de protection de prise",
                "detail": "Référence, taille",
                "sev": 3,
                "rpn": 36,
                "cdve": None,
            },
            {
                "sub": "Q04-013",
                "label": "Plaque d'identification",
                "detail": (
                    "Plaque, étiquette de fonction, adhésif de bout, manchon"
                ),
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q04-014",
                "label": "Frettage",
                "detail": (
                    "Référence frette plastique, référence frette ficelle"
                ),
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q05",
        "label": "Serrage",
        "hint": "Trop serré, pas assez, desserré",
        "isTest": False,
        "objects": [
            {
                "sub": "Q05-001",
                "label": "Élément électrique",
                "detail": (
                    "Raccordement arrière, connecteur, module VG, cosse,"
                    " disjoncteur"
                ),
                "sev": 8,
                "rpn": 480,
                "cdve": None,
            },
            {
                "sub": "Q05-002",
                "label": "Mécanique",
                "detail": (
                    "Vis, fil de freinage, vernis frangible, pince, bloc diode,"
                    " BAND-IT, barre VT"
                ),
                "sev": 4,
                "rpn": 160,
                "cdve": None,
            },
            {
                "sub": "Q05-003",
                "label": "Collier corde",
                "detail": "Sur-serré / sous-serré / vis desserrée",
                "sev": 4,
                "rpn": 240,
                "cdve": None,
            },
            {
                "sub": "Q05-004",
                "label": "Frettage",
                "detail": "Collier plastique, frette ficelle",
                "sev": 4,
                "rpn": 120,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q06",
        "label": "Mise en œuvre câblage",
        "hint": "Cheminement, gainage, contact/clash",
        "isTest": False,
        "objects": [
            {
                "sub": "Q06-001",
                "label": "Harnais",
                "detail": (
                    "Cheminement, gestion de câble, sur/sous-longueur, mauvaise"
                    " destination"
                ),
                "sev": 4,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q06-002",
                "label": "Mauvaise installation de gaine",
                "detail": "Ligne visible, mauvaise torsion, branche, chaussette",
                "sev": 4,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q06-003",
                "label": "Ruban amalgamant",
                "detail": "Chevauchement, chevauchement permis",
                "sev": 3,
                "rpn": 75,
                "cdve": None,
            },
            {
                "sub": "Q06-004",
                "label": "Câble en contact avec élément structurel",
                "detail": "Clash avec plaque, rampe, tuyau, vis, bielle",
                "sev": 5,
                "rpn": 120,
                "cdve": None,
            },
            {
                "sub": "Q06-005",
                "label": "Câble en contact avec composant électrique",
                "detail": "Clash avec VG, connecteur",
                "sev": 5,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q06-006",
                "label": "Mauvais positionnement d'anneau thermo",
                "detail": "Collier plastique, ficelle",
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
            {
                "sub": "Q06-007",
                "label": "Frange sur raccordement arrière",
                "detail": "Gaine non sécurisée, gaine trop courte",
                "sev": 3,
                "rpn": 90,
                "cdve": None,
            },
            {
                "sub": "Q06-008",
                "label": "Gainage",
                "detail": (
                    "Trop court, en contact avec passe-fil, non sécurisé au"
                    " connecteur"
                ),
                "sev": 4,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q06-009",
                "label": "Route non reprise après test",
                "detail": "Câblage non terminé",
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
            {
                "sub": "Q06-010",
                "label": "Identification",
                "detail": (
                    "Positionnement flamme, plaque, manchon - décalé, non"
                    " spécifié"
                ),
                "sev": 4,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q06-011",
                "label": "Implémentation frettage",
                "detail": "Nœud cabestan double, longueur de frette coupée",
                "sev": 3,
                "rpn": 90,
                "cdve": None,
            },
            {
                "sub": "Q06-012",
                "label": "Connexions dans collier Band-it",
                "detail": "",
                "sev": 5,
                "rpn": 60,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q07",
        "label": "Sertissage standard",
        "hint": "Contacts et cosses cuivre/alu",
        "isTest": False,
        "objects": [
            {
                "sub": "Q07-001",
                "label": "Contact aluminium",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 135,
                "cdve": "Q07-006",
            },
            {
                "sub": "Q07-002",
                "label": "Contact cuivre",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 180,
                "cdve": "Q07-007",
            },
            {
                "sub": "Q07-003",
                "label": "Manchon auto-soudeur",
                "detail": "Déformation, surchauffe",
                "sev": 9,
                "rpn": 180,
                "cdve": "Q07-008",
            },
            {
                "sub": "Q07-004",
                "label": "Cosse cuivre",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 135,
                "cdve": "Q07-009",
            },
            {
                "sub": "Q07-005",
                "label": "Cosse aluminium",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 135,
                "cdve": "Q07-010",
            },
        ],
    },
    {
        "code": "Q08",
        "label": "Sertissage spécifique",
        "hint": "Quadrax, twinax, coax, fibre, brasure",
        "isTest": False,
        "objects": [
            {
                "sub": "Q08-001",
                "label": "Contact QUADRAX",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 27,
                "cdve": None,
            },
            {
                "sub": "Q08-002",
                "label": "Contact TWINAX",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 27,
                "cdve": None,
            },
            {
                "sub": "Q08-003",
                "label": "Contact TRIAXIAL",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 27,
                "cdve": None,
            },
            {
                "sub": "Q08-004",
                "label": "Contact BUSCAN",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 27,
                "cdve": None,
            },
            {
                "sub": "Q08-005",
                "label": "Contact Coax",
                "detail": "Dénudage, Sertissage",
                "sev": 9,
                "rpn": 27,
                "cdve": None,
            },
            {
                "sub": "Q08-006",
                "label": "Contact fibre optique",
                "detail": "Dénudage, Collage",
                "sev": 6,
                "rpn": 18,
                "cdve": None,
            },
            {
                "sub": "Q08-007",
                "label": "Brasure",
                "detail": "Soudure non conforme",
                "sev": 9,
                "rpn": 135,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q09",
        "label": "Métallisation / bonding",
        "hint": "Protection, point de masse",
        "isTest": False,
        "objects": [
            {
                "sub": "Q09-001",
                "label": "Protection non appliquée",
                "detail": "Vaseline, peinture de protection",
                "sev": 6,
                "rpn": 42,
                "cdve": "Q09-004",
            },
            {
                "sub": "Q09-002",
                "label": "Application de protection",
                "detail": "Partiellement appliquée, métallisation visible",
                "sev": 6,
                "rpn": 42,
                "cdve": "Q09-005",
            },
            {
                "sub": "Q09-003",
                "label": "Point de masse",
                "detail": "Oxydation, diamètre de brosse non conforme",
                "sev": 6,
                "rpn": 42,
                "cdve": "Q09-006",
            },
        ],
    },
    {
        "code": "Q10",
        "label": "Dommage structure",
        "hint": "Plaque, structure, main courante, tuyauterie",
        "isTest": False,
        "objects": [
            {
                "sub": "Q10-001",
                "label": "Plaque endommagée",
                "detail": "Impact, rayure, plié, salissure",
                "sev": 4,
                "rpn": 120,
                "cdve": None,
            },
            {
                "sub": "Q10-002",
                "label": "Structure endommagée",
                "detail": "Impact, rayure, salissure",
                "sev": 4,
                "rpn": 120,
                "cdve": None,
            },
            {
                "sub": "Q10-003",
                "label": "Main courante endommagée",
                "detail": "Impact, rayure, plié, salie",
                "sev": 4,
                "rpn": 100,
                "cdve": None,
            },
            {
                "sub": "Q10-004",
                "label": "Colonne",
                "detail": "Impact, rayure, salissure",
                "sev": 4,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q10-005",
                "label": "Tuyauterie endommagée",
                "detail": "Impact, rayure, salissure",
                "sev": 4,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q10-006",
                "label": "Mécanisme",
                "detail": (
                    "Insert, vis - filetages endommagés, vis cassées à"
                    " l'intérieur"
                ),
                "sev": 4,
                "rpn": 160,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q11",
        "label": "Dommage élément élec.",
        "hint": "Câble, composant, cosse, contact abîmés",
        "isTest": False,
        "objects": [
            {
                "sub": "Q11-001",
                "label": "Câble coupé",
                "detail": "",
                "sev": 8,
                "rpn": 48,
                "cdve": None,
            },
            {
                "sub": "Q11-014",
                "label": "Câble rayé, endommagé",
                "detail": "",
                "sev": 8,
                "rpn": 480,
                "cdve": None,
            },
            {
                "sub": "Q11-002",
                "label": "Identification",
                "detail": "Onde, étiquette, manchon - déchiré, sali",
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q11-003",
                "label": "Composant",
                "detail": (
                    "Module VG, disjoncteur, module barre VT, connecteur"
                ),
                "sev": 4,
                "rpn": 168,
                "cdve": "Q11-016",
            },
            {
                "sub": "Q11-004",
                "label": "Gaine de protection",
                "detail": "Textile, annelée, EMI",
                "sev": 4,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q11-005",
                "label": "Cosse",
                "detail": "Cuivre, aluminium",
                "sev": 4,
                "rpn": 140,
                "cdve": "Q11-018",
            },
            {
                "sub": "Q11-006",
                "label": "Contact",
                "detail": "Cuivre, aluminium",
                "sev": 9,
                "rpn": 189,
                "cdve": "Q11-019",
            },
            {
                "sub": "Q11-007",
                "label": "Ruban amalgamant",
                "detail": "Déchiré, sali",
                "sev": 3,
                "rpn": 45,
                "cdve": None,
            },
            {
                "sub": "Q11-008",
                "label": "Gaine thermorétractable",
                "detail": "Déchirée, salie",
                "sev": 3,
                "rpn": 45,
                "cdve": None,
            },
            {
                "sub": "Q11-009",
                "label": "Métallisation tresse de masse",
                "detail": "Brins cassés",
                "sev": 4,
                "rpn": 60,
                "cdve": "Q11-022",
            },
            {
                "sub": "Q11-010",
                "label": "Collier de câble",
                "detail": "Plastique, métal, support en V",
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
            {
                "sub": "Q11-011",
                "label": "Collier BAND-IT",
                "detail": "Collier métal, bande PTFE",
                "sev": 5,
                "rpn": 40,
                "cdve": None,
            },
            {
                "sub": "Q11-012",
                "label": "Barre VT",
                "detail": "Module endommagé, rail déformé",
                "sev": 3,
                "rpn": 60,
                "cdve": None,
            },
            {
                "sub": "Q11-013",
                "label": "Manchons d'étanchéité endommagés",
                "detail": "",
                "sev": 4,
                "rpn": 112,
                "cdve": "Q11-026",
            },
        ],
    },
    {
        "code": "Q12",
        "label": "Impression / marquage",
        "hint": "Jauge, type, longueur, identification câble",
        "isTest": False,
        "objects": [
            {
                "sub": "Q12-001",
                "label": "Erreur de jauge câble",
                "detail": "G20, G18",
                "sev": 4,
                "rpn": 80,
                "cdve": "Q12-007",
            },
            {
                "sub": "Q12-002",
                "label": "Erreur type de câble",
                "detail": "DR, AD",
                "sev": 4,
                "rpn": 120,
                "cdve": "Q12-008",
            },
            {
                "sub": "Q12-003",
                "label": "Erreur longueur de câble",
                "detail": "Trop court, trop long",
                "sev": 4,
                "rpn": 60,
                "cdve": None,
            },
            {
                "sub": "Q12-004",
                "label": "Identification de câble",
                "detail": "Lisibilité, erreur numéro d'ID",
                "sev": 4,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q12-005",
                "label": "Identification",
                "detail": "Manchon, plaque, étiquette - lisibilité",
                "sev": 3,
                "rpn": 45,
                "cdve": None,
            },
            {
                "sub": "Q12-006",
                "label": "Barre VT",
                "detail": (
                    "Erreur d'identification de module, référence de module"
                ),
                "sev": 3,
                "rpn": 63,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q13",
        "label": "Dossier de fabrication",
        "hint": "Opération, tampon, traçabilité, doc",
        "isTest": False,
        "objects": [
            {
                "sub": "Q13-001",
                "label": "Opération",
                "detail": "Non badgé, ordre des opérations non respecté",
                "sev": 3,
                "rpn": 72,
                "cdve": None,
            },
            {
                "sub": "Q13-002",
                "label": "Tampon",
                "detail": "Non apposé sur fiche suiveuse, partiellement visible",
                "sev": 3,
                "rpn": 36,
                "cdve": None,
            },
            {
                "sub": "Q13-003",
                "label": "Étiquette de traçabilité",
                "detail": "CT176 non complété, CT129D non complété",
                "sev": 4,
                "rpn": 64,
                "cdve": None,
            },
            {
                "sub": "Q13-004",
                "label": "Documentation",
                "detail": "Manquante, non conforme",
                "sev": 4,
                "rpn": 80,
                "cdve": None,
            },
            {
                "sub": "Q13-005",
                "label": "Entrée outillage",
                "detail": "Non effectuée, erreur trousse à outils",
                "sev": 4,
                "rpn": 48,
                "cdve": None,
            },
        ],
    },
    {
        "code": "Q16",
        "label": "FOD",
        "hint": "Corps étranger",
        "isTest": False,
        "objects": [
            {
                "sub": "Q16-001",
                "label": "Outils",
                "detail": "Lampe torche, miroir, clé, tournevis",
                "sev": 8,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q16-002",
                "label": "Attaches et pièces avion",
                "detail": "Boulons, rondelles, écrous",
                "sev": 8,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q16-003",
                "label": "Effets personnels",
                "detail": "Badge, lunettes, téléphone, ordinateur",
                "sev": 8,
                "rpn": 96,
                "cdve": None,
            },
            {
                "sub": "Q16-004",
                "label": "Débris industriels",
                "detail": "Copeaux, poussière, isolation",
                "sev": 8,
                "rpn": 128,
                "cdve": None,
            },
            {
                "sub": "Q16-005",
                "label": "Éléments supplémentaires",
                "detail": "Consommables, bouchons, fiche d'instruction",
                "sev": 8,
                "rpn": 128,
                "cdve": None,
            },
            {
                "sub": "Q16-006",
                "label": "Maintenance",
                "detail": "Objet laissé dans la zone, atelier, couloir",
                "sev": 4,
                "rpn": 48,
                "cdve": None,
            },
        ],
    },
    {
        "code": "T01",
        "label": "Câble manquant (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T01",
                "label": "Câble manquant",
                "detail": "Cuivre, aluminium, fibre optique",
                "sev": 8,
                "rpn": 80,
                "cdve": None,
            }
        ],
    },
    {
        "code": "T02",
        "label": "Erreur de branchement (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T02",
                "label": "Erreur de connexion",
                "detail": "Cuivre, aluminium, fibre optique",
                "sev": 8,
                "rpn": 96,
                "cdve": None,
            }
        ],
    },
    {
        "code": "T03",
        "label": "Shunt manquant (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T03",
                "label": "Shunt manquant",
                "detail": "Électrique, Mécanique",
                "sev": 8,
                "rpn": 96,
                "cdve": None,
            }
        ],
    },
    {
        "code": "T04",
        "label": "Inversion de branchement (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T04",
                "label": "Inversion de connexion",
                "detail": "Cuivre, Aluminium, Fibre optique",
                "sev": 8,
                "rpn": 96,
                "cdve": None,
            }
        ],
    },
    {
        "code": "T05",
        "label": "Câble non connecté (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T05",
                "label": "Câble non connecté",
                "detail": "Cuivre, aluminium, fibre optique",
                "sev": 8,
                "rpn": 200,
                "cdve": None,
            }
        ],
    },
    {
        "code": "T06",
        "label": "Perte optique NC (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T06",
                "label": (
                    "Mesure de perte d'insertion sur liaisons optiques non"
                    " conformes"
                ),
                "detail": "",
                "sev": 6,
                "rpn": 72,
                "cdve": None,
            }
        ],
    },
    {
        "code": "T07",
        "label": "Résistance métallisation NC (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T07",
                "label": (
                    "Mesure de résistance sur métallisation non conforme"
                ),
                "detail": "VN, VG, VH",
                "sev": 6,
                "rpn": 36,
                "cdve": "T07-CDVE",
            }
        ],
    },
    {
        "code": "T08",
        "label": "Résistance linéique NC (test)",
        "hint": "",
        "isTest": True,
        "objects": [
            {
                "sub": "T08",
                "label": "Mesure de résistance linéique non conforme",
                "detail": "Gaine EMI, surtressage",
                "sev": 6,
                "rpn": 36,
                "cdve": "T08-CDVE",
            }
        ],
    },
]


PRODUITS = [
    "MIP A350",
    "MIP 400M",
    "740VU",
    "PTVU",
    "300VU",
    "OHP",
    "E Rudder",
    "MFRL",
    "MDCD",
    "Autre",
]

DETECTIONS = ["Poste", "Test", "Contrôle Final", "Réception", "Client", "Autre"]


# --- VERIFIED FIN MAPPING (MIN 6 PER CODE) ---
FIN_MAPPING = {
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
}

# --- GLOBAL FALLBACK (TOP 10 VERIFIED FINS OVERALL) ---
FIN_GLOBAL_SUGGEST = [
    "740VU", "300VT101", "300VT400", "9KS", "115VM", 
    "3RN1A", "3RN3B", "51CV", "300VT301", "3CB"
]

# --- HELPERS ---

def gen_line(seq, sub, qty, loc, obj_label, detail, comment):
    bits = [loc if loc else "-", obj_label]

    if detail:
        bits.append(detail)

    if comment:
        bits.append(comment)

    qty_str = f" - QTE {qty}" if qty > 1 else ""

    return f"DEF {seq} - {sub}{qty_str} : {' — '.join(bits)}"


# --- STATE MANAGEMENT ---

if "screen" not in st.session_state:
    st.session_state.screen = "header"

if "header" not in st.session_state:
    st.session_state.header = {"msn": "", "produit": "MIP A350", "detection": "Poste"}

if "defects" not in st.session_state:
    st.session_state.defects = []

if "sel_nature" not in st.session_state:
    st.session_state.sel_nature = None

if "sel_obj" not in st.session_state:
    st.session_state.sel_obj = None

if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

if "duplicate_from" not in st.session_state:
    st.session_state.duplicate_from = None


# Variables persistantes pour ne pas perdre les textes entre les écrans
if "ctx_combo_val" not in st.session_state:
    st.session_state.ctx_combo_val = ""

if "ctx_text_val" not in st.session_state:
    st.session_state.ctx_text_val = ""

if "act_combo_val" not in st.session_state:
    st.session_state.act_combo_val = ""

if "act_text_val" not in st.session_state:
    st.session_state.act_text_val = ""


def change_screen(name):
    st.session_state.screen = name
    st.rerun()


# Fonction pour sauvegarder l'état des textes avant de changer d'écran ou recharger la page
def save_list_state():
    if "ctx_combo_widget" in st.session_state:
        st.session_state.ctx_combo_val = st.session_state.ctx_combo_widget

    if "ctx_text_widget" in st.session_state:
        st.session_state.ctx_text_val = st.session_state.ctx_text_widget

    if "act_combo_widget" in st.session_state:
        st.session_state.act_combo_val = st.session_state.act_combo_widget

    if "act_text_widget" in st.session_state:
        st.session_state.act_text_val = st.session_state.act_text_widget


is_test = st.session_state.header["detection"] == "Test"


# --- TOP APP BAR ---

st.title("NC · Saisie Structurée")

if st.session_state.screen != "header":
    h = st.session_state.header
    st.info(f"**MSN {h['msn']}** | {h['produit']} | {h['detection']}")


# --- SCREEN 1: HEADER ---

if st.session_state.screen == "header":
    st.subheader("Nouvelle NC")

    msn = st.text_input(
        "MSN", value=st.session_state.header["msn"], placeholder="ex. 2160"
    )

    default_prod_idx = (
        PRODUITS.index(st.session_state.header["produit"])
        if st.session_state.header["produit"] in PRODUITS
        else len(PRODUITS) - 1
    )

    produit_sel = st.selectbox("Produit", PRODUITS, index=default_prod_idx)

    if produit_sel == "Autre":
        produit_val = st.text_input(
            "Préciser le produit :",
            value=(
                st.session_state.header["produit"]
                if st.session_state.header["produit"] not in PRODUITS
                else ""
            ),
        )
    else:
        produit_val = produit_sel

    default_det_idx = (
        DETECTIONS.index(st.session_state.header["detection"])
        if st.session_state.header["detection"] in DETECTIONS
        else len(DETECTIONS) - 1
    )

    detection_sel = st.selectbox("Détection", DETECTIONS, index=default_det_idx)

    if detection_sel == "Autre":
        detection_val = st.text_input(
            "Préciser la détection :",
            value=(
                st.session_state.header["detection"]
                if st.session_state.header["detection"] not in DETECTIONS
                else ""
            ),
        )
    else:
        detection_val = detection_sel

    btn_disabled = not (msn.strip() and produit_val.strip() and detection_val.strip())

    if st.button("Continuer", type="primary", disabled=btn_disabled):
        st.session_state.header = {
            "msn": msn,
            "produit": produit_val,
            "detection": detection_val,
        }

        change_screen("list")


# --- SCREEN 2: LIST ---

elif st.session_state.screen == "list":
    # 1. CONTEXTE DE DÉCOUVERTE (Wrapped in a container)

    with st.container(border=True):
        st.subheader("Contexte de découverte")

        ctx_opts = [
            "",
            "Lors de l'inspection du montage",
            "Lors du contrôle final",
            "Lors du contrôle après test",
            "Sur la ligne de production, nous constatons",
        ]

        default_ctx_idx = (
            ctx_opts.index(st.session_state.ctx_combo_val)
            if st.session_state.ctx_combo_val in ctx_opts
            else 0
        )

        c_col1, c_col2 = st.columns([1, 2])

        with c_col1:
            st.selectbox(
                "Modèles",
                ctx_opts,
                index=default_ctx_idx,
                key="ctx_combo_widget",
                on_change=save_list_state,
            )

        with c_col2:
            st.text_area(
                "Texte du contexte",
                value=st.session_state.ctx_text_val,
                key="ctx_text_widget",
                label_visibility="hidden",
                placeholder="Saisir la suite du contexte ici...",
                height=90,
                on_change=save_list_state,
            )

    # 2. LISTE DES DÉFAUTS (Wrapped in a container)

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])

        c1.subheader("Défauts de la NC")

        if c2.button("Modifier les infos de la NC"):
            change_screen("header")

        if not st.session_state.defects:
            st.warning("Aucun défaut enregistré pour l'instant.")

        else:
            for i, d in enumerate(st.session_state.defects):
                with st.container(border=True):
                    col_a, col_b = st.columns([4, 1])

                    with col_a:
                        st.markdown(
                            f"**Défaut {i+1}** · {d['natureLabel']}"
                            f" `{d['sub']}`"
                        )

                        badges = (
                            f":{'red' if d['sev'] == 'MAJEURE' else 'orange'}[**{d['sev']}**]"
                        )

                        if d["cdve"]:
                            badges += " | :violet[**CDVE**]"

                        if d["qty"] > 1:
                            badges += f" | :gray[**×{d['qty']}**]"

                        st.markdown(badges)

                        st.code(d["line"], language="markdown")

                    with col_b:
                        if st.button("Modifier", key=f"edit_{i}"):
                            save_list_state()

                            st.session_state.edit_idx = i
                            st.session_state.duplicate_from = None
                            st.session_state.sel_nature = next(
                                n
                                for n in NATURES
                                if n["code"] == d["code"]
                            )

                            st.session_state.sel_obj = next(
                                o
                                for o in st.session_state.sel_nature["objects"]
                                if o["sub"] == d["sub"] or o["cdve"] == d["sub"]
                            )

                            change_screen("detail")

                        if st.button("Supprimer", key=f"del_{i}"):
                            save_list_state()

                            st.session_state.defects.pop(i)

                            st.rerun()

        b1, b2, b3 = st.columns(3)

        if b1.button("+ Ajouter", type="primary"):
            save_list_state()

            st.session_state.edit_idx = None
            st.session_state.duplicate_from = None

            change_screen("nature")

        if b2.button(
            "Dupliquer le dernier", disabled=not st.session_state.defects
        ):
            save_list_state()

            last = st.session_state.defects[-1]

            st.session_state.edit_idx = None
            st.session_state.duplicate_from = len(st.session_state.defects) - 1

            st.session_state.sel_nature = next(
                n for n in NATURES if n["code"] == last["code"]
            )

            st.session_state.sel_obj = next(
                o
                for o in st.session_state.sel_nature["objects"]
                if o["sub"] == last["sub"] or o["cdve"] == last["sub"]
            )

            change_screen("detail")

    # 3. ACTION DEMANDÉE (Wrapped in a container)

    with st.container(border=True):
        st.subheader("Action demandée")

        act_opts = [
            "",
            "Nous demandons la re-fabrication",
            "Merci de remettre en conformité",
            "Nous demandons le remplacement de l'équipement",
            "Veuillez s'il vous plait procéder à son remplacement",
        ]

        default_act_idx = (
            act_opts.index(st.session_state.act_combo_val)
            if st.session_state.act_combo_val in act_opts
            else 0
        )

        a_col1, a_col2 = st.columns([1, 2])

        with a_col1:
            st.selectbox(
                "Modèles",
                act_opts,
                index=default_act_idx,
                key="act_combo_widget",
                on_change=save_list_state,
            )

        with a_col2:
            st.text_area(
                "Texte de l'action",
                value=st.session_state.act_text_val,
                key="act_text_widget",
                label_visibility="hidden",
                placeholder="Saisir la suite de l'action ici...",
                height=90,
                on_change=save_list_state,
            )

    if st.button(
        "Terminer",
        type="primary",
        disabled=not st.session_state.defects,
        use_container_width=True,
    ):
        save_list_state()
        change_screen("review")


# --- SCREEN 3: NATURE (STEP 1) ---

elif st.session_state.screen == "nature":
    if st.button("← Retour"):
        change_screen("list")

    st.subheader("Étape 1 — Nature du défaut")

    query = st.text_input(
        "Recherche rapide (ex. 'contact', 'T04')", ""
    ).strip().lower()

    if query and len(query) >= 2:
        for n in NATURES:
            for o in n["objects"]:
                haystack = (
                    f"{n['code']} {n['label']} {o['label']} {o['detail']}"
                    f" {o['sub']}".lower()
                )

                if query in haystack:
                    if st.button(
                        f"{o['label']} ({o['sub']}) — {n['label']}",
                        key=f"srch_{o['sub']}",
                    ):
                        st.session_state.sel_nature = n
                        st.session_state.sel_obj = o
                        change_screen("detail")

    else:
        sorted_natures = sorted(
            NATURES, key=lambda x: 0 if x["isTest"] == is_test else 1
        )

        cols = st.columns(2)

        for idx, n in enumerate(sorted_natures):
            with cols[idx % 2]:
                if st.button(
                    f"{n['label']} ({n['code']})\n\n{n['hint']}",
                    key=f"nat_{n['code']}",
                ):
                    st.session_state.sel_nature = n
                    change_screen("object")


# --- SCREEN 4: OBJECT (STEP 2) ---

elif st.session_state.screen == "object":
    if st.button("← Retour Natures"):
        change_screen("nature")

    nat = st.session_state.sel_nature

    st.subheader(f"Étape 2 — {nat['label']} ({nat['code']})")

    for o in nat["objects"]:
        with st.container(border=True):
            st.markdown(f"**{o['label']}** (`{o['sub']}`)\n\n*{o['detail']}*")

            if st.button(
                "Sélectionner", key=f"obj_{o['sub']}", type="primary"
            ):
                st.session_state.sel_obj = o
                change_screen("detail")


# --- SCREEN 5: DETAIL (STEP 3 & FORM) ---

elif st.session_state.screen == "detail":
    back_to = (
        "list"
        if (
            st.session_state.edit_idx is not None
            or st.session_state.duplicate_from is not None
        )
        else "object"
    )

    if st.button("← Annuler"):
        st.session_state.duplicate_from = None
        change_screen(back_to)

    nat = st.session_state.sel_nature
    obj = st.session_state.sel_obj

    st.subheader(f"Détails : {obj['label']}")

    if st.session_state.edit_idx is not None:
        existing = st.session_state.defects[st.session_state.edit_idx]
    elif st.session_state.duplicate_from is not None:
        existing = st.session_state.defects[
            st.session_state.duplicate_from
        ].copy()
    else:
        existing = {}

    cdve_active = False
    if obj.get("cdve"):
        st.info("**Option CDVE disponible**")
        cdve_active = st.checkbox(
            f"Circuit Commandes de Vol (bascule vers code {obj['cdve']})",
            value=existing.get("cdve", False),
        )

    eff_sub = obj["cdve"] if cdve_active else obj["sub"]
    eff_sev = 10 if cdve_active else obj["sev"]

    # --- DYNAMIC FIN SUGGESTIONS LOGIC ---
    current_code = nat["code"]
    suggested_fins = FIN_MAPPING.get(current_code, FIN_GLOBAL_SUGGEST).copy()
    
    if "Autre" not in suggested_fins:
        suggested_fins.append("Autre")

    existing_loc = existing.get("loc", "")
    
    # Check if the existing location is within our suggested dropdown options
    if existing_loc in suggested_fins:
        default_fin_idx = suggested_fins.index(existing_loc)
    else:
        default_fin_idx = 0

    loc_sel = st.selectbox(
        "Localisation (FIN / Zone)", suggested_fins, index=default_fin_idx
    )

    default_custom_loc = (
        existing_loc if existing_loc and existing_loc not in suggested_fins else ""
    )
    loc_custom = st.text_input(
        "Ou saisir manuellement :", value=default_custom_loc
    )
    
    final_loc = loc_custom.strip() if loc_custom.strip() else loc_sel

    detail = st.text_input(
        "Précision (optionnel)",
        value=existing.get("detail", ""),
        placeholder=obj["detail"],
    )

    qty = st.number_input("Quantité", min_value=1, value=existing.get("qty", 1))

    auto_sev = "MAJEURE" if eff_sev >= 8 else "MINEURE"
    default_sev_idx = 0 if existing.get("sev", auto_sev) == "MINEURE" else 1

    sev = st.selectbox("Sévérité", ["MINEURE", "MAJEURE"], index=default_sev_idx)

    comment = st.text_area(
        "Complément libre (optionnel)",
        value=existing.get("comment", ""),
        max_chars=200,
    )

    seq = (
        st.session_state.edit_idx + 1
        if st.session_state.edit_idx is not None
        else len(st.session_state.defects) + 1
    )

    line_preview = gen_line(
        seq, eff_sub, qty, final_loc, obj["label"], detail, comment
    )

    st.markdown("**Aperçu texte généré :**")
    st.code(line_preview, language="markdown")

    if st.button("Enregistrer le défaut", type="primary"):
        entry = {
            "code": nat["code"],
            "natureLabel": nat["label"],
            "sub": eff_sub,
            "objLabel": obj["label"],
            "detail": detail,
            "loc": final_loc,
            "qty": qty,
            "sev": sev,
            "comment": comment,
            "sevNum": eff_sev,
            "cdve": cdve_active,
            "line": line_preview,
        }

        if st.session_state.edit_idx is not None:
            st.session_state.defects[st.session_state.edit_idx] = entry
        else:
            st.session_state.defects.append(entry)

        st.session_state.duplicate_from = None
        change_screen("list")


# --- SCREEN 6: REVIEW ---

elif st.session_state.screen == "review":
    if st.button("← Retour à la liste"):
        change_screen("list")

    st.subheader("Bilan & Soumission")

    h = st.session_state.header

    total_qty = sum(d["qty"] for d in st.session_state.defects)

    # 1. HEADER
    sap_text = (
        f"### DEFAUTS v1 | PRODUIT: {h['produit']} | DETECTION:"
        f" {h['detection'].upper()}\n\n"
    )

    # 2. CONTEXTE
    full_context = (
        f"{st.session_state.ctx_combo_val} {st.session_state.ctx_text_val}".strip()
    )

    if full_context:
        sap_text += f"{full_context}\n\n"

    # 3. LISTE DES DÉFAUTS
    for d in st.session_state.defects:
        sap_text += f"{d['line']}\n"

    # 4. ACTION DEMANDÉE
    full_action = (
        f"{st.session_state.act_combo_val} {st.session_state.act_text_val}".strip()
    )

    if full_action:
        sap_text += f"\n{full_action}\n"

    # 5. FOOTER
    sap_text += f"\n### TOTAL: {total_qty}"

    st.markdown("**Texte SAP final :**")
    st.code(sap_text, language="markdown")

    if st.button("Soumettre la NC", type="primary"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = {
            "timestamp": timestamp,
            "msn": h["msn"],
            "produit": h["produit"],
            "detection": h["detection"],
            "total_defauts": total_qty,
            "texte_sap": sap_text,
        }

        new_df = pd.DataFrame([row])

        nc_writer_dataset = Dataset.get("nc_writer_dataset")

        try:
            existing_df = nc_writer_dataset.read_table(format="pandas")
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        except Exception:
            combined_df = new_df

        nc_writer_dataset.write_table(combined_df)

        st.success("NC soumise avec succès.")

        st.session_state.defects = []
        st.session_state.header = {
            "msn": "",
            "produit": "MIP A350",
            "detection": "Poste",
        }
        st.session_state.ctx_combo_val = ""
        st.session_state.ctx_text_val = ""
        st.session_state.act_combo_val = ""
        st.session_state.act_text_val = ""
        change_screen("header")