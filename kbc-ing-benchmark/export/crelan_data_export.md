# Export des données Crelan — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque Crelan (code `CRELAN`, segment : traditionnelle).

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
| 2024-06-10 | Crelan | Fusion avec AXA Bank Belgium, migration IT d'environ 840 000 clients (week-end des 8 et 9 juin) |

## Fiches produits Crelan

| Fiche produit | Termes de recherche Crelan |
|---|---|
| Application mobile bancaire (Crelan vs ING) (`app_mobile_crelan`) | Crelan app |
| Carte de crédit (Crelan vs ING) (`carte_credit_crelan`) | Crelan visa |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | Crelan |
| Contexte — fusion d'AXA Bank Belgium dans Crelan (juin 2024) (`contexte_fusion_crelan_axa`) | Crelan, AXA Bank, AXA Banque |

### Notes produit

- `investissement_courtage` : l'offre d'investissement de Crelan repose sur des fonds, des plans d'investissement et du conseil, pas sur une plateforme de courtage d'actions comparable à Bolero. Le `product_id` est conservé pour la symétrie inter-banques.

## Données Google Trends brutes

1572 points hebdomadaires, 5 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`crelan_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (112)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| contexte_fusion_crelan_axa | AXA Banque | 2021-09-12 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2021-10-03 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2021-10-10 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2021-11-14 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2021-11-21 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2021-12-12 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-01-02 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-01-16 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-02-20 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-03-13 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-05-15 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-06-26 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-07-31 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-08-21 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-08-28 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-10-02 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2022-10-09 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-01-01 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-01-15 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-01-29 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-02-19 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-02-26 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-03-05 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-04-02 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-04-09 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-04-30 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-07-09 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-07-30 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Bank | 2023-08-20 | 5 | Tendance soutenue | 3.321 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Bank | 2023-08-27 | 4 | Tendance soutenue | 2.397 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-08-27 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-09-24 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-10-22 | 2 | Pic isolé | 1.74 | 0.625 |  |
| carte_credit_crelan | Crelan visa | 2023-10-29 | 40 | Pic isolé | 1.68 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | AXA Banque | 2023-11-12 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-11-26 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2023-12-31 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2024-01-07 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2024-01-28 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Bank | 2024-02-18 | 4 | Pic isolé | 2.397 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2024-02-18 | 2 | Pic isolé | 1.74 | 0.625 |  |
| carte_credit_crelan | Crelan visa | 2024-03-17 | 42 | Pic isolé | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | AXA Banque | 2024-03-31 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2024-04-07 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| app_mobile_crelan | Crelan app | 2024-06-02 | 10 | Tendance soutenue | 2.17 | 0.345 | selected_low_coverage,asymmetric |
| contexte_fusion_crelan_axa | AXA Banque | 2024-06-02 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| app_mobile_crelan | Crelan app | 2024-06-09 | 47 | Tendance soutenue | 11.996 | 0.345 | selected_low_coverage,asymmetric |
| contexte_fusion_crelan_axa | AXA Bank | 2024-06-09 | 4 | Pic isolé | 2.397 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Banque | 2024-06-09 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | Crelan | 2024-06-09 | 58 | Tendance soutenue | 5.078 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-06-09 | 50 | Tendance soutenue | 4.965 | 1.000 |  |
| app_mobile_crelan | Crelan app | 2024-06-16 | 11 | Tendance soutenue | 2.436 | 0.345 | selected_low_coverage,asymmetric |
| contexte_fusion_crelan_axa | AXA Banque | 2024-06-16 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | Crelan | 2024-06-16 | 43 | Tendance soutenue | 2.829 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-06-16 | 38 | Tendance soutenue | 2.912 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2024-06-23 | 52 | Pic isolé | 2.375 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2024-06-23 | 39 | Tendance soutenue | 2.229 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-06-23 | 34 | Tendance soutenue | 2.228 | 1.000 |  |
| app_mobile_crelan | Crelan app | 2024-06-30 | 8 | Pic isolé | 1.639 | 0.345 | selected_low_coverage,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2024-06-30 | 39 | Tendance soutenue | 2.229 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-06-30 | 34 | Tendance soutenue | 2.228 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2024-07-07 | 50 | Tendance soutenue | 2.259 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2024-07-07 | 37 | Tendance soutenue | 1.929 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-07-07 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2024-07-14 | 48 | Tendance soutenue | 2.143 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2024-07-14 | 36 | Tendance soutenue | 1.779 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-07-14 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2024-07-21 | 44 | Tendance soutenue | 1.911 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2024-07-28 | 43 | Tendance soutenue | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2024-08-18 | 42 | Pic isolé | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2024-09-01 | 44 | Tendance soutenue | 2.979 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-09-01 | 38 | Tendance soutenue | 2.912 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2024-09-08 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2024-09-08 | 38 | Tendance soutenue | 2.079 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-09-08 | 33 | Tendance soutenue | 2.057 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2024-09-22 | 37 | Tendance soutenue | 1.506 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2024-09-29 | 41 | Tendance soutenue | 1.738 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_traditionnelles | Crelan | 2024-09-29 | 30 | Pic isolé | 1.544 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | 2024-12-15 | 36 | Pic isolé | 1.779 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-12-15 | 32 | Pic isolé | 1.886 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2024-12-29 | 30 | Pic isolé | 1.544 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2025-02-23 | 43 | Tendance soutenue | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-03-02 | 42 | Tendance soutenue | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-03-09 | 37 | Tendance soutenue | 1.506 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2025-03-23 | 35 | Tendance soutenue | 1.629 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2025-03-23 | 31 | Tendance soutenue | 1.715 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | 2025-03-30 | 38 | Tendance soutenue | 2.079 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2025-03-30 | 33 | Tendance soutenue | 2.057 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2025-05-18 | 37 | Tendance soutenue | 1.506 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-05-25 | 46 | Tendance soutenue | 2.027 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-06-01 | 47 | Tendance soutenue | 2.085 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-06-22 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_traditionnelles | Crelan | 2025-06-29 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2025-07-06 | 42 | Pic isolé | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| contexte_fusion_crelan_axa | Crelan | 2025-07-06 | 36 | Pic isolé | 1.779 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | 2025-07-06 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| carte_credit_crelan | Crelan visa | 2025-11-02 | 42 | Tendance soutenue | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| app_mobile_crelan | Crelan app | 2025-11-09 | 13 | Pic isolé | 2.967 | 0.345 | selected_low_coverage,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-11-09 | 41 | Tendance soutenue | 1.738 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2025-11-30 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-02-01 | 41 | Pic isolé | 1.738 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-02-15 | 43 | Pic isolé | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-03-01 | 43 | Pic isolé | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-04-12 | 38 | Pic isolé | 1.564 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| app_mobile_crelan | Crelan app | 2026-05-10 | 8 | Pic isolé | 1.639 | 0.345 | selected_low_coverage,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-05-10 | 44 | Tendance soutenue | 1.911 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-05-17 | 39 | Tendance soutenue | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-06-28 | 65 | Pic isolé | 3.129 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-07-12 | 38 | Pic isolé | 1.564 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-07-26 | 51 | Tendance soutenue | 2.317 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-08-02 | 42 | Tendance soutenue | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | 2026-08-16 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
