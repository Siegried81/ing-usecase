# Pipeline Google Trends — ING vs KBC vs CBC

Document de passation technique, destiné à un agent qui doit comprendre et
pouvoir opérer ce pipeline sans contexte préalable. Décrit uniquement le
pipeline **Trends** (collecte, anomalies, visualisation, export). Le
pipeline `campaigns/` (rapprochement avec des campagnes publicitaires
réelles) est construit **en aval** de celui-ci, en lecture seule sur ses
tables — il est mentionné en fin de document mais pas détaillé ici.

## 1. Objectif

Mesurer, par produit bancaire (compte à vue, carte de crédit, app mobile,
etc.), l'intérêt de recherche Google en Belgique pour **ING** face à huit
banques concurrentes — **KBC**, **CBC**, **BNP Paribas Fortis**,
**Argenta**, **Crelan** (banques traditionnelles), **Revolut**, **N26** et
**bunq** (néobanques) — sur 5 ans, et détecter automatiquement les pics
anormaux d'intérêt de recherche. Ces pics sont les dates candidates à
vérifier manuellement (le pipeline ne collecte aucune donnée publicitaire
lui-même). ING est l'ancre commune : chaque fiche compare toujours ING à
une ou plusieurs des huit autres banques, jamais deux concurrents entre eux
sans ING dans la même requête.

**Fait métier clé** : CBC Banque & Assurance est la marque commerciale de
KBC Group pour la Wallonie et Bruxelles francophone — l'équivalent de la
marque KBC en Flandre. Même groupe, marques distinctes, recherches Google
distinctes. Le pipeline les traite comme des entités de recherche
indépendantes, mais garde la trace de leur lien de parenté à certains
endroits précis (voir section 7).

**Extension six banques (BNPPF, Argenta, Crelan, Revolut, N26, bunq)** :
ajoutée après coup par un protocole de résolution empirique des termes
(`collectors/term_resolver.py`, section 7bis) — contrairement aux 18 fiches
d'origine, dont les termes ont été choisis à la main, les termes de
l'extension ont été sélectionnés par test réel contre Google Trends parmi
plusieurs candidats par langue, avec rejet automatique de ceux dont le
volume est trop faible une fois normalisé face à ING. Résultat notable :
sur 43 fiches produit candidates, seules 10 ont survécu (voir section 3) —
Revolut n'en garde qu'une, N26 et bunq aucune (ces deux banques
n'apparaissent plus qu'au niveau marque). Ce n'est pas un défaut du
pipeline : c'est la mesure réelle d'un volume de recherche quasi nul pour
des requêtes produit très spécifiques face à un acteur historique aussi
dominant qu'ING sur Google Trends Belgique.

## 2. Vue d'ensemble du flux

```
config.py (référentiel produits)
        │
        ▼
collectors/trends_collector.py  ──►  pytrends (API Google Trends)
        │
        ▼
benchmark.db : table trends_data (+ data/csv/*.csv, un CSV par fiche)
        │
        ▼
analysis/anomaly_detection.py
        │
        ▼
benchmark.db : table anomalies
        │
        ├──► app.py (Streamlit, visualisation)
        └──► export/*.py (Markdown + CSV, données à plat)
```

Chaque étape lit dans SQLite et/ou écrit dans SQLite — il n'y a pas
d'état caché ailleurs. La base est `benchmark.db` à la racine du projet
(`kbc-ing-benchmark/benchmark.db`), absente du dépôt git (regénérée
localement).

## 3. Le référentiel produits (`config.py`)

Tout part de `PRODUCTS`, une liste de **32 fiches** (`dict`) — les 18
fiches d'origine, strictement inchangées, suivies des 14 fiches ajoutées
par l'extension six banques — chacune avec :

```python
{
    "product_id": "compte_professionnel",       # identifiant stable, clé primaire logique
    "product_label": "Compte professionnel / indépendant",  # libellé humain (FR)
    "terms": [
        {"term": "KBC zakelijke rekening", "bank": "KBC", "language": "nl"},
        {"term": "compte professionnel ING", "bank": "ING", "language": "fr"},
        ...
    ],
}
```

**Contrainte dure : au maximum 5 `terms` par fiche.** C'est la limite
imposée par l'API `pytrends` (paramètre `kw_list` d'un appel
`build_payload`). `trends_collector.py` lève une exception si une fiche
en a plus.

Les 18 fiches se répartissent en 3 groupes :

1. **9 fiches "KBC vs ING"** (`compte_professionnel`, `compte_a_vue`,
   `compte_epargne`, `investissement_courtage`, `app_mobile`,
   `carte_credit`, `epargne_pension`, `assurance_habitation`,
   `pret_hypothecaire`) — chacune compare les termes KBC et ING pour ce
   produit.
2. **8 fiches "CBC vs ING"** (mêmes noms de produit, suffixées `_cbc`,
   ex. `compte_professionnel_cbc`) — même principe mais avec les termes
   CBC à la place de KBC. Il n'existe **pas** de fiche
   `investissement_courtage_cbc` : CBC n'a pas d'offre de courtage propre
   (Bolero est une plateforme partagée par tout KBC Group), donc pas de
   terme CBC distinct à interroger.
3. **1 fiche `marque_generique`** : les 3 marques seules (`KBC`, `ING`,
   et le topic CBC — voir section 7), sans contexte produit. C'est la
   seule fiche des 18 d'origine à contenir 3 banques dans la même requête.

Les 14 fiches ajoutées par l'extension (suffixe par banque, voir table
1.1 du brief d'extension : `_bnppf`, `_argenta`, `_crelan`, `_revolut` -
N26 et bunq n'ont aucune fiche produit, voir plus bas) :

4. **10 fiches produit "banque vs ING"**, une par combinaison
   (produit de base, banque) ayant passé le protocole de résolution de la
   section 7bis - `PRODUCT_SELECT_COVERAGE` (0.50) ou, à défaut,
   `PRODUCT_FLOOR_COVERAGE` (0.25) :
   - BNPPF (4) : `compte_a_vue_bnppf`, `app_mobile_bnppf`,
     `carte_credit_bnppf` (slot `nl` supprimé), `epargne_pension_bnppf`
     (slot `nl` supprimé) ;
   - ARGENTA (3) : `compte_a_vue_argenta`, `compte_epargne_argenta` (slot
     `fr` supprimé), `app_mobile_argenta` ;
   - CRELAN (2) : `app_mobile_crelan`, `carte_credit_crelan` (slot `nl`
     supprimé) ;
   - REVOLUT (1) : `compte_a_vue_revolut` (slot `nl` supprimé) ;
   - N26 et BUNQ : **aucune** - les 5 et 6 fiches candidates de chaque
     banque ont toutes été rejetées (couverture sous 0.25, voir
     `data/term_validation_report.md`). Ces deux banques n'apparaissent
     que dans `marque_generique_neobanques` (voir point 5).
5. **2 fiches marque** : `marque_generique_traditionnelles` (ING, KBC,
   topic BNPPF, topic ARGENTA, chaîne `Crelan`) et
   `marque_generique_neobanques` (ING, KBC, chaîne `Revolut`, topic N26,
   chaîne `bunq`). `ING` et `KBC` y sont repris à l'identique de
   `marque_generique`, pour permettre un futur rescaling inter-fiches (hors
   périmètre de ce pipeline, mais la structure le permet).
6. **2 fiches contexte**, expliquant chacune une rupture de marché connue :
   `contexte_integration_bnppf_bpost` (ING, topic BNPPF, `bpost bank`,
   `bpost banque` - marque absorbée le 22/01/2024) et
   `contexte_fusion_crelan_axa` (ING, chaîne `Crelan`, `AXA Bank`,
   `AXA Banque` - marque absorbée le 10/06/2024). Les termes de marque
   prédécesseure portent le `bank` de la banque qui les a absorbées.

Les 33 fiches candidates restantes (sur 43) ont été intégralement
supprimées, faute d'un seul slot dépassant le seuil plancher - voir
`data/term_validation_report.md`, section « Fiches et slots supprimes »,
pour la liste complète et le motif (couverture observée) de chacune.

`GEO = "BE"` et `TIMEFRAME = "today 5-y"` sont fixes pour tout le
pipeline (mêmes constantes utilisées partout, jamais codées en dur
ailleurs).

## 4. Collecte (`collectors/trends_collector.py`)

**Principe** : une fiche = un appel `pytrends.build_payload(kw_list, ...)`
+ `interest_over_time()`. Les valeurs Google Trends (0-100) ne sont
comparables **qu'à l'intérieur d'un même appel** — c'est pour ça que la
structure est "une fiche = une requête indépendante" plutôt que 18 appels
mélangés : comparer une valeur de la fiche `app_mobile` à une valeur de
`carte_credit` n'a aucun sens.

**Granularité réelle** : Google Trends bascule automatiquement en
hebdomadaire au-delà d'environ 270 jours de plage — sur 5 ans, on obtient
donc des points **hebdomadaires** (~262 points par terme), jamais
journaliers ni mensuels, quel que soit ce que le nom `TIMEFRAME` suggère.

**Robustesse réseau** (Google Trends limite agressivement le débit) :
- séquentiel strict, aucune parallélisation ;
- pause fixe de `MIN_DELAY_SECONDS = 60` s après **chaque** fiche traitée
  avec succès ;
- sur erreur 429, backoff exponentiel avec jitter : jusqu'à
  `MAX_RETRIES = 5` tentatives, délai initial `INITIAL_BACKOFF_SECONDS = 30` s
  (doublé + jitter aléatoire à chaque échec) ;
- **reprenable** : avant de traiter une fiche, le script vérifie si
  `trends_data` contient déjà des lignes pour ce `product_id` — si oui, il
  la saute. Un lancement interrompu peut être relancé tel quel, seules les
  fiches manquantes sont retéléchargées. Piège : si on modifie les termes
  d'une fiche déjà collectée (ex. ajout d'un terme), il faut supprimer ses
  lignes existantes (`DELETE FROM trends_data WHERE product_id = ...`)
  avant de relancer, sinon la fiche est sautée avec l'ancien contenu.

**Sorties** : un CSV par fiche dans `data/csv/{product_id}.csv` (colonne
`Time` + une colonne par terme, format brut pytrends) **et** une écriture
en base dans `trends_data` au format long (une ligne par
terme × date), via upsert sur `UNIQUE(product_id, term, date)`.

Durée réelle observée pour une collecte complète à froid (18 fiches) :
entre ~9 minutes (sans rate-limit) et ~25 minutes (avec 429 fréquents).

## 5. Schéma de base (`db/schema.sql`)

```sql
CREATE TABLE trends_data (
    product_id TEXT NOT NULL, product_label TEXT NOT NULL, term TEXT NOT NULL,
    bank TEXT NOT NULL, language TEXT NOT NULL, date TEXT NOT NULL, value INTEGER NOT NULL,
    UNIQUE (product_id, term, date)
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY, product_label TEXT NOT NULL, term_count INTEGER NOT NULL
);

CREATE TABLE anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL, term TEXT NOT NULL, bank TEXT NOT NULL,
    date TEXT NOT NULL, value INTEGER NOT NULL,
    anomaly_type TEXT NOT NULL CHECK (anomaly_type IN ('isolated_spike', 'sustained_trend')),
    deviation_score REAL NOT NULL,
    UNIQUE (product_id, term, date)
);
```

S'y ajoute `term_validation`, la trace d'audit de la résolution des termes
(voir section 7bis et `collectors/term_resolver.py`) : une ligne par
candidat testé, par appel pytrends où il est apparu.

```sql
CREATE TABLE term_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL CHECK (scope IN ('brand', 'product', 'brand_fiche', 'context_fiche')),
    product_id TEXT NOT NULL, bank TEXT NOT NULL, slot_language TEXT NOT NULL,
    candidate_rank INTEGER NOT NULL, term TEXT NOT NULL,
    term_kind TEXT NOT NULL CHECK (term_kind IN ('string', 'topic')),
    topic_title TEXT, topic_type TEXT, call_index INTEGER NOT NULL,
    nonzero_points INTEGER NOT NULL, total_points INTEGER NOT NULL,
    coverage REAL NOT NULL, mean_value REAL NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('selected', 'selected_low_coverage', 'rejected', 'dropped', 'info_only')),
    flags TEXT, tested_at TEXT NOT NULL,
    UNIQUE (scope, product_id, bank, slot_language, term, call_index)
);
```

Conventions de lecture de cette table :
- `call_index > 0` = observation brute de l'appel n° *call_index* ;
  `call_index = 0` = ligne de synthèse, c'est-à-dire le terme finalement
  retenu (ou, si `verdict = 'dropped'`, la meilleure observation du slot
  abandonné). **Ne jamais lire autre chose que `call_index = 0` pour savoir
  ce qui a été retenu.**
- `slot_language = '__done__'` est une ligne-marqueur technique : elle
  signale que la fiche est entièrement résolue et rend le résolveur
  reprenable. Elle doit être exclue de toute lecture métier.
- `scope = 'brand'` utilise un `product_id` synthétique
  `__brand__{BANK}` ; `scope` vaut `brand_fiche` ou `context_fiche` pour
  les appels de contrôle, qui n'éliminent aucun terme.
- Le collecteur ne lit **jamais** cette table : seules `config.PRODUCTS`
  fait foi pour ce qui est collecté. `app.py` et `export/export_common.py`
  la lisent uniquement pour afficher couverture et flags.

Points d'attention :
- `bank` est un `TEXT` libre, **sans contrainte `CHECK`** — les 9 valeurs
  réellement utilisées sont `'ING'`, `'KBC'`, `'CBC'`, `'BNPPF'`,
  `'ARGENTA'`, `'CRELAN'`, `'REVOLUT'`, `'N26'`, `'BUNQ'`, mais rien
  n'empêche d'en insérer une autre en base. Ne pas supposer une énumération
  stricte côté SQL ; elle n'existe que dans `config.BANK_DISPLAY_LABELS`
  (liste de référence, doublée de `config.BANK_SEGMENTS` pour la
  distinction traditionnelle / néobanque) et dans le code applicatif.
  Attention : la table `campaigns` du pipeline aval, elle, **a** une
  contrainte `CHECK (bank IN ('KBC', 'CBC', 'ING'))` — voir section 12.
- `language` vaut `'fr'`, `'nl'`, `'en'` ou `'multi'`. `'multi'` a été
  introduit par l'extension pour les termes réellement indépendants de la
  langue (topics Knowledge Graph de marque, noms d'application). Les
  termes neutres antérieurs à l'extension (topic CBC, noms d'app KBC/ING)
  restent étiquetés `'en'` : ils n'ont pas été retouchés pour ne pas
  rompre la continuité des 18 fiches d'origine.
- `products` est un simple annuaire (label + nombre de termes), synchronisé
  automatiquement par `trends_collector.py` à chaque run — pas de logique
  métier dessus.
- `date` est stockée en `TEXT` format `YYYY-MM-DD` partout (jamais de type
  `DATE` natif SQLite, qui n'existe pas).
- État réel constaté au moment de la rédaction : 18 602 lignes dans
  `trends_data`, 473 dans `anomalies`, 18 dans `products`, plage de dates
  2021-09-12 → 2026-09-13.

## 6. Détection d'anomalies (`analysis/anomaly_detection.py`)

Exécutée comme étape séparée (`python analysis/anomaly_detection.py`),
**jamais** recalculée à l'affichage — l'app Streamlit lit uniquement la
table déjà peuplée.

Pour chaque série `(product_id, term)` (donc pour chaque terme
individuellement — KBC et ING d'une même fiche ne sont jamais comparés
entre eux ici, seulement chacun contre sa propre historique) :

1. `overall_mean`, `overall_std` = moyenne et écart-type de la série
   entière. Si `overall_std == 0` (série constante, typiquement des zéros
   plats), la série est ignorée — aucune anomalie possible.
2. `seasonal_mean` = moyenne des valeurs groupées par mois calendaire
   (`date.dt.month`), sur toutes les années disponibles — profil de
   saisonnalité de référence pour ce terme.
3. Un point est **candidat anomalie** s'il vérifie **simultanément** :
   - `z_score = (valeur - overall_mean) / overall_std >= Z_SCORE_THRESHOLD` (1.5)
   - `valeur / seasonal_mean[mois] >= SEASONAL_RATIO_THRESHOLD` (1.3)
4. Les points candidats consécutifs (mêmes index adjacents dans la série
   triée par date) sont regroupés en "runs" :
   - run de longueur 1 → `anomaly_type = 'isolated_spike'`
   - run de longueur ≥ 2 → `anomaly_type = 'sustained_trend'`
5. `deviation_score` stocké = le `z_score` de ce point précis (pas une
   moyenne du run).

Le script fait un `DELETE FROM anomalies` puis réinsère tout à chaque
run — **les `id` ne sont pas stables d'un run à l'autre**. Toute table qui
référence `anomalies.id` par clé étrangère (c'est le cas de
`campaign_anomaly_matches` dans le pipeline aval) doit être régénérée
après un nouveau run de détection.

## 7. Le cas CBC : désambiguïsation Google Trends

Problème découvert empiriquement : la chaîne `"CBC"` seule est polluée au
niveau international sur Google Trends — elle capte aussi *Carcinome
basocellulaire*, *CBC News* / Radio-Canada, *CBC Kids*, et *hémogramme*
(numération formule sanguine), même avec `geo='BE'`.

Test réalisé via `pytrends.suggestions()` puis comparaison de couverture
réelle (`interest_over_time()`, geo=BE, 5 ans) :

| Formulation | Type | Moyenne | Points non-nuls |
|---|---|---|---|
| `"CBC"` | string brute | 71.6 | 262/262 (mais pollué) |
| `"CBC Banque"` | string | 7.3 | 262/262 |
| `"CBC Banque et Assurance"` | string | 0.008 | 1/262 (quasi vide, trop spécifique) |
| `/g/1z3t2x3c8` | **topic Knowledge Graph** | **54.2** | **262/262** |

`/g/1z3t2x3c8` est le topic Knowledge Graph "CBC Banque & Assurance"
(type "Sujet"), retourné en premier résultat par
`pytrends.suggestions(keyword="CBC Banque")`. C'est le seul terme CBC du
pipeline à être un **topic mid** plutôt qu'une chaîne de recherche brute
— tous les autres termes (KBC, ING, et les termes produits CBC comme
`"compte à vue CBC"`) sont des chaînes classiques passées telles quelles à
`pytrends`.

Conséquence pratique : la colonne `term` de `trends_data`/`anomalies`
contient littéralement la chaîne `"/g/1z3t2x3c8"` pour ce terme précis (
c'est ce que `pytrends` retourne comme nom de colonne pour un topic).
Pour l'affichage humain, `config.TERM_DISPLAY_LABELS` fait la
correspondance :

```python
TERM_DISPLAY_LABELS = {"/g/1z3t2x3c8": "CBC Banque & Assurance"}
```

Toute UI ou export qui affiche un `term` doit passer par
`TERM_DISPLAY_LABELS.get(term, term)` (fonction `display_term()`,
dupliquée à l'identique dans `app.py` et `export/export_common.py`) —
sinon ce terme précis s'affiche comme un identifiant technique illisible.

**KBC et CBC dans le code** : en dehors de ce topic mid, KBC et CBC sont
traités comme deux valeurs de `bank` totalement indépendantes dans tout le
pipeline Trends (aucun regroupement). Le regroupement "KBC = CBC" n'existe
que dans le pipeline `campaigns/` en aval (voir section 9), pas ici.

## 7bis. Désambiguïsation des marques ajoutées en extension

Même méthode que pour CBC ci-dessus, appliquée systématiquement aux six
banques ajoutées (`collectors/term_resolver.py`, phase 1A) : pour chaque
marque, les topics Knowledge Graph renvoyés par `pytrends.suggestions()`
sont testés **dans le même appel** que les chaînes brutes candidates, donc
sous la même normalisation, puis comparés en couverture (points non nuls /
points totaux) et en moyenne.

Un topic n'est retenu que si (a) son `title` contient le nom de la marque,
(b) son `type` évoque une banque / société financière / entreprise, et (c)
sa couverture atteint `BRAND_MIN_COVERAGE` (0.90). À défaut, la chaîne
brute la plus spécifique est retenue avec le flag `ambiguous_string`.

| Banque | Terme retenu | Type | Couverture | Moyenne | Alternative écartée |
|---|---|---|---|---|---|
| BNPPF | `/m/07sc3dj` (topic "BNP Paribas Fortis") | Banque | 1.000 | 56.7 | chaîne `BNP Paribas Fortis` (moyenne 20.9) et 3 topics d'agences locales (Waremme, Hasselt, Ans), couverture 0.000 |
| ARGENTA | `/m/03lmky` (topic "Argenta") | Banque | 1.000 | 44.5 | topic BBVA "Banco Bilbao Vizcaya Argentaria" (couverture 0.498), topics d'agences (Lede, Renaix) à 0.000 |
| N26 | `/g/11c1p5t9vb` (topic "N26") | Banque | 0.985 | 12.6 | topic "N26 Bank AG" (Berlin), couverture 0.011 |
| CRELAN | chaîne `Crelan` | — | 1.000 | 38.2 | topic `/m/0h4w6d` équivalent (couverture 1.000, moyenne 37.7) |
| REVOLUT | chaîne `Revolut` | — | 1.000 | 21.8 | topic `/g/11clggwh1c` équivalent (couverture 1.000, moyenne 23.5) |
| BUNQ | chaîne `bunq` | — | 1.000 | — | aucun topic de type banque renvoyé par `suggestions()` |

Lecture : les trois marques ambiguës hors contexte bancaire (`BNP` = groupe
français, `Argenta` = commune italienne, `N26` = route régionale
Leuven–Mechelen) passent par un topic ; les trois marques non ambiguës
gardent une chaîne brute, cohérente avec le traitement existant de `KBC` et
`ING`. Les topics d'agences locales sont un piège récurrent de
`suggestions()` : ils portent exactement le même titre que la marque mais
ont une couverture nulle.

**Contrôle informatif sur l'existant** (ne modifie rien, les 18 fiches
d'origine restent inchangées) : la chaîne `ING` (couverture 1.000, moyenne
59.3) fait jeu égal avec son topic `/m/01hlqz` "Groupe ING" (1.000, 58.1) ;
la chaîne `KBC` (1.000, 63.7) est même plus couvrante que les topics
"KBC Bank" `/m/06t05x` (1.000, 40.6) et "KBC Group N.V." `/m/0g4dpgt`
(0.808, 16.5). Aucun changement n'est donc justifié sur ces deux termes, et
un changement casserait de toute façon la continuité des séries existantes.

## 8. Visualisation (`app.py`, Streamlit)

`streamlit run app.py` (port par défaut 8501). Lecture seule sur
`trends_data` et `anomalies`, via `@st.cache_data`.

**Navigation** : un sélecteur « Comparaison » dans la barre latérale, et
non un onglet par fiche — avec le périmètre étendu, le nombre de fiches
rend une barre d'onglets unique inexploitable. Options, dans l'ordre :
KBC (valeur par défaut), CBC, BNP Paribas Fortis, Argenta, Crelan,
Revolut, N26, bunq, « Marques & contexte ». Chaque option affiche en
onglets les fiches de la banque choisie, dans l'ordre de
`config.PRODUCTS`.

ING n'a pas d'option propre : c'est l'ancre commune présente dans toutes
les fiches. « Marques & contexte » regroupe `marque_generique`, les deux
fiches de marque et les deux fiches de contexte (liste
`BRAND_CONTEXT_FICHES` dans `app.py`) ; ces fiches sont exclues des vues
par banque, sinon elles apparaîtraient dans plusieurs vues à la fois via
leurs ancres ING/KBC. Aucune fiche n'est devenue inaccessible.

Chaque onglet :
- un graphique Plotly : une courbe par terme de la fiche, couleur par
  index de terme (palette fixe à 5 couleurs), style de trait par banque
  (dict `BANK_DASH` : `dash` ING, `solid` KBC, `dashdot` CBC, `dot` BNPPF
  et Revolut, `longdash` Argenta et N26, `longdashdot` Crelan et bunq).
  La réutilisation des styles est volontaire : deux banques qui partagent
  un style n'apparaissent jamais dans la même fiche. Marqueurs distincts
  pour `isolated_spike` (losange) vs `sustained_trend` (étoile) ;
- des lignes verticales pointillées aux dates `config.KNOWN_EVENTS` des
  banques présentes dans la fiche, surmontées d'un marqueur dont
  l'info-bulle donne le libellé de l'événement. `KNOWN_EVENTS` est
  **purement d'affichage** : la détection d'anomalies ne le lit jamais ;
- sous le graphique, la mention des termes portant un flag
  (`selected_low_coverage`, `broad_fallback`, `asymmetric`,
  `ambiguous_string`), lue dans `term_validation` ;
- un tableau des anomalies de cette fiche ;
- un tableau de données brutes filtrable (par terme, par période).

Libellés : `display_term()` (mid → nom lisible) et `display_bank()` (code
banque → libellé d'affichage, ex. `BNPPF` → « BNP Paribas Fortis »), tous
deux dupliqués à l'identique dans `app.py` et `export/export_common.py`,
selon la duplication déjà en place dans le projet.

Aucune écriture en base depuis cette app — purement consultatif.

## 9. Exports (`export/`)

Chaque script `export_*.py` est un point d'entrée fin qui appelle
`export_common.run_export(bank, ...)` ou `run_export_all(...)` :

| Script | Filtre | Sorties |
|---|---|---|
| `export_kbc_data.py` | `bank='KBC'` | `kbc_trends_data.csv`, `kbc_data_export.md` |
| `export_ing_data.py` | `bank='ING'` | `ing_trends_data.csv`, `ing_data_export.md` |
| `export_cbc_data.py` | `bank='CBC'` | `cbc_trends_data.csv`, `cbc_data_export.md` |
| `export_bnppf_data.py` | `bank='BNPPF'` | `bnppf_trends_data.csv`, `bnppf_data_export.md` |
| `export_argenta_data.py` | `bank='ARGENTA'` | `argenta_trends_data.csv`, `argenta_data_export.md` |
| `export_crelan_data.py` | `bank='CRELAN'` | `crelan_trends_data.csv`, `crelan_data_export.md` |
| `export_revolut_data.py` | `bank='REVOLUT'` | `revolut_trends_data.csv`, `revolut_data_export.md` |
| `export_n26_data.py` | `bank='N26'` | `n26_trends_data.csv`, `n26_data_export.md` |
| `export_bunq_data.py` | `bank='BUNQ'` | `bunq_trends_data.csv`, `bunq_data_export.md` |
| `export_all_data.py` | aucun | `all_trends_data.csv`, `all_data_export.md` |

Chaque `.md` contient : méthodologie (source, granularité, seuils de
détection, **méthode de sélection des termes** et renvoi au rapport de
validation), **section « Événements structurels connus »**
(`config.KNOWN_EVENTS` filtrés par banque ; tous les événements dans
l'export global), liste des fiches concernées avec leurs termes, notes
produit propres à la banque, référence au CSV joint, et un tableau complet
des anomalies détectées. Ce tableau porte deux colonnes supplémentaires,
**couverture du terme** et **flags du terme**, jointes depuis
`term_validation` ; elles restent vides pour les 18 fiches historiques,
qui sont antérieures au protocole de sélection.

Le CSV, lui, ne change pas : c'est la table `trends_data` brute
correspondante (toutes les colonnes, sans transformation).

Ces exports sont la donnée d'entrée officielle pour tout pipeline externe
qui veut consommer ce projet sans toucher à SQLite directement.

## 10. Comment tout relancer depuis zéro

```bash
cd kbc-ing-benchmark
pip install -r requirements.txt

python collectors/term_resolver.py         # 1-3 h, reprenable ; uniquement si
                                           # on ajoute une banque ou des termes

# revue humaine de data/term_validation_report.md,
# puis report des termes retenus dans config.PRODUCTS

python collectors/trends_collector.py      # ~10 min à 2 h, reprenable si interrompu
python analysis/anomaly_detection.py       # quelques secondes

python export/export_kbc_data.py
python export/export_ing_data.py
python export/export_cbc_data.py
python export/export_bnppf_data.py
python export/export_argenta_data.py
python export/export_crelan_data.py
python export/export_revolut_data.py
python export/export_n26_data.py
python export/export_bunq_data.py
python export/export_all_data.py

python campaigns/scoring.py                # obligatoire : régénère les
python campaigns/reports.py                # correspondances (ids d'anomalies)

streamlit run app.py                       # UI sur http://localhost:8501
```

Les étapes 1 à 3 (résolution des termes, revue, mise à jour de
`config.PRODUCTS`) ne servent qu'à faire entrer de nouveaux termes dans le
périmètre. Une simple mise à jour des données part directement de
`trends_collector.py`.

L'étape `campaigns/` n'est pas optionnelle après une détection : chaque run
de `anomaly_detection.py` vide et réinsère la table `anomalies`, donc les
`id` changent et `campaign_anomaly_matches` pointe sur des lignes
obsolètes tant qu'on ne relance pas `scoring.py` (voir section 6).

Pour ajouter une fiche produit ou un terme : éditer `config.PRODUCTS`,
relancer `trends_collector.py` (skip automatique de ce qui existe déjà,
voir section 4) puis `anomaly_detection.py`, les exports et la
régénération `campaigns/`.

## 11. Pièges connus (déjà rencontrés, à ne pas re-découvrir)

- **Encodage console Windows** : les caractères accentués (`é`, `à`...)
  s'affichent parfois comme `�` dans un terminal Git Bash/PowerShell. Les
  données elles-mêmes sont en UTF-8 correct en base — c'est uniquement un
  problème d'affichage du terminal, vérifié à plusieurs reprises en
  écrivant dans un fichier puis en le relisant.
- **`pytrends.suggestions()` et bare strings pour des noms de marque
  courts/ambigus** : toujours vérifier la désambiguïsation Knowledge Graph
  avant d'ajouter un nouveau terme de marque générique (voir méthode
  section 7) — un nom court peut être pollué sans que le volume élevé ne
  le laisse deviner.
- **Limite pytrends de 5 termes/requête** : toute nouvelle fiche ou tout
  ajout de terme à une fiche existante doit être vérifié contre cette
  limite avant collecte (le script lève une exception si dépassée, mais
  autant l'anticiper).
- **`ON CONFLICT` vs suppression complète** : `trends_data` et `products`
  utilisent un upsert (les anciennes lignes non concernées survivent).
  `anomalies` est entièrement vidée et régénérée à chaque run de
  `anomaly_detection.py` (voir section 6) — les deux tables n'ont pas la
  même politique de rafraîchissement, à garder en tête si on modifie l'un
  des deux scripts.

Pièges propres à l'extension multi-banques :

- **Volume de recherche réel des termes produit** : c'est le piège majeur,
  et il concerne aussi les 18 fiches d'origine. En Belgique, les requêtes
  produit du type « compte professionnel ING » ont un volume quasi nul :
  dans la fiche `compte_professionnel` déjà collectée, *tous* les termes,
  ING et KBC compris, ont entre 0 et 5 points non nuls sur 262. Une série
  pareille est du bruit : un pic isolé y devient mécaniquement une
  « anomalie ». Ne jamais conclure d'une couverture faible d'un terme
  concurrent qu'il est « moins cherché que l'incumbent » sans regarder la
  couverture des termes ING de la même fiche.
- **Normalisation à l'intérieur d'une fiche** : la couverture d'un terme
  se mesure toujours dans la composition réelle de sa fiche. Les valeurs
  renvoyées sont des entiers 0-100 rapportés au pic du terme le plus fort
  de la requête, donc un terme faible dans une fiche par ailleurs forte est
  arrondi à 0. Tester un terme seul donnerait une couverture flatteuse et
  fausse.
- **Cours de bourse** : ne jamais accoler à une marque `aandeel`,
  `aandelen`, `action(s)`, `bourse` ou `cours`. BNP Paribas et KBC sont
  cotées et Crelan émet des parts coopératives : ces requêtes captent la
  recherche de cours, pas l'intérêt produit.
- **`BNP`, `N26`, `Argenta` seuls** : ambigus au niveau marque (groupe
  BNP Paribas français, route régionale Leuven–Mechelen, commune
  italienne), d'où le topic obligatoire (section 7bis). En contexte produit
  belge (`compte à vue BNP`, `BNP woonkrediet`), le jeton `BNP` est en
  revanche sans ambiguïté.
- **Ordre des mots** : sans effet en broad match. Deux candidats qui ne
  diffèrent que par l'ordre des mots sont le même terme — ne pas gaspiller
  un appel à les départager.
- **Marques sœurs hors périmètre** : Hello bank! et Fintro (groupe BNP
  Paribas Fortis) ne sont captées par aucun terme BNPPF.
- **Ruptures structurelles attendues** : intégration de bpost banque
  (janvier 2024), fusion AXA Bank → Crelan (juin 2024) et lancements
  néobanques produisent des anomalies réelles qui ne sont **pas** des
  campagnes publicitaires. Elles sont documentées dans
  `config.KNOWN_EVENTS` et affichées, jamais soustraites des données.
- **Forcer la re-résolution d'une fiche** : le résolveur saute toute fiche
  ayant déjà sa ligne-marqueur `__done__`. Pour la retester, supprimer ses
  lignes `term_validation` (`DELETE FROM term_validation WHERE product_id
  = ...`), exactement comme on supprime des lignes `trends_data` pour
  forcer une recollecte.

## 12. Audit `campaigns/` : disponibilité pour les six nouvelles banques

Audit uniquement - aucune ligne de `campaigns/` n'a été modifiée, comme
demandé par le brief d'extension. `campaigns/` reste un pipeline construit
pour 3 banques (KBC, CBC, ING) et n'est **pas prêt** pour BNPPF, Argenta,
Crelan, Revolut, N26 ou bunq :

- **`db/schema.sql`, table `campaigns`** : `bank TEXT NOT NULL CHECK (bank
  IN ('KBC', 'CBC', 'ING'))`. C'est un blocage dur au niveau base : tout
  `INSERT` d'une campagne pour une des six nouvelles banques échoue
  immédiatement, avant même d'atteindre le code Python. Idem pour `language
  TEXT NOT NULL CHECK (language IN ('FR', 'NL', 'FR+NL'))`, sans impact
  direct des nouvelles banques (mêmes langues) mais à garder en tête si un
  jour `'multi'` devait y apparaître.
- **`campaigns/seed_data.py`** : catalogue saisi à la main, exclusivement
  KBC/CBC/ING. Aucune campagne des six nouvelles banques n'existe - normal,
  ce n'est pas un défaut de code, juste un catalogue pas encore alimenté.
- **`campaigns/reports.py`** : `BANK_ORDER = ["KBC", "CBC", "ING"]` pilote
  toutes les sections par banque et le comparatif agrégé
  (`campaigns_comparison.md`). Une campagne d'une nouvelle banque, même si
  elle existait en base (ce que la contrainte `CHECK` empêche de toute
  façon), n'apparaîtrait dans aucun rapport tant que cette liste n'est pas
  étendue.
- **`campaigns/app.py`** : mêmes symptômes côté UI - `BANK_COLOR = {"KBC":
  ..., "CBC": ..., "ING": ...}` et les onglets sont construits à partir de
  `BANK_ORDER` (importé de `reports.py`). Étendre `BANK_ORDER` sans étendre
  `BANK_COLOR` en parallèle ferait échouer l'app sur un `KeyError`.
- **`campaigns/load_campaigns.py`** : la ligne de log de fin de chargement
  compte explicitement KBC/CBC/ING (`sum(1 for c in CAMPAIGNS if
  c["bank"] == "KBC")`, etc.) - une nouvelle banque serait chargée en base
  sans erreur mais absente de ce résumé.
- **`campaigns/scoring.py`** : deux endroits à distinguer.
  - `find_matches()` : `same_camp_banks = ("KBC", "CBC") if
    campaign["bank"] in ("KBC", "CBC") else (campaign["bank"],)` - gère
    déjà correctement une nouvelle banque comme groupe singleton. Pas de
    problème ici.
  - `camp()` (utilisée par `is_seasonal_confound`) : `return {"KBC", "CBC"}
    if bank in ("KBC", "CBC") else {"ING"}` - **bug latent**, pas une
    simple omission : pour toute banque autre que KBC/CBC, la fonction
    renvoie `{"ING"}` au lieu de `{bank}`. Si une campagne d'une nouvelle
    banque existait un jour, son propre groupe de confusion saisonnière
    serait pris à tort pour celui d'ING, faussant silencieusement la
    détection de confond saisonnier - sans erreur ni avertissement.

Pour rendre `campaigns/` compatible avec les neuf banques, il faudrait (hors
périmètre de cet audit, non fait ici) : lever la contrainte `CHECK` sur
`campaigns.bank`, étendre `BANK_ORDER` et `BANK_COLOR`, et remplacer le
`else {"ING"}` de `camp()` par `else {bank}`.

## 13. Ce qui n'est PAS dans ce pipeline

- Aucune collecte de données publicitaires (Meta Ad Library, Google Ads
  Transparency Center, presse) — volontairement hors périmètre.
- Le rapprochement anomalies ↔ campagnes réelles et le scoring d'impact
  vivent dans `campaigns/` (tables `campaigns`, `campaign_anomaly_matches`,
  `campaign_scores`, app Streamlit séparée sur le port 8502). Ce module
  **lit** `anomalies` en lecture seule mais ne fait partie d'aucune étape
  décrite ci-dessus — c'est un pipeline distinct, construit après coup,
  avec son propre catalogue de campagnes saisi manuellement (pas de
  scraping automatisé).
