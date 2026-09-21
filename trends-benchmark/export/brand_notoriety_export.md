# Export notoriété de marque — Benchmark ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Le projet compare uniquement la notoriété de marque (recherche du nom de banque, sans contexte produit) des 9 banques du panel : ING, KBC, CBC, BNP Paribas Fortis, Argenta, Crelan, Revolut, N26, bunq.

## Méthodologie

- **Source Google Trends** : bibliothèque `pytrends`, geo=`BE`, timeframe=`today 5-y`.
- **Granularité réelle** : hebdomadaire (Google Trends bascule automatiquement en hebdomadaire pour une fenêtre de 5 ans, pas mensuel).
- **Chaînage / share of search** : les 9 banques sont réparties sur 3 fiches (`marque_generique`, `marque_generique_traditionnelles`, `marque_generique_neobanques`), limite pytrends de 5 termes par requête oblige. `ING` et `KBC` apparaissent, inchangés, dans les 3 requêtes : ils servent d'ancre commune. Pour chaque fiche autre que la référence (`marque_generique`), un facteur d'échelle unique est calculé sur la moyenne des deux ancres, puis appliqué à ses autres termes (voir `analysis/share_of_search.py`). La part de voix se calcule ensuite sur le volume rescalé : `part(banque) = volume_rescalé(banque) / somme_9_banques`, sur la somme des valeurs de toute la période (pas une moyenne des parts hebdomadaires, pour ne pas sur-pondérer les semaines à volume quasi nul).
- **Limite du chaînage** : cette technique suppose que le ratio d'échelle entre deux requêtes pytrends reste stable sur toute la période - hypothèse standard de cette méthode, mais approximative.
- **Détection d'anomalies** (par terme) : moyenne d'intérêt calculée par mois calendaire sur toutes les années disponibles (profil de saisonnalité de référence). Un point est flagué s'il dépasse à la fois (a) la moyenne générale du terme de plus de 1.5 écart-type (z-score ≥ 1.5) et (b) 1.3× la moyenne saisonnière normale de son mois. Les points flagués consécutifs sont groupés : un seul point isolé est un **pic isolé** (`isolated_spike`), deux points consécutifs ou plus sont une **tendance soutenue** (`sustained_trend`).
- **Désambiguïsation des marques** (BNPPF, Argenta, N26 passent par un topic Knowledge Graph plutôt qu'une chaîne brute) : voir `data/term_validation_report.md` et `docs/pipeline_google_trends.md` section 7bis.
- **Hors périmètre** : ce projet ne collecte aucune donnée publicitaire (Meta Ad Library, Google Ads Transparency Center). Le rapprochement entre ces anomalies et des campagnes publicitaires réelles est fait dans un pipeline séparé, en utilisant cet export comme donnée d'entrée.

## Événements structurels connus

Ruptures de marché documentées, fournies pour interprétation : elles produisent des anomalies attendues qui ne sont pas des campagnes publicitaires. Cette liste n'intervient jamais dans la détection.

| Date | Banque | Événement |
|---|---|---|
| 2024-01-22 | BNP Paribas Fortis | Intégration de bpost banque (environ 1 million de clients migrés) |
| 2024-03-14 | N26 | Lancement du compte épargne en Belgique |
| 2024-06-10 | Crelan | Fusion avec AXA Bank Belgium, migration IT d'environ 840 000 clients (week-end des 8 et 9 juin) |
| 2024-12-17 | bunq | bunq Stocks disponible en Belgique |
| 2025-05-01 | Revolut | Comptes belges (IBAN BE) pour les nouveaux clients, migration des clients existants au cours de 2025 |
| 2025-08-21 | Revolut | Lancement du compte épargne à intérêts versés quotidiennement (date de couverture presse) |
| 2026-07-24 | bunq | Lancement des IBAN belges et de Wero en Belgique (date de couverture presse) |

## Fiches marque

| Fiche | Termes de recherche (banque) |
|---|---|
| Marque (recherche générique) (`marque_generique`) | KBC (KBC), ING (ING), CBC Banque & Assurance (CBC) |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | ING (ING), KBC (KBC), BNP Paribas Fortis (BNP Paribas Fortis), Argenta (Argenta), Crelan (Crelan) |
| Marques — néobanques (`marque_generique_neobanques`) | ING (ING), KBC (KBC), Revolut (Revolut), N26 (N26), bunq (bunq) |
| Marques — banques traditionnelles (2) (`marque_generique_traditionnelles_2`) | ING (ING), KBC (KBC), Belfius (Belfius), Beobank (Beobank), VDK Bank (VDK Bank) |
| Marques — banques digitales sans réseau d'agences (`marque_generique_digitales`) | ING (ING), KBC (KBC), Hello bank! (Hello bank!), Keytrade Bank (Keytrade Bank) |

## Part de voix (share of search)

Part de chaque banque sur le volume de recherche total du panel des 9 banques, sur l'ensemble de la période. Détail hebdomadaire dans **`brand_share_of_search.csv`**.

| Banque | Part de voix |
|---|---|
| KBC | 21.3% |
| Belfius | 18.4% |
| ING | 18.2% |
| BNP Paribas Fortis | 15.4% |
| Argenta | 9.2% |
| Crelan | 7.1% |
| Beobank | 4.5% |
| CBC | 2.1% |
| Revolut | 1.6% |
| VDK Bank | 1.2% |
| Keytrade Bank | 0.4% |
| Hello bank! | 0.4% |
| N26 | 0.3% |
| bunq | 0.0% |

Facteurs d'échelle appliqués (chaînage vers `marque_generique`) :

| Fiche source | Facteur |
|---|---|
| marque_generique | 1.0000 |
| marque_generique_digitales | 0.9993 |
| marque_generique_neobanques | 1.0047 |
| marque_generique_traditionnelles | 1.0047 |
| marque_generique_traditionnelles_2 | 0.9993 |

## Données Google Trends brutes

5764 points hebdomadaires, du 2021-09-12 au 2026-09-20. Fournies séparément dans **`brand_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) et, sous forme rescalée avec part de voix, dans **`brand_share_of_search.csv`** (3668 lignes) - non incluses ici pour garder ce document lisible.

## Anomalies détectées (262)

| Fiche | Terme | Banque | Date | Valeur | Type d'anomalie | Score de déviation | Flags du terme |
|---|---|---|---|---|---|---|---|
| marque_generique | ING | ING | 2021-09-26 | 77 | Pic isolé | 2.698 |  |
| marque_generique_digitales | ING | ING | 2021-09-26 | 74 | Pic isolé | 2.418 |  |
| marque_generique_neobanques | ING | ING | 2021-09-26 | 76 | Pic isolé | 2.67 |  |
| marque_generique_traditionnelles | ING | ING | 2021-09-26 | 76 | Pic isolé | 2.67 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2021-09-26 | 74 | Pic isolé | 2.418 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-10-17 | 8 | Pic isolé | 2.008 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-10-31 | 8 | Pic isolé | 2.008 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2021-11-14 | 2 | Pic isolé | 1.875 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-11-28 | 8 | Pic isolé | 2.008 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-12-12 | 8 | Tendance soutenue | 2.008 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2021-12-12 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2021-12-12 | 72 | Pic isolé | 2.82 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-12-19 | 8 | Tendance soutenue | 2.008 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-12-26 | 8 | Tendance soutenue | 2.008 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2021-12-26 | 66 | Tendance soutenue | 2.175 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-01-02 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2022-01-02 | 2 | Pic isolé | 1.875 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-01-02 | 70 | Tendance soutenue | 2.605 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-01-09 | 9 | Tendance soutenue | 3.084 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-01-09 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique | CBC Banque & Assurance | CBC | 2022-01-16 | 9 | Tendance soutenue | 3.084 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-01-23 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique | CBC Banque & Assurance | CBC | 2022-01-30 | 9 | Pic isolé | 3.084 |  |
| marque_generique | ING | ING | 2022-01-30 | 78 | Pic isolé | 2.816 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-01-30 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | ING | ING | 2022-01-30 | 74 | Pic isolé | 2.418 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-01-30 | 69 | Pic isolé | 2.497 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2022-01-30 | 74 | Pic isolé | 2.418 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-02-06 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique | ING | ING | 2022-02-27 | 75 | Pic isolé | 2.462 |  |
| marque_generique_digitales | ING | ING | 2022-02-27 | 74 | Pic isolé | 2.418 |  |
| marque_generique_neobanques | ING | ING | 2022-02-27 | 76 | Pic isolé | 2.67 |  |
| marque_generique_neobanques | bunq | bunq | 2022-02-27 | 1 | Pic isolé | 5.302 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-02-27 | 63 | Tendance soutenue | 1.852 |  |
| marque_generique_traditionnelles | ING | ING | 2022-02-27 | 76 | Pic isolé | 2.67 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2022-02-27 | 74 | Pic isolé | 2.418 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-06 | 62 | Tendance soutenue | 1.745 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-20 | 61 | Tendance soutenue | 1.637 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-27 | 63 | Tendance soutenue | 1.852 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-04-03 | 8 | Pic isolé | 2.008 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-04-03 | 64 | Tendance soutenue | 1.96 |  |
| marque_generique_neobanques | N26 | N26 | 2022-04-24 | 5 | Pic isolé | 9.316 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-04-24 | 73 | Tendance soutenue | 2.927 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-05-01 | 8 | Pic isolé | 2.008 |  |
| marque_generique | ING | ING | 2022-05-01 | 69 | Pic isolé | 1.754 |  |
| marque_generique_digitales | ING | ING | 2022-05-01 | 70 | Pic isolé | 1.93 |  |
| marque_generique_neobanques | ING | ING | 2022-05-01 | 73 | Pic isolé | 2.306 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-05-01 | 62 | Tendance soutenue | 1.745 |  |
| marque_generique_traditionnelles | ING | ING | 2022-05-01 | 73 | Pic isolé | 2.306 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2022-05-01 | 70 | Pic isolé | 1.93 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2022-05-22 | 5 | Pic isolé | 2.141 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-05-29 | 60 | Tendance soutenue | 1.53 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-05 | 60 | Tendance soutenue | 1.53 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-06-12 | 8 | Pic isolé | 2.008 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-12 | 61 | Tendance soutenue | 1.637 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-19 | 62 | Tendance soutenue | 1.745 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-06-26 | 8 | Pic isolé | 2.008 |  |
| marque_generique | KBC | KBC | 2022-06-26 | 82 | Tendance soutenue | 2.085 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-06-26 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_digitales | ING | ING | 2022-06-26 | 68 | Pic isolé | 1.687 |  |
| marque_generique_neobanques | KBC | KBC | 2022-06-26 | 78 | Tendance soutenue | 1.732 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-26 | 68 | Tendance soutenue | 2.39 |  |
| marque_generique_traditionnelles | KBC | KBC | 2022-06-26 | 78 | Tendance soutenue | 1.732 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2022-06-26 | 68 | Pic isolé | 1.687 |  |
| marque_generique | ING | ING | 2022-07-03 | 69 | Pic isolé | 1.754 |  |
| marque_generique | KBC | KBC | 2022-07-03 | 81 | Tendance soutenue | 1.972 |  |
| marque_generique_neobanques | ING | ING | 2022-07-03 | 68 | Pic isolé | 1.7 |  |
| marque_generique_neobanques | KBC | KBC | 2022-07-03 | 83 | Tendance soutenue | 2.317 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-03 | 69 | Tendance soutenue | 2.497 |  |
| marque_generique_traditionnelles | ING | ING | 2022-07-03 | 68 | Pic isolé | 1.7 |  |
| marque_generique_traditionnelles | KBC | KBC | 2022-07-03 | 83 | Tendance soutenue | 2.317 |  |
| marque_generique_traditionnelles_2 | Belfius | Belfius | 2022-07-03 | 75 | Pic isolé | 3.135 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-10 | 61 | Tendance soutenue | 1.637 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-07-31 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-31 | 69 | Tendance soutenue | 2.497 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-08-07 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-07 | 66 | Tendance soutenue | 2.175 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-21 | 62 | Tendance soutenue | 1.745 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-28 | 64 | Tendance soutenue | 1.96 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-04 | 63 | Tendance soutenue | 1.852 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-11 | 62 | Tendance soutenue | 1.745 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-18 | 65 | Tendance soutenue | 2.067 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-25 | 63 | Tendance soutenue | 1.852 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2022-10-02 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_traditionnelles_2 | Belfius | Belfius | 2022-11-13 | 71 | Pic isolé | 2.507 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2022-11-20 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2022-11-27 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2022-11-27 | 5 | Pic isolé | 2.141 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2022-12-18 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-02-19 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | bunq | bunq | 2023-04-02 | 1 | Pic isolé | 5.302 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2023-07-02 | 7 | Pic isolé | 5.412 |  |
| marque_generique | KBC | KBC | 2023-08-20 | 83 | Tendance soutenue | 2.198 |  |
| marque_generique_digitales | KBC | KBC | 2023-08-20 | 84 | Tendance soutenue | 2.385 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-08-20 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | KBC | KBC | 2023-08-20 | 86 | Tendance soutenue | 2.667 |  |
| marque_generique_traditionnelles | Argenta | Argenta | 2023-08-20 | 62 | Tendance soutenue | 9.206 |  |
| marque_generique_traditionnelles | KBC | KBC | 2023-08-20 | 86 | Tendance soutenue | 2.667 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2023-08-20 | 5 | Tendance soutenue | 2.141 |  |
| marque_generique_traditionnelles_2 | Beobank | Beobank | 2023-08-20 | 18 | Tendance soutenue | 2.945 |  |
| marque_generique_traditionnelles_2 | KBC | KBC | 2023-08-20 | 84 | Tendance soutenue | 2.385 |  |
| marque_generique | ING | ING | 2023-08-27 | 71 | Pic isolé | 1.99 |  |
| marque_generique | KBC | KBC | 2023-08-27 | 90 | Tendance soutenue | 2.989 |  |
| marque_generique_digitales | ING | ING | 2023-08-27 | 71 | Pic isolé | 2.052 |  |
| marque_generique_digitales | KBC | KBC | 2023-08-27 | 93 | Tendance soutenue | 3.439 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-08-27 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | ING | ING | 2023-08-27 | 69 | Pic isolé | 1.821 |  |
| marque_generique_neobanques | KBC | KBC | 2023-08-27 | 94 | Tendance soutenue | 3.603 |  |
| marque_generique_traditionnelles | Argenta | Argenta | 2023-08-27 | 52 | Tendance soutenue | 6.556 |  |
| marque_generique_traditionnelles | ING | ING | 2023-08-27 | 69 | Pic isolé | 1.821 |  |
| marque_generique_traditionnelles | KBC | KBC | 2023-08-27 | 94 | Tendance soutenue | 3.603 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2023-08-27 | 5 | Tendance soutenue | 2.141 |  |
| marque_generique_traditionnelles_2 | Belfius | Belfius | 2023-08-27 | 76 | Pic isolé | 3.291 |  |
| marque_generique_traditionnelles_2 | Beobank | Beobank | 2023-08-27 | 19 | Tendance soutenue | 3.571 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2023-08-27 | 71 | Pic isolé | 2.052 |  |
| marque_generique_traditionnelles_2 | KBC | KBC | 2023-08-27 | 93 | Tendance soutenue | 3.439 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-09-24 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-10-01 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-10-08 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-10-22 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-11-26 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-12-03 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-12-10 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2023-12-31 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2023-12-31 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-01-07 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-01-07 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-01-21 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2024-01-21 | 81 | Pic isolé | 3.787 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-01-28 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-01-28 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-02-25 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-03-03 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-03-17 | 2 | Pic isolé | 1.875 |  |
| marque_generique | ING | ING | 2024-03-24 | 90 | Pic isolé | 4.233 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-03-24 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_digitales | ING | ING | 2024-03-24 | 87 | Pic isolé | 4.001 |  |
| marque_generique_neobanques | ING | ING | 2024-03-24 | 87 | Pic isolé | 4.002 |  |
| marque_generique_traditionnelles | ING | ING | 2024-03-24 | 87 | Pic isolé | 4.002 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2024-03-24 | 87 | Pic isolé | 4.001 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-04-07 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-04-07 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-05-05 | 2 | Pic isolé | 1.875 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-09 | 50 | Tendance soutenue | 4.965 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-16 | 38 | Tendance soutenue | 2.912 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-23 | 34 | Tendance soutenue | 2.228 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-30 | 34 | Tendance soutenue | 2.228 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-07-07 | 32 | Tendance soutenue | 1.886 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-07-14 | 32 | Tendance soutenue | 1.886 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-08-04 | 2 | Pic isolé | 1.875 |  |
| marque_generique | ING | ING | 2024-08-25 | 73 | Tendance soutenue | 2.226 |  |
| marque_generique_digitales | ING | ING | 2024-08-25 | 72 | Tendance soutenue | 2.174 |  |
| marque_generique_neobanques | ING | ING | 2024-08-25 | 74 | Tendance soutenue | 2.427 |  |
| marque_generique_traditionnelles | ING | ING | 2024-08-25 | 74 | Tendance soutenue | 2.427 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2024-08-25 | 5 | Tendance soutenue | 2.141 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2024-08-25 | 72 | Tendance soutenue | 2.174 |  |
| marque_generique | CBC Banque & Assurance | CBC | 2024-09-01 | 9 | Pic isolé | 3.084 |  |
| marque_generique | ING | ING | 2024-09-01 | 82 | Tendance soutenue | 3.288 |  |
| marque_generique | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.12 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-09-01 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_digitales | ING | ING | 2024-09-01 | 74 | Tendance soutenue | 2.418 |  |
| marque_generique_digitales | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.259 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-09-01 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | ING | ING | 2024-09-01 | 74 | Tendance soutenue | 2.427 |  |
| marque_generique_neobanques | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.304 |  |
| marque_generique_traditionnelles | Argenta | Argenta | 2024-09-01 | 45 | Pic isolé | 4.7 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-09-01 | 38 | Tendance soutenue | 2.912 |  |
| marque_generique_traditionnelles | ING | ING | 2024-09-01 | 74 | Tendance soutenue | 2.427 |  |
| marque_generique_traditionnelles | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.304 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2024-09-01 | 6 | Tendance soutenue | 3.776 |  |
| marque_generique_traditionnelles_2 | Belfius | Belfius | 2024-09-01 | 90 | Pic isolé | 5.487 |  |
| marque_generique_traditionnelles_2 | ING | ING | 2024-09-01 | 74 | Tendance soutenue | 2.418 |  |
| marque_generique_traditionnelles_2 | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.259 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-09-08 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-09-08 | 33 | Tendance soutenue | 2.057 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-09-29 | 30 | Pic isolé | 1.544 |  |
| marque_generique_traditionnelles_2 | Belfius | Belfius | 2024-10-27 | 88 | Pic isolé | 5.174 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2024-11-03 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-11-03 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-11-17 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-12-01 | 2 | Pic isolé | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-12-15 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | bunq | bunq | 2024-12-15 | 1 | Pic isolé | 5.302 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-12-15 | 32 | Pic isolé | 1.886 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-12-22 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2024-12-29 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-12-29 | 30 | Pic isolé | 1.544 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2024-12-29 | 5 | Pic isolé | 2.141 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-01-05 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-01-26 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | bunq | bunq | 2025-03-16 | 1 | Pic isolé | 5.302 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-03-23 | 31 | Tendance soutenue | 1.715 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-03-30 | 33 | Tendance soutenue | 2.057 |  |
| marque_generique_neobanques | bunq | bunq | 2025-05-25 | 1 | Pic isolé | 5.302 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-06-29 | 32 | Tendance soutenue | 1.886 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2025-07-06 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-07-06 | 32 | Tendance soutenue | 1.886 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2025-07-27 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-08-03 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-08-17 | 12 | Tendance soutenue | 2.742 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-08-24 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2025-08-31 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-08-31 | 2 | Pic isolé | 1.875 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2025-08-31 | 5 | Pic isolé | 2.141 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2025-09-07 | 2 | Tendance soutenue | 3.079 | ambiguous_string |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-09-14 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | bunq | bunq | 2025-09-14 | 1 | Pic isolé | 5.302 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-09-21 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-09-28 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-10-12 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-11-02 | 9 | Pic isolé | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-11-23 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | bunq | bunq | 2025-11-23 | 1 | Pic isolé | 5.302 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-11-30 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-12-07 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-12-14 | 9 | Pic isolé | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2025-12-28 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-12-28 | 9 | Pic isolé | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-01-11 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-01-18 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-01-25 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-02-01 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | bunq | bunq | 2026-02-15 | 1 | Pic isolé | 5.302 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-03-08 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-03-15 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-03-15 | 10 | Tendance soutenue | 1.976 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-03-22 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-03-22 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-03-29 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-04-05 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-04-12 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-04-19 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-05-03 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-03 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-05-10 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-10 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2026-05-10 | 5 | Tendance soutenue | 2.141 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-05-17 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-17 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2026-05-17 | 5 | Tendance soutenue | 2.141 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-05-24 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2026-05-24 | 5 | Tendance soutenue | 2.141 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-31 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-06-07 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-06-07 | 10 | Tendance soutenue | 1.976 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-06-14 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-06-21 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-06-28 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-07-05 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-07-05 | 9 | Pic isolé | 1.593 |  |
| marque_generique_traditionnelles_2 | VDK Bank | VDK Bank | 2026-07-05 | 5 | Pic isolé | 2.141 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-07-12 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-07-19 | 2 | Tendance soutenue | 1.875 |  |
| marque_generique_neobanques | bunq | bunq | 2026-07-26 | 1 | Pic isolé | 5.302 |  |
| marque_generique_digitales | Keytrade Bank | Keytrade Bank | 2026-08-02 | 2 | Pic isolé | 1.875 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-02 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-09 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-16 | 10 | Tendance soutenue | 1.976 |  |
| marque_generique_digitales | Hello bank! | Hello bank! | 2026-08-23 | 2 | Pic isolé | 3.079 | ambiguous_string |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-30 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-09-06 | 9 | Tendance soutenue | 1.593 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-09-13 | 19 | Tendance soutenue | 5.424 |  |
