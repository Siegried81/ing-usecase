# Export notoriété de marque — Benchmark ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Le projet compare uniquement la notoriété de marque (recherche du nom de banque, sans contexte produit) des 9 banques du panel : ING, KBC, CBC, BNP Paribas Fortis, Argenta, Crelan, Revolut, N26, bunq.

## Méthodologie

- **Source Google Trends** : bibliothèque `pytrends`, geo=`BE`, timeframe=`today 5-y`.
- **Granularité réelle** : hebdomadaire (Google Trends bascule automatiquement en hebdomadaire pour une fenêtre de 5 ans, pas mensuel).
- **Chaînage / share of search** : les 9 banques sont réparties sur 3 fiches (`marque_generique`, `marque_generique_traditionnelles`, `marque_generique_neobanques`), limite pytrends de 5 termes par requête oblige. `ING` et `KBC` apparaissent, inchangés, dans les 3 requêtes : ils servent d'ancre commune. Pour chaque fiche autre que la référence (`marque_generique`), un facteur d'échelle unique est calculé sur la moyenne des deux ancres, puis appliqué à ses autres termes (voir `analysis/share_of_search.py`). La part de voix se calcule ensuite sur le volume rescalé : `part(banque) = volume_rescalé(banque) / somme_9_banques`, sur la somme des valeurs de toute la période (pas une moyenne des parts hebdomadaires, pour ne pas sur-pondérer les semaines à volume quasi nul).
- **Limite du chaînage** : cette technique suppose que le ratio d'échelle entre deux requêtes pytrends reste stable sur toute la période - hypothèse standard de cette méthode, mais approximative.
- **Désambiguïsation des marques** (BNPPF, Argenta, N26 passent par un topic Knowledge Graph plutôt qu'une chaîne brute) : voir `data/term_validation_report.md` et `docs/pipeline_google_trends.md` section 7bis.
- **Hors périmètre** : ce projet ne collecte aucune donnée publicitaire (Meta Ad Library, Google Ads Transparency Center). Cet export mesure la part de voix de marque et son évolution, rien d'autre.

## Événements structurels connus

Ruptures de marché documentées, fournies pour interprétation : elles produisent des mouvements attendus qui ne sont pas des campagnes publicitaires. Cette liste n'intervient dans aucun calcul.

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
