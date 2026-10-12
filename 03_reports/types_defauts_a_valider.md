# Types de défauts — proposition à valider

Document de travail. N'hésite pas à écrire directement dedans, barrer, renommer.
Version du 4 septembre 2026.

---

## L'idée en trois phrases

On garde les codes officiels de retouche (Q01, Q03… T04…) pour **écrire** les NC. Rien ne change de ce côté.

Ce qu'on ajoute, c'est un niveau au-dessus, pour **lire** les chiffres : 26 types de défauts, regroupés en 6 familles. Personne ne le saisit à la main, c'est calculé à partir du code officiel.

Pourquoi : aujourd'hui on ne peut pas répondre à « c'est quoi notre principal problème ? ». Le code SAP met 43 % des NC dans une seule case (« Electrical Assembly Installation »), et la cause est « People » une fois sur deux. Ça ne permet de décider de rien.

---

## Les 6 familles

Le regroupement s'est fait sur une question simple : **qu'est-ce qui empêcherait ce défaut ?** Deux défauts qui se corrigent de la même manière vont ensemble.

| Famille | Ce que ça veut dire | Ce qui le corrige | Volume |
|---|---|---|---|
| **Sélection** | La bonne pièce, mais au mauvais endroit. On s'est trompé entre deux choses qui se ressemblent. | Détrompage, marquage, revoir l'instruction. Pas la formation. | 891 (38 %) |
| **Exécution** | Le geste est fait, mais pas au standard. | Outillage, calibration, gamme, formation au geste. | 560 (24 %) |
| **Omission** | Une étape ou une pièce a été sautée. | Un signal qui force le contrôle au poste. | 417 (18 %) |
| **Manipulation** | Abîmé en le manipulant. | Protection, conditionnement, environnement. | 273 (12 %) |
| **Amont** | C'est arrivé faux. | Atelier câbles, fournisseur, appro. | 77 (3 %) |
| **Process** | Papier, traçabilité. | Discipline documentaire. | 4 (0 %) |

Le chiffre à retenir : **38 % de nos défauts sont des erreurs de sélection**. Et quand on regarde les inversions en détail, 99 % se font entre deux bornes voisines ou jumelles — jamais entre deux bornes éloignées. Ça veut dire que le problème est dans la tâche (deux choses qui se ressemblent trop), pas dans l'attention des gens. C'est pour ça que ça ne bouge pas malgré les rappels.

---

## Les 26 types

Le préfixe du nom donne la famille, donc il n'y a rien à apprendre par cœur.

**Sélection**
- INVERSION_BRANCHEMENT — 372
- ERREUR_BRANCHEMENT — 299
- ERREUR_REF_HABILLAGE — 153
- ERREUR_REF_ELECTRIQUE — 67

**Exécution** (MEO = mise en œuvre)
- MEO_FRETTAGE_COLLIER — 144
- MEO_SERRAGE — 97
- MEO_GAINAGE — 90
- MEO_CHEMINEMENT — 86
- MEO_SERTISSAGE_STANDARD — 56
- MEO_METALLISATION — 42
- MEO_SERTISSAGE_SPECIFIQUE — 32
- MEO_FINITION — 8
- MESURE_NON_CONFORME — 5

**Omission**
- MANQUANT_HABILLAGE — 140
- OUBLI_VERROUILLAGE — 110
- MANQUANT_CABLE_ELEMENT — 89
- MANQUANT_OBTURATION — 32
- FOD — 20
- MANQUANT_IDENTIFICATION — 15
- NON_CONNECTE — 11

**Manipulation**
- DOMMAGE_COMPOSANT — 144
- DOMMAGE_STRUCTURE — 61
- DOMMAGE_CABLE — 53
- DOMMAGE_HABILLAGE — 15

**Amont**
- AMONT_IMPRESSION — 77

**Process**
- PROCESS_DOSSIER — 4

Plus une case « Autre » pour ce qui ne rentre nulle part : 124 défauts, soit 5 %.

---

## Les choix qu'on a faits, et pourquoi

**Un type appartient toujours à une seule famille.**
C'est ce qui oblige à séparer des choses qui se ressemblent. Un frettage qui manque et un frettage mal serré, ce sont deux types différents : le premier c'est un oubli, le second c'est un geste. On ne les corrige pas pareil, donc on ne les compte pas ensemble. La grille officielle fait déjà cette distinction (Q03-005 contre Q05-004), on ne fait que la suivre.

**On est parti des codes officiels, pas d'une liste inventée.**
Les 123 sous-codes de la grille tombent tous dans un des 26 types. Aucun trou. C'était la condition pour que ce soit utilisable : si un code officiel n'a pas de place, le système est faux.

**On n'a rien demandé de plus à celui qui saisit.**
Le type se calcule à partir du code. Si demain quelqu'un écrit Q03-006, on sait que c'est un collier manquant, donc une omission. Zéro clic en plus.

**On a évité les catégories fourre-tout.**
Le plus gros type fait 16 % du volume. À comparer aux 43 % du code SAP actuel. Un Pareto où une barre écrase tout ne sert à rien.

**Une case « Autre » existe, volontairement.**
La grille officielle n'en a pas, et c'est probablement une des raisons pour lesquelles beaucoup de monde ne code pas : quand on ne trouve pas son cas, on abandonne et on écrit du texte. On propose de regarder les « Autre » une fois par semaine ; si un même cas revient dix fois, il devient un vrai type.

---

## Ce dont on n'est pas sûr

À discuter, justement.

- **DOMMAGE_STRUCTURE et PROCESS_DOSSIER sont presque vides** (61 et 4). Est-ce que ces défauts n'arrivent pas chez nous, ou est-ce qu'ils sont déclarés ailleurs ?
- **Sertissage standard / spécifique** : on les a séparés parce que l'outillage et la qualification ne sont pas les mêmes (Q07 contre Q08). À confirmer que ça a du sens côté atelier.
- **La distinction habillage / électrique** sur les erreurs de référence : est-ce qu'elle parle aux gens du terrain, ou est-ce qu'on ferait mieux d'avoir un seul type ?
- **Les noms.** Ils sont provisoires. Si « MEO_ » ne parle pas, on renomme.

---

## Une limite à connaître

Sur les 2 346 défauts analysés dans l'historique, on est sûr du classement pour environ la moitié — ceux où l'équipe test a écrit son code. Pour l'autre moitié (contrôle final, inspection MIP), il n'y a pas de code dans le texte, donc on devine à partir des mots. On le sait, et chaque défaut porte un niveau de confiance pour qu'on ne raconte pas d'histoires sur un graphe.

Ça se règle tout seul dès que la saisie se fait avec un code. Ce n'est pas un problème d'analyse, c'est un problème de saisie.

---
---

# Annexe — exemples réels par type

Tous les exemples sont des vrais extraits de NC de janvier à juillet 2026.

### Sélection

**INVERSION_BRANCHEMENT** — deux fils intervertis
> 115VMB INVERSION DE BRANCHEMENT ENTRE LES BORNES R ET S
> 115VMB INVERSION DE BRANCHEMENT ENTRE LES BORNES AA ET CC (QUADRAX)

**ERREUR_BRANCHEMENT** — un fil sur la mauvaise borne
> 7XCA CABLE EN B3 AU LIEU DE B2
> 11XCA CABLE EN D1 AU LIEU DE X2

**ERREUR_REF_ELECTRIQUE** — mauvaise référence sur un élément électrique
> 10REA ET 23XEA RELAIS INVERSES
> 1033VC MAUVAIS DETROMPAGE

**ERREUR_REF_HABILLAGE** — mauvaise référence sur de l'habillage
> INVERSION DE PLAQUETTE ENTRE 2WTA ET 2WTB

### Exécution

**MEO_SERRAGE**
> route 2M, FIN 1GG B, backshell desserré

**MEO_GAINAGE**
> ROUTE ESS 2M : liseré apparent et gaine vrillée, reprendre le gainage
> Gaine ouverte, finition non terminée sur la prise 20TC1-A

**MEO_CHEMINEMENT**
> route 1M, reprendre cheminement, clash entre support lacote et structure
> ROUTE ESS 1M 1MD 1MG : liseré apparent

**MEO_FRETTAGE_COLLIER**
> ROUTE ESS 2S 2SF et ROUTE ESS 2M 2MF : frète à reprendre

**MEO_SERTISSAGE_STANDARD**
> 1608VC019 BORNE 40 MAUVAIS SERTISSAGE
> 300VT200 BORNE 3G MAUVAIS SERTISSAGE

**MEO_METALLISATION**
> Bleu de métallisation à reprendre sur 100VN121, 100VN123, 110VN145
> 100VN131 : bleu sous rondelle à reprendre

**MEO_FINITION**
> sur platine, reprendre finition du FIN 11CP1 C
> 10FC1 A, finition du connecteur à effectuer

### Omission

**OUBLI_VERROUILLAGE**
> 12KS1 BORNE 3 DEVERROUILLE
> 100VT400 BORNE 6H DEVERROUILLEE

**MANQUANT_OBTURATION**
> FIN 411VC007 A : manque 4 obturateurs
> route 1M, FIN 411VC001 A, il manque 8 obturateurs noirs

**MANQUANT_HABILLAGE**
> FIN 1608VC064 A : Mq obturateur
> FIN 1608VC097 A : manque une frète sur reprise de blindage panneau arrière

**MANQUANT_CABLE_ELEMENT**
> route 2M, FIN 1608VC058 A, il manque la gaine thermo sur le câble

**MANQUANT_IDENTIFICATION**
> au déballage nous constatons qu'il manque l'étiquette d'identification SATO

**NON_CONNECTE**
> 3RN2A CABLE EN < P NON CONNECTE
> 115VMA DR24 N°3119-0344 NON CONNECTE AU GND

**FOD**
> FIN 11CP1 A. FOD, brin métallique entre les câbles
> FOD poussière : sur table, platine aspiration PYLONE

### Manipulation

**DOMMAGE_CABLE**
> CABLE COUPE ENTRE 1608VC062A BORNE 19 ET 100VT400 5D

**DOMMAGE_COMPOSANT**
> Endommagement fibre : fibre 3161-0582 cassée

**DOMMAGE_HABILLAGE**
> Étiquette collante endommagée sur la prise 1608VC006-A
> Sur platine relais, étiquette FIN 721VN abîmée

**DOMMAGE_STRUCTURE**
> Contact entre la route P et la structure au niveau de la dérivation de 6PB2

### Amont

**AMONT_IMPRESSION**
> FIN 4DB2 A : surlongueur de câble
> route 2M, avant FIN 300VD002 A, un câble en sur-longueur sur le harnais

### Process

**PROCESS_DOSSIER**
> 1027709295 - GR non rempli
