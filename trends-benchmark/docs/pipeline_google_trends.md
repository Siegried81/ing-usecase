# Pipeline Google Trends — notoriété de marque ING vs concurrents

Document de passation technique, destiné à un agent qui doit comprendre et
pouvoir opérer ce pipeline sans contexte préalable. Décrit uniquement le
pipeline **Trends** (collecte, part de voix, visualisation,
export). Le pipeline `campaigns/` (rapprochement avec des campagnes
publicitaires réelles) est construit **en aval** de celui-ci, en lecture
seule sur ses tables — il est mentionné en fin de document mais pas
détaillé ici.

## 1. Objectif

Mesurer la **notoriété de marque** d'ING face à huit banques concurrentes
en Belgique sur Google Trends — **KBC**, **CBC**, **BNP Paribas Fortis**,
**Argenta**, **Crelan** (banques traditionnelles), **Revolut**, **N26** et
**bunq** (néobanques) — via un **share of search** : la part de recherches
de chaque banque sur le volume total du panel des 9 banques. C'est un
indicateur classique de force de marque, corrélé aux parts de marché.

**Recentrage de périmètre (2026-09-21)** : le projet a d'abord comparé ING
à chaque concurrent produit par produit (compte à vue, carte de crédit,
etc. — 32 fiches à un moment donné), avant d'être recentré sur la seule
notoriété de marque. Les fiches produit ont été retirées de
`config.PRODUCTS` ; seules les 3 fiches marque génériques subsistent. Les
données historiques des fiches produit restent dans `trends_data` et
`trends_data` (rien n'est supprimé en base), mais ne sont plus lues par
aucune étape du pipeline — voir section 11.

**Fait métier clé** : CBC Banque & Assurance est la marque commerciale de
KBC Group pour la Wallonie et Bruxelles francophone — l'équivalent de la
marque KBC en Flandre. Même groupe, marques distinctes, recherches Google
distinctes. Le pipeline les traite comme des entités de recherche
indépendantes, mais garde la trace de leur lien de parenté à certains
endroits précis (voir section 7).

## 2. Vue d'ensemble du flux

```
config.py (référentiel des 3 fiches marque)
        │
        ▼
collectors/trends_collector.py  ──►  pytrends (API Google Trends)
        │
        ▼
benchmark.db : table trends_data (+ data/csv/*.csv, un CSV par fiche)
        │
        └──► analysis/share_of_search.py  ──► benchmark.db : table brand_share_of_search
                        │
                        ▼
        ┌───────────────┴───────────────┐
        ▼                               ▼
   app.py (Streamlit)         export/export_brand_notoriety.py
```

Chaque étape lit dans SQLite et/ou écrit dans SQLite — il n'y a pas
d'état caché ailleurs. La base est `benchmark.db` à la racine du projet
(`kbc-ing-benchmark/benchmark.db`), absente du dépôt git (regénérée
localement). `share_of_search.py` lit `trends_data` et n'écrit que dans sa
propre table.

## 3. Le référentiel produits (`config.py`)

`PRODUCTS` ne contient plus que **3 fiches**, toutes des fiches marque
(aucune fiche produit) :

```python
PRODUCTS = [
    {"product_id": "marque_generique", "terms": [KBC, ING, CBC (topic)]},
    {"product_id": "marque_generique_traditionnelles", "terms": [ING, KBC, BNPPF (topic), ARGENTA (topic), CRELAN]},
    {"product_id": "marque_generique_neobanques", "terms": [ING, KBC, REVOLUT, N26 (topic), BUNQ]},
]
```

**Contrainte dure : au maximum 5 `terms` par fiche.** C'est la limite
imposée par l'API `pytrends` (paramètre `kw_list` d'un appel
`build_payload`). Avec 9 banques à comparer, il en faut donc au moins 3
fiches : `ING` et `KBC` apparaissent, **strictement inchangés**, dans les
3 fiches, ce qui sert de pont commun (voir section 7ter) pour reconstituer
les 9 banques sur une seule échelle malgré cette limite.

Pourquoi certaines banques utilisent un topic Knowledge Graph plutôt qu'une
chaîne de recherche brute (BNPPF, Argenta, N26, et CBC depuis l'origine) et
pas d'autres (Crelan, Revolut, bunq, ING, KBC) : voir sections 7 et 7bis,
inchangées par le recentrage — ce travail de désambiguïsation reste
entièrement valable, seul le périmètre des fiches produit a changé.

`GEO = "BE"` et `TIMEFRAME = "today 5-y"` sont fixes pour tout le
pipeline (mêmes constantes utilisées partout, jamais codées en dur
ailleurs).

## 4. Collecte (`collectors/trends_collector.py`)

**Principe** : une fiche = un appel `pytrends.build_payload(kw_list, ...)`
+ `interest_over_time()`. Les valeurs Google Trends (0-100) ne sont
comparables **qu'à l'intérieur d'un même appel** — c'est pour ça que la
structure est "une fiche = une requête indépendante", et c'est aussi
pourquoi une technique de chaînage dédiée (section 7ter) est nécessaire
pour comparer des banques réparties sur plusieurs fiches.

**Granularité réelle** : Google Trends bascule automatiquement en
hebdomadaire au-delà d'environ 270 jours de plage — sur 5 ans, on obtient
donc des points **hebdomadaires** (262 points par terme), jamais
journaliers ni mensuels, quel que soit ce que le nom `TIMEFRAME` suggère.

**Robustesse réseau** (Google Trends limite agressivement le débit),
logique partagée avec `collectors/term_resolver.py` via
`collectors/pytrends_network.py` :
- séquentiel strict, aucune parallélisation ;
- pause fixe de `MIN_DELAY_SECONDS = 60` s après **chaque** fiche traitée
  avec succès ;
- sur erreur 429, backoff exponentiel avec jitter : jusqu'à
  `MAX_RETRIES = 5` tentatives, délai initial `INITIAL_BACKOFF_SECONDS = 30` s
  (doublé + jitter aléatoire à chaque échec) ;
- **reprenable** : avant de traiter une fiche, le script vérifie si
  `trends_data` contient déjà des lignes pour ce `product_id` — si oui, il
  la saute. Piège : si on modifie les termes d'une fiche déjà collectée, il
  faut supprimer ses lignes existantes (`DELETE FROM trends_data WHERE
  product_id = ...`) avant de relancer, sinon la fiche est sautée avec
  l'ancien contenu.

**Sorties** : un CSV par fiche dans `data/csv/{product_id}.csv` **et** une
écriture en base dans `trends_data` au format long (une ligne par
terme × date), via upsert sur `UNIQUE(product_id, term, date)`.

Les 3 fiches marque sont déjà collectées (2021-09-12 → 2026-09-13) : après
le recentrage de périmètre, relancer ce script ne fait rien de nouveau
(tout est déjà en base) — il ne redevient utile que si un terme de marque
change ou qu'une fiche est ajoutée.

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

```

`term_validation` (trace d'audit de la résolution des termes de marque,
voir section 7bis et `collectors/term_resolver.py`) : une ligne par
candidat testé, par appel pytrends où il est apparu. Schéma et conventions
de lecture inchangés par le recentrage — voir le fichier `db/schema.sql`
pour le détail complet des colonnes.

**Nouvelle table `brand_share_of_search`** (voir section 7ter), entièrement
dérivée de `trends_data`, vidée et recalculée à chaque run de
`analysis/share_of_search.py` (même politique de rafraîchissement que
`brand_share_of_search`) :

```sql
CREATE TABLE brand_share_of_search (
    bank TEXT NOT NULL, date TEXT NOT NULL, source_fiche TEXT NOT NULL,
    raw_value INTEGER NOT NULL, scale_factor REAL NOT NULL,
    rescaled_value REAL NOT NULL, share_pct REAL NOT NULL,
    UNIQUE (bank, date)
);
```

Points d'attention :
- `bank` est un `TEXT` libre, **sans contrainte `CHECK`**, dans toutes les
  tables ci-dessus — les 9 valeurs réellement utilisées sont référencées
  dans `config.BANK_DISPLAY_LABELS` (doublée de `config.BANK_SEGMENTS` pour
  la distinction traditionnelle / néobanque). La table `campaigns` du
  pipeline aval, elle, **a** une contrainte `CHECK (bank IN ('KBC', 'CBC',
  'ING'))` — voir section 12.
- `language` vaut `'fr'`, `'nl'`, `'en'` ou `'multi'` (introduit par
  l'extension six banques pour les termes indépendants de la langue :
  topics Knowledge Graph de marque, `ING`/`KBC` eux-mêmes dans les fiches
  marque). Les termes neutres antérieurs (topic CBC) restent étiquetés
  `'en'`, pour ne pas rompre la continuité historique.
- **`trends_data` contient encore les lignes des 29
  anciennes fiches produit** (compte à vue, carte de crédit, etc.),
  jamais supprimées lors du recentrage de périmètre. Elles sont
  silencieusement ignorées par `app.py` et `export/` (qui ne lisent que ce
  qui est dans `config.PRODUCTS`, ou filtrent explicitement sur les 3
  `product_id` de fiches marque). Voir section 11 pour le piège associé.
- `date` est stockée en `TEXT` format `YYYY-MM-DD` partout (jamais de type
  `DATE` natif SQLite, qui n'existe pas).

## 7. Le cas CBC : désambiguïsation Google Trends

Problème découvert empiriquement : la chaîne `"CBC"` seule est polluée au
niveau international sur Google Trends — elle capte aussi *Carcinome
basocellulaire*, *CBC News* / Radio-Canada, *CBC Kids*, et *hémogramme*,
même avec `geo='BE'`.

Test réalisé via `pytrends.suggestions()` puis comparaison de couverture
réelle (`interest_over_time()`, geo=BE, 5 ans) :

| Formulation | Type | Moyenne | Points non-nuls |
|---|---|---|---|
| `"CBC"` | string brute | 71.6 | 262/262 (mais pollué) |
| `"CBC Banque"` | string | 7.3 | 262/262 |
| `"CBC Banque et Assurance"` | string | 0.008 | 1/262 (quasi vide, trop spécifique) |
| `/g/1z3t2x3c8` | **topic Knowledge Graph** | **54.2** | **262/262** |

`/g/1z3t2x3c8` est le topic Knowledge Graph "CBC Banque & Assurance",
retourné en premier résultat par `pytrends.suggestions(keyword="CBC
Banque")`. Conséquence pratique : la colonne `term` de
`trends_data` contient littéralement la chaîne
`"/g/1z3t2x3c8"` — pour l'affichage humain, `config.TERM_DISPLAY_LABELS`
fait la correspondance, via `display_term()` (dupliquée à l'identique dans
`app.py` et `export/export_common.py`).

**KBC et CBC dans le code** : traités comme deux valeurs de `bank`
totalement indépendantes dans tout le pipeline Trends. Le regroupement
"KBC = CBC" n'existe que dans le pipeline `campaigns/` en aval (section 12).

## 7bis. Désambiguïsation des marques ajoutées en extension

Même méthode que pour CBC ci-dessus, appliquée systématiquement aux six
banques ajoutées lors de l'extension multi-banques
(`collectors/term_resolver.py`, phase 1A) : pour chaque marque, les topics
Knowledge Graph renvoyés par `pytrends.suggestions()` sont testés **dans le
même appel** que les chaînes brutes candidates, sous la même normalisation,
puis comparés en couverture (points non nuls / points totaux) et en
moyenne.

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

Les trois marques ambiguës hors contexte bancaire (`BNP` = groupe français,
`Argenta` = commune italienne, `N26` = route régionale Leuven–Mechelen)
passent par un topic ; les trois marques non ambiguës gardent une chaîne
brute, cohérente avec le traitement existant de `KBC` et `ING`.

**Contrôle informatif sur l'existant** (ne modifie rien) : la chaîne `ING`
(couverture 1.000, moyenne 59.3) fait jeu égal avec son topic `/m/01hlqz`
"Groupe ING" (1.000, 58.1) ; la chaîne `KBC` (1.000, 63.7) est même plus
couvrante que ses deux topics. Aucun changement n'est donc justifié.

## 7ter. Chaînage et part de voix (`analysis/share_of_search.py`)

C'est le cœur du recentrage de périmètre : comparer 9 banques alors
qu'une requête pytrends est limitée à 5 termes.

**Principe** : `ING` et `KBC` apparaissent, chaîne strictement identique,
dans les 3 fiches marque. Comme les valeurs 0-100 d'une fiche sont
normalisées par rapport au pic de *cette* requête, la même chaîne `ING`
peut avoir une valeur légèrement différente d'une fiche à l'autre (l'autre
contenu de la requête change le pic de normalisation) — c'est justement ce
qui permet de calculer un facteur de correction :

1. `marque_generique` est la fiche de référence (`config.
   SHARE_OF_SEARCH_REFERENCE_FICHE`) — ses valeurs `ING`/`KBC`/`CBC` sont
   prises telles quelles, sans rescaling.
2. Pour chaque autre fiche marque (`marque_generique_traditionnelles`,
   `marque_generique_neobanques`) :
   `facteur = (moyenne(ING_référence) + moyenne(KBC_référence)) /
   (moyenne(ING_fiche) + moyenne(KBC_fiche))`, moyennes calculées sur les
   262 semaines communes. La somme des deux ancres (pas une seule) amortit
   le bruit d'une ancre proche de zéro une semaine donnée.
3. Chaque terme non-ancre de cette fiche (ex. BNPPF, Argenta, Crelan) est
   multiplié par ce facteur unique, semaine par semaine :
   `valeur_rescalée(t) = valeur_brute(t) × facteur`.
4. Résultat : les 9 banques sur une échelle hebdomadaire commune, stockée
   dans `brand_share_of_search`.
5. Part de voix hebdomadaire : `part(banque, t) = valeur_rescalée(banque,
   t) / somme_9_banques(t)` — les parts d'une même semaine somment
   toujours à 1.0 (vérifié).
6. Part de voix agrégée (métrique phare, calculée à l'affichage/export, pas
   stockée) : `somme_t(valeur_rescalée) / somme_t(somme_9_banques)` — la
   somme des valeurs sur toute la période, pas une moyenne simple des
   parts hebdomadaires, pour ne pas sur-pondérer les semaines à volume
   total quasi nul.

**Limite à connaître** : cette technique de chaînage suppose que le ratio
d'échelle entre deux requêtes pytrends reste stable sur toute la période —
hypothèse standard de cette méthode (largement utilisée pour contourner la
limite de 5 termes de Google Trends), mais approximative : elle ne capture
pas une éventuelle dérive du facteur d'échelle dans le temps.

Résultat observé (part de voix agrégée sur 5 ans, run du 2026-09-21) : KBC
28.4 %, ING 24.2 %, BNPPF 20.5 %, Argenta 12.2 %, Crelan 9.4 %, CBC 2.7 %,
Revolut 2.2 %, N26 0.4 %, bunq 0.0 %. Facteurs d'échelle observés très
proches de 1.0 (≈1.0047 pour les deux fiches pont) : `ING`/`KBC` sont les
termes dominants dans les 3 fiches, donc peu sensibles au reste du contenu
de la requête — signe que le chaînage introduit ici une correction mineure,
pas une extrapolation hasardeuse.

## 8. Visualisation (`app.py`, Streamlit)

`streamlit run app.py` (port par défaut 8501). Lecture seule sur
`trends_data`, `term_validation` et `brand_share_of_search`,
via `@st.cache_data`.

**Navigation** : sélecteur « Comparaison » dans la barre latérale. Options,
dans l'ordre : KBC (valeur par défaut), CBC, BNP Paribas Fortis, Argenta,
Crelan, Revolut, N26, bunq, « Marques », « Part de voix ».

- Chaque option par banque affiche, en onglets, les fiches marque qui
  contiennent cette banque (1 fiche pour la plupart, jusqu'à 3 pour KBC qui
  apparaît dans les 3 comme ancre). ING n'a pas d'option propre : c'est
  l'ancre commune de toutes les fiches.
- « Marques » affiche les 3 fiches marque sans filtre par banque.
- **« Part de voix »** est la vue dédiée au share of search (section 7ter) :
  un graphique multi-lignes des 9 banques sur l'échelle commune rescalée
  (couleurs distinctes par banque, `BANK_COLOR` — le style de trait par
  banque `BANK_DASH` des autres onglets ne suffit plus puisque les 9
  banques apparaissent ensemble ici), un tableau de part de voix agrégée,
  le détail des facteurs d'échelle appliqués, et les lignes verticales
  `config.KNOWN_EVENTS`.

Dans les onglets par fiche (hors « Part de voix »), chaque graphique
affiche : une courbe par terme (style de trait par banque), les lignes verticales
`KNOWN_EVENTS` des banques présentes, et sous le graphique la mention des
termes flaggés (`selected_low_coverage`, `broad_fallback`, `asymmetric`,
`ambiguous_string`, lus dans `term_validation`) et
un tableau de données brutes filtrable.

Libellés : `display_term()` et `display_bank()`, dupliqués à l'identique
dans `app.py` et `export/export_common.py`. Aucune écriture en base depuis
cette app — purement consultatif.

## 9. Export (`export/`)

**Un seul export**, `export_brand_notoriety.py` (les 9 exports par banque
+ l'export global de l'ancienne ère produit ont été supprimés avec le
recentrage — il n'y a plus de données produit par banque à exporter
séparément) :

| Script | Sorties |
|---|---|
| `export_brand_notoriety.py` | `brand_trends_data.csv`, `brand_share_of_search.csv`, `brand_notoriety_export.md` |

Le `.md` contient : méthodologie (source, granularité, **chaînage/share of
search et sa limite**, renvoi à la
désambiguïsation des marques), la section « Événements structurels
connus », les 3 fiches marque avec leurs termes, la **part de voix agrégée
par banque** et les facteurs d'échelle appliqués, et un tableau complet des
part de voix agrégée par banque.

Les deux CSV : `brand_trends_data.csv` est la table `trends_data` brute,
filtrée aux 3 fiches marque (3406 lignes) ; `brand_share_of_search.csv` est
le détail hebdomadaire de `brand_share_of_search` (2358 lignes = 9 banques
× 262 semaines), utile pour tracer l'évolution de la part de voix dans le
temps sans repasser par SQLite.

## 10. Comment tout relancer depuis zéro

```bash
cd kbc-ing-benchmark
pip install -r requirements.txt

python collectors/trends_collector.py      # déjà tout collecté ; ne fait rien
                                            # tant que config.PRODUCTS ne change pas
python analysis/share_of_search.py         # quelques secondes

python export/export_brand_notoriety.py

python campaigns/scoring.py                # obligatoire : régénère les
python campaigns/reports.py                # correspondances

streamlit run app.py                       # UI sur http://localhost:8501
```

`collectors/term_resolver.py` (résolution de nouveaux termes de marque,
1-3h, reprenable) ne sert que si une marque doit être re-résolue ou
qu'une banque est ajoutée — voir sa docstring et
`data/term_validation_report.md` pour le protocole complet.

Pour ajouter une fiche marque ou modifier un terme : éditer
`config.PRODUCTS`, relancer `trends_collector.py` (skip automatique de ce
qui existe déjà), puis `share_of_search.py`,
l'export et la régénération `campaigns/`.

## 11. Pièges connus (déjà rencontrés, à ne pas re-découvrir)

- **Encodage console Windows** : les caractères accentués s'affichent
  parfois comme `�` dans un terminal Git Bash/PowerShell. Les données
  elles-mêmes sont en UTF-8 correct en base — uniquement un problème
  d'affichage terminal.
- **`pytrends.suggestions()` et bare strings pour des noms de marque
  courts/ambigus** : toujours vérifier la désambiguïsation Knowledge Graph
  avant d'ajouter un nouveau terme de marque (section 7bis).
- **Limite pytrends de 5 termes/requête** : c'est la raison d'être du
  chaînage de la section 7ter. Toute nouvelle banque à ajouter doit être
  pensée en termes de fiche pont (avec ING+KBC comme ancre), pas comme un
  6ᵉ terme dans une fiche déjà pleine.
- **Volume de recherche réel des termes produit** : constat qui a motivé le
  recentrage de périmètre. Sur les 43 fiches produit testées lors de
  l'extension multi-banques, 33 ont été intégralement rejetées : une fois
  normalisé face au volume de recherche d'ING dans la même requête, le
  volume des termes produit des nouvelles banques est presque
  systématiquement écrasé à 0. Le niveau marque, en comparaison, a un
  volume bien plus robuste pour les 9 banques (section 7ter).
- **Données orphelines des anciennes fiches produit** : `trends_data` et
  contient encore les lignes des 29 fiches produit
  retirées de `config.PRODUCTS` lors du recentrage — volontairement
  conservées (pas de `DELETE`), mais invisibles depuis `app.py` et
  `export/` (qui filtrent sur `config.PRODUCTS` ou sur les 3 `product_id`
  en vigueur). Ne pas s'étonner de leur présence si on interroge
  `trends_data` directement en SQL.
- **Chaînage et normalisation** : la couverture ou la valeur d'un terme se
  mesure toujours dans la composition réelle de sa fiche pytrends — jamais
  en comparant directement des valeurs brutes entre deux fiches
  différentes sans passer par le facteur d'échelle de la section 7ter.
- **`ON CONFLICT` vs suppression complète** : `trends_data` et `products`
  utilisent un upsert. `brand_share_of_search` est
  entièrement vidées et régénérées à chaque run de leur script respectif.
- **Forcer la re-résolution d'un terme de marque** : le résolveur saute
  toute fiche ayant déjà sa ligne-marqueur `__done__` dans
  `term_validation`. Pour la retester, supprimer ses lignes
  `term_validation`, exactement comme on supprime des lignes `trends_data`
  pour forcer une recollecte.

## 12. Audit `campaigns/` : disponibilité pour les six nouvelles banques

**`campaigns/` est orphelin depuis le retrait de la détection d'anomalies.**
Tout ce module était construit sur la table supprimée : il ne peut plus
tourner en l'état. Aucune ligne n'en a été modifiée — le code reste sur
disque en attendant une décision (le retirer, ou le reconstruire sur une
autre base). L'audit ci-dessous date de l'extension multi-banques et reste
la description de ce qu'il faudrait reprendre : `campaigns/` a été
construit pour 3 banques (KBC, CBC, ING) et n'est **pas prêt** pour BNPPF,
Argenta, Crelan, Revolut, N26 ou bunq :

- **`db/schema.sql`, table `campaigns`** : `bank TEXT NOT NULL CHECK (bank
  IN ('KBC', 'CBC', 'ING'))`. Tout `INSERT` d'une campagne pour une des six
  nouvelles banques échoue immédiatement, avant même d'atteindre le code
  Python.
- **`campaigns/seed_data.py`** : catalogue saisi à la main, exclusivement
  KBC/CBC/ING.
- **`campaigns/reports.py`** : `BANK_ORDER = ["KBC", "CBC", "ING"]` pilote
  toutes les sections par banque et le comparatif agrégé.
- **`campaigns/app.py`** : `BANK_COLOR = {"KBC": ..., "CBC": ..., "ING":
  ...}` et les onglets construits à partir de `BANK_ORDER`. Étendre
  `BANK_ORDER` sans étendre `BANK_COLOR` en parallèle ferait échouer l'app
  sur un `KeyError`.
- **`campaigns/load_campaigns.py`** : la ligne de log de fin de chargement
  compte explicitement KBC/CBC/ING.
- **`campaigns/scoring.py`** : `find_matches()` gère déjà correctement une
  nouvelle banque comme groupe singleton, mais `camp()` (utilisée par
  `is_seasonal_confound`) a un **bug latent** : `return {"KBC", "CBC"} if
  bank in ("KBC", "CBC") else {"ING"}` renvoie `{"ING"}` au lieu de
  `{bank}` pour toute banque hors KBC/CBC — mélangerait silencieusement le
  contrôle de confond saisonnier d'une nouvelle banque avec celui d'ING si
  une campagne existait un jour pour elle.
- `MARQUE_GENERIQUE_FICHE = "marque_generique"` (case spéciale existante
  dans `scoring.py`, antérieure à toute extension) ne référence que la
  fiche marque d'origine, pas `marque_generique_traditionnelles` ni
  `marque_generique_neobanques`.

## 13. Ce qui n'est PAS dans ce pipeline

- Aucune collecte de données publicitaires (Meta Ad Library, Google Ads
  Transparency Center, presse) — volontairement hors périmètre.
- Toute comparaison au niveau produit (compte à vue, carte de crédit, app
  mobile...) est **hors périmètre depuis le recentrage** : le projet ne
  compare plus que la notoriété de marque. Les anciennes fiches produit
  restent en base à titre historique (section 11) mais ne sont plus
  alimentées ni affichées.
- La détection d'anomalies a été retirée du pipeline : plus de seuils, plus
  de table, plus de section d'export. Ce niveau de lecture appartenait à une
  version antérieure ; le pipeline rapporte désormais la part de voix et son
  évolution. `campaigns/`, qui reposait entièrement dessus, est orphelin
  (section 12).
