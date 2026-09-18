# Export des données bunq — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque bunq (code `BUNQ`, segment : néobanque).

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
| 2024-12-17 | bunq | bunq Stocks disponible en Belgique |
| 2026-07-24 | bunq | Lancement des IBAN belges et de Wero en Belgique (date de couverture presse) |

## Fiches produits bunq

| Fiche produit | Termes de recherche bunq |
|---|---|
| Marques — néobanques (`marque_generique_neobanques`) | bunq |

### Notes produit

- `app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau d'agences.

## Données Google Trends brutes

262 points hebdomadaires, 1 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`bunq_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (9)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| marque_generique_neobanques | bunq | 2022-02-27 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2023-04-02 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2024-12-15 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2025-03-16 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2025-05-25 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2025-09-14 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2025-11-23 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2026-02-15 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | 2026-07-26 | 1 | Pic isolé | 5.302 | 0.038 |  |
