# Export des données ING — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Toutes les données ci-dessous concernent uniquement la banque ING (code `ING`, segment : traditionnelle).

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

## Fiches produits ING

| Fiche produit | Termes de recherche ING |
|---|---|
| Compte professionnel / indépendant (`compte_professionnel`) | compte professionnel ING, ING zakelijke rekening, Business'Bank ING |
| Compte à vue particulier (`compte_a_vue`) | compte à vue ING, ING zichtrekening, ING Do Basic |
| Compte épargne particulier (`compte_epargne`) | compte épargne ING, ING spaarrekening, ING Orange Savings |
| Investissement / courtage en ligne (`investissement_courtage`) | ING Self Invest |
| Application mobile bancaire (`app_mobile`) | ING Banking, ING Smart Banking |
| Carte de crédit (`carte_credit`) | carte de crédit ING, ING kredietkaart, ING Card |
| Épargne-pension (`epargne_pension`) | épargne pension ING, ING pensioensparen, ING Star Fund |
| Assurance habitation (`assurance_habitation`) | assurance habitation ING, ING Home Insurance |
| Prêt hypothécaire (`pret_hypothecaire`) | prêt hypothécaire ING, ING hypothecair krediet |
| Compte professionnel / indépendant (CBC vs ING) (`compte_professionnel_cbc`) | compte professionnel ING, ING zakelijke rekening, Business'Bank ING |
| Compte à vue particulier (CBC vs ING) (`compte_a_vue_cbc`) | compte à vue ING, ING zichtrekening, ING Do Basic |
| Compte épargne particulier (CBC vs ING) (`compte_epargne_cbc`) | compte épargne ING, ING spaarrekening, ING Orange Savings |
| Application mobile bancaire (CBC vs ING) (`app_mobile_cbc`) | ING Banking, ING Smart Banking |
| Carte de crédit (CBC vs ING) (`carte_credit_cbc`) | carte de crédit ING, ING kredietkaart, ING Card |
| Épargne-pension (CBC vs ING) (`epargne_pension_cbc`) | épargne pension ING, ING pensioensparen, ING Star Fund |
| Assurance habitation (CBC vs ING) (`assurance_habitation_cbc`) | assurance habitation ING, ING Home Insurance |
| Prêt hypothécaire (CBC vs ING) (`pret_hypothecaire_cbc`) | prêt hypothécaire ING, ING hypothecair krediet |
| Marque (recherche générique) (`marque_generique`) | ING |
| Compte à vue particulier (BNP Paribas Fortis vs ING) (`compte_a_vue_bnppf`) | compte à vue ING, ING zichtrekening, ING Do Basic |
| Application mobile bancaire (BNP Paribas Fortis vs ING) (`app_mobile_bnppf`) | ING Banking, ING Smart Banking |
| Carte de crédit (BNP Paribas Fortis vs ING) (`carte_credit_bnppf`) | carte de crédit ING, ING kredietkaart, ING Card |
| Épargne-pension (BNP Paribas Fortis vs ING) (`epargne_pension_bnppf`) | épargne pension ING, ING pensioensparen, ING Star Fund |
| Compte à vue particulier (Argenta vs ING) (`compte_a_vue_argenta`) | compte à vue ING, ING zichtrekening, ING Do Basic |
| Compte épargne particulier (Argenta vs ING) (`compte_epargne_argenta`) | compte épargne ING, ING spaarrekening, ING Orange Savings |
| Application mobile bancaire (Argenta vs ING) (`app_mobile_argenta`) | ING Banking, ING Smart Banking |
| Application mobile bancaire (Crelan vs ING) (`app_mobile_crelan`) | ING Banking, ING Smart Banking |
| Carte de crédit (Crelan vs ING) (`carte_credit_crelan`) | carte de crédit ING, ING kredietkaart, ING Card |
| Compte à vue particulier (Revolut vs ING) (`compte_a_vue_revolut`) | compte à vue ING, ING zichtrekening, ING Do Basic |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | ING |
| Marques — néobanques (`marque_generique_neobanques`) | ING |
| Contexte — intégration de bpost banque dans BNP Paribas Fortis (janvier 2024) (`contexte_integration_bnppf_bpost`) | ING |
| Contexte — fusion d'AXA Bank Belgium dans Crelan (juin 2024) (`contexte_fusion_crelan_axa`) | ING |

## Données Google Trends brutes

19650 points hebdomadaires, 23 termes, du 2021-09-12 au 2026-09-13. Fournies séparément dans **`ing_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (525)

| Fiche produit | Terme | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|
| app_mobile | ING Banking | 2021-09-19 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-09-19 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | 2021-09-19 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_cbc | ING Banking | 2021-09-19 | 58 | Tendance soutenue | 1.924 |  |  |
| app_mobile_crelan | ING Banking | 2021-09-19 | 57 | Tendance soutenue | 1.94 |  |  |
| epargne_pension | ING pensioensparen | 2021-09-19 | 51 | Pic isolé | 12.41 |  |  |
| epargne_pension_cbc | ING pensioensparen | 2021-09-19 | 51 | Pic isolé | 12.398 |  |  |
| app_mobile | ING Banking | 2021-09-26 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-09-26 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_bnppf | ING Banking | 2021-09-26 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_cbc | ING Banking | 2021-09-26 | 59 | Tendance soutenue | 2.028 |  |  |
| app_mobile_crelan | ING Banking | 2021-09-26 | 61 | Tendance soutenue | 2.366 |  |  |
| contexte_fusion_crelan_axa | ING | 2021-09-26 | 88 | Pic isolé | 2.73 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | 2021-09-26 | 88 | Pic isolé | 2.728 | 1.000 |  |
| epargne_pension_bnppf | ING Star Fund | 2021-09-26 | 46 | Tendance soutenue | 3.504 |  |  |
| marque_generique | ING | 2021-09-26 | 77 | Pic isolé | 2.698 |  |  |
| marque_generique_neobanques | ING | 2021-09-26 | 76 | Pic isolé | 2.67 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2021-09-26 | 76 | Pic isolé | 2.67 | 1.000 |  |
| app_mobile | ING Banking | 2021-10-03 | 17 | Tendance soutenue | 2.799 |  |  |
| app_mobile_argenta | ING Banking | 2021-10-03 | 65 | Tendance soutenue | 2.791 |  |  |
| app_mobile_bnppf | ING Banking | 2021-10-03 | 65 | Tendance soutenue | 2.791 |  |  |
| app_mobile_cbc | ING Banking | 2021-10-03 | 67 | Tendance soutenue | 2.863 |  |  |
| app_mobile_crelan | ING Banking | 2021-10-03 | 65 | Tendance soutenue | 2.791 |  |  |
| carte_credit_bnppf | carte de crédit ING | 2021-10-03 | 37 | Pic isolé | 6.564 |  |  |
| carte_credit_crelan | carte de crédit ING | 2021-10-03 | 37 | Pic isolé | 6.564 |  |  |
| epargne_pension | ING Star Fund | 2021-10-03 | 49 | Pic isolé | 3.152 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2021-10-03 | 41 | Tendance soutenue | 3.088 |  |  |
| epargne_pension_cbc | ING Star Fund | 2021-10-03 | 49 | Pic isolé | 3.154 |  |  |
| app_mobile | ING Banking | 2021-10-10 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile_cbc | ING Banking | 2021-10-10 | 62 | Tendance soutenue | 2.341 |  |  |
| app_mobile | ING Banking | 2021-10-17 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-10-17 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | 2021-10-17 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_cbc | ING Banking | 2021-10-17 | 58 | Tendance soutenue | 1.924 |  |  |
| app_mobile_crelan | ING Banking | 2021-10-17 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile | ING Banking | 2021-10-24 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile | ING Smart Banking | 2021-10-24 | 1 | Pic isolé | 11.402 |  |  |
| app_mobile_argenta | ING Banking | 2021-10-24 | 63 | Tendance soutenue | 2.578 |  |  |
| app_mobile_bnppf | ING Banking | 2021-10-24 | 63 | Tendance soutenue | 2.578 |  |  |
| app_mobile_cbc | ING Banking | 2021-10-24 | 62 | Tendance soutenue | 2.341 |  |  |
| app_mobile_cbc | ING Smart Banking | 2021-10-24 | 4 | Pic isolé | 11.402 |  |  |
| app_mobile_crelan | ING Banking | 2021-10-24 | 63 | Tendance soutenue | 2.578 |  |  |
| carte_credit | ING Card | 2021-10-24 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit_bnppf | ING Card | 2021-10-24 | 94 | Pic isolé | 1.783 |  |  |
| carte_credit_cbc | ING Card | 2021-10-24 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit_crelan | ING Card | 2021-10-24 | 94 | Pic isolé | 1.783 |  |  |
| app_mobile | ING Banking | 2021-10-31 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-10-31 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_bnppf | ING Banking | 2021-10-31 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_cbc | ING Banking | 2021-10-31 | 59 | Tendance soutenue | 2.028 |  |  |
| app_mobile_crelan | ING Banking | 2021-10-31 | 61 | Tendance soutenue | 2.366 |  |  |
| epargne_pension | ING Star Fund | 2021-10-31 | 50 | Pic isolé | 3.223 |  |  |
| epargne_pension_cbc | ING Star Fund | 2021-10-31 | 50 | Pic isolé | 3.224 |  |  |
| app_mobile | ING Banking | 2021-11-07 | 19 | Tendance soutenue | 3.613 |  |  |
| app_mobile_argenta | ING Banking | 2021-11-07 | 71 | Tendance soutenue | 3.43 |  |  |
| app_mobile_bnppf | ING Banking | 2021-11-07 | 71 | Tendance soutenue | 3.43 |  |  |
| app_mobile_cbc | ING Banking | 2021-11-07 | 75 | Tendance soutenue | 3.697 |  |  |
| app_mobile_crelan | ING Banking | 2021-11-07 | 71 | Tendance soutenue | 3.43 |  |  |
| app_mobile_argenta | ING Banking | 2021-11-14 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_bnppf | ING Banking | 2021-11-14 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_cbc | ING Banking | 2021-11-14 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_crelan | ING Banking | 2021-11-14 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile | ING Banking | 2021-11-21 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-11-21 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_bnppf | ING Banking | 2021-11-21 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_cbc | ING Banking | 2021-11-21 | 59 | Tendance soutenue | 2.028 |  |  |
| app_mobile_crelan | ING Banking | 2021-11-21 | 58 | Tendance soutenue | 2.046 |  |  |
| epargne_pension | ING Star Fund | 2021-11-21 | 53 | Pic isolé | 3.435 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2021-11-21 | 37 | Pic isolé | 2.756 |  |  |
| epargne_pension_cbc | ING Star Fund | 2021-11-21 | 53 | Pic isolé | 3.437 |  |  |
| app_mobile | ING Banking | 2021-11-28 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-11-28 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | 2021-11-28 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_cbc | ING Banking | 2021-11-28 | 58 | Tendance soutenue | 1.924 |  |  |
| app_mobile_crelan | ING Banking | 2021-11-28 | 57 | Tendance soutenue | 1.94 |  |  |
| carte_credit | ING kredietkaart | 2021-11-28 | 25 | Pic isolé | 6.225 |  |  |
| carte_credit_cbc | ING kredietkaart | 2021-11-28 | 25 | Pic isolé | 6.272 |  |  |
| app_mobile_argenta | ING Banking | 2021-12-05 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_argenta | ING Smart Banking | 2021-12-05 | 4 | Pic isolé | 16.155 |  |  |
| app_mobile_bnppf | ING Banking | 2021-12-05 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_bnppf | ING Smart Banking | 2021-12-05 | 4 | Pic isolé | 16.155 |  |  |
| app_mobile_cbc | ING Banking | 2021-12-05 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_crelan | ING Banking | 2021-12-05 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_crelan | ING Smart Banking | 2021-12-05 | 4 | Pic isolé | 16.155 |  |  |
| carte_credit_bnppf | ING Card | 2021-12-05 | 92 | Pic isolé | 1.688 |  |  |
| carte_credit_crelan | ING Card | 2021-12-05 | 92 | Pic isolé | 1.688 |  |  |
| pret_hypothecaire | prêt hypothécaire ING | 2021-12-05 | 71 | Pic isolé | 9.541 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire ING | 2021-12-05 | 61 | Pic isolé | 9.546 |  |  |
| app_mobile | ING Banking | 2021-12-12 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile_argenta | ING Banking | 2021-12-12 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | 2021-12-12 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_cbc | ING Banking | 2021-12-12 | 61 | Tendance soutenue | 2.237 |  |  |
| app_mobile_crelan | ING Banking | 2021-12-12 | 57 | Tendance soutenue | 1.94 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2021-12-12 | 48 | Pic isolé | 3.67 |  |  |
| app_mobile | ING Banking | 2021-12-19 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile_argenta | ING Banking | 2021-12-19 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_bnppf | ING Banking | 2021-12-19 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_cbc | ING Banking | 2021-12-19 | 61 | Tendance soutenue | 2.237 |  |  |
| app_mobile_crelan | ING Banking | 2021-12-19 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile | ING Banking | 2021-12-26 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2021-12-26 | 60 | Tendance soutenue | 2.259 |  |  |
| app_mobile_bnppf | ING Banking | 2021-12-26 | 60 | Tendance soutenue | 2.259 |  |  |
| app_mobile_cbc | ING Banking | 2021-12-26 | 57 | Tendance soutenue | 1.819 |  |  |
| app_mobile_crelan | ING Banking | 2021-12-26 | 60 | Tendance soutenue | 2.259 |  |  |
| epargne_pension | ING Star Fund | 2021-12-26 | 63 | Pic isolé | 4.142 |  |  |
| epargne_pension_cbc | ING Star Fund | 2021-12-26 | 63 | Pic isolé | 4.144 |  |  |
| app_mobile | ING Banking | 2022-01-02 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2022-01-02 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_bnppf | ING Banking | 2022-01-02 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_cbc | ING Banking | 2022-01-02 | 60 | Tendance soutenue | 2.132 |  |  |
| app_mobile_crelan | ING Banking | 2022-01-02 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_argenta | ING Banking | 2022-01-09 | 56 | Tendance soutenue | 1.834 |  |  |
| app_mobile_bnppf | ING Banking | 2022-01-09 | 56 | Tendance soutenue | 1.834 |  |  |
| app_mobile_crelan | ING Banking | 2022-01-09 | 56 | Tendance soutenue | 1.834 |  |  |
| carte_credit | ING Card | 2022-01-09 | 81 | Pic isolé | 1.862 |  |  |
| carte_credit_bnppf | ING Card | 2022-01-09 | 89 | Pic isolé | 1.545 |  |  |
| carte_credit_cbc | ING Card | 2022-01-09 | 81 | Pic isolé | 1.862 |  |  |
| carte_credit_crelan | ING Card | 2022-01-09 | 89 | Pic isolé | 1.545 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2022-01-09 | 50 | Pic isolé | 3.836 |  |  |
| app_mobile | ING Banking | 2022-01-16 | 15 | Pic isolé | 1.985 |  |  |
| app_mobile_argenta | ING Banking | 2022-01-16 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | 2022-01-16 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_cbc | ING Banking | 2022-01-16 | 59 | Pic isolé | 2.028 |  |  |
| app_mobile_crelan | ING Banking | 2022-01-16 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile | ING Banking | 2022-01-30 | 17 | Tendance soutenue | 2.799 |  |  |
| app_mobile_argenta | ING Banking | 2022-01-30 | 64 | Tendance soutenue | 2.685 |  |  |
| app_mobile_bnppf | ING Banking | 2022-01-30 | 64 | Tendance soutenue | 2.685 |  |  |
| app_mobile_cbc | ING Banking | 2022-01-30 | 66 | Tendance soutenue | 2.758 |  |  |
| app_mobile_crelan | ING Banking | 2022-01-30 | 64 | Tendance soutenue | 2.685 |  |  |
| carte_credit | ING Card | 2022-01-30 | 77 | Tendance soutenue | 1.646 |  |  |
| carte_credit_cbc | ING Card | 2022-01-30 | 77 | Tendance soutenue | 1.646 |  |  |
| marque_generique | ING | 2022-01-30 | 78 | Pic isolé | 2.816 |  |  |
| app_mobile | ING Banking | 2022-02-06 | 14 | Tendance soutenue | 1.578 |  |  |
| app_mobile_argenta | ING Banking | 2022-02-06 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_bnppf | ING Banking | 2022-02-06 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_cbc | ING Banking | 2022-02-06 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_crelan | ING Banking | 2022-02-06 | 53 | Tendance soutenue | 1.514 |  |  |
| carte_credit | ING Card | 2022-02-06 | 76 | Tendance soutenue | 1.592 |  |  |
| carte_credit_cbc | ING Card | 2022-02-06 | 76 | Tendance soutenue | 1.592 |  |  |
| app_mobile | ING Banking | 2022-02-13 | 14 | Tendance soutenue | 1.578 |  |  |
| app_mobile_argenta | ING Banking | 2022-02-13 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_bnppf | ING Banking | 2022-02-13 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_cbc | ING Banking | 2022-02-13 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_crelan | ING Banking | 2022-02-13 | 53 | Tendance soutenue | 1.514 |  |  |
| epargne_pension | ING Star Fund | 2022-02-20 | 41 | Pic isolé | 2.587 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2022-02-20 | 29 | Pic isolé | 2.091 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-02-20 | 41 | Pic isolé | 2.588 |  |  |
| app_mobile | ING Banking | 2022-02-27 | 14 | Pic isolé | 1.578 |  |  |
| app_mobile_argenta | ING Banking | 2022-02-27 | 56 | Pic isolé | 1.834 |  |  |
| app_mobile_bnppf | ING Banking | 2022-02-27 | 56 | Pic isolé | 1.834 |  |  |
| app_mobile_cbc | ING Banking | 2022-02-27 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_crelan | ING Banking | 2022-02-27 | 56 | Pic isolé | 1.834 |  |  |
| contexte_fusion_crelan_axa | ING | 2022-02-27 | 87 | Pic isolé | 2.624 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | 2022-02-27 | 87 | Pic isolé | 2.622 | 1.000 |  |
| marque_generique | ING | 2022-02-27 | 75 | Pic isolé | 2.462 |  |  |
| marque_generique_neobanques | ING | 2022-02-27 | 76 | Pic isolé | 2.67 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2022-02-27 | 76 | Pic isolé | 2.67 | 1.000 |  |
| app_mobile_cbc | ING Banking | 2022-03-06 | 57 | Tendance soutenue | 1.819 |  |  |
| investissement_courtage | ING Self Invest | 2022-03-06 | 2 | Tendance soutenue | 4.342 |  |  |
| compte_a_vue | ING zichtrekening | 2022-03-13 | 19 | Pic isolé | 4.71 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2022-03-13 | 48 | Pic isolé | 4.545 |  |  |
| investissement_courtage | ING Self Invest | 2022-03-13 | 2 | Tendance soutenue | 4.342 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2022-03-27 | 17 | Pic isolé | 2.695 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2022-03-27 | 10 | Pic isolé | 2.795 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2022-03-27 | 25 | Pic isolé | 2.705 |  |  |
| epargne_pension | ING Star Fund | 2022-04-03 | 36 | Pic isolé | 2.234 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-04-03 | 36 | Pic isolé | 2.235 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2022-04-17 | 15 | Pic isolé | 2.35 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2022-04-17 | 9 | Pic isolé | 2.492 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2022-04-17 | 23 | Pic isolé | 2.47 |  |  |
| compte_a_vue | ING zichtrekening | 2022-05-01 | 12 | Pic isolé | 2.913 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2022-05-01 | 31 | Pic isolé | 2.874 |  |  |
| contexte_fusion_crelan_axa | ING | 2022-05-01 | 84 | Pic isolé | 2.308 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | 2022-05-01 | 84 | Pic isolé | 2.306 | 1.000 |  |
| marque_generique | ING | 2022-05-01 | 69 | Pic isolé | 1.754 |  |  |
| marque_generique_neobanques | ING | 2022-05-01 | 73 | Pic isolé | 2.306 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2022-05-01 | 73 | Pic isolé | 2.306 | 1.000 |  |
| carte_credit | ING Card | 2022-05-22 | 83 | Pic isolé | 1.97 |  |  |
| carte_credit_bnppf | ING Card | 2022-05-22 | 98 | Pic isolé | 1.974 |  |  |
| carte_credit_cbc | ING Card | 2022-05-22 | 83 | Pic isolé | 1.97 |  |  |
| carte_credit_crelan | ING Card | 2022-05-22 | 98 | Pic isolé | 1.973 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2022-06-12 | 37 | Pic isolé | 2.756 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2022-06-19 | 31 | Pic isolé | 5.431 |  |  |
| carte_credit_crelan | ING kredietkaart | 2022-06-19 | 31 | Pic isolé | 5.431 |  |  |
| carte_credit_bnppf | carte de crédit ING | 2022-06-26 | 28 | Pic isolé | 4.929 |  |  |
| carte_credit_crelan | carte de crédit ING | 2022-06-26 | 28 | Pic isolé | 4.929 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2022-06-26 | 39 | Pic isolé | 2.922 |  |  |
| carte_credit | ING Card | 2022-07-03 | 79 | Pic isolé | 1.754 |  |  |
| carte_credit_bnppf | ING Card | 2022-07-03 | 90 | Tendance soutenue | 1.593 |  |  |
| carte_credit_cbc | ING Card | 2022-07-03 | 79 | Pic isolé | 1.754 |  |  |
| carte_credit_crelan | ING Card | 2022-07-03 | 90 | Tendance soutenue | 1.593 |  |  |
| marque_generique | ING | 2022-07-03 | 69 | Pic isolé | 1.754 |  |  |
| marque_generique_neobanques | ING | 2022-07-03 | 68 | Pic isolé | 1.7 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2022-07-03 | 68 | Pic isolé | 1.7 | 1.000 |  |
| carte_credit_bnppf | ING Card | 2022-07-10 | 100 | Tendance soutenue | 2.069 |  |  |
| carte_credit_crelan | ING Card | 2022-07-10 | 100 | Tendance soutenue | 2.068 |  |  |
| compte_professionnel | ING zakelijke rekening | 2022-07-31 | 81 | Pic isolé | 12.661 |  |  |
| compte_professionnel_cbc | ING zakelijke rekening | 2022-07-31 | 79 | Pic isolé | 12.702 |  |  |
| carte_credit | ING Card | 2022-08-07 | 77 | Pic isolé | 1.646 |  |  |
| carte_credit_bnppf | ING Card | 2022-08-07 | 94 | Pic isolé | 1.783 |  |  |
| carte_credit_cbc | ING Card | 2022-08-07 | 77 | Pic isolé | 1.646 |  |  |
| carte_credit_crelan | ING Card | 2022-08-07 | 94 | Pic isolé | 1.783 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2022-08-28 | 23 | Pic isolé | 3.73 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2022-08-28 | 13 | Pic isolé | 3.705 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2022-08-28 | 34 | Pic isolé | 3.764 |  |  |
| epargne_pension | ING Star Fund | 2022-08-28 | 48 | Pic isolé | 3.082 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-08-28 | 48 | Pic isolé | 3.083 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2022-09-11 | 28 | Pic isolé | 4.888 |  |  |
| carte_credit_crelan | ING kredietkaart | 2022-09-11 | 28 | Pic isolé | 4.888 |  |  |
| epargne_pension | ING Star Fund | 2022-09-11 | 41 | Pic isolé | 2.587 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-09-11 | 41 | Pic isolé | 2.588 |  |  |
| compte_a_vue | compte à vue ING | 2022-10-02 | 15 | Pic isolé | 15.876 |  |  |
| compte_a_vue_cbc | compte à vue ING | 2022-10-02 | 39 | Pic isolé | 15.942 |  |  |
| epargne_pension | ING Star Fund | 2022-10-09 | 57 | Pic isolé | 3.718 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-10-09 | 57 | Pic isolé | 3.719 |  |  |
| carte_credit | carte de crédit ING | 2022-10-16 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit_cbc | carte de crédit ING | 2022-10-16 | 23 | Pic isolé | 6.18 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2022-10-23 | 25 | Pic isolé | 4.074 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2022-10-23 | 14 | Pic isolé | 4.009 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2022-10-23 | 37 | Pic isolé | 4.117 |  |  |
| epargne_pension | ING Star Fund | 2022-11-06 | 48 | Tendance soutenue | 3.082 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-11-06 | 48 | Tendance soutenue | 3.083 |  |  |
| carte_credit | ING kredietkaart | 2022-11-13 | 25 | Pic isolé | 6.225 |  |  |
| carte_credit_cbc | ING kredietkaart | 2022-11-13 | 25 | Pic isolé | 6.272 |  |  |
| epargne_pension | ING Star Fund | 2022-11-13 | 40 | Tendance soutenue | 2.516 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-11-13 | 40 | Tendance soutenue | 2.517 |  |  |
| epargne_pension | ING Star Fund | 2022-11-27 | 39 | Pic isolé | 2.446 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-11-27 | 39 | Pic isolé | 2.447 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2022-12-04 | 36 | Pic isolé | 2.673 |  |  |
| epargne_pension | ING pensioensparen | 2022-12-18 | 42 | Pic isolé | 10.203 |  |  |
| epargne_pension_cbc | ING pensioensparen | 2022-12-18 | 42 | Pic isolé | 10.193 |  |  |
| compte_epargne | ING spaarrekening | 2022-12-25 | 38 | Tendance soutenue | 2.95 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2022-12-25 | 26 | Tendance soutenue | 2.965 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2022-12-25 | 77 | Tendance soutenue | 2.907 |  |  |
| epargne_pension | ING Star Fund | 2022-12-25 | 50 | Pic isolé | 3.223 |  |  |
| epargne_pension_cbc | ING Star Fund | 2022-12-25 | 50 | Pic isolé | 3.224 |  |  |
| compte_epargne | ING spaarrekening | 2023-01-01 | 47 | Tendance soutenue | 3.81 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-01-01 | 31 | Tendance soutenue | 3.67 |  |  |
| compte_epargne_argenta | compte épargne ING | 2023-01-01 | 7 | Pic isolé | 9.702 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-01-01 | 97 | Tendance soutenue | 3.839 |  |  |
| compte_professionnel | ING zakelijke rekening | 2023-01-01 | 63 | Pic isolé | 9.826 |  |  |
| compte_professionnel_cbc | ING zakelijke rekening | 2023-01-01 | 61 | Pic isolé | 9.786 |  |  |
| compte_epargne | ING spaarrekening | 2023-01-08 | 35 | Tendance soutenue | 2.663 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-01-08 | 26 | Tendance soutenue | 2.965 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-01-08 | 72 | Tendance soutenue | 2.674 |  |  |
| epargne_pension | ING Star Fund | 2023-01-08 | 48 | Tendance soutenue | 3.082 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-01-08 | 36 | Tendance soutenue | 2.673 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-01-08 | 48 | Tendance soutenue | 3.083 |  |  |
| compte_epargne | ING Orange Savings | 2023-01-15 | 11 | Pic isolé | 6.485 |  |  |
| compte_epargne | ING spaarrekening | 2023-01-15 | 24 | Tendance soutenue | 1.612 |  |  |
| compte_epargne_cbc | ING Orange Savings | 2023-01-15 | 22 | Pic isolé | 6.557 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-01-15 | 49 | Tendance soutenue | 1.602 |  |  |
| epargne_pension | ING Star Fund | 2023-01-15 | 48 | Tendance soutenue | 3.082 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-01-15 | 34 | Tendance soutenue | 2.507 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-01-15 | 48 | Tendance soutenue | 3.083 |  |  |
| compte_epargne | ING spaarrekening | 2023-01-22 | 25 | Tendance soutenue | 1.708 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-01-22 | 19 | Tendance soutenue | 1.977 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-01-22 | 51 | Tendance soutenue | 1.695 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-01-22 | 49 | Tendance soutenue | 3.753 |  |  |
| epargne_pension_bnppf | épargne pension ING | 2023-01-22 | 39 | Pic isolé | 16.155 |  |  |
| compte_epargne | ING spaarrekening | 2023-01-29 | 29 | Tendance soutenue | 2.09 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-01-29 | 20 | Tendance soutenue | 2.118 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-01-29 | 60 | Tendance soutenue | 2.115 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-01-29 | 34 | Tendance soutenue | 2.507 |  |  |
| carte_credit | ING Card | 2023-02-05 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit | ING kredietkaart | 2023-02-05 | 26 | Pic isolé | 6.48 |  |  |
| carte_credit_cbc | ING Card | 2023-02-05 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit_cbc | ING kredietkaart | 2023-02-05 | 26 | Pic isolé | 6.529 |  |  |
| investissement_courtage | ING Self Invest | 2023-02-05 | 3 | Pic isolé | 6.595 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2023-03-05 | 28 | Pic isolé | 4.888 |  |  |
| carte_credit_crelan | ING kredietkaart | 2023-03-05 | 28 | Pic isolé | 4.888 |  |  |
| epargne_pension | ING Star Fund | 2023-03-05 | 42 | Pic isolé | 2.658 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-03-05 | 37 | Pic isolé | 2.756 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-03-05 | 42 | Pic isolé | 2.659 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2023-03-19 | 24 | Pic isolé | 4.164 |  |  |
| carte_credit_crelan | ING kredietkaart | 2023-03-19 | 24 | Pic isolé | 4.164 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-03-26 | 31 | Pic isolé | 2.257 |  |  |
| carte_credit_bnppf | ING Card | 2023-04-16 | 98 | Pic isolé | 1.974 |  |  |
| carte_credit_crelan | ING Card | 2023-04-16 | 98 | Pic isolé | 1.973 |  |  |
| compte_epargne | compte épargne ING | 2023-04-23 | 13 | Pic isolé | 8.862 |  |  |
| compte_epargne_cbc | compte épargne ING | 2023-04-23 | 26 | Pic isolé | 8.405 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-04-23 | 38 | Pic isolé | 2.839 |  |  |
| epargne_pension | ING Star Fund | 2023-05-21 | 49 | Pic isolé | 3.152 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-05-21 | 35 | Pic isolé | 2.59 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-05-21 | 49 | Pic isolé | 3.154 |  |  |
| compte_professionnel | compte professionnel ING | 2023-05-28 | 73 | Pic isolé | 9.898 |  |  |
| compte_professionnel_cbc | compte professionnel ING | 2023-05-28 | 71 | Pic isolé | 9.883 |  |  |
| compte_a_vue | ING Do Basic | 2023-06-04 | 18 | Pic isolé | 16.155 |  |  |
| compte_a_vue_argenta | ING Do Basic | 2023-06-04 | 22 | Pic isolé | 11.402 |  |  |
| compte_a_vue_bnppf | ING Do Basic | 2023-06-04 | 13 | Pic isolé | 11.402 |  |  |
| compte_a_vue_cbc | ING Do Basic | 2023-06-04 | 46 | Pic isolé | 16.155 |  |  |
| compte_a_vue_revolut | ING Do Basic | 2023-06-04 | 32 | Pic isolé | 11.224 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2023-07-09 | 27 | Pic isolé | 4.419 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2023-07-09 | 15 | Pic isolé | 4.312 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2023-07-09 | 39 | Pic isolé | 4.353 |  |  |
| carte_credit_bnppf | ING Card | 2023-07-16 | 96 | Pic isolé | 1.878 |  |  |
| carte_credit_crelan | ING Card | 2023-07-16 | 96 | Pic isolé | 1.878 |  |  |
| compte_epargne | ING spaarrekening | 2023-07-30 | 32 | Tendance soutenue | 2.377 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-07-30 | 21 | Pic isolé | 2.259 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-07-30 | 66 | Tendance soutenue | 2.394 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-07-30 | 52 | Pic isolé | 4.002 |  |  |
| carte_credit | ING Card | 2023-08-06 | 75 | Pic isolé | 1.538 |  |  |
| carte_credit_bnppf | ING Card | 2023-08-06 | 93 | Pic isolé | 1.736 |  |  |
| carte_credit_cbc | ING Card | 2023-08-06 | 75 | Pic isolé | 1.538 |  |  |
| carte_credit_crelan | ING Card | 2023-08-06 | 93 | Pic isolé | 1.735 |  |  |
| compte_epargne | ING spaarrekening | 2023-08-06 | 27 | Tendance soutenue | 1.899 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-08-06 | 55 | Tendance soutenue | 1.882 |  |  |
| compte_epargne | ING spaarrekening | 2023-08-20 | 45 | Tendance soutenue | 3.619 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-08-20 | 28 | Tendance soutenue | 3.247 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-08-20 | 92 | Tendance soutenue | 3.606 |  |  |
| investissement_courtage | ING Self Invest | 2023-08-20 | 3 | Tendance soutenue | 6.595 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2023-08-27 | 21 | Pic isolé | 3.385 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2023-08-27 | 12 | Pic isolé | 3.402 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2023-08-27 | 31 | Pic isolé | 3.411 |  |  |
| compte_epargne | ING spaarrekening | 2023-08-27 | 37 | Tendance soutenue | 2.854 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-08-27 | 26 | Tendance soutenue | 2.965 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-08-27 | 76 | Tendance soutenue | 2.86 |  |  |
| contexte_fusion_crelan_axa | ING | 2023-08-27 | 80 | Pic isolé | 1.885 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | 2023-08-27 | 80 | Pic isolé | 1.884 | 1.000 |  |
| investissement_courtage | ING Self Invest | 2023-08-27 | 3 | Tendance soutenue | 6.595 |  |  |
| marque_generique | ING | 2023-08-27 | 71 | Pic isolé | 1.99 |  |  |
| marque_generique_neobanques | ING | 2023-08-27 | 69 | Pic isolé | 1.821 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2023-08-27 | 69 | Pic isolé | 1.821 | 1.000 |  |
| carte_credit_bnppf | ING kredietkaart | 2023-09-03 | 29 | Pic isolé | 5.069 |  |  |
| carte_credit_crelan | ING kredietkaart | 2023-09-03 | 29 | Pic isolé | 5.069 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2023-09-24 | 19 | Pic isolé | 3.04 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2023-09-24 | 11 | Pic isolé | 3.099 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2023-09-24 | 27 | Pic isolé | 2.941 |  |  |
| epargne_pension | ING Star Fund | 2023-09-24 | 59 | Pic isolé | 3.859 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-09-24 | 47 | Pic isolé | 3.587 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-09-24 | 59 | Pic isolé | 3.861 |  |  |
| carte_credit_bnppf | ING Card | 2023-10-29 | 89 | Pic isolé | 1.545 |  |  |
| carte_credit_crelan | ING Card | 2023-10-29 | 89 | Pic isolé | 1.545 |  |  |
| compte_epargne | ING spaarrekening | 2023-10-29 | 42 | Pic isolé | 3.332 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-10-29 | 29 | Pic isolé | 3.388 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-10-29 | 87 | Pic isolé | 3.373 |  |  |
| compte_a_vue_argenta | compte à vue ING | 2023-11-05 | 21 | Pic isolé | 8.437 |  |  |
| compte_a_vue_bnppf | compte à vue ING | 2023-11-05 | 12 | Pic isolé | 8.571 |  |  |
| compte_a_vue_revolut | compte à vue ING | 2023-11-05 | 30 | Pic isolé | 8.386 |  |  |
| epargne_pension | ING Star Fund | 2023-11-12 | 47 | Tendance soutenue | 3.011 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-11-12 | 47 | Tendance soutenue | 3.012 |  |  |
| epargne_pension | ING Star Fund | 2023-11-19 | 43 | Tendance soutenue | 2.728 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-11-19 | 39 | Pic isolé | 2.922 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-11-19 | 43 | Tendance soutenue | 2.73 |  |  |
| compte_epargne | ING spaarrekening | 2023-11-26 | 27 | Pic isolé | 1.899 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2023-11-26 | 17 | Pic isolé | 1.695 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2023-11-26 | 56 | Pic isolé | 1.928 |  |  |
| compte_epargne | compte épargne ING | 2023-12-03 | 14 | Pic isolé | 9.554 |  |  |
| compte_epargne_cbc | compte épargne ING | 2023-12-03 | 30 | Pic isolé | 9.719 |  |  |
| epargne_pension | ING Star Fund | 2023-12-17 | 60 | Tendance soutenue | 3.93 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2023-12-17 | 42 | Pic isolé | 3.171 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-12-17 | 60 | Tendance soutenue | 3.932 |  |  |
| carte_credit_bnppf | carte de crédit ING | 2023-12-24 | 31 | Pic isolé | 5.474 |  |  |
| carte_credit_crelan | carte de crédit ING | 2023-12-24 | 31 | Pic isolé | 5.474 |  |  |
| compte_a_vue | ING zichtrekening | 2023-12-24 | 16 | Pic isolé | 3.94 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2023-12-24 | 43 | Pic isolé | 4.053 |  |  |
| epargne_pension | ING Star Fund | 2023-12-24 | 50 | Tendance soutenue | 3.223 |  |  |
| epargne_pension_cbc | ING Star Fund | 2023-12-24 | 50 | Tendance soutenue | 3.224 |  |  |
| compte_epargne | ING spaarrekening | 2024-01-28 | 23 | Pic isolé | 1.517 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2024-01-28 | 48 | Pic isolé | 1.556 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2024-01-28 | 60 | Pic isolé | 4.667 |  |  |
| epargne_pension_bnppf | ING pensioensparen | 2024-01-28 | 36 | Pic isolé | 15.906 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2024-02-04 | 16 | Pic isolé | 1.554 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2024-03-03 | 20 | Pic isolé | 3.212 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2024-03-03 | 11 | Pic isolé | 3.099 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2024-03-03 | 29 | Pic isolé | 3.176 |  |  |
| compte_epargne | ING spaarrekening | 2024-03-10 | 23 | Pic isolé | 1.517 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2024-03-10 | 47 | Pic isolé | 1.509 |  |  |
| app_mobile | ING Banking | 2024-03-24 | 26 | Pic isolé | 6.461 |  |  |
| app_mobile_argenta | ING Banking | 2024-03-24 | 100 | Pic isolé | 6.515 |  |  |
| app_mobile_bnppf | ING Banking | 2024-03-24 | 100 | Pic isolé | 6.515 |  |  |
| app_mobile_cbc | ING Banking | 2024-03-24 | 100 | Pic isolé | 6.306 |  |  |
| app_mobile_crelan | ING Banking | 2024-03-24 | 100 | Pic isolé | 6.515 |  |  |
| carte_credit | ING Card | 2024-03-24 | 100 | Pic isolé | 2.888 |  |  |
| carte_credit_bnppf | ING Card | 2024-03-24 | 92 | Pic isolé | 1.688 |  |  |
| carte_credit_cbc | ING Card | 2024-03-24 | 100 | Pic isolé | 2.889 |  |  |
| carte_credit_crelan | ING Card | 2024-03-24 | 92 | Pic isolé | 1.688 |  |  |
| contexte_fusion_crelan_axa | ING | 2024-03-24 | 100 | Pic isolé | 3.997 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | 2024-03-24 | 100 | Pic isolé | 3.994 | 1.000 |  |
| marque_generique | ING | 2024-03-24 | 90 | Pic isolé | 4.233 |  |  |
| marque_generique_neobanques | ING | 2024-03-24 | 87 | Pic isolé | 4.002 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2024-03-24 | 87 | Pic isolé | 4.002 | 1.000 |  |
| carte_credit | carte de crédit ING | 2024-04-07 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit_cbc | carte de crédit ING | 2024-04-07 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit | ING kredietkaart | 2024-04-28 | 24 | Pic isolé | 5.969 |  |  |
| carte_credit_cbc | ING kredietkaart | 2024-04-28 | 24 | Pic isolé | 6.014 |  |  |
| carte_credit | carte de crédit ING | 2024-05-26 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2024-05-26 | 39 | Pic isolé | 6.879 |  |  |
| carte_credit_bnppf | carte de crédit ING | 2024-05-26 | 34 | Pic isolé | 6.019 |  |  |
| carte_credit_cbc | carte de crédit ING | 2024-05-26 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit_crelan | ING kredietkaart | 2024-05-26 | 39 | Pic isolé | 6.879 |  |  |
| carte_credit_crelan | carte de crédit ING | 2024-05-26 | 34 | Pic isolé | 6.019 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2024-07-14 | 28 | Pic isolé | 4.592 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2024-07-14 | 16 | Pic isolé | 4.615 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2024-07-14 | 42 | Pic isolé | 4.706 |  |  |
| compte_a_vue | ING zichtrekening | 2024-08-25 | 24 | Tendance soutenue | 5.993 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2024-08-25 | 35 | Tendance soutenue | 5.799 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2024-08-25 | 20 | Tendance soutenue | 5.828 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2024-08-25 | 62 | Tendance soutenue | 5.921 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2024-08-25 | 51 | Tendance soutenue | 5.765 |  |  |
| compte_epargne | ING spaarrekening | 2024-08-25 | 41 | Tendance soutenue | 3.237 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2024-08-25 | 27 | Tendance soutenue | 3.106 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2024-08-25 | 84 | Tendance soutenue | 3.233 |  |  |
| contexte_fusion_crelan_axa | ING | 2024-08-25 | 85 | Pic isolé | 2.413 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | 2024-08-25 | 85 | Tendance soutenue | 2.411 | 1.000 |  |
| marque_generique | ING | 2024-08-25 | 73 | Tendance soutenue | 2.226 |  |  |
| marque_generique_neobanques | ING | 2024-08-25 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2024-08-25 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| compte_a_vue | ING zichtrekening | 2024-09-01 | 39 | Tendance soutenue | 9.843 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2024-09-01 | 46 | Tendance soutenue | 7.696 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2024-09-01 | 26 | Tendance soutenue | 7.648 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2024-09-01 | 100 | Tendance soutenue | 9.657 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2024-09-01 | 67 | Tendance soutenue | 7.648 |  |  |
| compte_epargne | ING spaarrekening | 2024-09-01 | 49 | Tendance soutenue | 4.001 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2024-09-01 | 32 | Tendance soutenue | 3.811 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2024-09-01 | 100 | Tendance soutenue | 3.979 |  |  |
| contexte_integration_bnppf_bpost | ING | 2024-09-01 | 85 | Tendance soutenue | 2.411 | 1.000 |  |
| marque_generique | ING | 2024-09-01 | 82 | Tendance soutenue | 3.288 |  |  |
| marque_generique_neobanques | ING | 2024-09-01 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| marque_generique_traditionnelles | ING | 2024-09-01 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| carte_credit | ING kredietkaart | 2024-09-08 | 26 | Pic isolé | 6.48 |  |  |
| carte_credit_bnppf | carte de crédit ING | 2024-09-08 | 53 | Pic isolé | 9.469 |  |  |
| carte_credit_cbc | ING kredietkaart | 2024-09-08 | 26 | Pic isolé | 6.529 |  |  |
| carte_credit_crelan | carte de crédit ING | 2024-09-08 | 53 | Pic isolé | 9.469 |  |  |
| compte_a_vue | ING zichtrekening | 2024-09-08 | 28 | Tendance soutenue | 7.02 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2024-09-08 | 74 | Tendance soutenue | 7.101 |  |  |
| compte_epargne | ING spaarrekening | 2024-09-08 | 32 | Tendance soutenue | 2.377 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2024-09-08 | 18 | Tendance soutenue | 1.836 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2024-09-08 | 65 | Tendance soutenue | 2.348 |  |  |
| compte_a_vue | ING zichtrekening | 2024-09-22 | 19 | Pic isolé | 4.71 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2024-09-22 | 49 | Pic isolé | 4.643 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2024-12-15 | 38 | Pic isolé | 2.839 |  |  |
| compte_epargne | ING spaarrekening | 2024-12-29 | 25 | Pic isolé | 1.708 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2024-12-29 | 20 | Pic isolé | 2.118 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2024-12-29 | 52 | Pic isolé | 1.742 |  |  |
| epargne_pension | ING Star Fund | 2025-01-19 | 71 | Pic isolé | 4.708 |  |  |
| epargne_pension_cbc | ING Star Fund | 2025-01-19 | 71 | Pic isolé | 4.709 |  |  |
| compte_epargne_argenta | compte épargne ING | 2025-01-26 | 8 | Pic isolé | 11.106 |  |  |
| investissement_courtage | ING Self Invest | 2025-02-16 | 3 | Pic isolé | 6.595 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2025-02-23 | 16 | Pic isolé | 1.554 |  |  |
| compte_professionnel | Business'Bank ING | 2025-03-02 | 79 | Pic isolé | 10.904 |  |  |
| compte_professionnel_cbc | Business'Bank ING | 2025-03-02 | 76 | Pic isolé | 10.885 |  |  |
| epargne_pension_bnppf | ING Star Fund | 2025-03-02 | 49 | Pic isolé | 3.753 |  |  |
| carte_credit_bnppf | carte de crédit ING | 2025-03-16 | 32 | Pic isolé | 5.656 |  |  |
| carte_credit_crelan | carte de crédit ING | 2025-03-16 | 32 | Pic isolé | 5.656 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2025-04-27 | 23 | Pic isolé | 3.73 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2025-04-27 | 13 | Pic isolé | 3.705 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2025-04-27 | 34 | Pic isolé | 3.764 |  |  |
| compte_epargne_argenta | ING Orange Savings | 2025-04-27 | 10 | Pic isolé | 9.819 |  |  |
| investissement_courtage | ING Self Invest | 2025-05-25 | 3 | Pic isolé | 6.595 |  |  |
| pret_hypothecaire | prêt hypothécaire ING | 2025-05-25 | 75 | Pic isolé | 10.085 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire ING | 2025-05-25 | 64 | Pic isolé | 10.022 |  |  |
| assurance_habitation | ING Home Insurance | 2025-06-08 | 79 | Pic isolé | 16.155 |  |  |
| assurance_habitation_cbc | ING Home Insurance | 2025-06-08 | 64 | Pic isolé | 16.155 |  |  |
| compte_epargne | ING Orange Savings | 2025-08-10 | 19 | Pic isolé | 11.278 |  |  |
| compte_epargne_cbc | ING Orange Savings | 2025-08-10 | 38 | Pic isolé | 11.401 |  |  |
| compte_epargne_argenta | ING Orange Savings | 2025-08-17 | 13 | Pic isolé | 12.791 |  |  |
| compte_epargne | ING spaarrekening | 2025-08-24 | 23 | Pic isolé | 1.517 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2025-08-24 | 16 | Pic isolé | 1.554 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2025-08-24 | 48 | Pic isolé | 1.556 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2025-09-07 | 22 | Pic isolé | 3.557 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2025-09-07 | 13 | Pic isolé | 3.705 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2025-09-07 | 33 | Pic isolé | 3.647 |  |  |
| compte_professionnel | compte professionnel ING | 2025-11-02 | 93 | Pic isolé | 12.636 |  |  |
| compte_professionnel_cbc | compte professionnel ING | 2025-11-02 | 90 | Pic isolé | 12.553 |  |  |
| pret_hypothecaire | ING hypothecair krediet | 2025-12-14 | 69 | Pic isolé | 9.396 |  |  |
| pret_hypothecaire_cbc | ING hypothecair krediet | 2025-12-14 | 59 | Pic isolé | 9.327 |  |  |
| pret_hypothecaire | prêt hypothécaire ING | 2026-01-25 | 60 | Pic isolé | 8.046 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire ING | 2026-01-25 | 52 | Pic isolé | 8.121 |  |  |
| compte_a_vue_argenta | ING Do Basic | 2026-02-08 | 22 | Pic isolé | 11.402 |  |  |
| compte_a_vue_bnppf | ING Do Basic | 2026-02-08 | 13 | Pic isolé | 11.402 |  |  |
| compte_a_vue_revolut | ING Do Basic | 2026-02-08 | 33 | Pic isolé | 11.577 |  |  |
| compte_epargne | ING spaarrekening | 2026-02-22 | 25 | Pic isolé | 1.708 |  |  |
| compte_epargne_cbc | ING spaarrekening | 2026-02-22 | 51 | Pic isolé | 1.695 |  |  |
| carte_credit | ING kredietkaart | 2026-04-05 | 29 | Pic isolé | 7.248 |  |  |
| carte_credit_cbc | ING kredietkaart | 2026-04-05 | 29 | Pic isolé | 7.301 |  |  |
| epargne_pension | épargne pension ING | 2026-04-12 | 100 | Pic isolé | 16.148 |  |  |
| epargne_pension_cbc | épargne pension ING | 2026-04-12 | 100 | Pic isolé | 16.148 |  |  |
| pret_hypothecaire | ING hypothecair krediet | 2026-04-19 | 96 | Pic isolé | 13.106 |  |  |
| pret_hypothecaire_cbc | ING hypothecair krediet | 2026-04-19 | 83 | Pic isolé | 13.156 |  |  |
| compte_a_vue_argenta | ING zichtrekening | 2026-05-03 | 21 | Pic isolé | 3.385 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | 2026-05-03 | 12 | Pic isolé | 3.402 |  |  |
| compte_a_vue_revolut | ING zichtrekening | 2026-05-03 | 30 | Pic isolé | 3.294 |  |  |
| app_mobile | ING Smart Banking | 2026-05-17 | 1 | Pic isolé | 11.402 |  |  |
| app_mobile_cbc | ING Smart Banking | 2026-05-17 | 4 | Pic isolé | 11.402 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2026-05-24 | 30 | Pic isolé | 5.25 |  |  |
| carte_credit_crelan | ING kredietkaart | 2026-05-24 | 30 | Pic isolé | 5.25 |  |  |
| compte_epargne | compte épargne ING | 2026-06-07 | 12 | Pic isolé | 8.17 |  |  |
| compte_epargne_cbc | compte épargne ING | 2026-06-07 | 25 | Pic isolé | 8.076 |  |  |
| carte_credit_bnppf | ING kredietkaart | 2026-06-28 | 43 | Pic isolé | 7.603 |  |  |
| carte_credit_crelan | ING kredietkaart | 2026-06-28 | 43 | Pic isolé | 7.603 |  |  |
| compte_professionnel | Business'Bank ING | 2026-07-05 | 86 | Pic isolé | 11.878 |  |  |
| compte_professionnel_cbc | Business'Bank ING | 2026-07-05 | 83 | Pic isolé | 11.896 |  |  |
| compte_a_vue_argenta | compte à vue ING | 2026-07-19 | 34 | Pic isolé | 13.715 |  |  |
| compte_a_vue_bnppf | compte à vue ING | 2026-07-19 | 19 | Pic isolé | 13.624 |  |  |
| compte_a_vue_revolut | compte à vue ING | 2026-07-19 | 49 | Pic isolé | 13.754 |  |  |
| carte_credit | carte de crédit ING | 2026-08-02 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit_cbc | carte de crédit ING | 2026-08-02 | 35 | Pic isolé | 9.472 |  |  |
| assurance_habitation | assurance habitation ING | 2026-08-30 | 4 | Tendance soutenue | 7.181 |  |  |
| assurance_habitation_cbc | assurance habitation ING | 2026-08-30 | 6 | Tendance soutenue | 11.402 |  |  |
| compte_a_vue | compte à vue ING | 2026-08-30 | 2 | Tendance soutenue | 2.05 |  |  |
| compte_a_vue_cbc | compte à vue ING | 2026-08-30 | 5 | Tendance soutenue | 1.978 |  |  |
| compte_epargne | ING Orange Savings | 2026-08-30 | 16 | Pic isolé | 9.481 |  |  |
| compte_epargne | compte épargne ING | 2026-08-30 | 4 | Tendance soutenue | 2.633 |  |  |
| compte_epargne_argenta | ING spaarrekening | 2026-08-30 | 16 | Pic isolé | 1.554 |  |  |
| compte_epargne_argenta | compte épargne ING | 2026-08-30 | 2 | Tendance soutenue | 2.684 |  |  |
| compte_epargne_cbc | ING Orange Savings | 2026-08-30 | 31 | Pic isolé | 9.282 |  |  |
| compte_epargne_cbc | compte épargne ING | 2026-08-30 | 8 | Tendance soutenue | 2.491 |  |  |
| compte_professionnel_cbc | compte professionnel ING | 2026-08-30 | 14 | Pic isolé | 1.87 |  |  |
| assurance_habitation | assurance habitation ING | 2026-09-06 | 8 | Tendance soutenue | 14.444 |  |  |
| assurance_habitation_cbc | assurance habitation ING | 2026-09-06 | 6 | Tendance soutenue | 11.402 |  |  |
| compte_a_vue | ING zichtrekening | 2026-09-06 | 7 | Pic isolé | 1.63 |  |  |
| compte_a_vue | compte à vue ING | 2026-09-06 | 2 | Tendance soutenue | 2.05 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2026-09-06 | 18 | Tendance soutenue | 1.596 |  |  |
| compte_a_vue_cbc | compte à vue ING | 2026-09-06 | 4 | Tendance soutenue | 1.568 |  |  |
| compte_epargne | compte épargne ING | 2026-09-06 | 4 | Tendance soutenue | 2.633 |  |  |
| compte_epargne_argenta | compte épargne ING | 2026-09-06 | 3 | Tendance soutenue | 4.088 |  |  |
| compte_epargne_cbc | compte épargne ING | 2026-09-06 | 8 | Tendance soutenue | 2.491 |  |  |
| epargne_pension_bnppf | ING pensioensparen | 2026-09-06 | 4 | Tendance soutenue | 1.7 |  |  |
| carte_credit | ING kredietkaart | 2026-09-13 | 7 | Pic isolé | 1.622 |  |  |
| compte_a_vue_cbc | ING zichtrekening | 2026-09-13 | 24 | Tendance soutenue | 2.186 |  |  |
| compte_epargne | compte épargne ING | 2026-09-13 | 4 | Tendance soutenue | 2.633 |  |  |
| compte_epargne_argenta | compte épargne ING | 2026-09-13 | 3 | Tendance soutenue | 4.088 |  |  |
| compte_epargne_cbc | compte épargne ING | 2026-09-13 | 12 | Tendance soutenue | 3.806 |  |  |
| epargne_pension_bnppf | ING pensioensparen | 2026-09-13 | 5 | Tendance soutenue | 2.144 |  |  |
