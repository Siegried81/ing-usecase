# Export des données CBC — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque CBC (code `CBC`, segment : traditionnelle).

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

## Fiches produits CBC

| Fiche produit | Termes de recherche CBC |
|---|---|
| Compte professionnel / indépendant (CBC vs ING) (`compte_professionnel_cbc`) | compte professionnel CBC, KBC Business Pro |
| Compte à vue particulier (CBC vs ING) (`compte_a_vue_cbc`) | compte à vue CBC |
| Compte épargne particulier (CBC vs ING) (`compte_epargne_cbc`) | compte épargne CBC |
| Application mobile bancaire (CBC vs ING) (`app_mobile_cbc`) | CBC Mobile, CBC Touch |
| Carte de crédit (CBC vs ING) (`carte_credit_cbc`) | carte de crédit CBC |
| Épargne-pension (CBC vs ING) (`epargne_pension_cbc`) | épargne pension CBC |
| Assurance habitation (CBC vs ING) (`assurance_habitation_cbc`) | assurance CBC |
| Prêt hypothécaire (CBC vs ING) (`pret_hypothecaire_cbc`) | prêt hypothécaire CBC |
| Marque (recherche générique) (`marque_generique`) | CBC Banque & Assurance |

## Données Google Trends brutes

2882 points hebdomadaires, 11 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`cbc_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (73)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| app_mobile_cbc | CBC Touch | 2021-09-12 | 40 | Pic isolé | 1.738 |  |  |
| app_mobile_cbc | CBC Mobile | 2021-09-19 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Touch | 2021-09-26 | 43 | Tendance soutenue | 2.36 |  |  |
| app_mobile_cbc | CBC Touch | 2021-10-03 | 46 | Tendance soutenue | 2.982 |  |  |
| app_mobile_cbc | CBC Mobile | 2021-10-17 | 7 | Pic isolé | 5.831 |  |  |
| carte_credit_cbc | carte de crédit CBC | 2021-10-17 | 33 | Pic isolé | 10.513 |  |  |
| marque_generique | CBC Banque & Assurance | 2021-10-17 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2021-10-31 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2021-11-28 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2021-12-12 | 8 | Tendance soutenue | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2021-12-19 | 8 | Tendance soutenue | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2021-12-26 | 8 | Tendance soutenue | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-01-09 | 9 | Tendance soutenue | 3.084 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-01-16 | 9 | Tendance soutenue | 3.084 |  |  |
| assurance_habitation_cbc | assurance CBC | 2022-01-23 | 75 | Pic isolé | 1.745 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-01-30 | 9 | Pic isolé | 3.084 |  |  |
| app_mobile_cbc | CBC Mobile | 2022-02-20 | 3 | Pic isolé | 2.337 |  |  |
| app_mobile_cbc | CBC Mobile | 2022-03-27 | 4 | Pic isolé | 3.21 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-04-03 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-05-01 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-06-12 | 8 | Pic isolé | 2.008 |  |  |
| app_mobile_cbc | CBC Mobile | 2022-06-19 | 4 | Pic isolé | 3.21 |  |  |
| marque_generique | CBC Banque & Assurance | 2022-06-26 | 8 | Pic isolé | 2.008 |  |  |
| app_mobile_cbc | CBC Mobile | 2022-07-03 | 4 | Pic isolé | 3.21 |  |  |
| assurance_habitation_cbc | assurance CBC | 2022-07-10 | 72 | Pic isolé | 1.642 |  |  |
| app_mobile_cbc | CBC Mobile | 2022-07-17 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | 2022-12-04 | 4 | Pic isolé | 3.21 |  |  |
| assurance_habitation_cbc | assurance CBC | 2023-01-01 | 72 | Pic isolé | 1.642 |  |  |
| epargne_pension_cbc | épargne pension CBC | 2023-01-15 | 40 | Pic isolé | 16.155 |  |  |
| assurance_habitation_cbc | assurance CBC | 2023-01-22 | 75 | Pic isolé | 1.745 |  |  |
| app_mobile_cbc | CBC Mobile | 2023-03-12 | 4 | Pic isolé | 3.21 |  |  |
| carte_credit_cbc | carte de crédit CBC | 2023-03-19 | 29 | Pic isolé | 9.225 |  |  |
| compte_a_vue_cbc | compte à vue CBC | 2023-04-30 | 61 | Pic isolé | 12.079 |  |  |
| app_mobile_cbc | CBC Mobile | 2023-06-18 | 4 | Pic isolé | 3.21 |  |  |
| assurance_habitation_cbc | assurance CBC | 2023-07-02 | 69 | Pic isolé | 1.539 |  |  |
| carte_credit_cbc | carte de crédit CBC | 2023-09-03 | 25 | Pic isolé | 7.938 |  |  |
| assurance_habitation_cbc | assurance CBC | 2023-09-10 | 74 | Pic isolé | 1.711 |  |  |
| app_mobile_cbc | CBC Mobile | 2023-12-10 | 4 | Tendance soutenue | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | 2023-12-17 | 4 | Tendance soutenue | 3.21 |  |  |
| assurance_habitation_cbc | assurance CBC | 2024-03-31 | 69 | Pic isolé | 1.539 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire CBC | 2024-04-14 | 100 | Pic isolé | 13.906 |  |  |
| app_mobile_cbc | CBC Mobile | 2024-05-19 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | 2024-06-09 | 4 | Pic isolé | 3.21 |  |  |
| compte_epargne_cbc | compte épargne CBC | 2024-06-09 | 24 | Pic isolé | 15.909 |  |  |
| assurance_habitation_cbc | assurance CBC | 2024-08-11 | 78 | Pic isolé | 1.848 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire CBC | 2024-08-25 | 59 | Pic isolé | 8.17 |  |  |
| marque_generique | CBC Banque & Assurance | 2024-09-01 | 9 | Pic isolé | 3.084 |  |  |
| app_mobile_cbc | CBC Touch | 2024-09-29 | 40 | Pic isolé | 1.738 |  |  |
| app_mobile_cbc | CBC Mobile | 2024-10-20 | 6 | Pic isolé | 4.957 |  |  |
| compte_professionnel_cbc | compte professionnel CBC | 2024-11-03 | 100 | Pic isolé | 12.643 |  |  |
| app_mobile_cbc | CBC Touch | 2025-01-05 | 45 | Pic isolé | 2.775 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-02-23 | 100 | Pic isolé | 2.603 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-03-23 | 87 | Pic isolé | 2.157 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-06-08 | 76 | Pic isolé | 1.779 |  |  |
| app_mobile_cbc | CBC Touch | 2025-06-29 | 39 | Pic isolé | 1.53 |  |  |
| compte_professionnel_cbc | compte professionnel CBC | 2025-08-17 | 79 | Pic isolé | 9.969 |  |  |
| app_mobile_cbc | CBC Touch | 2025-08-24 | 43 | Pic isolé | 2.36 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-09-07 | 86 | Pic isolé | 2.123 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-10-05 | 90 | Pic isolé | 2.26 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-11-02 | 77 | Pic isolé | 1.814 |  |  |
| assurance_habitation_cbc | assurance CBC | 2025-12-21 | 99 | Pic isolé | 2.569 |  |  |
| compte_a_vue_cbc | compte à vue CBC | 2025-12-21 | 54 | Pic isolé | 10.682 |  |  |
| assurance_habitation_cbc | assurance CBC | 2026-01-11 | 68 | Pic isolé | 1.505 |  |  |
| assurance_habitation_cbc | assurance CBC | 2026-02-01 | 87 | Pic isolé | 2.157 |  |  |
| app_mobile_cbc | CBC Mobile | 2026-02-08 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | 2026-03-29 | 5 | Pic isolé | 4.084 |  |  |
| assurance_habitation_cbc | assurance CBC | 2026-03-29 | 68 | Pic isolé | 1.505 |  |  |
| app_mobile_cbc | CBC Mobile | 2026-05-03 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | 2026-08-23 | 5 | Pic isolé | 4.084 |  |  |
| assurance_habitation_cbc | assurance CBC | 2026-08-30 | 87 | Pic isolé | 2.157 |  |  |
| compte_epargne_cbc | compte épargne CBC | 2026-08-30 | 3 | Tendance soutenue | 1.922 |  |  |
| compte_epargne_cbc | compte épargne CBC | 2026-09-06 | 3 | Tendance soutenue | 1.922 |  |  |
| compte_professionnel_cbc | KBC Business Pro | 2026-09-06 | 8 | Pic isolé | 16.155 |  |  |
