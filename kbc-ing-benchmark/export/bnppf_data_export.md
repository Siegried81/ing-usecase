# Export des données BNP Paribas Fortis — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque BNP Paribas Fortis (code `BNPPF`, segment : traditionnelle).

## Méthodologie

- **Source Google Trends** : bibliothèque `pytrends`, geo=`BE`, timeframe=`today 5-y`.
- **Granularité réelle** : hebdomadaire (Google Trends bascule automatiquement en hebdomadaire pour une fenêtre de 5 ans, pas mensuel).
- **Détection d'anomalies** (par terme) : moyenne d'intérêt calculée par mois calendaire sur toutes les années disponibles (profil de saisonnalité de référence). Un point est flagué s'il dépasse à la fois (a) la moyenne générale du terme de plus de 1.5 écart-type (z-score ≥ 1.5) et (b) 1.3× la moyenne saisonnière normale de son mois. Les points flagués consécutifs sont groupés : un seul point isolé est un **pic isolé** (`isolated_spike`), deux points consécutifs ou plus sont une **tendance soutenue** (`sustained_trend`).
- **Hors périmètre** : ce projet ne collecte aucune donnée publicitaire (Meta Ad Library, Google Ads Transparency Center). Le rapprochement entre ces anomalies et des campagnes publicitaires réelles est fait dans un pipeline séparé, en utilisant cet export comme donnée d'entrée.
- **Sélection des termes (banques ajoutées en extension)** : pour chaque fiche, les termes ING de référence sont repris à l'identique, puis un terme par langue est choisi parmi une liste ordonnée de candidats testés en conditions réelles (même géographie, même période, même composition de fiche). Un candidat est retenu si sa couverture — points non nuls / points totaux — atteint 0.50 ; à défaut, le meilleur candidat observé est conservé s'il atteint le plancher de 0.25 (verdict `selected_low_coverage`), sinon le slot est supprimé.
- **Broad match** : un terme sans guillemets capte les recherches contenant tous ses mots, dans n'importe quel ordre ; ajouter un mot restreint le périmètre. Les candidats de repli sont donc volontairement de plus en plus larges, et un terme retenu à ce titre porte le flag `broad_fallback`.
- **Flags** : `selected_low_coverage` (série peu couverte, anomalies plus bruitées), `broad_fallback` (terme volontairement large), `asymmetric` (le terme retenu n'est pas la transposition exacte du terme ING, la comparaison n'est plus strictement symétrique), `ambiguous_string` (marque retenue sous forme de chaîne brute faute de topic Knowledge Graph valide).
- **Détail complet de la sélection** : voir `data/term_validation_report.md` et la table `term_validation` de `benchmark.db` (un enregistrement par candidat testé).

## Événements structurels connus

Ruptures de marché documentées, fournies pour interprétation : elles produisent des anomalies attendues qui ne sont pas des campagnes publicitaires. Cette liste n'intervient jamais dans la détection.

| Date | Banque | Événement |
|---|---|---|
| 2024-01-22 | BNP Paribas Fortis | Intégration de bpost banque (environ 1 million de clients migrés) |

## Fiches produits BNP Paribas Fortis

| Fiche produit | Termes de recherche BNP Paribas Fortis |
|---|---|
| Compte à vue particulier (BNP Paribas Fortis vs ING) (`compte_a_vue_bnppf`) | compte BNP, BNP rekening |
| Application mobile bancaire (BNP Paribas Fortis vs ING) (`app_mobile_bnppf`) | easy banking app |
| Carte de crédit (BNP Paribas Fortis vs ING) (`carte_credit_bnppf`) | BNP visa |
| Épargne-pension (BNP Paribas Fortis vs ING) (`epargne_pension_bnppf`) | BNP pension |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | BNP Paribas Fortis |
| Contexte — intégration de bpost banque dans BNP Paribas Fortis (janvier 2024) (`contexte_integration_bnppf_bpost`) | BNP Paribas Fortis, bpost bank, bpost banque |

### Notes produit

- Les termes produit utilisent le jeton `BNP` : en broad match, `compte à vue BNP` inclut `compte à vue BNP Paribas Fortis`, qui est un sous-ensemble strict et donc toujours moins couvrant.
- Les recherches passant par les marques sœurs Hello bank! et Fintro ne sont pas captées par ces termes.

## Données Google Trends brutes

2358 points hebdomadaires, 8 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`bnppf_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (187)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| carte_credit_bnppf | BNP visa | 2021-09-12 | 81 | Tendance soutenue | 2.197 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2021-09-19 | 68 | Tendance soutenue | 1.609 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2021-09-26 | 3 | Pic isolé | 1.84 | 0.563 |  |
| carte_credit_bnppf | BNP visa | 2021-10-03 | 66 | Tendance soutenue | 1.518 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2021-10-10 | 75 | Tendance soutenue | 1.926 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2021-10-24 | 66 | Tendance soutenue | 1.518 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2021-10-31 | 84 | Tendance soutenue | 2.333 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2021-11-07 | 69 | Tendance soutenue | 1.654 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2021-11-21 | 79 | Pic isolé | 2.107 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost banque | 2021-11-21 | 4 | Pic isolé | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | BNP rekening | 2021-12-05 | 18 | Tendance soutenue | 2.381 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2021-12-12 | 13 | Tendance soutenue | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2021-12-12 | 83 | Pic isolé | 2.83 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2021-12-12 | 72 | Pic isolé | 2.82 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2021-12-26 | 76 | Tendance soutenue | 2.176 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2021-12-26 | 4 | Pic isolé | 1.502 | 0.590 |  |
| epargne_pension_bnppf | BNP pension | 2021-12-26 | 73 | Pic isolé | 1.524 | 0.625 | broad_fallback,asymmetric |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2021-12-26 | 66 | Tendance soutenue | 2.175 | 1.000 |  |
| compte_a_vue_bnppf | BNP rekening | 2022-01-02 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-01-02 | 81 | Tendance soutenue | 2.643 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-01-02 | 70 | Tendance soutenue | 2.605 | 1.000 |  |
| carte_credit_bnppf | BNP visa | 2022-01-30 | 69 | Pic isolé | 1.654 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-01-30 | 79 | Pic isolé | 2.457 | 1.000 |  |
| epargne_pension_bnppf | BNP pension | 2022-01-30 | 96 | Pic isolé | 2.374 | 0.625 | broad_fallback,asymmetric |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-01-30 | 69 | Pic isolé | 2.497 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-02-27 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | 2022-02-27 | 3 | Pic isolé | 1.84 | 0.563 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-02-27 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| carte_credit_bnppf | BNP visa | 2022-03-06 | 71 | Pic isolé | 1.745 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-03-06 | 71 | Tendance soutenue | 1.709 | 1.000 |  |
| epargne_pension_bnppf | BNP pension | 2022-03-06 | 96 | Tendance soutenue | 2.374 | 0.625 | broad_fallback,asymmetric |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-03-06 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| epargne_pension_bnppf | BNP pension | 2022-03-13 | 83 | Tendance soutenue | 1.894 | 0.625 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-03-20 | 70 | Tendance soutenue | 1.616 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-03-20 | 61 | Tendance soutenue | 1.637 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-03-27 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-03-27 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-04-03 | 74 | Tendance soutenue | 1.989 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-04-03 | 64 | Tendance soutenue | 1.96 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-04-24 | 84 | Tendance soutenue | 2.924 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-04-24 | 73 | Tendance soutenue | 2.927 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-05-01 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-05-01 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| compte_a_vue_bnppf | BNP rekening | 2022-05-08 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-05-29 | 69 | Tendance soutenue | 1.522 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-05-29 | 60 | Tendance soutenue | 1.53 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-06-05 | 69 | Tendance soutenue | 1.522 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-06-05 | 60 | Tendance soutenue | 1.53 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-06-12 | 70 | Tendance soutenue | 1.616 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-06-12 | 61 | Tendance soutenue | 1.637 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-06-19 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | 2022-06-19 | 3 | Pic isolé | 1.84 | 0.563 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-06-19 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| carte_credit_bnppf | BNP visa | 2022-06-26 | 80 | Tendance soutenue | 2.152 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-06-26 | 78 | Tendance soutenue | 2.363 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-06-26 | 68 | Tendance soutenue | 2.39 | 1.000 |  |
| carte_credit_bnppf | BNP visa | 2022-07-03 | 77 | Tendance soutenue | 2.016 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-07-03 | 79 | Tendance soutenue | 2.457 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-07-03 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-07-03 | 69 | Tendance soutenue | 2.497 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-07-10 | 70 | Tendance soutenue | 1.616 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-07-10 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-07-10 | 61 | Tendance soutenue | 1.637 | 1.000 |  |
| app_mobile_bnppf | easy banking app | 2022-07-31 | 10 | Tendance soutenue | 1.901 | 0.713 | asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-07-31 | 79 | Tendance soutenue | 2.457 | 1.000 |  |
| epargne_pension_bnppf | BNP pension | 2022-07-31 | 84 | Pic isolé | 1.931 | 0.625 | broad_fallback,asymmetric |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-07-31 | 69 | Tendance soutenue | 2.497 | 1.000 |  |
| app_mobile_bnppf | easy banking app | 2022-08-07 | 14 | Tendance soutenue | 3.053 | 0.713 | asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-08-07 | 76 | Tendance soutenue | 2.176 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-08-07 | 66 | Tendance soutenue | 2.175 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-08-21 | 71 | Tendance soutenue | 1.709 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-08-21 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-08-28 | 74 | Tendance soutenue | 1.989 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-08-28 | 64 | Tendance soutenue | 1.96 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-09-04 | 73 | Tendance soutenue | 1.896 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-09-04 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-09-11 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-09-11 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-09-18 | 75 | Tendance soutenue | 2.083 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-09-18 | 65 | Tendance soutenue | 2.067 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2022-09-25 | 73 | Tendance soutenue | 1.896 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-09-25 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2022-09-25 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-10-02 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-10-23 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-11-20 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | 2022-11-27 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2022-11-27 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| epargne_pension_bnppf | BNP pension | 2022-11-27 | 75 | Pic isolé | 1.598 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | 2022-12-18 | 75 | Pic isolé | 1.598 | 0.625 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2023-01-01 | 91 | Pic isolé | 4.248 | 1.000 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | 2023-01-15 | 90 | Pic isolé | 2.152 | 0.625 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost banque | 2023-01-22 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-01-29 | 19 | Pic isolé | 2.544 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost banque | 2023-01-29 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-02-26 | 4 | Pic isolé | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-04-09 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2023-04-16 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-04-16 | 4 | Pic isolé | 1.502 | 0.590 |  |
| carte_credit_bnppf | BNP visa | 2023-04-23 | 85 | Pic isolé | 2.379 | 0.743 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2023-04-30 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-04-30 | 4 | Pic isolé | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-05-14 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost banque | 2023-05-21 | 4 | Pic isolé | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-06-18 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2023-07-02 | 3 | Pic isolé | 1.84 | 0.563 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-07-16 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2023-07-30 | 3 | Pic isolé | 1.84 | 0.563 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-08-20 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2023-08-20 | 72 | Tendance soutenue | 2.741 | 1.000 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2023-08-20 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-08-20 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | compte BNP | 2023-08-27 | 61 | Tendance soutenue | 1.868 | 1.000 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost banque | 2023-08-27 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-09-03 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-09-10 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-09-24 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | BNP rekening | 2023-10-01 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost banque | 2023-10-01 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| compte_a_vue_bnppf | compte BNP | 2023-10-22 | 57 | Pic isolé | 1.551 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2023-11-19 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2023-12-24 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-12-24 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2023-12-31 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | 2024-01-07 | 3 | Tendance soutenue | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2024-01-07 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| epargne_pension_bnppf | BNP pension | 2024-01-07 | 94 | Pic isolé | 2.3 | 0.625 | broad_fallback,asymmetric |
| app_mobile_bnppf | easy banking app | 2024-01-14 | 10 | Tendance soutenue | 1.901 | 0.713 | asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-01-14 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | bpost bank | 2024-01-14 | 3 | Tendance soutenue | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2024-01-14 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| app_mobile_bnppf | easy banking app | 2024-01-21 | 42 | Tendance soutenue | 11.114 | 0.713 | asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-01-21 | 17 | Tendance soutenue | 2.218 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-01-21 | 100 | Tendance soutenue | 4.963 | 1.000 | broad_fallback,asymmetric |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | 2024-01-21 | 93 | Pic isolé | 3.764 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | 2024-01-21 | 4 | Tendance soutenue | 2.8 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | 2024-01-21 | 7 | Tendance soutenue | 3.412 | 0.590 |  |
| epargne_pension_bnppf | BNP pension | 2024-01-21 | 83 | Pic isolé | 1.894 | 0.625 | broad_fallback,asymmetric |
| marque_generique_traditionnelles | BNP Paribas Fortis | 2024-01-21 | 81 | Pic isolé | 3.787 | 1.000 |  |
| app_mobile_bnppf | easy banking app | 2024-01-28 | 9 | Tendance soutenue | 1.613 | 0.713 | asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-01-28 | 62 | Tendance soutenue | 1.947 | 1.000 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2024-02-04 | 66 | Pic isolé | 1.518 | 0.743 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-02-04 | 61 | Tendance soutenue | 1.868 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-02-11 | 16 | Pic isolé | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-02-11 | 61 | Tendance soutenue | 1.868 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-03-03 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-04-07 | 19 | Pic isolé | 2.544 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2024-07-07 | 68 | Pic isolé | 1.609 | 0.743 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-07-07 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-08-04 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-08-25 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-08-25 | 81 | Tendance soutenue | 3.455 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-09-01 | 96 | Tendance soutenue | 4.645 | 1.000 | broad_fallback,asymmetric |
| app_mobile_bnppf | easy banking app | 2024-09-08 | 9 | Pic isolé | 1.613 | 0.713 | asymmetric |
| compte_a_vue_bnppf | compte BNP | 2024-09-08 | 62 | Tendance soutenue | 1.947 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-09-15 | 18 | Tendance soutenue | 2.381 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-09-22 | 13 | Tendance soutenue | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-10-06 | 14 | Tendance soutenue | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2024-10-13 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2024-12-08 | 71 | Pic isolé | 1.745 | 0.743 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2025-01-05 | 68 | Pic isolé | 2.423 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-01-19 | 14 | Tendance soutenue | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-01-26 | 13 | Tendance soutenue | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-02-09 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2025-04-06 | 83 | Pic isolé | 2.288 | 0.743 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-04-06 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | 2025-05-04 | 100 | Pic isolé | 2.521 | 0.625 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-05-18 | 21 | Pic isolé | 2.87 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-06-01 | 16 | Pic isolé | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | 2025-07-06 | 72 | Pic isolé | 1.79 | 0.743 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-07-06 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | 2025-07-13 | 78 | Pic isolé | 1.709 | 0.625 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-07-27 | 16 | Pic isolé | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-11-23 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | 2025-12-07 | 79 | Pic isolé | 1.746 | 0.625 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-12-14 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2025-12-21 | 17 | Tendance soutenue | 2.218 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2025-12-28 | 57 | Pic isolé | 1.551 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-01-11 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-02-08 | 17 | Pic isolé | 2.218 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-05-03 | 22 | Pic isolé | 3.033 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | 2026-05-03 | 100 | Pic isolé | 4.963 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-05-24 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-05-31 | 16 | Tendance soutenue | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-08-02 | 18 | Tendance soutenue | 2.381 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-08-09 | 14 | Tendance soutenue | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | 2026-08-23 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
