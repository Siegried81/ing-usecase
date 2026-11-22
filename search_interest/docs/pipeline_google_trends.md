# Pipeline Google Trends : notoriété de marque ING vs concurrents

Pipeline autonome (config, base SQLite, app Streamlit propres). Il n'importe rien de
`src/comparator` ; le comparateur lit seulement `search_interest/export/` via
`src/comparator/trends.py`.

## 1. Objectif

Mesurer la notoriété de marque d'ING face à huit concurrents en Belgique via un
**share of search** : part de recherches de chaque banque sur le volume total du
panel de 9 banques. Traditionnelles : KBC, CBC, BNP Paribas Fortis, Argenta,
Crelan. Néobanques : Revolut, N26, bunq. CBC est la marque francophone de KBC
Group ; les deux sont traitées comme entités de recherche indépendantes.

Le périmètre a été recentré sur la marque (fiches produit retirées de
`config.PRODUCTS`) : les anciennes lignes restent en base mais aucune étape ne les lit.

## 2. Flux

```
config.py (3 fiches marque) → collectors/trends_collector.py (pytrends)
  → benchmark.db : trends_data (+ data/csv/*.csv)
  → analysis/share_of_search.py → table brand_share_of_search
  → app.py (Streamlit)  |  export/export_brand_notoriety.py
```

`benchmark.db` n'est pas versionnée (régénérée localement). `GEO = "BE"`,
`TIMEFRAME = "today 5-y"` : points hebdomadaires (262 par terme).

## 3. Collecte

Une fiche = un appel `build_payload` + `interest_over_time()` ; les valeurs 0-100
ne sont comparables qu'au sein d'un même appel. **Maximum 5 termes par fiche**
(limite pytrends), d'où 3 fiches : référence, traditionnelles, néobanques, avec
`ING` et `KBC` identiques dans les trois comme ancres.

Robustesse : séquentiel, pause de 60 s par fiche, backoff exponentiel sur 429
(5 essais, 30 s initiales), reprenable (une fiche déjà en base est sautée ; pour
changer ses termes, supprimer d'abord ses lignes `trends_data`).

## 4. Désambiguïsation des marques

Les chaînes courtes sont polluées (`CBC` capte CBC News, hémogramme...). Pour
chaque marque ambiguë, `collectors/term_resolver.py` teste les topics Knowledge
Graph de `pytrends.suggestions()` contre les chaînes brutes dans le même appel. Un
topic est retenu si son titre contient la marque, si son type est une banque ou
société, et si sa couverture atteint `BRAND_MIN_COVERAGE` (0.90). Sinon la chaîne la
plus spécifique est gardée avec le flag `ambiguous_string`.

Retenus comme topics : CBC (`/g/1z3t2x3c8`), BNPPF (`/m/07sc3dj`), Argenta
(`/m/03lmky`), N26 (`/g/11c1p5t9vb`). Chaînes brutes : ING, KBC, Crelan, Revolut,
bunq. `config.TERM_DISPLAY_LABELS` et `display_term()` donnent les libellés.

## 5. Chaînage et part de voix (`analysis/share_of_search.py`)

1. La fiche `marque_generique` est la référence, sans rescaling.
2. Pour chaque autre fiche : `facteur = (moy(ING_réf) + moy(KBC_réf)) / (moy(ING_fiche) + moy(KBC_fiche))`
   sur les semaines communes ; les termes non-ancres sont multipliés par ce facteur.
3. Part hebdomadaire = valeur rescalée / somme des 9 banques ; part agrégée =
   somme des valeurs / somme des totaux (pas une moyenne de parts).

Limite : le chaînage suppose un ratio d'échelle stable dans le temps.

## 6. Visualisation et export

`streamlit run app.py` (lecture seule) : un onglet par comparaison, plus « Marques »
et « Part de voix » (9 banques sur l'échelle commune, facteurs, événements
`config.KNOWN_EVENTS`). `export/export_brand_notoriety.py` écrit
`brand_trends_data.csv`, `brand_share_of_search.csv` et `brand_notoriety_export.md`
(méthodologie, parts agrégées, facteurs). Ces fichiers sont générés : ne pas les
éditer.

## 7. Relancer

```bash
cd search_interest
pip install -r requirements.txt
python collectors/trends_collector.py     # saute ce qui est déjà en base
python analysis/share_of_search.py
python export/export_brand_notoriety.py
streamlit run app.py                      # http://localhost:8501
```

Pour ajouter une marque ou un terme : éditer `config.PRODUCTS` en gardant
ING+KBC comme ancres, relancer la collecte, puis le chaînage et l'export.

## 8. Pièges

- Toujours vérifier la désambiguïsation Knowledge Graph avant d'ajouter un terme.
- Ne jamais comparer des valeurs brutes de deux fiches sans le facteur d'échelle.
- `trends_data` utilise un upsert ; `brand_share_of_search` est vidée et régénérée
  à chaque run.
- Pour forcer la re-résolution d'un terme, supprimer ses lignes `term_validation`.
- Les valeurs produit des nouvelles banques s'écrasent à 0 face au volume d'ING :
  raison du recentrage sur la marque.

## 9. Hors périmètre

Pas de données publicitaires, pas de niveau produit, pas de détection d'anomalies.
