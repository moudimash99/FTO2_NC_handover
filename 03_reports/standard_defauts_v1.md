# Standard de rédaction des défauts — « DEFAUTS v1 »
*Objectif : que chaque défaut écrit une seule fois, par n'importe quelle équipe, soit lisible par un humain ET par la machine — comptage, classification, localisation et alertes deviennent automatiques et fiables à ~100%.*

## Principe de conception

Aucune liste fermée ne couvrira jamais tous les défauts possibles. Le standard couvre donc tous les cas par construction, avec trois mécanismes : des **champs à position fixe** pour les quatre informations critiques machine (n°, type, localisation, quantité) ; une **queue en texte libre** pour toute la nuance humaine ; et des **soupapes explicites** (code `AUT`, localisation `ZONE …` ou `-`) pour que personne ne soit jamais bloqué. Si un défaut ne rentre pas dans une case, il rentre dans la soupape — et la soupape est surveillée (détecteur de symptômes nouveaux).

## Le gabarit

```
### DEFAUTS v1 | MSN: 2160 | PRODUIT: 740VU | DETECTION: TEST
DEF 1 - T04 - 3RN3B : inversion bornes J <-> H
DEF 2 - Q01 - 115VMB : contact broche 12 non verrouillé
DEF 3 - M01 - 411VC007A - QTE 4 : obturateurs manquants
DEF 4 - C02 - 1608VC070A - CABLE 2424-0135 : câble coupé côté connecteur
DEF 5 - AUT - ZONE PLANCHE SUP : trace de colle non identifiée
DEF 6 - L01 - - : câble 3161-0582 reçu trop court de 40 mm
### TOTAL: 9
```

## Grammaire d'une ligne

`DEF <n> - <CODE> - <LOC> [- CABLE <réf>] [- QTE <k>] : <texte libre>`

| Champ | Obligatoire | Contenu |
|---|---|---|
| `<n>` | oui | Numéro séquentiel dans la NC, jamais réutilisé |
| `<CODE>` | oui | Code type défaut (table ci-dessous) ; `AUT` si aucun ne convient |
| `<LOC>` | oui | FIN (ex. 3RN3B) ; sinon `ZONE <nom>` ; sinon `-` |
| `CABLE <réf>` | si pertinent | Référence du câble concerné |
| `QTE <k>` | si k>1 | Nombre de défauts identiques sur cette ligne |
| `<texte libre>` | oui | Description courte ; pour une inversion, toujours `bornes X <-> Y` |

En-tête : `### DEFAUTS v1 | MSN: … | PRODUIT: … | DETECTION: …` avec DETECTION ∈ {POSTE, TEST, CONTROLE FINAL, RECEPTION, CLIENT}. Pied : `### TOTAL: <somme des défauts, QTE comprises>` — c'est une somme de contrôle : la machine la vérifie et toute incohérence part en file d'exceptions.

## Règles (les cas limites, tous couverts)

1. **Une ligne = un défaut ; un défaut = une ligne.** Pas de sous-listes dans le texte libre.
2. **Défauts identiques multiples** (même code, même endroit) → une ligne avec `QTE k`.
3. **Références individuelles** (câbles manquants avec réfs différentes) → une ligne par câble, car chaque réf doit être traçable.
4. **Pas de FIN applicable** (défaut cosmétique, zone, généralité) → `ZONE <nom>` ou `-`. Jamais laisser vide.
5. **Type inconnu ou nouveau** → `AUT` + texte libre. Ne jamais forcer un mauvais code : les `AUT` sont analysés chaque semaine et deviennent des codes si récurrents.
6. **Défauts découverts après création** (en retouche) → lignes ajoutées à la suite avec les numéros suivants, `### TOTAL` mis à jour. Numérotation append-only : on ne renumérote jamais.
7. **Une NC = un MSN + un produit.** Deux produits → deux NC.
8. **Inversion** → toujours nommer les deux bornes (`J <-> H`) : c'est ce qui permet de détecter les paires récurrentes.
9. **Défaut fournisseur / reçu non conforme** → code `R01` ou `L01` + DETECTION: RECEPTION ; l'imputation formelle reste dans les champs SAP (Y4).
10. **Programme classifié** → le gabarit ne change rien aux règles de classification existantes ; n'écrire que ce qui est déjà autorisé en texte long.

## Table des codes

**Codes existants (usage observé — significations à confirmer sur la fiche officielle) :**
T01/T03 câble manquant · T02 câble en mauvaise borne · T04 inversion de branchement · T05 (à confirmer) · Q01 borne/contact déverrouillé · Q03, Q06, Q10, Q12 (à confirmer) · Q04 erreur plaquette/référence · Q05 sertissage · Q07 sertissage/blindage · Q08 blindage/tresse · Q11 prise cassée

**Extensions proposées (placeholders — à réconcilier avec la fiche officielle en atelier) :**
M01 pièce manquante · L01 longueur non conforme · R01 défaut à réception · C01 composant cassé · C02 câble endommagé/coupé · H01 composant HS/continuité · F01 fixation/visserie · F02 cheminement/contrainte · F03 métallisation/bonding · FOD corps étranger · E01 étiquette/marquage · N01 non connecté · FRE freinage/frètes · TOR serrage/couple · AUT autre

Règle d'or : **ne jamais renuméroter les codes existants** — le terrain les connaît. On étend, on ne remplace pas. Option pour l'atelier : associer à chaque code une sévérité par défaut (majeure/mineure), ce qui automatise aussi ce comptage-là.

## Contrat machine

Toute NC portant l'en-tête `### DEFAUTS v1` est parsée en mode strict par `nc_defect_parser.py` (format `template_v1`) : comptage exact QTE comprises, classification par code (prioritaire sur les mots-clés), FIN extrait du champ LOC, vérification de la somme de contrôle. Une ligne malformée ou un TOTAL incohérent → drapeau en file d'exceptions, jamais de comptage silencieusement faux. Les anciens formats (DEF n-CODE, Def1:, listes numérotées, listes N°, narratif) restent parsés à l'identique — la migration peut être progressive, équipe par équipe.

## Déploiement suggéré

Pilote avec une seule équipe d'abord — celle au plus gros gain : contrôle final (gros bundles, zéro code aujourd'hui). Insérer le gabarit comme texte standard SAP (module de texte / raccourci) pour que le coût d'écriture soit quasi nul. Mesurer l'adoption sur la tuile santé-données : % de NC au format v1 par équipe, par semaine. Atelier de 30 minutes avec les trois équipes pour réconcilier la table des codes et fixer le critère majeure/mineure — ce sont les deux seules décisions humaines restantes.
