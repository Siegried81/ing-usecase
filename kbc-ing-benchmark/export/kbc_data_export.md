# Export des données KBC — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque KBC (code `KBC`, segment : traditionnelle).

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

Aucun événement structurel connu pour cette banque sur la période couverte.

## Fiches produits KBC

| Fiche produit | Termes de recherche KBC |
|---|---|
| Compte professionnel / indépendant (`compte_professionnel`) | KBC zakelijke rekening, KBC Business Pro |
| Compte à vue particulier (`compte_a_vue`) | KBC zichtrekening, Compte Plus KBC |
| Compte épargne particulier (`compte_epargne`) | KBC spaarrekening, KBC Start2Save |
| Investissement / courtage en ligne (`investissement_courtage`) | Bolero |
| Application mobile bancaire (`app_mobile`) | KBC Mobile, KBC Touch |
| Carte de crédit (`carte_credit`) | KBC kredietkaart, KBC Flex Budget |
| Épargne-pension (`epargne_pension`) | KBC pensioensparen, KBC Pension Savings Fund |
| Assurance habitation (`assurance_habitation`) | KBC brandverzekering |
| Prêt hypothécaire (`pret_hypothecaire`) | KBC hypothecair krediet |
| Marque (recherche générique) (`marque_generique`) | KBC |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | KBC |
| Marques — néobanques (`marque_generique_neobanques`) | KBC |

## Données Google Trends brutes

4716 points hebdomadaires, 16 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`kbc_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (142)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| app_mobile | KBC Touch | 2021-09-26 | 90 | Pic isolé | 1.835 |  |  |
| epargne_pension | KBC pensioensparen | 2021-09-26 | 54 | Pic isolé | 3.31 |  |  |
| app_mobile | KBC Mobile | 2021-10-10 | 5 | Tendance soutenue | 2.466 |  |  |
| app_mobile | KBC Mobile | 2021-10-17 | 5 | Tendance soutenue | 2.466 |  |  |
| app_mobile | KBC Mobile | 2021-10-24 | 6 | Tendance soutenue | 3.57 |  |  |
| assurance_habitation | KBC brandverzekering | 2021-10-31 | 66 | Pic isolé | 4.433 |  |  |
| compte_a_vue | KBC zichtrekening | 2021-11-07 | 28 | Pic isolé | 2.456 |  |  |
| app_mobile | KBC Touch | 2021-11-28 | 89 | Pic isolé | 1.754 |  |  |
| compte_a_vue | KBC zichtrekening | 2021-11-28 | 23 | Pic isolé | 1.947 |  |  |
| epargne_pension | KBC pensioensparen | 2021-11-28 | 49 | Pic isolé | 2.977 |  |  |
| app_mobile | KBC Mobile | 2021-12-05 | 5 | Pic isolé | 2.466 |  |  |
| pret_hypothecaire | KBC hypothecair krediet | 2021-12-12 | 100 | Pic isolé | 11.541 |  |  |
| app_mobile | KBC Touch | 2022-01-02 | 100 | Tendance soutenue | 2.646 |  |  |
| epargne_pension | KBC pensioensparen | 2022-01-02 | 76 | Pic isolé | 4.777 |  |  |
| investissement_courtage | Bolero | 2022-01-02 | 100 | Pic isolé | 3.361 |  |  |
| app_mobile | KBC Mobile | 2022-01-09 | 5 | Pic isolé | 2.466 |  |  |
| app_mobile | KBC Touch | 2022-01-09 | 98 | Tendance soutenue | 2.483 |  |  |
| compte_a_vue | KBC zichtrekening | 2022-01-16 | 24 | Pic isolé | 2.048 |  |  |
| compte_a_vue | KBC zichtrekening | 2022-01-30 | 21 | Pic isolé | 1.743 |  |  |
| assurance_habitation | KBC brandverzekering | 2022-02-13 | 100 | Tendance soutenue | 6.833 |  |  |
| assurance_habitation | KBC brandverzekering | 2022-02-20 | 79 | Tendance soutenue | 5.351 |  |  |
| epargne_pension | KBC pensioensparen | 2022-02-20 | 39 | Pic isolé | 2.31 |  |  |
| compte_a_vue | KBC zichtrekening | 2022-04-10 | 19 | Pic isolé | 1.539 |  |  |
| compte_a_vue | KBC zichtrekening | 2022-05-01 | 21 | Pic isolé | 1.743 |  |  |
| epargne_pension | KBC pensioensparen | 2022-06-05 | 45 | Pic isolé | 2.71 |  |  |
| compte_a_vue | Compte Plus KBC | 2022-06-12 | 16 | Pic isolé | 7.614 |  |  |
| app_mobile | KBC Mobile | 2022-06-26 | 5 | Pic isolé | 2.466 |  |  |
| app_mobile | KBC Touch | 2022-06-26 | 89 | Tendance soutenue | 1.754 |  |  |
| marque_generique | KBC | 2022-06-26 | 82 | Tendance soutenue | 2.085 |  |  |
| marque_generique_neobanques | KBC | 2022-06-26 | 78 | Tendance soutenue | 1.732 | 1.000 |  |
| marque_generique_traditionnelles | KBC | 2022-06-26 | 78 | Tendance soutenue | 1.732 | 1.000 |  |
| app_mobile | KBC Touch | 2022-07-03 | 95 | Tendance soutenue | 2.24 |  |  |
| epargne_pension | KBC pensioensparen | 2022-07-03 | 51 | Pic isolé | 3.11 |  |  |
| marque_generique | KBC | 2022-07-03 | 81 | Tendance soutenue | 1.972 |  |  |
| marque_generique_neobanques | KBC | 2022-07-03 | 83 | Tendance soutenue | 2.317 | 1.000 |  |
| marque_generique_traditionnelles | KBC | 2022-07-03 | 83 | Tendance soutenue | 2.317 | 1.000 |  |
| app_mobile | KBC Touch | 2022-07-10 | 90 | Tendance soutenue | 1.835 |  |  |
| carte_credit | KBC kredietkaart | 2022-07-24 | 34 | Pic isolé | 1.516 |  |  |
| carte_credit | KBC Flex Budget | 2022-10-23 | 21 | Pic isolé | 9.216 |  |  |
| compte_epargne | KBC spaarrekening | 2022-12-25 | 40 | Tendance soutenue | 1.599 |  |  |
| epargne_pension | KBC pensioensparen | 2022-12-25 | 77 | Pic isolé | 4.844 |  |  |
| compte_epargne | KBC spaarrekening | 2023-01-01 | 60 | Tendance soutenue | 2.987 |  |  |
| assurance_habitation | KBC brandverzekering | 2023-01-29 | 58 | Pic isolé | 3.868 |  |  |
| compte_epargne | KBC spaarrekening | 2023-02-05 | 41 | Pic isolé | 1.668 |  |  |
| app_mobile | KBC Mobile | 2023-03-05 | 6 | Pic isolé | 3.57 |  |  |
| assurance_habitation | KBC brandverzekering | 2023-03-12 | 47 | Pic isolé | 3.091 |  |  |
| epargne_pension | KBC pensioensparen | 2023-05-28 | 42 | Pic isolé | 2.51 |  |  |
| assurance_habitation | KBC brandverzekering | 2023-06-11 | 47 | Pic isolé | 3.091 |  |  |
| carte_credit | KBC kredietkaart | 2023-07-16 | 62 | Pic isolé | 3.4 |  |  |
| compte_epargne | KBC spaarrekening | 2023-07-30 | 46 | Pic isolé | 2.015 |  |  |
| epargne_pension | KBC pensioensparen | 2023-07-30 | 59 | Pic isolé | 3.644 |  |  |
| carte_credit | KBC kredietkaart | 2023-08-20 | 34 | Pic isolé | 1.516 |  |  |
| compte_epargne | KBC spaarrekening | 2023-08-20 | 100 | Tendance soutenue | 5.762 |  |  |
| marque_generique | KBC | 2023-08-20 | 83 | Tendance soutenue | 2.198 |  |  |
| marque_generique_neobanques | KBC | 2023-08-20 | 86 | Tendance soutenue | 2.667 | 1.000 |  |
| marque_generique_traditionnelles | KBC | 2023-08-20 | 86 | Tendance soutenue | 2.667 | 1.000 |  |
| compte_epargne | KBC spaarrekening | 2023-08-27 | 80 | Tendance soutenue | 4.374 |  |  |
| marque_generique | KBC | 2023-08-27 | 90 | Tendance soutenue | 2.989 |  |  |
| marque_generique_neobanques | KBC | 2023-08-27 | 94 | Tendance soutenue | 3.603 | 1.000 |  |
| marque_generique_traditionnelles | KBC | 2023-08-27 | 94 | Tendance soutenue | 3.603 | 1.000 |  |
| assurance_habitation | KBC brandverzekering | 2023-09-17 | 54 | Pic isolé | 3.586 |  |  |
| compte_professionnel | KBC zakelijke rekening | 2023-10-15 | 62 | Pic isolé | 6.82 |  |  |
| compte_epargne | KBC Start2Save | 2023-10-22 | 15 | Pic isolé | 6.737 |  |  |
| pret_hypothecaire | KBC hypothecair krediet | 2023-11-12 | 71 | Pic isolé | 8.164 |  |  |
| compte_epargne | KBC Start2Save | 2023-11-26 | 15 | Pic isolé | 6.737 |  |  |
| epargne_pension | KBC pensioensparen | 2023-11-26 | 48 | Pic isolé | 2.91 |  |  |
| carte_credit | KBC kredietkaart | 2023-12-17 | 36 | Pic isolé | 1.651 |  |  |
| compte_a_vue | Compte Plus KBC | 2023-12-24 | 21 | Pic isolé | 10.027 |  |  |
| compte_epargne | KBC spaarrekening | 2023-12-24 | 51 | Tendance soutenue | 2.362 |  |  |
| compte_epargne | KBC spaarrekening | 2023-12-31 | 50 | Tendance soutenue | 2.293 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-01-07 | 100 | Tendance soutenue | 9.789 |  |  |
| compte_epargne | KBC Start2Save | 2024-01-07 | 12 | Pic isolé | 5.358 |  |  |
| compte_epargne | KBC spaarrekening | 2024-01-07 | 41 | Tendance soutenue | 1.668 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-01-14 | 26 | Tendance soutenue | 2.252 |  |  |
| carte_credit | KBC kredietkaart | 2024-03-10 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | KBC kredietkaart | 2024-03-24 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | KBC kredietkaart | 2024-04-21 | 38 | Pic isolé | 1.786 |  |  |
| carte_credit | KBC kredietkaart | 2024-05-12 | 36 | Tendance soutenue | 1.651 |  |  |
| epargne_pension | KBC pensioensparen | 2024-05-12 | 49 | Pic isolé | 2.977 |  |  |
| carte_credit | KBC kredietkaart | 2024-05-19 | 39 | Tendance soutenue | 1.853 |  |  |
| assurance_habitation | KBC brandverzekering | 2024-05-26 | 73 | Pic isolé | 4.927 |  |  |
| epargne_pension | KBC pensioensparen | 2024-05-26 | 58 | Pic isolé | 3.577 |  |  |
| assurance_habitation | KBC brandverzekering | 2024-06-16 | 56 | Pic isolé | 3.727 |  |  |
| carte_credit | KBC kredietkaart | 2024-07-28 | 36 | Tendance soutenue | 1.651 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-07-28 | 20 | Pic isolé | 1.641 |  |  |
| carte_credit | KBC kredietkaart | 2024-08-04 | 36 | Tendance soutenue | 1.651 |  |  |
| carte_credit | KBC kredietkaart | 2024-08-18 | 35 | Pic isolé | 1.584 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-08-25 | 25 | Tendance soutenue | 2.15 |  |  |
| compte_epargne | KBC spaarrekening | 2024-08-25 | 39 | Tendance soutenue | 1.53 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-09-01 | 42 | Tendance soutenue | 3.882 |  |  |
| compte_epargne | KBC spaarrekening | 2024-09-01 | 89 | Tendance soutenue | 4.999 |  |  |
| marque_generique | KBC | 2024-09-01 | 100 | Pic isolé | 4.12 |  |  |
| marque_generique_neobanques | KBC | 2024-09-01 | 100 | Pic isolé | 4.304 | 1.000 |  |
| marque_generique_traditionnelles | KBC | 2024-09-01 | 100 | Pic isolé | 4.304 | 1.000 |  |
| pret_hypothecaire | KBC hypothecair krediet | 2024-09-01 | 67 | Pic isolé | 7.698 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-09-08 | 34 | Tendance soutenue | 3.067 |  |  |
| compte_epargne | KBC spaarrekening | 2024-09-08 | 48 | Tendance soutenue | 2.154 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-09-29 | 24 | Pic isolé | 2.048 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-11-03 | 21 | Tendance soutenue | 1.743 |  |  |
| compte_a_vue | KBC zichtrekening | 2024-11-10 | 19 | Tendance soutenue | 1.539 |  |  |
| epargne_pension | KBC pensioensparen | 2024-11-24 | 61 | Pic isolé | 3.777 |  |  |
| epargne_pension | KBC pensioensparen | 2024-12-08 | 52 | Pic isolé | 3.177 |  |  |
| epargne_pension | KBC pensioensparen | 2024-12-22 | 67 | Pic isolé | 4.177 |  |  |
| compte_epargne | KBC spaarrekening | 2024-12-29 | 41 | Pic isolé | 1.668 |  |  |
| epargne_pension | KBC pensioensparen | 2025-01-05 | 48 | Pic isolé | 2.91 |  |  |
| compte_professionnel | KBC zakelijke rekening | 2025-03-09 | 84 | Pic isolé | 9.281 |  |  |
| compte_a_vue | KBC zichtrekening | 2025-03-16 | 21 | Pic isolé | 1.743 |  |  |
| carte_credit | KBC kredietkaart | 2025-03-23 | 34 | Pic isolé | 1.516 |  |  |
| carte_credit | KBC kredietkaart | 2025-04-06 | 36 | Pic isolé | 1.651 |  |  |
| investissement_courtage | Bolero | 2025-04-06 | 93 | Pic isolé | 2.723 |  |  |
| epargne_pension | KBC pensioensparen | 2025-05-18 | 61 | Pic isolé | 3.777 |  |  |
| carte_credit | KBC kredietkaart | 2025-06-08 | 34 | Pic isolé | 1.516 |  |  |
| investissement_courtage | Bolero | 2025-07-27 | 85 | Pic isolé | 1.994 |  |  |
| compte_a_vue | Compte Plus KBC | 2025-08-10 | 21 | Pic isolé | 10.027 |  |  |
| assurance_habitation | KBC brandverzekering | 2025-08-31 | 62 | Pic isolé | 4.15 |  |  |
| compte_a_vue | KBC zichtrekening | 2025-08-31 | 27 | Pic isolé | 2.354 |  |  |
| investissement_courtage | Bolero | 2025-10-05 | 84 | Tendance soutenue | 1.903 |  |  |
| investissement_courtage | Bolero | 2025-10-12 | 82 | Tendance soutenue | 1.721 |  |  |
| assurance_habitation | KBC brandverzekering | 2025-11-30 | 58 | Pic isolé | 3.868 |  |  |
| epargne_pension | KBC pensioensparen | 2025-12-21 | 63 | Pic isolé | 3.91 |  |  |
| investissement_courtage | Bolero | 2025-12-28 | 90 | Pic isolé | 2.45 |  |  |
| epargne_pension | KBC pensioensparen | 2026-01-04 | 61 | Pic isolé | 3.777 |  |  |
| epargne_pension | KBC pensioensparen | 2026-01-25 | 49 | Pic isolé | 2.977 |  |  |
| carte_credit | KBC kredietkaart | 2026-02-01 | 35 | Pic isolé | 1.584 |  |  |
| carte_credit | KBC Flex Budget | 2026-02-22 | 30 | Pic isolé | 13.204 |  |  |
| carte_credit | KBC kredietkaart | 2026-03-15 | 36 | Pic isolé | 1.651 |  |  |
| compte_a_vue | KBC zichtrekening | 2026-03-22 | 27 | Pic isolé | 2.354 |  |  |
| compte_epargne | KBC Start2Save | 2026-04-19 | 20 | Pic isolé | 9.036 |  |  |
| carte_credit | KBC kredietkaart | 2026-05-17 | 40 | Pic isolé | 1.92 |  |  |
| compte_a_vue | KBC zichtrekening | 2026-05-17 | 19 | Pic isolé | 1.539 |  |  |
| investissement_courtage | Bolero | 2026-06-07 | 87 | Pic isolé | 2.176 |  |  |
| compte_epargne | KBC Start2Save | 2026-06-28 | 14 | Pic isolé | 6.277 |  |  |
| assurance_habitation | KBC brandverzekering | 2026-07-19 | 84 | Pic isolé | 5.704 |  |  |
| carte_credit | KBC kredietkaart | 2026-07-19 | 59 | Tendance soutenue | 3.199 |  |  |
| carte_credit | KBC kredietkaart | 2026-07-26 | 37 | Tendance soutenue | 1.718 |  |  |
| compte_a_vue | KBC zichtrekening | 2026-07-26 | 25 | Pic isolé | 2.15 |  |  |
| compte_professionnel | KBC zakelijke rekening | 2026-08-23 | 100 | Pic isolé | 11.071 |  |  |
| compte_epargne | KBC Start2Save | 2026-08-30 | 6 | Tendance soutenue | 2.599 |  |  |
| epargne_pension | KBC Pension Savings Fund | 2026-08-30 | 6 | Tendance soutenue | 12.395 |  |  |
| compte_epargne | KBC Start2Save | 2026-09-06 | 6 | Tendance soutenue | 2.599 |  |  |
| epargne_pension | KBC Pension Savings Fund | 2026-09-06 | 5 | Tendance soutenue | 10.314 |  |  |
| assurance_habitation | KBC brandverzekering | 2026-09-13 | 26 | Pic isolé | 1.609 |  |  |
