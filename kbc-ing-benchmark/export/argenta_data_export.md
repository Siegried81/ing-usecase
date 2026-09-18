# Export des données Argenta — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque Argenta (code `ARGENTA`, segment : traditionnelle).

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

## Fiches produits Argenta

| Fiche produit | Termes de recherche Argenta |
|---|---|
| Compte à vue particulier (Argenta vs ING) (`compte_a_vue_argenta`) | compte Argenta, Argenta rekening |
| Compte épargne particulier (Argenta vs ING) (`compte_epargne_argenta`) | Argenta spaarrekening |
| Application mobile bancaire (Argenta vs ING) (`app_mobile_argenta`) | Argenta app |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | Argenta |

### Notes produit

- `investissement_courtage` : l'offre d'investissement d'Argenta repose sur des fonds, des plans d'investissement et du conseil, pas sur une plateforme de courtage d'actions comparable à Bolero. Le `product_id` est conservé pour la symétrie inter-banques.

## Données Google Trends brutes

1310 points hebdomadaires, 5 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`argenta_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (57)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| app_mobile_argenta | Argenta app | 2022-01-30 | 19 | Pic isolé | 5.221 | 0.877 | asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2022-12-25 | 27 | Tendance soutenue | 1.729 | 0.575 |  |
| compte_epargne_argenta | Argenta spaarrekening | 2023-01-01 | 25 | Tendance soutenue | 1.541 | 0.575 |  |
| app_mobile_argenta | Argenta app | 2023-03-12 | 13 | Pic isolé | 2.976 | 0.877 | asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2023-05-21 | 25 | Pic isolé | 1.541 | 0.575 |  |
| compte_epargne_argenta | Argenta spaarrekening | 2023-07-30 | 25 | Pic isolé | 1.541 | 0.575 |  |
| app_mobile_argenta | Argenta app | 2023-08-06 | 10 | Pic isolé | 1.854 | 0.877 | asymmetric |
| compte_a_vue_argenta | compte Argenta | 2023-08-13 | 38 | Tendance soutenue | 2.358 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | 2023-08-20 | 48 | Tendance soutenue | 1.737 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2023-08-20 | 100 | Tendance soutenue | 7.028 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2023-08-20 | 100 | Tendance soutenue | 8.609 | 0.575 |  |
| marque_generique_traditionnelles | Argenta | 2023-08-20 | 62 | Tendance soutenue | 9.206 | 1.000 |  |
| compte_a_vue_argenta | Argenta rekening | 2023-08-27 | 68 | Tendance soutenue | 3.071 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2023-08-27 | 44 | Tendance soutenue | 2.81 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2023-08-27 | 64 | Tendance soutenue | 5.216 | 0.575 |  |
| marque_generique_traditionnelles | Argenta | 2023-08-27 | 52 | Tendance soutenue | 6.556 | 1.000 |  |
| compte_a_vue_argenta | compte Argenta | 2023-09-03 | 39 | Tendance soutenue | 2.433 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2023-09-03 | 28 | Tendance soutenue | 1.824 | 0.575 |  |
| app_mobile_argenta | Argenta app | 2023-09-24 | 12 | Pic isolé | 2.602 | 0.877 | asymmetric |
| compte_a_vue_argenta | Argenta rekening | 2023-10-29 | 47 | Pic isolé | 1.67 | 0.736 | broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2023-11-26 | 25 | Pic isolé | 1.541 | 0.575 |  |
| compte_epargne_argenta | Argenta spaarrekening | 2023-12-24 | 26 | Pic isolé | 1.635 | 0.575 |  |
| compte_a_vue_argenta | Argenta rekening | 2023-12-31 | 47 | Pic isolé | 1.67 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2023-12-31 | 28 | Pic isolé | 1.605 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2024-02-18 | 32 | Tendance soutenue | 1.906 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2024-02-25 | 33 | Tendance soutenue | 1.981 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2024-08-18 | 37 | Tendance soutenue | 2.283 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2024-08-25 | 57 | Tendance soutenue | 3.789 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | 2024-09-01 | 51 | Pic isolé | 1.937 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2024-09-01 | 47 | Tendance soutenue | 3.036 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2024-09-01 | 47 | Pic isolé | 3.614 | 0.575 |  |
| marque_generique_traditionnelles | Argenta | 2024-09-01 | 45 | Pic isolé | 4.7 | 1.000 |  |
| compte_a_vue_argenta | compte Argenta | 2024-09-08 | 45 | Tendance soutenue | 2.885 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2024-12-08 | 30 | Pic isolé | 1.756 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2024-12-29 | 32 | Pic isolé | 2.201 | 0.575 |  |
| app_mobile_argenta | Argenta app | 2025-01-05 | 10 | Pic isolé | 1.854 | 0.877 | asymmetric |
| compte_a_vue_argenta | compte Argenta | 2025-01-05 | 29 | Pic isolé | 1.68 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| app_mobile_argenta | Argenta app | 2025-01-19 | 10 | Tendance soutenue | 1.854 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | 2025-01-26 | 14 | Tendance soutenue | 3.35 | 0.877 | asymmetric |
| compte_a_vue_argenta | compte Argenta | 2025-04-06 | 29 | Pic isolé | 1.68 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2025-06-15 | 28 | Pic isolé | 1.605 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2025-07-06 | 39 | Pic isolé | 2.433 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2025-08-24 | 33 | Pic isolé | 1.981 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2025-09-28 | 34 | Pic isolé | 2.057 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| app_mobile_argenta | Argenta app | 2025-10-05 | 11 | Pic isolé | 2.228 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | 2025-12-28 | 12 | Pic isolé | 2.602 | 0.877 | asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2025-12-28 | 28 | Pic isolé | 1.824 | 0.575 |  |
| compte_a_vue_argenta | Argenta rekening | 2026-01-25 | 46 | Pic isolé | 1.603 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | 2026-03-08 | 43 | Pic isolé | 2.735 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne_argenta | Argenta spaarrekening | 2026-03-29 | 26 | Pic isolé | 1.635 | 0.575 |  |
| app_mobile_argenta | Argenta app | 2026-05-31 | 13 | Pic isolé | 2.976 | 0.877 | asymmetric |
| compte_a_vue_argenta | Argenta rekening | 2026-06-07 | 46 | Tendance soutenue | 1.603 | 0.736 | broad_fallback,asymmetric |
| app_mobile_argenta | Argenta app | 2026-06-14 | 10 | Pic isolé | 1.854 | 0.877 | asymmetric |
| compte_a_vue_argenta | Argenta rekening | 2026-06-14 | 47 | Tendance soutenue | 1.67 | 0.736 | broad_fallback,asymmetric |
| app_mobile_argenta | Argenta app | 2026-07-05 | 11 | Pic isolé | 2.228 | 0.877 | asymmetric |
| compte_a_vue_argenta | compte Argenta | 2026-08-09 | 30 | Pic isolé | 1.756 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | 2026-08-23 | 47 | Pic isolé | 1.67 | 0.736 | broad_fallback,asymmetric |
