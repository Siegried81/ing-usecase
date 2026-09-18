# Export des données Revolut — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque Revolut (code `REVOLUT`, segment : néobanque).

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
| 2025-05-01 | Revolut | Comptes belges (IBAN BE) pour les nouveaux clients, migration des clients existants au cours de 2025 |
| 2025-08-21 | Revolut | Lancement du compte épargne à intérêts versés quotidiennement (date de couverture presse) |

## Fiches produits Revolut

| Fiche produit | Termes de recherche Revolut |
|---|---|
| Compte à vue particulier (Revolut vs ING) (`compte_a_vue_revolut`) | compte Revolut |
| Marques — néobanques (`marque_generique_neobanques`) | Revolut |

### Notes produit

- `app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau d'agences.

## Données Google Trends brutes

524 points hebdomadaires, 2 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`revolut_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (49)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| compte_a_vue_revolut | compte Revolut | 2024-08-25 | 79 | Pic isolé | 1.893 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2024-12-29 | 69 | Pic isolé | 1.542 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-04-06 | 92 | Pic isolé | 2.349 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-06-22 | 70 | Pic isolé | 1.577 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-07-06 | 73 | Pic isolé | 1.683 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-08-10 | 77 | Tendance soutenue | 1.823 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-08-17 | 100 | Tendance soutenue | 2.63 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2025-08-17 | 12 | Tendance soutenue | 2.742 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2025-08-24 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2025-09-07 | 72 | Pic isolé | 1.647 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-09-21 | 72 | Pic isolé | 1.647 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2025-11-02 | 83 | Pic isolé | 2.034 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2025-11-02 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2025-11-23 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2025-11-30 | 81 | Pic isolé | 1.963 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2025-11-30 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2025-12-14 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2025-12-28 | 9 | Pic isolé | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-01-04 | 70 | Pic isolé | 1.577 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-01-11 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-01-18 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-02-22 | 77 | Pic isolé | 1.823 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-03-15 | 10 | Tendance soutenue | 1.976 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-03-22 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-04-05 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-04-12 | 71 | Pic isolé | 1.612 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-04-12 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-04-19 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-05-03 | 81 | Tendance soutenue | 1.963 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-05-03 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-05-10 | 78 | Tendance soutenue | 1.858 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-05-10 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-05-17 | 71 | Tendance soutenue | 1.612 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-05-17 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-05-24 | 70 | Tendance soutenue | 1.577 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | 2026-05-31 | 68 | Tendance soutenue | 1.507 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-05-31 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-06-07 | 74 | Tendance soutenue | 1.718 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-06-07 | 10 | Tendance soutenue | 1.976 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-06-28 | 85 | Pic isolé | 2.104 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-07-05 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-08-02 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-08-09 | 71 | Tendance soutenue | 1.612 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-08-09 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| compte_a_vue_revolut | compte Revolut | 2026-08-16 | 73 | Tendance soutenue | 1.683 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| marque_generique_neobanques | Revolut | 2026-08-16 | 10 | Tendance soutenue | 1.976 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-08-30 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-09-06 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | 2026-09-13 | 19 | Tendance soutenue | 5.424 | 1.000 |  |
