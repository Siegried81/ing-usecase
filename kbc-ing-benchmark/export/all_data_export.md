# Export combiné — Benchmark marketing ING vs concurrents

Document généré automatiquement à partir de `benchmark.db`, destiné à servir d'entrée à un autre pipeline (rapprochement avec les campagnes publicitaires réelles). Couvre les 9 banques du périmètre (ING, KBC, CBC, BNP Paribas Fortis, Argenta, Crelan, Revolut, N26, bunq) dans un seul document ; voir les exports par banque (`kbc_data_export.md`, `ing_data_export.md`, `cbc_data_export.md`, `bnppf_data_export.md`, `argenta_data_export.md`, `crelan_data_export.md`, `revolut_data_export.md`, `n26_data_export.md`, `bunq_data_export.md`) pour les versions filtrées.

## Méthodologie

- **Source Google Trends** : bibliothèque `pytrends`, geo=`BE`, timeframe=`today 5-y`.
- **Granularité réelle** : hebdomadaire (Google Trends bascule automatiquement en hebdomadaire pour une fenêtre de 5 ans, pas mensuel).
- **Détection d'anomalies** (par terme) : moyenne d'intérêt calculée par mois calendaire sur toutes les années disponibles (profil de saisonnalité de référence). Un point est flagué s'il dépasse à la fois (a) la moyenne générale du terme de plus de 1.5 écart-type (z-score ≥ 1.5) et (b) 1.3× la moyenne saisonnière normale de son mois. Les points flagués consécutifs sont groupés : un seul point isolé est un **pic isolé** (`isolated_spike`), deux points consécutifs ou plus sont une **tendance soutenue** (`sustained_trend`).
- **Comparabilité des valeurs** : chaque fiche est une requête pytrends indépendante (jusqu'à 5 termes) ; les valeurs 0-100 ne sont comparables qu'à l'intérieur d'une même fiche (`product_id`), jamais entre deux fiches différentes.
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
| 2024-03-14 | N26 | Lancement du compte épargne en Belgique |
| 2024-06-10 | Crelan | Fusion avec AXA Bank Belgium, migration IT d'environ 840 000 clients (week-end des 8 et 9 juin) |
| 2024-12-17 | bunq | bunq Stocks disponible en Belgique |
| 2025-05-01 | Revolut | Comptes belges (IBAN BE) pour les nouveaux clients, migration des clients existants au cours de 2025 |
| 2025-08-21 | Revolut | Lancement du compte épargne à intérêts versés quotidiennement (date de couverture presse) |
| 2026-07-24 | bunq | Lancement des IBAN belges et de Wero en Belgique (date de couverture presse) |

## Fiches produits (32)

| Fiche produit | Termes de recherche (banque) |
|---|---|
| Compte professionnel / indépendant (`compte_professionnel`) | KBC zakelijke rekening (KBC), compte professionnel ING (ING), ING zakelijke rekening (ING), Business'Bank ING (ING), KBC Business Pro (KBC) |
| Compte à vue particulier (`compte_a_vue`) | KBC zichtrekening (KBC), compte à vue ING (ING), ING zichtrekening (ING), ING Do Basic (ING), Compte Plus KBC (KBC) |
| Compte épargne particulier (`compte_epargne`) | KBC spaarrekening (KBC), compte épargne ING (ING), ING spaarrekening (ING), ING Orange Savings (ING), KBC Start2Save (KBC) |
| Investissement / courtage en ligne (`investissement_courtage`) | Bolero (KBC), ING Self Invest (ING) |
| Application mobile bancaire (`app_mobile`) | KBC Mobile (KBC), ING Banking (ING), ING Smart Banking (ING), KBC Touch (KBC) |
| Carte de crédit (`carte_credit`) | KBC kredietkaart (KBC), carte de crédit ING (ING), ING kredietkaart (ING), ING Card (ING), KBC Flex Budget (KBC) |
| Épargne-pension (`epargne_pension`) | KBC pensioensparen (KBC), épargne pension ING (ING), ING pensioensparen (ING), ING Star Fund (ING), KBC Pension Savings Fund (KBC) |
| Assurance habitation (`assurance_habitation`) | KBC brandverzekering (KBC), assurance habitation ING (ING), ING Home Insurance (ING) |
| Prêt hypothécaire (`pret_hypothecaire`) | KBC hypothecair krediet (KBC), prêt hypothécaire ING (ING), ING hypothecair krediet (ING) |
| Compte professionnel / indépendant (CBC vs ING) (`compte_professionnel_cbc`) | compte professionnel CBC (CBC), KBC Business Pro (CBC), compte professionnel ING (ING), ING zakelijke rekening (ING), Business'Bank ING (ING) |
| Compte à vue particulier (CBC vs ING) (`compte_a_vue_cbc`) | compte à vue CBC (CBC), compte à vue ING (ING), ING zichtrekening (ING), ING Do Basic (ING) |
| Compte épargne particulier (CBC vs ING) (`compte_epargne_cbc`) | compte épargne CBC (CBC), compte épargne ING (ING), ING spaarrekening (ING), ING Orange Savings (ING) |
| Application mobile bancaire (CBC vs ING) (`app_mobile_cbc`) | CBC Mobile (CBC), CBC Touch (CBC), ING Banking (ING), ING Smart Banking (ING) |
| Carte de crédit (CBC vs ING) (`carte_credit_cbc`) | carte de crédit CBC (CBC), carte de crédit ING (ING), ING kredietkaart (ING), ING Card (ING) |
| Épargne-pension (CBC vs ING) (`epargne_pension_cbc`) | épargne pension CBC (CBC), épargne pension ING (ING), ING pensioensparen (ING), ING Star Fund (ING) |
| Assurance habitation (CBC vs ING) (`assurance_habitation_cbc`) | assurance CBC (CBC), assurance habitation ING (ING), ING Home Insurance (ING) |
| Prêt hypothécaire (CBC vs ING) (`pret_hypothecaire_cbc`) | prêt hypothécaire CBC (CBC), prêt hypothécaire ING (ING), ING hypothecair krediet (ING) |
| Marque (recherche générique) (`marque_generique`) | KBC (KBC), ING (ING), CBC Banque & Assurance (CBC) |
| Compte à vue particulier (BNP Paribas Fortis vs ING) (`compte_a_vue_bnppf`) | compte à vue ING (ING), ING zichtrekening (ING), ING Do Basic (ING), compte BNP (BNP Paribas Fortis), BNP rekening (BNP Paribas Fortis) |
| Application mobile bancaire (BNP Paribas Fortis vs ING) (`app_mobile_bnppf`) | ING Banking (ING), ING Smart Banking (ING), easy banking app (BNP Paribas Fortis) |
| Carte de crédit (BNP Paribas Fortis vs ING) (`carte_credit_bnppf`) | carte de crédit ING (ING), ING kredietkaart (ING), ING Card (ING), BNP visa (BNP Paribas Fortis) |
| Épargne-pension (BNP Paribas Fortis vs ING) (`epargne_pension_bnppf`) | épargne pension ING (ING), ING pensioensparen (ING), ING Star Fund (ING), BNP pension (BNP Paribas Fortis) |
| Compte à vue particulier (Argenta vs ING) (`compte_a_vue_argenta`) | compte à vue ING (ING), ING zichtrekening (ING), ING Do Basic (ING), compte Argenta (Argenta), Argenta rekening (Argenta) |
| Compte épargne particulier (Argenta vs ING) (`compte_epargne_argenta`) | compte épargne ING (ING), ING spaarrekening (ING), ING Orange Savings (ING), Argenta spaarrekening (Argenta) |
| Application mobile bancaire (Argenta vs ING) (`app_mobile_argenta`) | ING Banking (ING), ING Smart Banking (ING), Argenta app (Argenta) |
| Application mobile bancaire (Crelan vs ING) (`app_mobile_crelan`) | ING Banking (ING), ING Smart Banking (ING), Crelan app (Crelan) |
| Carte de crédit (Crelan vs ING) (`carte_credit_crelan`) | carte de crédit ING (ING), ING kredietkaart (ING), ING Card (ING), Crelan visa (Crelan) |
| Compte à vue particulier (Revolut vs ING) (`compte_a_vue_revolut`) | compte à vue ING (ING), ING zichtrekening (ING), ING Do Basic (ING), compte Revolut (Revolut) |
| Marques — banques traditionnelles (`marque_generique_traditionnelles`) | ING (ING), KBC (KBC), BNP Paribas Fortis (BNP Paribas Fortis), Argenta (Argenta), Crelan (Crelan) |
| Marques — néobanques (`marque_generique_neobanques`) | ING (ING), KBC (KBC), Revolut (Revolut), N26 (N26), bunq (bunq) |
| Contexte — intégration de bpost banque dans BNP Paribas Fortis (janvier 2024) (`contexte_integration_bnppf_bpost`) | ING (ING), BNP Paribas Fortis (BNP Paribas Fortis), bpost bank (BNP Paribas Fortis), bpost banque (BNP Paribas Fortis) |
| Contexte — fusion d'AXA Bank Belgium dans Crelan (juin 2024) (`contexte_fusion_crelan_axa`) | ING (ING), Crelan (Crelan), AXA Bank (Crelan), AXA Banque (Crelan) |

### Notes produit

- **BNP Paribas Fortis** — Les termes produit utilisent le jeton `BNP` : en broad match, `compte à vue BNP` inclut `compte à vue BNP Paribas Fortis`, qui est un sous-ensemble strict et donc toujours moins couvrant.
- **BNP Paribas Fortis** — Les recherches passant par les marques sœurs Hello bank! et Fintro ne sont pas captées par ces termes.
- **Argenta** — `investissement_courtage` : l'offre d'investissement d'Argenta repose sur des fonds, des plans d'investissement et du conseil, pas sur une plateforme de courtage d'actions comparable à Bolero. Le `product_id` est conservé pour la symétrie inter-banques.
- **Crelan** — `investissement_courtage` : l'offre d'investissement de Crelan repose sur des fonds, des plans d'investissement et du conseil, pas sur une plateforme de courtage d'actions comparable à Bolero. Le `product_id` est conservé pour la symétrie inter-banques.
- **Revolut** — `app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau d'agences.
- **N26** — `app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau d'agences.
- **bunq** — `app_mobile` mesure l'intérêt pour l'application, qui est le canal unique de cette banque : cette fiche n'est pas comparable à celle d'une banque à réseau d'agences.

## Données Google Trends brutes

33536 points hebdomadaires, 71 termes, du 2021-09-12 au 2026-09-13, toutes banques confondues. Fournies séparément dans **`all_trends_data.csv`** (colonnes : product_id, product_label, term, bank, language, date, value) — non incluses ici pour garder ce document lisible.

## Anomalies détectées (1155)

| Fiche produit | Terme | Banque | Date | Valeur | Type d'anomalie | Score de déviation | Couverture du terme | Flags du terme |
|---|---|---|---|---|---|---|---|---|
| app_mobile | ING Banking | ING | 2021-09-19 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | ING Banking | ING | 2021-09-26 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | KBC Touch | KBC | 2021-09-26 | 90 | Pic isolé | 1.835 |  |  |
| app_mobile | ING Banking | ING | 2021-10-03 | 17 | Tendance soutenue | 2.799 |  |  |
| app_mobile | ING Banking | ING | 2021-10-10 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile | KBC Mobile | KBC | 2021-10-10 | 5 | Tendance soutenue | 2.466 |  |  |
| app_mobile | ING Banking | ING | 2021-10-17 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | KBC Mobile | KBC | 2021-10-17 | 5 | Tendance soutenue | 2.466 |  |  |
| app_mobile | ING Banking | ING | 2021-10-24 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile | ING Smart Banking | ING | 2021-10-24 | 1 | Pic isolé | 11.402 |  |  |
| app_mobile | KBC Mobile | KBC | 2021-10-24 | 6 | Tendance soutenue | 3.57 |  |  |
| app_mobile | ING Banking | ING | 2021-10-31 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | ING Banking | ING | 2021-11-07 | 19 | Tendance soutenue | 3.613 |  |  |
| app_mobile | ING Banking | ING | 2021-11-21 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | ING Banking | ING | 2021-11-28 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | KBC Touch | KBC | 2021-11-28 | 89 | Pic isolé | 1.754 |  |  |
| app_mobile | KBC Mobile | KBC | 2021-12-05 | 5 | Pic isolé | 2.466 |  |  |
| app_mobile | ING Banking | ING | 2021-12-12 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile | ING Banking | ING | 2021-12-19 | 16 | Tendance soutenue | 2.392 |  |  |
| app_mobile | ING Banking | ING | 2021-12-26 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | ING Banking | ING | 2022-01-02 | 15 | Tendance soutenue | 1.985 |  |  |
| app_mobile | KBC Touch | KBC | 2022-01-02 | 100 | Tendance soutenue | 2.646 |  |  |
| app_mobile | KBC Mobile | KBC | 2022-01-09 | 5 | Pic isolé | 2.466 |  |  |
| app_mobile | KBC Touch | KBC | 2022-01-09 | 98 | Tendance soutenue | 2.483 |  |  |
| app_mobile | ING Banking | ING | 2022-01-16 | 15 | Pic isolé | 1.985 |  |  |
| app_mobile | ING Banking | ING | 2022-01-30 | 17 | Tendance soutenue | 2.799 |  |  |
| app_mobile | ING Banking | ING | 2022-02-06 | 14 | Tendance soutenue | 1.578 |  |  |
| app_mobile | ING Banking | ING | 2022-02-13 | 14 | Tendance soutenue | 1.578 |  |  |
| app_mobile | ING Banking | ING | 2022-02-27 | 14 | Pic isolé | 1.578 |  |  |
| app_mobile | KBC Mobile | KBC | 2022-06-26 | 5 | Pic isolé | 2.466 |  |  |
| app_mobile | KBC Touch | KBC | 2022-06-26 | 89 | Tendance soutenue | 1.754 |  |  |
| app_mobile | KBC Touch | KBC | 2022-07-03 | 95 | Tendance soutenue | 2.24 |  |  |
| app_mobile | KBC Touch | KBC | 2022-07-10 | 90 | Tendance soutenue | 1.835 |  |  |
| app_mobile | KBC Mobile | KBC | 2023-03-05 | 6 | Pic isolé | 3.57 |  |  |
| app_mobile | ING Banking | ING | 2024-03-24 | 26 | Pic isolé | 6.461 |  |  |
| app_mobile | ING Smart Banking | ING | 2026-05-17 | 1 | Pic isolé | 11.402 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-09-19 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-09-26 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-10-03 | 65 | Tendance soutenue | 2.791 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-10-17 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-10-24 | 63 | Tendance soutenue | 2.578 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-10-31 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-11-07 | 71 | Tendance soutenue | 3.43 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-11-14 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-11-21 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-11-28 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-12-05 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_argenta | ING Smart Banking | ING | 2021-12-05 | 4 | Pic isolé | 16.155 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-12-12 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-12-19 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_argenta | ING Banking | ING | 2021-12-26 | 60 | Tendance soutenue | 2.259 |  |  |
| app_mobile_argenta | ING Banking | ING | 2022-01-02 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_argenta | ING Banking | ING | 2022-01-09 | 56 | Tendance soutenue | 1.834 |  |  |
| app_mobile_argenta | ING Banking | ING | 2022-01-16 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_argenta | Argenta app | Argenta | 2022-01-30 | 19 | Pic isolé | 5.221 | 0.877 | asymmetric |
| app_mobile_argenta | ING Banking | ING | 2022-01-30 | 64 | Tendance soutenue | 2.685 |  |  |
| app_mobile_argenta | ING Banking | ING | 2022-02-06 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_argenta | ING Banking | ING | 2022-02-13 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_argenta | ING Banking | ING | 2022-02-27 | 56 | Pic isolé | 1.834 |  |  |
| app_mobile_argenta | Argenta app | Argenta | 2023-03-12 | 13 | Pic isolé | 2.976 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2023-08-06 | 10 | Pic isolé | 1.854 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2023-09-24 | 12 | Pic isolé | 2.602 | 0.877 | asymmetric |
| app_mobile_argenta | ING Banking | ING | 2024-03-24 | 100 | Pic isolé | 6.515 |  |  |
| app_mobile_argenta | Argenta app | Argenta | 2025-01-05 | 10 | Pic isolé | 1.854 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2025-01-19 | 10 | Tendance soutenue | 1.854 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2025-01-26 | 14 | Tendance soutenue | 3.35 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2025-10-05 | 11 | Pic isolé | 2.228 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2025-12-28 | 12 | Pic isolé | 2.602 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2026-05-31 | 13 | Pic isolé | 2.976 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2026-06-14 | 10 | Pic isolé | 1.854 | 0.877 | asymmetric |
| app_mobile_argenta | Argenta app | Argenta | 2026-07-05 | 11 | Pic isolé | 2.228 | 0.877 | asymmetric |
| app_mobile_bnppf | ING Banking | ING | 2021-09-19 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-09-26 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-10-03 | 65 | Tendance soutenue | 2.791 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-10-17 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-10-24 | 63 | Tendance soutenue | 2.578 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-10-31 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-11-07 | 71 | Tendance soutenue | 3.43 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-11-14 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-11-21 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-11-28 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-12-05 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_bnppf | ING Smart Banking | ING | 2021-12-05 | 4 | Pic isolé | 16.155 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-12-12 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-12-19 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2021-12-26 | 60 | Tendance soutenue | 2.259 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-01-02 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-01-09 | 56 | Tendance soutenue | 1.834 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-01-16 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-01-30 | 64 | Tendance soutenue | 2.685 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-02-06 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-02-13 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_bnppf | ING Banking | ING | 2022-02-27 | 56 | Pic isolé | 1.834 |  |  |
| app_mobile_bnppf | easy banking app | BNP Paribas Fortis | 2022-07-31 | 10 | Tendance soutenue | 1.901 | 0.713 | asymmetric |
| app_mobile_bnppf | easy banking app | BNP Paribas Fortis | 2022-08-07 | 14 | Tendance soutenue | 3.053 | 0.713 | asymmetric |
| app_mobile_bnppf | easy banking app | BNP Paribas Fortis | 2024-01-14 | 10 | Tendance soutenue | 1.901 | 0.713 | asymmetric |
| app_mobile_bnppf | easy banking app | BNP Paribas Fortis | 2024-01-21 | 42 | Tendance soutenue | 11.114 | 0.713 | asymmetric |
| app_mobile_bnppf | easy banking app | BNP Paribas Fortis | 2024-01-28 | 9 | Tendance soutenue | 1.613 | 0.713 | asymmetric |
| app_mobile_bnppf | ING Banking | ING | 2024-03-24 | 100 | Pic isolé | 6.515 |  |  |
| app_mobile_bnppf | easy banking app | BNP Paribas Fortis | 2024-09-08 | 9 | Pic isolé | 1.613 | 0.713 | asymmetric |
| app_mobile_cbc | CBC Touch | CBC | 2021-09-12 | 40 | Pic isolé | 1.738 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2021-09-19 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-09-19 | 58 | Tendance soutenue | 1.924 |  |  |
| app_mobile_cbc | CBC Touch | CBC | 2021-09-26 | 43 | Tendance soutenue | 2.36 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-09-26 | 59 | Tendance soutenue | 2.028 |  |  |
| app_mobile_cbc | CBC Touch | CBC | 2021-10-03 | 46 | Tendance soutenue | 2.982 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-10-03 | 67 | Tendance soutenue | 2.863 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-10-10 | 62 | Tendance soutenue | 2.341 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2021-10-17 | 7 | Pic isolé | 5.831 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-10-17 | 58 | Tendance soutenue | 1.924 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-10-24 | 62 | Tendance soutenue | 2.341 |  |  |
| app_mobile_cbc | ING Smart Banking | ING | 2021-10-24 | 4 | Pic isolé | 11.402 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-10-31 | 59 | Tendance soutenue | 2.028 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-11-07 | 75 | Tendance soutenue | 3.697 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-11-14 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-11-21 | 59 | Tendance soutenue | 2.028 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-11-28 | 58 | Tendance soutenue | 1.924 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-12-05 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-12-12 | 61 | Tendance soutenue | 2.237 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-12-19 | 61 | Tendance soutenue | 2.237 |  |  |
| app_mobile_cbc | ING Banking | ING | 2021-12-26 | 57 | Tendance soutenue | 1.819 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-01-02 | 60 | Tendance soutenue | 2.132 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-01-16 | 59 | Pic isolé | 2.028 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-01-30 | 66 | Tendance soutenue | 2.758 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-02-06 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-02-13 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2022-02-20 | 3 | Pic isolé | 2.337 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-02-27 | 56 | Tendance soutenue | 1.715 |  |  |
| app_mobile_cbc | ING Banking | ING | 2022-03-06 | 57 | Tendance soutenue | 1.819 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2022-03-27 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2022-06-19 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2022-07-03 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2022-07-17 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2022-12-04 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2023-03-12 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2023-06-18 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2023-12-10 | 4 | Tendance soutenue | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2023-12-17 | 4 | Tendance soutenue | 3.21 |  |  |
| app_mobile_cbc | ING Banking | ING | 2024-03-24 | 100 | Pic isolé | 6.306 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2024-05-19 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2024-06-09 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Touch | CBC | 2024-09-29 | 40 | Pic isolé | 1.738 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2024-10-20 | 6 | Pic isolé | 4.957 |  |  |
| app_mobile_cbc | CBC Touch | CBC | 2025-01-05 | 45 | Pic isolé | 2.775 |  |  |
| app_mobile_cbc | CBC Touch | CBC | 2025-06-29 | 39 | Pic isolé | 1.53 |  |  |
| app_mobile_cbc | CBC Touch | CBC | 2025-08-24 | 43 | Pic isolé | 2.36 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2026-02-08 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2026-03-29 | 5 | Pic isolé | 4.084 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2026-05-03 | 4 | Pic isolé | 3.21 |  |  |
| app_mobile_cbc | ING Smart Banking | ING | 2026-05-17 | 4 | Pic isolé | 11.402 |  |  |
| app_mobile_cbc | CBC Mobile | CBC | 2026-08-23 | 5 | Pic isolé | 4.084 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-09-19 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-09-26 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-10-03 | 65 | Tendance soutenue | 2.791 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-10-17 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-10-24 | 63 | Tendance soutenue | 2.578 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-10-31 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-11-07 | 71 | Tendance soutenue | 3.43 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-11-14 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-11-21 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-11-28 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-12-05 | 55 | Tendance soutenue | 1.727 |  |  |
| app_mobile_crelan | ING Smart Banking | ING | 2021-12-05 | 4 | Pic isolé | 16.155 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-12-12 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-12-19 | 61 | Tendance soutenue | 2.366 |  |  |
| app_mobile_crelan | ING Banking | ING | 2021-12-26 | 60 | Tendance soutenue | 2.259 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-01-02 | 58 | Tendance soutenue | 2.046 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-01-09 | 56 | Tendance soutenue | 1.834 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-01-16 | 57 | Tendance soutenue | 1.94 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-01-30 | 64 | Tendance soutenue | 2.685 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-02-06 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-02-13 | 53 | Tendance soutenue | 1.514 |  |  |
| app_mobile_crelan | ING Banking | ING | 2022-02-27 | 56 | Pic isolé | 1.834 |  |  |
| app_mobile_crelan | ING Banking | ING | 2024-03-24 | 100 | Pic isolé | 6.515 |  |  |
| app_mobile_crelan | Crelan app | Crelan | 2024-06-02 | 10 | Tendance soutenue | 2.17 | 0.345 | selected_low_coverage,asymmetric |
| app_mobile_crelan | Crelan app | Crelan | 2024-06-09 | 47 | Tendance soutenue | 11.996 | 0.345 | selected_low_coverage,asymmetric |
| app_mobile_crelan | Crelan app | Crelan | 2024-06-16 | 11 | Tendance soutenue | 2.436 | 0.345 | selected_low_coverage,asymmetric |
| app_mobile_crelan | Crelan app | Crelan | 2024-06-30 | 8 | Pic isolé | 1.639 | 0.345 | selected_low_coverage,asymmetric |
| app_mobile_crelan | Crelan app | Crelan | 2025-11-09 | 13 | Pic isolé | 2.967 | 0.345 | selected_low_coverage,asymmetric |
| app_mobile_crelan | Crelan app | Crelan | 2026-05-10 | 8 | Pic isolé | 1.639 | 0.345 | selected_low_coverage,asymmetric |
| assurance_habitation | KBC brandverzekering | KBC | 2021-10-31 | 66 | Pic isolé | 4.433 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2022-02-13 | 100 | Tendance soutenue | 6.833 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2022-02-20 | 79 | Tendance soutenue | 5.351 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2023-01-29 | 58 | Pic isolé | 3.868 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2023-03-12 | 47 | Pic isolé | 3.091 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2023-06-11 | 47 | Pic isolé | 3.091 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2023-09-17 | 54 | Pic isolé | 3.586 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2024-05-26 | 73 | Pic isolé | 4.927 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2024-06-16 | 56 | Pic isolé | 3.727 |  |  |
| assurance_habitation | ING Home Insurance | ING | 2025-06-08 | 79 | Pic isolé | 16.155 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2025-08-31 | 62 | Pic isolé | 4.15 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2025-11-30 | 58 | Pic isolé | 3.868 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2026-07-19 | 84 | Pic isolé | 5.704 |  |  |
| assurance_habitation | assurance habitation ING | ING | 2026-08-30 | 4 | Tendance soutenue | 7.181 |  |  |
| assurance_habitation | assurance habitation ING | ING | 2026-09-06 | 8 | Tendance soutenue | 14.444 |  |  |
| assurance_habitation | KBC brandverzekering | KBC | 2026-09-13 | 26 | Pic isolé | 1.609 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2022-01-23 | 75 | Pic isolé | 1.745 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2022-07-10 | 72 | Pic isolé | 1.642 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2023-01-01 | 72 | Pic isolé | 1.642 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2023-01-22 | 75 | Pic isolé | 1.745 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2023-07-02 | 69 | Pic isolé | 1.539 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2023-09-10 | 74 | Pic isolé | 1.711 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2024-03-31 | 69 | Pic isolé | 1.539 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2024-08-11 | 78 | Pic isolé | 1.848 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-02-23 | 100 | Pic isolé | 2.603 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-03-23 | 87 | Pic isolé | 2.157 |  |  |
| assurance_habitation_cbc | ING Home Insurance | ING | 2025-06-08 | 64 | Pic isolé | 16.155 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-06-08 | 76 | Pic isolé | 1.779 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-09-07 | 86 | Pic isolé | 2.123 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-10-05 | 90 | Pic isolé | 2.26 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-11-02 | 77 | Pic isolé | 1.814 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2025-12-21 | 99 | Pic isolé | 2.569 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2026-01-11 | 68 | Pic isolé | 1.505 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2026-02-01 | 87 | Pic isolé | 2.157 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2026-03-29 | 68 | Pic isolé | 1.505 |  |  |
| assurance_habitation_cbc | assurance CBC | CBC | 2026-08-30 | 87 | Pic isolé | 2.157 |  |  |
| assurance_habitation_cbc | assurance habitation ING | ING | 2026-08-30 | 6 | Tendance soutenue | 11.402 |  |  |
| assurance_habitation_cbc | assurance habitation ING | ING | 2026-09-06 | 6 | Tendance soutenue | 11.402 |  |  |
| carte_credit | ING Card | ING | 2021-10-24 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit | ING kredietkaart | ING | 2021-11-28 | 25 | Pic isolé | 6.225 |  |  |
| carte_credit | ING Card | ING | 2022-01-09 | 81 | Pic isolé | 1.862 |  |  |
| carte_credit | ING Card | ING | 2022-01-30 | 77 | Tendance soutenue | 1.646 |  |  |
| carte_credit | ING Card | ING | 2022-02-06 | 76 | Tendance soutenue | 1.592 |  |  |
| carte_credit | ING Card | ING | 2022-05-22 | 83 | Pic isolé | 1.97 |  |  |
| carte_credit | ING Card | ING | 2022-07-03 | 79 | Pic isolé | 1.754 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2022-07-24 | 34 | Pic isolé | 1.516 |  |  |
| carte_credit | ING Card | ING | 2022-08-07 | 77 | Pic isolé | 1.646 |  |  |
| carte_credit | carte de crédit ING | ING | 2022-10-16 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit | KBC Flex Budget | KBC | 2022-10-23 | 21 | Pic isolé | 9.216 |  |  |
| carte_credit | ING kredietkaart | ING | 2022-11-13 | 25 | Pic isolé | 6.225 |  |  |
| carte_credit | ING Card | ING | 2023-02-05 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit | ING kredietkaart | ING | 2023-02-05 | 26 | Pic isolé | 6.48 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2023-07-16 | 62 | Pic isolé | 3.4 |  |  |
| carte_credit | ING Card | ING | 2023-08-06 | 75 | Pic isolé | 1.538 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2023-08-20 | 34 | Pic isolé | 1.516 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2023-12-17 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-03-10 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | ING Card | ING | 2024-03-24 | 100 | Pic isolé | 2.888 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-03-24 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | carte de crédit ING | ING | 2024-04-07 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-04-21 | 38 | Pic isolé | 1.786 |  |  |
| carte_credit | ING kredietkaart | ING | 2024-04-28 | 24 | Pic isolé | 5.969 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-05-12 | 36 | Tendance soutenue | 1.651 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-05-19 | 39 | Tendance soutenue | 1.853 |  |  |
| carte_credit | carte de crédit ING | ING | 2024-05-26 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-07-28 | 36 | Tendance soutenue | 1.651 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-08-04 | 36 | Tendance soutenue | 1.651 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2024-08-18 | 35 | Pic isolé | 1.584 |  |  |
| carte_credit | ING kredietkaart | ING | 2024-09-08 | 26 | Pic isolé | 6.48 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2025-03-23 | 34 | Pic isolé | 1.516 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2025-04-06 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2025-06-08 | 34 | Pic isolé | 1.516 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2026-02-01 | 35 | Pic isolé | 1.584 |  |  |
| carte_credit | KBC Flex Budget | KBC | 2026-02-22 | 30 | Pic isolé | 13.204 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2026-03-15 | 36 | Pic isolé | 1.651 |  |  |
| carte_credit | ING kredietkaart | ING | 2026-04-05 | 29 | Pic isolé | 7.248 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2026-05-17 | 40 | Pic isolé | 1.92 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2026-07-19 | 59 | Tendance soutenue | 3.199 |  |  |
| carte_credit | KBC kredietkaart | KBC | 2026-07-26 | 37 | Tendance soutenue | 1.718 |  |  |
| carte_credit | carte de crédit ING | ING | 2026-08-02 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit | ING kredietkaart | ING | 2026-09-13 | 7 | Pic isolé | 1.622 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-09-12 | 81 | Tendance soutenue | 2.197 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-09-19 | 68 | Tendance soutenue | 1.609 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-10-03 | 66 | Tendance soutenue | 1.518 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | carte de crédit ING | ING | 2021-10-03 | 37 | Pic isolé | 6.564 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-10-10 | 75 | Tendance soutenue | 1.926 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-10-24 | 66 | Tendance soutenue | 1.518 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING Card | ING | 2021-10-24 | 94 | Pic isolé | 1.783 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-10-31 | 84 | Tendance soutenue | 2.333 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-11-07 | 69 | Tendance soutenue | 1.654 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2021-11-21 | 79 | Pic isolé | 2.107 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING Card | ING | 2021-12-05 | 92 | Pic isolé | 1.688 |  |  |
| carte_credit_bnppf | ING Card | ING | 2022-01-09 | 89 | Pic isolé | 1.545 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2022-01-30 | 69 | Pic isolé | 1.654 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2022-03-06 | 71 | Pic isolé | 1.745 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING Card | ING | 2022-05-22 | 98 | Pic isolé | 1.974 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2022-06-19 | 31 | Pic isolé | 5.431 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2022-06-26 | 80 | Tendance soutenue | 2.152 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | carte de crédit ING | ING | 2022-06-26 | 28 | Pic isolé | 4.929 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2022-07-03 | 77 | Tendance soutenue | 2.016 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING Card | ING | 2022-07-03 | 90 | Tendance soutenue | 1.593 |  |  |
| carte_credit_bnppf | ING Card | ING | 2022-07-10 | 100 | Tendance soutenue | 2.069 |  |  |
| carte_credit_bnppf | ING Card | ING | 2022-08-07 | 94 | Pic isolé | 1.783 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2022-09-11 | 28 | Pic isolé | 4.888 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2023-03-05 | 28 | Pic isolé | 4.888 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2023-03-19 | 24 | Pic isolé | 4.164 |  |  |
| carte_credit_bnppf | ING Card | ING | 2023-04-16 | 98 | Pic isolé | 1.974 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2023-04-23 | 85 | Pic isolé | 2.379 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING Card | ING | 2023-07-16 | 96 | Pic isolé | 1.878 |  |  |
| carte_credit_bnppf | ING Card | ING | 2023-08-06 | 93 | Pic isolé | 1.736 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2023-09-03 | 29 | Pic isolé | 5.069 |  |  |
| carte_credit_bnppf | ING Card | ING | 2023-10-29 | 89 | Pic isolé | 1.545 |  |  |
| carte_credit_bnppf | carte de crédit ING | ING | 2023-12-24 | 31 | Pic isolé | 5.474 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2024-02-04 | 66 | Pic isolé | 1.518 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING Card | ING | 2024-03-24 | 92 | Pic isolé | 1.688 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2024-05-26 | 39 | Pic isolé | 6.879 |  |  |
| carte_credit_bnppf | carte de crédit ING | ING | 2024-05-26 | 34 | Pic isolé | 6.019 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2024-07-07 | 68 | Pic isolé | 1.609 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | carte de crédit ING | ING | 2024-09-08 | 53 | Pic isolé | 9.469 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2024-12-08 | 71 | Pic isolé | 1.745 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | carte de crédit ING | ING | 2025-03-16 | 32 | Pic isolé | 5.656 |  |  |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2025-04-06 | 83 | Pic isolé | 2.288 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | BNP visa | BNP Paribas Fortis | 2025-07-06 | 72 | Pic isolé | 1.79 | 0.743 | broad_fallback,asymmetric |
| carte_credit_bnppf | ING kredietkaart | ING | 2026-05-24 | 30 | Pic isolé | 5.25 |  |  |
| carte_credit_bnppf | ING kredietkaart | ING | 2026-06-28 | 43 | Pic isolé | 7.603 |  |  |
| carte_credit_cbc | carte de crédit CBC | CBC | 2021-10-17 | 33 | Pic isolé | 10.513 |  |  |
| carte_credit_cbc | ING Card | ING | 2021-10-24 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit_cbc | ING kredietkaart | ING | 2021-11-28 | 25 | Pic isolé | 6.272 |  |  |
| carte_credit_cbc | ING Card | ING | 2022-01-09 | 81 | Pic isolé | 1.862 |  |  |
| carte_credit_cbc | ING Card | ING | 2022-01-30 | 77 | Tendance soutenue | 1.646 |  |  |
| carte_credit_cbc | ING Card | ING | 2022-02-06 | 76 | Tendance soutenue | 1.592 |  |  |
| carte_credit_cbc | ING Card | ING | 2022-05-22 | 83 | Pic isolé | 1.97 |  |  |
| carte_credit_cbc | ING Card | ING | 2022-07-03 | 79 | Pic isolé | 1.754 |  |  |
| carte_credit_cbc | ING Card | ING | 2022-08-07 | 77 | Pic isolé | 1.646 |  |  |
| carte_credit_cbc | carte de crédit ING | ING | 2022-10-16 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit_cbc | ING kredietkaart | ING | 2022-11-13 | 25 | Pic isolé | 6.272 |  |  |
| carte_credit_cbc | ING Card | ING | 2023-02-05 | 80 | Pic isolé | 1.808 |  |  |
| carte_credit_cbc | ING kredietkaart | ING | 2023-02-05 | 26 | Pic isolé | 6.529 |  |  |
| carte_credit_cbc | carte de crédit CBC | CBC | 2023-03-19 | 29 | Pic isolé | 9.225 |  |  |
| carte_credit_cbc | ING Card | ING | 2023-08-06 | 75 | Pic isolé | 1.538 |  |  |
| carte_credit_cbc | carte de crédit CBC | CBC | 2023-09-03 | 25 | Pic isolé | 7.938 |  |  |
| carte_credit_cbc | ING Card | ING | 2024-03-24 | 100 | Pic isolé | 2.889 |  |  |
| carte_credit_cbc | carte de crédit ING | ING | 2024-04-07 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit_cbc | ING kredietkaart | ING | 2024-04-28 | 24 | Pic isolé | 6.014 |  |  |
| carte_credit_cbc | carte de crédit ING | ING | 2024-05-26 | 23 | Pic isolé | 6.18 |  |  |
| carte_credit_cbc | ING kredietkaart | ING | 2024-09-08 | 26 | Pic isolé | 6.529 |  |  |
| carte_credit_cbc | ING kredietkaart | ING | 2026-04-05 | 29 | Pic isolé | 7.301 |  |  |
| carte_credit_cbc | carte de crédit ING | ING | 2026-08-02 | 35 | Pic isolé | 9.472 |  |  |
| carte_credit_crelan | carte de crédit ING | ING | 2021-10-03 | 37 | Pic isolé | 6.564 |  |  |
| carte_credit_crelan | ING Card | ING | 2021-10-24 | 94 | Pic isolé | 1.783 |  |  |
| carte_credit_crelan | ING Card | ING | 2021-12-05 | 92 | Pic isolé | 1.688 |  |  |
| carte_credit_crelan | ING Card | ING | 2022-01-09 | 89 | Pic isolé | 1.545 |  |  |
| carte_credit_crelan | ING Card | ING | 2022-05-22 | 98 | Pic isolé | 1.973 |  |  |
| carte_credit_crelan | ING kredietkaart | ING | 2022-06-19 | 31 | Pic isolé | 5.431 |  |  |
| carte_credit_crelan | carte de crédit ING | ING | 2022-06-26 | 28 | Pic isolé | 4.929 |  |  |
| carte_credit_crelan | ING Card | ING | 2022-07-03 | 90 | Tendance soutenue | 1.593 |  |  |
| carte_credit_crelan | ING Card | ING | 2022-07-10 | 100 | Tendance soutenue | 2.068 |  |  |
| carte_credit_crelan | ING Card | ING | 2022-08-07 | 94 | Pic isolé | 1.783 |  |  |
| carte_credit_crelan | ING kredietkaart | ING | 2022-09-11 | 28 | Pic isolé | 4.888 |  |  |
| carte_credit_crelan | ING kredietkaart | ING | 2023-03-05 | 28 | Pic isolé | 4.888 |  |  |
| carte_credit_crelan | ING kredietkaart | ING | 2023-03-19 | 24 | Pic isolé | 4.164 |  |  |
| carte_credit_crelan | ING Card | ING | 2023-04-16 | 98 | Pic isolé | 1.973 |  |  |
| carte_credit_crelan | ING Card | ING | 2023-07-16 | 96 | Pic isolé | 1.878 |  |  |
| carte_credit_crelan | ING Card | ING | 2023-08-06 | 93 | Pic isolé | 1.735 |  |  |
| carte_credit_crelan | ING kredietkaart | ING | 2023-09-03 | 29 | Pic isolé | 5.069 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2023-10-29 | 40 | Pic isolé | 1.68 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | ING Card | ING | 2023-10-29 | 89 | Pic isolé | 1.545 |  |  |
| carte_credit_crelan | carte de crédit ING | ING | 2023-12-24 | 31 | Pic isolé | 5.474 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2024-03-17 | 42 | Pic isolé | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | ING Card | ING | 2024-03-24 | 92 | Pic isolé | 1.688 |  |  |
| carte_credit_crelan | ING kredietkaart | ING | 2024-05-26 | 39 | Pic isolé | 6.879 |  |  |
| carte_credit_crelan | carte de crédit ING | ING | 2024-05-26 | 34 | Pic isolé | 6.019 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2024-06-23 | 52 | Pic isolé | 2.375 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-07-07 | 50 | Tendance soutenue | 2.259 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-07-14 | 48 | Tendance soutenue | 2.143 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-07-21 | 44 | Tendance soutenue | 1.911 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-07-28 | 43 | Tendance soutenue | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-08-18 | 42 | Pic isolé | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-09-08 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | carte de crédit ING | ING | 2024-09-08 | 53 | Pic isolé | 9.469 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2024-09-22 | 37 | Tendance soutenue | 1.506 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2024-09-29 | 41 | Tendance soutenue | 1.738 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-02-23 | 43 | Tendance soutenue | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-03-02 | 42 | Tendance soutenue | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-03-09 | 37 | Tendance soutenue | 1.506 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | carte de crédit ING | ING | 2025-03-16 | 32 | Pic isolé | 5.656 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2025-05-18 | 37 | Tendance soutenue | 1.506 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-05-25 | 46 | Tendance soutenue | 2.027 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-06-01 | 47 | Tendance soutenue | 2.085 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-06-22 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-07-06 | 42 | Pic isolé | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-11-02 | 42 | Tendance soutenue | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-11-09 | 41 | Tendance soutenue | 1.738 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2025-11-30 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-02-01 | 41 | Pic isolé | 1.738 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-02-15 | 43 | Pic isolé | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-03-01 | 43 | Pic isolé | 1.853 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-04-12 | 38 | Pic isolé | 1.564 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-05-10 | 44 | Tendance soutenue | 1.911 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-05-17 | 39 | Tendance soutenue | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | ING kredietkaart | ING | 2026-05-24 | 30 | Pic isolé | 5.25 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2026-06-28 | 65 | Pic isolé | 3.129 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | ING kredietkaart | ING | 2026-06-28 | 43 | Pic isolé | 7.603 |  |  |
| carte_credit_crelan | Crelan visa | Crelan | 2026-07-12 | 38 | Pic isolé | 1.564 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-07-26 | 51 | Tendance soutenue | 2.317 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-08-02 | 42 | Tendance soutenue | 1.796 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| carte_credit_crelan | Crelan visa | Crelan | 2026-08-16 | 39 | Pic isolé | 1.622 | 0.318 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue | KBC zichtrekening | KBC | 2021-11-07 | 28 | Pic isolé | 2.456 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2021-11-28 | 23 | Pic isolé | 1.947 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2022-01-16 | 24 | Pic isolé | 2.048 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2022-01-30 | 21 | Pic isolé | 1.743 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2022-03-13 | 19 | Pic isolé | 4.71 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2022-04-10 | 19 | Pic isolé | 1.539 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2022-05-01 | 12 | Pic isolé | 2.913 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2022-05-01 | 21 | Pic isolé | 1.743 |  |  |
| compte_a_vue | Compte Plus KBC | KBC | 2022-06-12 | 16 | Pic isolé | 7.614 |  |  |
| compte_a_vue | compte à vue ING | ING | 2022-10-02 | 15 | Pic isolé | 15.876 |  |  |
| compte_a_vue | ING Do Basic | ING | 2023-06-04 | 18 | Pic isolé | 16.155 |  |  |
| compte_a_vue | Compte Plus KBC | KBC | 2023-12-24 | 21 | Pic isolé | 10.027 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2023-12-24 | 16 | Pic isolé | 3.94 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-01-07 | 100 | Tendance soutenue | 9.789 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-01-14 | 26 | Tendance soutenue | 2.252 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-07-28 | 20 | Pic isolé | 1.641 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2024-08-25 | 24 | Tendance soutenue | 5.993 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-08-25 | 25 | Tendance soutenue | 2.15 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2024-09-01 | 39 | Tendance soutenue | 9.843 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-09-01 | 42 | Tendance soutenue | 3.882 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2024-09-08 | 28 | Tendance soutenue | 7.02 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-09-08 | 34 | Tendance soutenue | 3.067 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2024-09-22 | 19 | Pic isolé | 4.71 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-09-29 | 24 | Pic isolé | 2.048 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-11-03 | 21 | Tendance soutenue | 1.743 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2024-11-10 | 19 | Tendance soutenue | 1.539 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2025-03-16 | 21 | Pic isolé | 1.743 |  |  |
| compte_a_vue | Compte Plus KBC | KBC | 2025-08-10 | 21 | Pic isolé | 10.027 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2025-08-31 | 27 | Pic isolé | 2.354 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2026-03-22 | 27 | Pic isolé | 2.354 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2026-05-17 | 19 | Pic isolé | 1.539 |  |  |
| compte_a_vue | KBC zichtrekening | KBC | 2026-07-26 | 25 | Pic isolé | 2.15 |  |  |
| compte_a_vue | compte à vue ING | ING | 2026-08-30 | 2 | Tendance soutenue | 2.05 |  |  |
| compte_a_vue | ING zichtrekening | ING | 2026-09-06 | 7 | Pic isolé | 1.63 |  |  |
| compte_a_vue | compte à vue ING | ING | 2026-09-06 | 2 | Tendance soutenue | 2.05 |  |  |
| compte_a_vue_argenta | ING zichtrekening | ING | 2022-03-27 | 17 | Pic isolé | 2.695 |  |  |
| compte_a_vue_argenta | ING zichtrekening | ING | 2022-04-17 | 15 | Pic isolé | 2.35 |  |  |
| compte_a_vue_argenta | ING zichtrekening | ING | 2022-08-28 | 23 | Pic isolé | 3.73 |  |  |
| compte_a_vue_argenta | ING zichtrekening | ING | 2022-10-23 | 25 | Pic isolé | 4.074 |  |  |
| compte_a_vue_argenta | ING Do Basic | ING | 2023-06-04 | 22 | Pic isolé | 11.402 |  |  |
| compte_a_vue_argenta | ING zichtrekening | ING | 2023-07-09 | 27 | Pic isolé | 4.419 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2023-08-13 | 38 | Tendance soutenue | 2.358 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2023-08-20 | 48 | Tendance soutenue | 1.737 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2023-08-20 | 100 | Tendance soutenue | 7.028 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2023-08-27 | 68 | Tendance soutenue | 3.071 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2023-08-27 | 21 | Pic isolé | 3.385 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2023-08-27 | 44 | Tendance soutenue | 2.81 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2023-09-03 | 39 | Tendance soutenue | 2.433 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2023-09-24 | 19 | Pic isolé | 3.04 |  |  |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2023-10-29 | 47 | Pic isolé | 1.67 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte à vue ING | ING | 2023-11-05 | 21 | Pic isolé | 8.437 |  |  |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2023-12-31 | 47 | Pic isolé | 1.67 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2023-12-31 | 28 | Pic isolé | 1.605 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-02-18 | 32 | Tendance soutenue | 1.906 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-02-25 | 33 | Tendance soutenue | 1.981 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2024-03-03 | 20 | Pic isolé | 3.212 |  |  |
| compte_a_vue_argenta | ING zichtrekening | ING | 2024-07-14 | 28 | Pic isolé | 4.592 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-08-18 | 37 | Tendance soutenue | 2.283 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2024-08-25 | 35 | Tendance soutenue | 5.799 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-08-25 | 57 | Tendance soutenue | 3.789 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2024-09-01 | 51 | Pic isolé | 1.937 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2024-09-01 | 46 | Tendance soutenue | 7.696 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-09-01 | 47 | Tendance soutenue | 3.036 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-09-08 | 45 | Tendance soutenue | 2.885 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2024-12-08 | 30 | Pic isolé | 1.756 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2025-01-05 | 29 | Pic isolé | 1.68 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2025-04-06 | 29 | Pic isolé | 1.68 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2025-04-27 | 23 | Pic isolé | 3.73 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2025-06-15 | 28 | Pic isolé | 1.605 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2025-07-06 | 39 | Pic isolé | 2.433 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | compte Argenta | Argenta | 2025-08-24 | 33 | Pic isolé | 1.981 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2025-09-07 | 22 | Pic isolé | 3.557 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2025-09-28 | 34 | Pic isolé | 2.057 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2026-01-25 | 46 | Pic isolé | 1.603 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | ING Do Basic | ING | 2026-02-08 | 22 | Pic isolé | 11.402 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2026-03-08 | 43 | Pic isolé | 2.735 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | ING zichtrekening | ING | 2026-05-03 | 21 | Pic isolé | 3.385 |  |  |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2026-06-07 | 46 | Tendance soutenue | 1.603 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2026-06-14 | 47 | Tendance soutenue | 1.67 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_argenta | compte à vue ING | ING | 2026-07-19 | 34 | Pic isolé | 13.715 |  |  |
| compte_a_vue_argenta | compte Argenta | Argenta | 2026-08-09 | 30 | Pic isolé | 1.756 | 0.253 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_argenta | Argenta rekening | Argenta | 2026-08-23 | 47 | Pic isolé | 1.67 | 0.736 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2021-12-05 | 18 | Tendance soutenue | 2.381 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2021-12-12 | 13 | Tendance soutenue | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2022-01-02 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2022-03-27 | 10 | Pic isolé | 2.795 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2022-04-17 | 9 | Pic isolé | 2.492 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2022-05-08 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2022-08-28 | 13 | Pic isolé | 3.705 |  |  |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2022-10-23 | 14 | Pic isolé | 4.009 |  |  |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2023-01-01 | 91 | Pic isolé | 4.248 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-01-29 | 19 | Pic isolé | 2.544 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-04-09 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-05-14 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING Do Basic | ING | 2023-06-04 | 13 | Pic isolé | 11.402 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-06-18 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2023-07-09 | 15 | Pic isolé | 4.312 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-07-16 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-08-20 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2023-08-20 | 72 | Tendance soutenue | 2.741 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2023-08-27 | 12 | Pic isolé | 3.402 |  |  |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2023-08-27 | 61 | Tendance soutenue | 1.868 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2023-09-24 | 11 | Pic isolé | 3.099 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-10-01 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2023-10-22 | 57 | Pic isolé | 1.551 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte à vue ING | ING | 2023-11-05 | 12 | Pic isolé | 8.571 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2023-11-19 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-01-14 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-01-21 | 17 | Tendance soutenue | 2.218 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-01-21 | 100 | Tendance soutenue | 4.963 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-01-28 | 62 | Tendance soutenue | 1.947 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-02-04 | 61 | Tendance soutenue | 1.868 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-02-11 | 16 | Pic isolé | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-02-11 | 61 | Tendance soutenue | 1.868 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-03-03 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2024-03-03 | 11 | Pic isolé | 3.099 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-04-07 | 19 | Pic isolé | 2.544 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-07-07 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2024-07-14 | 16 | Pic isolé | 4.615 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-08-04 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-08-25 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2024-08-25 | 20 | Tendance soutenue | 5.828 |  |  |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-08-25 | 81 | Tendance soutenue | 3.455 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2024-09-01 | 26 | Tendance soutenue | 7.648 |  |  |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-09-01 | 96 | Tendance soutenue | 4.645 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2024-09-08 | 62 | Tendance soutenue | 1.947 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-09-15 | 18 | Tendance soutenue | 2.381 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-09-22 | 13 | Tendance soutenue | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-10-06 | 14 | Tendance soutenue | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2024-10-13 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2025-01-05 | 68 | Pic isolé | 2.423 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-01-19 | 14 | Tendance soutenue | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-01-26 | 13 | Tendance soutenue | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-02-09 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-04-06 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2025-04-27 | 13 | Pic isolé | 3.705 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-05-18 | 21 | Pic isolé | 2.87 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-06-01 | 16 | Pic isolé | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-07-06 | 15 | Pic isolé | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-07-27 | 16 | Pic isolé | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2025-09-07 | 13 | Pic isolé | 3.705 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-11-23 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-12-14 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2025-12-21 | 17 | Tendance soutenue | 2.218 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2025-12-28 | 57 | Pic isolé | 1.551 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-01-11 | 14 | Pic isolé | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-02-08 | 17 | Pic isolé | 2.218 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING Do Basic | ING | 2026-02-08 | 13 | Pic isolé | 11.402 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-05-03 | 22 | Pic isolé | 3.033 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | ING zichtrekening | ING | 2026-05-03 | 12 | Pic isolé | 3.402 |  |  |
| compte_a_vue_bnppf | compte BNP | BNP Paribas Fortis | 2026-05-03 | 100 | Pic isolé | 4.963 | 1.000 | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-05-24 | 15 | Tendance soutenue | 1.892 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-05-31 | 16 | Tendance soutenue | 2.055 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | compte à vue ING | ING | 2026-07-19 | 19 | Pic isolé | 13.624 |  |  |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-08-02 | 18 | Tendance soutenue | 2.381 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-08-09 | 14 | Tendance soutenue | 1.729 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNP rekening | BNP Paribas Fortis | 2026-08-23 | 13 | Pic isolé | 1.566 | 0.268 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_cbc | ING zichtrekening | ING | 2022-03-13 | 48 | Pic isolé | 4.545 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2022-05-01 | 31 | Pic isolé | 2.874 |  |  |
| compte_a_vue_cbc | compte à vue ING | ING | 2022-10-02 | 39 | Pic isolé | 15.942 |  |  |
| compte_a_vue_cbc | compte à vue CBC | CBC | 2023-04-30 | 61 | Pic isolé | 12.079 |  |  |
| compte_a_vue_cbc | ING Do Basic | ING | 2023-06-04 | 46 | Pic isolé | 16.155 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2023-12-24 | 43 | Pic isolé | 4.053 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2024-08-25 | 62 | Tendance soutenue | 5.921 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2024-09-01 | 100 | Tendance soutenue | 9.657 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2024-09-08 | 74 | Tendance soutenue | 7.101 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2024-09-22 | 49 | Pic isolé | 4.643 |  |  |
| compte_a_vue_cbc | compte à vue CBC | CBC | 2025-12-21 | 54 | Pic isolé | 10.682 |  |  |
| compte_a_vue_cbc | compte à vue ING | ING | 2026-08-30 | 5 | Tendance soutenue | 1.978 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2026-09-06 | 18 | Tendance soutenue | 1.596 |  |  |
| compte_a_vue_cbc | compte à vue ING | ING | 2026-09-06 | 4 | Tendance soutenue | 1.568 |  |  |
| compte_a_vue_cbc | ING zichtrekening | ING | 2026-09-13 | 24 | Tendance soutenue | 2.186 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2022-03-27 | 25 | Pic isolé | 2.705 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2022-04-17 | 23 | Pic isolé | 2.47 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2022-08-28 | 34 | Pic isolé | 3.764 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2022-10-23 | 37 | Pic isolé | 4.117 |  |  |
| compte_a_vue_revolut | ING Do Basic | ING | 2023-06-04 | 32 | Pic isolé | 11.224 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2023-07-09 | 39 | Pic isolé | 4.353 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2023-08-27 | 31 | Pic isolé | 3.411 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2023-09-24 | 27 | Pic isolé | 2.941 |  |  |
| compte_a_vue_revolut | compte à vue ING | ING | 2023-11-05 | 30 | Pic isolé | 8.386 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2024-03-03 | 29 | Pic isolé | 3.176 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2024-07-14 | 42 | Pic isolé | 4.706 |  |  |
| compte_a_vue_revolut | ING zichtrekening | ING | 2024-08-25 | 51 | Tendance soutenue | 5.765 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2024-08-25 | 79 | Pic isolé | 1.893 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | ING zichtrekening | ING | 2024-09-01 | 67 | Tendance soutenue | 7.648 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2024-12-29 | 69 | Pic isolé | 1.542 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-04-06 | 92 | Pic isolé | 2.349 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | ING zichtrekening | ING | 2025-04-27 | 34 | Pic isolé | 3.764 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-06-22 | 70 | Pic isolé | 1.577 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-07-06 | 73 | Pic isolé | 1.683 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-08-10 | 77 | Tendance soutenue | 1.823 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-08-17 | 100 | Tendance soutenue | 2.63 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | ING zichtrekening | ING | 2025-09-07 | 33 | Pic isolé | 3.647 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-09-07 | 72 | Pic isolé | 1.647 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-09-21 | 72 | Pic isolé | 1.647 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-11-02 | 83 | Pic isolé | 2.034 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2025-11-30 | 81 | Pic isolé | 1.963 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-01-04 | 70 | Pic isolé | 1.577 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | ING Do Basic | ING | 2026-02-08 | 33 | Pic isolé | 11.577 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-02-22 | 77 | Pic isolé | 1.823 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-04-12 | 71 | Pic isolé | 1.612 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | ING zichtrekening | ING | 2026-05-03 | 30 | Pic isolé | 3.294 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-05-03 | 81 | Tendance soutenue | 1.963 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-05-10 | 78 | Tendance soutenue | 1.858 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-05-17 | 71 | Tendance soutenue | 1.612 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-05-24 | 70 | Tendance soutenue | 1.577 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-05-31 | 68 | Tendance soutenue | 1.507 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-06-07 | 74 | Tendance soutenue | 1.718 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-06-28 | 85 | Pic isolé | 2.104 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte à vue ING | ING | 2026-07-19 | 49 | Pic isolé | 13.754 |  |  |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-08-09 | 71 | Tendance soutenue | 1.612 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_a_vue_revolut | compte Revolut | Revolut | 2026-08-16 | 73 | Tendance soutenue | 1.683 | 0.479 | selected_low_coverage,broad_fallback,asymmetric |
| compte_epargne | ING spaarrekening | ING | 2022-12-25 | 38 | Tendance soutenue | 2.95 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2022-12-25 | 40 | Tendance soutenue | 1.599 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-01-01 | 47 | Tendance soutenue | 3.81 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-01-01 | 60 | Tendance soutenue | 2.987 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-01-08 | 35 | Tendance soutenue | 2.663 |  |  |
| compte_epargne | ING Orange Savings | ING | 2023-01-15 | 11 | Pic isolé | 6.485 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-01-15 | 24 | Tendance soutenue | 1.612 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-01-22 | 25 | Tendance soutenue | 1.708 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-01-29 | 29 | Tendance soutenue | 2.09 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-02-05 | 41 | Pic isolé | 1.668 |  |  |
| compte_epargne | compte épargne ING | ING | 2023-04-23 | 13 | Pic isolé | 8.862 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-07-30 | 32 | Tendance soutenue | 2.377 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-07-30 | 46 | Pic isolé | 2.015 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-08-06 | 27 | Tendance soutenue | 1.899 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-08-20 | 45 | Tendance soutenue | 3.619 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-08-20 | 100 | Tendance soutenue | 5.762 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-08-27 | 37 | Tendance soutenue | 2.854 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-08-27 | 80 | Tendance soutenue | 4.374 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2023-10-22 | 15 | Pic isolé | 6.737 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-10-29 | 42 | Pic isolé | 3.332 |  |  |
| compte_epargne | ING spaarrekening | ING | 2023-11-26 | 27 | Pic isolé | 1.899 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2023-11-26 | 15 | Pic isolé | 6.737 |  |  |
| compte_epargne | compte épargne ING | ING | 2023-12-03 | 14 | Pic isolé | 9.554 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-12-24 | 51 | Tendance soutenue | 2.362 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2023-12-31 | 50 | Tendance soutenue | 2.293 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2024-01-07 | 12 | Pic isolé | 5.358 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2024-01-07 | 41 | Tendance soutenue | 1.668 |  |  |
| compte_epargne | ING spaarrekening | ING | 2024-01-28 | 23 | Pic isolé | 1.517 |  |  |
| compte_epargne | ING spaarrekening | ING | 2024-03-10 | 23 | Pic isolé | 1.517 |  |  |
| compte_epargne | ING spaarrekening | ING | 2024-08-25 | 41 | Tendance soutenue | 3.237 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2024-08-25 | 39 | Tendance soutenue | 1.53 |  |  |
| compte_epargne | ING spaarrekening | ING | 2024-09-01 | 49 | Tendance soutenue | 4.001 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2024-09-01 | 89 | Tendance soutenue | 4.999 |  |  |
| compte_epargne | ING spaarrekening | ING | 2024-09-08 | 32 | Tendance soutenue | 2.377 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2024-09-08 | 48 | Tendance soutenue | 2.154 |  |  |
| compte_epargne | ING spaarrekening | ING | 2024-12-29 | 25 | Pic isolé | 1.708 |  |  |
| compte_epargne | KBC spaarrekening | KBC | 2024-12-29 | 41 | Pic isolé | 1.668 |  |  |
| compte_epargne | ING Orange Savings | ING | 2025-08-10 | 19 | Pic isolé | 11.278 |  |  |
| compte_epargne | ING spaarrekening | ING | 2025-08-24 | 23 | Pic isolé | 1.517 |  |  |
| compte_epargne | ING spaarrekening | ING | 2026-02-22 | 25 | Pic isolé | 1.708 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2026-04-19 | 20 | Pic isolé | 9.036 |  |  |
| compte_epargne | compte épargne ING | ING | 2026-06-07 | 12 | Pic isolé | 8.17 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2026-06-28 | 14 | Pic isolé | 6.277 |  |  |
| compte_epargne | ING Orange Savings | ING | 2026-08-30 | 16 | Pic isolé | 9.481 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2026-08-30 | 6 | Tendance soutenue | 2.599 |  |  |
| compte_epargne | compte épargne ING | ING | 2026-08-30 | 4 | Tendance soutenue | 2.633 |  |  |
| compte_epargne | KBC Start2Save | KBC | 2026-09-06 | 6 | Tendance soutenue | 2.599 |  |  |
| compte_epargne | compte épargne ING | ING | 2026-09-06 | 4 | Tendance soutenue | 2.633 |  |  |
| compte_epargne | compte épargne ING | ING | 2026-09-13 | 4 | Tendance soutenue | 2.633 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2022-12-25 | 27 | Tendance soutenue | 1.729 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2022-12-25 | 26 | Tendance soutenue | 2.965 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-01-01 | 25 | Tendance soutenue | 1.541 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-01-01 | 31 | Tendance soutenue | 3.67 |  |  |
| compte_epargne_argenta | compte épargne ING | ING | 2023-01-01 | 7 | Pic isolé | 9.702 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-01-08 | 26 | Tendance soutenue | 2.965 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-01-22 | 19 | Tendance soutenue | 1.977 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-01-29 | 20 | Tendance soutenue | 2.118 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-05-21 | 25 | Pic isolé | 1.541 | 0.575 |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-07-30 | 25 | Pic isolé | 1.541 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-07-30 | 21 | Pic isolé | 2.259 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-08-20 | 100 | Tendance soutenue | 8.609 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-08-20 | 28 | Tendance soutenue | 3.247 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-08-27 | 64 | Tendance soutenue | 5.216 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-08-27 | 26 | Tendance soutenue | 2.965 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-09-03 | 28 | Tendance soutenue | 1.824 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-10-29 | 29 | Pic isolé | 3.388 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-11-26 | 25 | Pic isolé | 1.541 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2023-11-26 | 17 | Pic isolé | 1.695 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2023-12-24 | 26 | Pic isolé | 1.635 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2024-02-04 | 16 | Pic isolé | 1.554 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2024-08-25 | 27 | Tendance soutenue | 3.106 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2024-09-01 | 47 | Pic isolé | 3.614 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2024-09-01 | 32 | Tendance soutenue | 3.811 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2024-09-08 | 18 | Tendance soutenue | 1.836 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2024-12-29 | 32 | Pic isolé | 2.201 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2024-12-29 | 20 | Pic isolé | 2.118 |  |  |
| compte_epargne_argenta | compte épargne ING | ING | 2025-01-26 | 8 | Pic isolé | 11.106 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2025-02-23 | 16 | Pic isolé | 1.554 |  |  |
| compte_epargne_argenta | ING Orange Savings | ING | 2025-04-27 | 10 | Pic isolé | 9.819 |  |  |
| compte_epargne_argenta | ING Orange Savings | ING | 2025-08-17 | 13 | Pic isolé | 12.791 |  |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2025-08-24 | 16 | Pic isolé | 1.554 |  |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2025-12-28 | 28 | Pic isolé | 1.824 | 0.575 |  |
| compte_epargne_argenta | Argenta spaarrekening | Argenta | 2026-03-29 | 26 | Pic isolé | 1.635 | 0.575 |  |
| compte_epargne_argenta | ING spaarrekening | ING | 2026-08-30 | 16 | Pic isolé | 1.554 |  |  |
| compte_epargne_argenta | compte épargne ING | ING | 2026-08-30 | 2 | Tendance soutenue | 2.684 |  |  |
| compte_epargne_argenta | compte épargne ING | ING | 2026-09-06 | 3 | Tendance soutenue | 4.088 |  |  |
| compte_epargne_argenta | compte épargne ING | ING | 2026-09-13 | 3 | Tendance soutenue | 4.088 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2022-12-25 | 77 | Tendance soutenue | 2.907 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-01-01 | 97 | Tendance soutenue | 3.839 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-01-08 | 72 | Tendance soutenue | 2.674 |  |  |
| compte_epargne_cbc | ING Orange Savings | ING | 2023-01-15 | 22 | Pic isolé | 6.557 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-01-15 | 49 | Tendance soutenue | 1.602 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-01-22 | 51 | Tendance soutenue | 1.695 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-01-29 | 60 | Tendance soutenue | 2.115 |  |  |
| compte_epargne_cbc | compte épargne ING | ING | 2023-04-23 | 26 | Pic isolé | 8.405 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-07-30 | 66 | Tendance soutenue | 2.394 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-08-06 | 55 | Tendance soutenue | 1.882 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-08-20 | 92 | Tendance soutenue | 3.606 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-08-27 | 76 | Tendance soutenue | 2.86 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-10-29 | 87 | Pic isolé | 3.373 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2023-11-26 | 56 | Pic isolé | 1.928 |  |  |
| compte_epargne_cbc | compte épargne ING | ING | 2023-12-03 | 30 | Pic isolé | 9.719 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2024-01-28 | 48 | Pic isolé | 1.556 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2024-03-10 | 47 | Pic isolé | 1.509 |  |  |
| compte_epargne_cbc | compte épargne CBC | CBC | 2024-06-09 | 24 | Pic isolé | 15.909 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2024-08-25 | 84 | Tendance soutenue | 3.233 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2024-09-01 | 100 | Tendance soutenue | 3.979 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2024-09-08 | 65 | Tendance soutenue | 2.348 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2024-12-29 | 52 | Pic isolé | 1.742 |  |  |
| compte_epargne_cbc | ING Orange Savings | ING | 2025-08-10 | 38 | Pic isolé | 11.401 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2025-08-24 | 48 | Pic isolé | 1.556 |  |  |
| compte_epargne_cbc | ING spaarrekening | ING | 2026-02-22 | 51 | Pic isolé | 1.695 |  |  |
| compte_epargne_cbc | compte épargne ING | ING | 2026-06-07 | 25 | Pic isolé | 8.076 |  |  |
| compte_epargne_cbc | ING Orange Savings | ING | 2026-08-30 | 31 | Pic isolé | 9.282 |  |  |
| compte_epargne_cbc | compte épargne CBC | CBC | 2026-08-30 | 3 | Tendance soutenue | 1.922 |  |  |
| compte_epargne_cbc | compte épargne ING | ING | 2026-08-30 | 8 | Tendance soutenue | 2.491 |  |  |
| compte_epargne_cbc | compte épargne CBC | CBC | 2026-09-06 | 3 | Tendance soutenue | 1.922 |  |  |
| compte_epargne_cbc | compte épargne ING | ING | 2026-09-06 | 8 | Tendance soutenue | 2.491 |  |  |
| compte_epargne_cbc | compte épargne ING | ING | 2026-09-13 | 12 | Tendance soutenue | 3.806 |  |  |
| compte_professionnel | ING zakelijke rekening | ING | 2022-07-31 | 81 | Pic isolé | 12.661 |  |  |
| compte_professionnel | ING zakelijke rekening | ING | 2023-01-01 | 63 | Pic isolé | 9.826 |  |  |
| compte_professionnel | compte professionnel ING | ING | 2023-05-28 | 73 | Pic isolé | 9.898 |  |  |
| compte_professionnel | KBC zakelijke rekening | KBC | 2023-10-15 | 62 | Pic isolé | 6.82 |  |  |
| compte_professionnel | Business'Bank ING | ING | 2025-03-02 | 79 | Pic isolé | 10.904 |  |  |
| compte_professionnel | KBC zakelijke rekening | KBC | 2025-03-09 | 84 | Pic isolé | 9.281 |  |  |
| compte_professionnel | compte professionnel ING | ING | 2025-11-02 | 93 | Pic isolé | 12.636 |  |  |
| compte_professionnel | Business'Bank ING | ING | 2026-07-05 | 86 | Pic isolé | 11.878 |  |  |
| compte_professionnel | KBC zakelijke rekening | KBC | 2026-08-23 | 100 | Pic isolé | 11.071 |  |  |
| compte_professionnel_cbc | ING zakelijke rekening | ING | 2022-07-31 | 79 | Pic isolé | 12.702 |  |  |
| compte_professionnel_cbc | ING zakelijke rekening | ING | 2023-01-01 | 61 | Pic isolé | 9.786 |  |  |
| compte_professionnel_cbc | compte professionnel ING | ING | 2023-05-28 | 71 | Pic isolé | 9.883 |  |  |
| compte_professionnel_cbc | compte professionnel CBC | CBC | 2024-11-03 | 100 | Pic isolé | 12.643 |  |  |
| compte_professionnel_cbc | Business'Bank ING | ING | 2025-03-02 | 76 | Pic isolé | 10.885 |  |  |
| compte_professionnel_cbc | compte professionnel CBC | CBC | 2025-08-17 | 79 | Pic isolé | 9.969 |  |  |
| compte_professionnel_cbc | compte professionnel ING | ING | 2025-11-02 | 90 | Pic isolé | 12.553 |  |  |
| compte_professionnel_cbc | Business'Bank ING | ING | 2026-07-05 | 83 | Pic isolé | 11.896 |  |  |
| compte_professionnel_cbc | compte professionnel ING | ING | 2026-08-30 | 14 | Pic isolé | 1.87 |  |  |
| compte_professionnel_cbc | KBC Business Pro | CBC | 2026-09-06 | 8 | Pic isolé | 16.155 |  |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2021-09-12 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | ING | ING | 2021-09-26 | 88 | Pic isolé | 2.73 | 1.000 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2021-10-03 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2021-10-10 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2021-11-14 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2021-11-21 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2021-12-12 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-01-02 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-01-16 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-02-20 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | ING | ING | 2022-02-27 | 87 | Pic isolé | 2.624 | 1.000 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-03-13 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | ING | ING | 2022-05-01 | 84 | Pic isolé | 2.308 | 1.000 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-05-15 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-06-26 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-07-31 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-08-21 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-08-28 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-10-02 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2022-10-09 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-01-01 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-01-15 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-01-29 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-02-19 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-02-26 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-03-05 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-04-02 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-04-09 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-04-30 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-07-09 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-07-30 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Bank | Crelan | 2023-08-20 | 5 | Tendance soutenue | 3.321 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Bank | Crelan | 2023-08-27 | 4 | Tendance soutenue | 2.397 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-08-27 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | ING | ING | 2023-08-27 | 80 | Pic isolé | 1.885 | 1.000 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-09-24 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-10-22 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-11-12 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-11-26 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2023-12-31 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-01-07 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-01-28 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Bank | Crelan | 2024-02-18 | 4 | Pic isolé | 2.397 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-02-18 | 2 | Pic isolé | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | ING | ING | 2024-03-24 | 100 | Pic isolé | 3.997 | 1.000 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-03-31 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-04-07 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-06-02 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | AXA Bank | Crelan | 2024-06-09 | 4 | Pic isolé | 2.397 | 0.701 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-06-09 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-06-09 | 58 | Tendance soutenue | 5.078 | 1.000 |  |
| contexte_fusion_crelan_axa | AXA Banque | Crelan | 2024-06-16 | 2 | Tendance soutenue | 1.74 | 0.625 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-06-16 | 43 | Tendance soutenue | 2.829 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-06-23 | 39 | Tendance soutenue | 2.229 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-06-30 | 39 | Tendance soutenue | 2.229 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-07-07 | 37 | Tendance soutenue | 1.929 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-07-14 | 36 | Tendance soutenue | 1.779 | 1.000 |  |
| contexte_fusion_crelan_axa | ING | ING | 2024-08-25 | 85 | Pic isolé | 2.413 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-09-01 | 44 | Tendance soutenue | 2.979 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-09-08 | 38 | Tendance soutenue | 2.079 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2024-12-15 | 36 | Pic isolé | 1.779 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2025-03-23 | 35 | Tendance soutenue | 1.629 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2025-03-30 | 38 | Tendance soutenue | 2.079 | 1.000 |  |
| contexte_fusion_crelan_axa | Crelan | Crelan | 2025-07-06 | 36 | Pic isolé | 1.779 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2021-09-26 | 88 | Pic isolé | 2.728 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2021-09-26 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2021-11-21 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2021-12-12 | 83 | Pic isolé | 2.83 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2021-12-26 | 76 | Tendance soutenue | 2.176 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2021-12-26 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-01-02 | 81 | Tendance soutenue | 2.643 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-01-30 | 79 | Pic isolé | 2.457 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-02-27 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2022-02-27 | 87 | Pic isolé | 2.622 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2022-02-27 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-06 | 71 | Tendance soutenue | 1.709 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-20 | 70 | Tendance soutenue | 1.616 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-27 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-04-03 | 74 | Tendance soutenue | 1.989 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-04-24 | 84 | Tendance soutenue | 2.924 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-05-01 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2022-05-01 | 84 | Pic isolé | 2.306 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-05-29 | 69 | Tendance soutenue | 1.522 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-05 | 69 | Tendance soutenue | 1.522 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-12 | 70 | Tendance soutenue | 1.616 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-19 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2022-06-19 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-26 | 78 | Tendance soutenue | 2.363 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-03 | 79 | Tendance soutenue | 2.457 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-07-03 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-10 | 70 | Tendance soutenue | 1.616 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-07-10 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-31 | 79 | Tendance soutenue | 2.457 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-07 | 76 | Tendance soutenue | 2.176 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-21 | 71 | Tendance soutenue | 1.709 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-28 | 74 | Tendance soutenue | 1.989 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-04 | 73 | Tendance soutenue | 1.896 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-11 | 72 | Tendance soutenue | 1.803 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-18 | 75 | Tendance soutenue | 2.083 | 1.000 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-25 | 73 | Tendance soutenue | 1.896 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-09-25 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-10-02 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-10-23 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-11-20 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2022-11-27 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2022-11-27 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-01-22 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-01-29 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-02-26 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2023-04-16 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-04-16 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2023-04-30 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-04-30 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-05-21 | 4 | Pic isolé | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2023-07-02 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2023-07-30 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2023-08-20 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-08-20 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2023-08-27 | 80 | Pic isolé | 1.884 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-08-27 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-09-03 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-09-10 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-09-24 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-10-01 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2023-12-24 | 3 | Pic isolé | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-12-24 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2023-12-31 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2024-01-07 | 3 | Tendance soutenue | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2024-01-07 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2024-01-14 | 3 | Tendance soutenue | 1.84 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2024-01-14 | 4 | Tendance soutenue | 1.502 | 0.590 |  |
| contexte_integration_bnppf_bpost | BNP Paribas Fortis | BNP Paribas Fortis | 2024-01-21 | 93 | Pic isolé | 3.764 | 1.000 |  |
| contexte_integration_bnppf_bpost | bpost bank | BNP Paribas Fortis | 2024-01-21 | 4 | Tendance soutenue | 2.8 | 0.563 |  |
| contexte_integration_bnppf_bpost | bpost banque | BNP Paribas Fortis | 2024-01-21 | 7 | Tendance soutenue | 3.412 | 0.590 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2024-03-24 | 100 | Pic isolé | 3.994 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2024-08-25 | 85 | Tendance soutenue | 2.411 | 1.000 |  |
| contexte_integration_bnppf_bpost | ING | ING | 2024-09-01 | 85 | Tendance soutenue | 2.411 | 1.000 |  |
| epargne_pension | ING pensioensparen | ING | 2021-09-19 | 51 | Pic isolé | 12.41 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2021-09-26 | 54 | Pic isolé | 3.31 |  |  |
| epargne_pension | ING Star Fund | ING | 2021-10-03 | 49 | Pic isolé | 3.152 |  |  |
| epargne_pension | ING Star Fund | ING | 2021-10-31 | 50 | Pic isolé | 3.223 |  |  |
| epargne_pension | ING Star Fund | ING | 2021-11-21 | 53 | Pic isolé | 3.435 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2021-11-28 | 49 | Pic isolé | 2.977 |  |  |
| epargne_pension | ING Star Fund | ING | 2021-12-26 | 63 | Pic isolé | 4.142 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2022-01-02 | 76 | Pic isolé | 4.777 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-02-20 | 41 | Pic isolé | 2.587 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2022-02-20 | 39 | Pic isolé | 2.31 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-04-03 | 36 | Pic isolé | 2.234 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2022-06-05 | 45 | Pic isolé | 2.71 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2022-07-03 | 51 | Pic isolé | 3.11 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-08-28 | 48 | Pic isolé | 3.082 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-09-11 | 41 | Pic isolé | 2.587 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-10-09 | 57 | Pic isolé | 3.718 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-11-06 | 48 | Tendance soutenue | 3.082 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-11-13 | 40 | Tendance soutenue | 2.516 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-11-27 | 39 | Pic isolé | 2.446 |  |  |
| epargne_pension | ING pensioensparen | ING | 2022-12-18 | 42 | Pic isolé | 10.203 |  |  |
| epargne_pension | ING Star Fund | ING | 2022-12-25 | 50 | Pic isolé | 3.223 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2022-12-25 | 77 | Pic isolé | 4.844 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-01-08 | 48 | Tendance soutenue | 3.082 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-01-15 | 48 | Tendance soutenue | 3.082 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-03-05 | 42 | Pic isolé | 2.658 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-05-21 | 49 | Pic isolé | 3.152 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2023-05-28 | 42 | Pic isolé | 2.51 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2023-07-30 | 59 | Pic isolé | 3.644 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-09-24 | 59 | Pic isolé | 3.859 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-11-12 | 47 | Tendance soutenue | 3.011 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-11-19 | 43 | Tendance soutenue | 2.728 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2023-11-26 | 48 | Pic isolé | 2.91 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-12-17 | 60 | Tendance soutenue | 3.93 |  |  |
| epargne_pension | ING Star Fund | ING | 2023-12-24 | 50 | Tendance soutenue | 3.223 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2024-05-12 | 49 | Pic isolé | 2.977 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2024-05-26 | 58 | Pic isolé | 3.577 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2024-11-24 | 61 | Pic isolé | 3.777 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2024-12-08 | 52 | Pic isolé | 3.177 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2024-12-22 | 67 | Pic isolé | 4.177 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2025-01-05 | 48 | Pic isolé | 2.91 |  |  |
| epargne_pension | ING Star Fund | ING | 2025-01-19 | 71 | Pic isolé | 4.708 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2025-05-18 | 61 | Pic isolé | 3.777 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2025-12-21 | 63 | Pic isolé | 3.91 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2026-01-04 | 61 | Pic isolé | 3.777 |  |  |
| epargne_pension | KBC pensioensparen | KBC | 2026-01-25 | 49 | Pic isolé | 2.977 |  |  |
| epargne_pension | épargne pension ING | ING | 2026-04-12 | 100 | Pic isolé | 16.148 |  |  |
| epargne_pension | KBC Pension Savings Fund | KBC | 2026-08-30 | 6 | Tendance soutenue | 12.395 |  |  |
| epargne_pension | KBC Pension Savings Fund | KBC | 2026-09-06 | 5 | Tendance soutenue | 10.314 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2021-09-26 | 46 | Tendance soutenue | 3.504 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2021-10-03 | 41 | Tendance soutenue | 3.088 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2021-11-21 | 37 | Pic isolé | 2.756 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2021-12-12 | 48 | Pic isolé | 3.67 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2021-12-26 | 73 | Pic isolé | 1.524 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2022-01-09 | 50 | Pic isolé | 3.836 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2022-01-30 | 96 | Pic isolé | 2.374 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2022-02-20 | 29 | Pic isolé | 2.091 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2022-03-06 | 96 | Tendance soutenue | 2.374 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2022-03-13 | 83 | Tendance soutenue | 1.894 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2022-06-12 | 37 | Pic isolé | 2.756 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2022-06-26 | 39 | Pic isolé | 2.922 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2022-07-31 | 84 | Pic isolé | 1.931 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2022-11-27 | 75 | Pic isolé | 1.598 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2022-12-04 | 36 | Pic isolé | 2.673 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2022-12-18 | 75 | Pic isolé | 1.598 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-01-08 | 36 | Tendance soutenue | 2.673 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2023-01-15 | 90 | Pic isolé | 2.152 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-01-15 | 34 | Tendance soutenue | 2.507 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-01-22 | 49 | Tendance soutenue | 3.753 |  |  |
| epargne_pension_bnppf | épargne pension ING | ING | 2023-01-22 | 39 | Pic isolé | 16.155 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-01-29 | 34 | Tendance soutenue | 2.507 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-03-05 | 37 | Pic isolé | 2.756 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-03-26 | 31 | Pic isolé | 2.257 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-04-23 | 38 | Pic isolé | 2.839 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-05-21 | 35 | Pic isolé | 2.59 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-07-30 | 52 | Pic isolé | 4.002 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-09-24 | 47 | Pic isolé | 3.587 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-11-19 | 39 | Pic isolé | 2.922 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2023-12-17 | 42 | Pic isolé | 3.171 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2024-01-07 | 94 | Pic isolé | 2.3 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2024-01-21 | 83 | Pic isolé | 1.894 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING Star Fund | ING | 2024-01-28 | 60 | Pic isolé | 4.667 |  |  |
| epargne_pension_bnppf | ING pensioensparen | ING | 2024-01-28 | 36 | Pic isolé | 15.906 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2024-12-15 | 38 | Pic isolé | 2.839 |  |  |
| epargne_pension_bnppf | ING Star Fund | ING | 2025-03-02 | 49 | Pic isolé | 3.753 |  |  |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2025-05-04 | 100 | Pic isolé | 2.521 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2025-07-13 | 78 | Pic isolé | 1.709 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNP pension | BNP Paribas Fortis | 2025-12-07 | 79 | Pic isolé | 1.746 | 0.625 | broad_fallback,asymmetric |
| epargne_pension_bnppf | ING pensioensparen | ING | 2026-09-06 | 4 | Tendance soutenue | 1.7 |  |  |
| epargne_pension_bnppf | ING pensioensparen | ING | 2026-09-13 | 5 | Tendance soutenue | 2.144 |  |  |
| epargne_pension_cbc | ING pensioensparen | ING | 2021-09-19 | 51 | Pic isolé | 12.398 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2021-10-03 | 49 | Pic isolé | 3.154 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2021-10-31 | 50 | Pic isolé | 3.224 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2021-11-21 | 53 | Pic isolé | 3.437 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2021-12-26 | 63 | Pic isolé | 4.144 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-02-20 | 41 | Pic isolé | 2.588 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-04-03 | 36 | Pic isolé | 2.235 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-08-28 | 48 | Pic isolé | 3.083 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-09-11 | 41 | Pic isolé | 2.588 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-10-09 | 57 | Pic isolé | 3.719 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-11-06 | 48 | Tendance soutenue | 3.083 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-11-13 | 40 | Tendance soutenue | 2.517 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-11-27 | 39 | Pic isolé | 2.447 |  |  |
| epargne_pension_cbc | ING pensioensparen | ING | 2022-12-18 | 42 | Pic isolé | 10.193 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2022-12-25 | 50 | Pic isolé | 3.224 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-01-08 | 48 | Tendance soutenue | 3.083 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-01-15 | 48 | Tendance soutenue | 3.083 |  |  |
| epargne_pension_cbc | épargne pension CBC | CBC | 2023-01-15 | 40 | Pic isolé | 16.155 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-03-05 | 42 | Pic isolé | 2.659 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-05-21 | 49 | Pic isolé | 3.154 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-09-24 | 59 | Pic isolé | 3.861 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-11-12 | 47 | Tendance soutenue | 3.012 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-11-19 | 43 | Tendance soutenue | 2.73 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-12-17 | 60 | Tendance soutenue | 3.932 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2023-12-24 | 50 | Tendance soutenue | 3.224 |  |  |
| epargne_pension_cbc | ING Star Fund | ING | 2025-01-19 | 71 | Pic isolé | 4.709 |  |  |
| epargne_pension_cbc | épargne pension ING | ING | 2026-04-12 | 100 | Pic isolé | 16.148 |  |  |
| investissement_courtage | Bolero | KBC | 2022-01-02 | 100 | Pic isolé | 3.361 |  |  |
| investissement_courtage | ING Self Invest | ING | 2022-03-06 | 2 | Tendance soutenue | 4.342 |  |  |
| investissement_courtage | ING Self Invest | ING | 2022-03-13 | 2 | Tendance soutenue | 4.342 |  |  |
| investissement_courtage | ING Self Invest | ING | 2023-02-05 | 3 | Pic isolé | 6.595 |  |  |
| investissement_courtage | ING Self Invest | ING | 2023-08-20 | 3 | Tendance soutenue | 6.595 |  |  |
| investissement_courtage | ING Self Invest | ING | 2023-08-27 | 3 | Tendance soutenue | 6.595 |  |  |
| investissement_courtage | ING Self Invest | ING | 2025-02-16 | 3 | Pic isolé | 6.595 |  |  |
| investissement_courtage | Bolero | KBC | 2025-04-06 | 93 | Pic isolé | 2.723 |  |  |
| investissement_courtage | ING Self Invest | ING | 2025-05-25 | 3 | Pic isolé | 6.595 |  |  |
| investissement_courtage | Bolero | KBC | 2025-07-27 | 85 | Pic isolé | 1.994 |  |  |
| investissement_courtage | Bolero | KBC | 2025-10-05 | 84 | Tendance soutenue | 1.903 |  |  |
| investissement_courtage | Bolero | KBC | 2025-10-12 | 82 | Tendance soutenue | 1.721 |  |  |
| investissement_courtage | Bolero | KBC | 2025-12-28 | 90 | Pic isolé | 2.45 |  |  |
| investissement_courtage | Bolero | KBC | 2026-06-07 | 87 | Pic isolé | 2.176 |  |  |
| marque_generique | ING | ING | 2021-09-26 | 77 | Pic isolé | 2.698 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-10-17 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-10-31 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-11-28 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-12-12 | 8 | Tendance soutenue | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-12-19 | 8 | Tendance soutenue | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2021-12-26 | 8 | Tendance soutenue | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-01-09 | 9 | Tendance soutenue | 3.084 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-01-16 | 9 | Tendance soutenue | 3.084 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-01-30 | 9 | Pic isolé | 3.084 |  |  |
| marque_generique | ING | ING | 2022-01-30 | 78 | Pic isolé | 2.816 |  |  |
| marque_generique | ING | ING | 2022-02-27 | 75 | Pic isolé | 2.462 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-04-03 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-05-01 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | ING | ING | 2022-05-01 | 69 | Pic isolé | 1.754 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-06-12 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2022-06-26 | 8 | Pic isolé | 2.008 |  |  |
| marque_generique | KBC | KBC | 2022-06-26 | 82 | Tendance soutenue | 2.085 |  |  |
| marque_generique | ING | ING | 2022-07-03 | 69 | Pic isolé | 1.754 |  |  |
| marque_generique | KBC | KBC | 2022-07-03 | 81 | Tendance soutenue | 1.972 |  |  |
| marque_generique | KBC | KBC | 2023-08-20 | 83 | Tendance soutenue | 2.198 |  |  |
| marque_generique | ING | ING | 2023-08-27 | 71 | Pic isolé | 1.99 |  |  |
| marque_generique | KBC | KBC | 2023-08-27 | 90 | Tendance soutenue | 2.989 |  |  |
| marque_generique | ING | ING | 2024-03-24 | 90 | Pic isolé | 4.233 |  |  |
| marque_generique | ING | ING | 2024-08-25 | 73 | Tendance soutenue | 2.226 |  |  |
| marque_generique | CBC Banque & Assurance | CBC | 2024-09-01 | 9 | Pic isolé | 3.084 |  |  |
| marque_generique | ING | ING | 2024-09-01 | 82 | Tendance soutenue | 3.288 |  |  |
| marque_generique | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.12 |  |  |
| marque_generique_neobanques | ING | ING | 2021-09-26 | 76 | Pic isolé | 2.67 | 1.000 |  |
| marque_generique_neobanques | ING | ING | 2022-02-27 | 76 | Pic isolé | 2.67 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2022-02-27 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | N26 | N26 | 2022-04-24 | 5 | Pic isolé | 9.316 | 0.828 |  |
| marque_generique_neobanques | ING | ING | 2022-05-01 | 73 | Pic isolé | 2.306 | 1.000 |  |
| marque_generique_neobanques | KBC | KBC | 2022-06-26 | 78 | Tendance soutenue | 1.732 | 1.000 |  |
| marque_generique_neobanques | ING | ING | 2022-07-03 | 68 | Pic isolé | 1.7 | 1.000 |  |
| marque_generique_neobanques | KBC | KBC | 2022-07-03 | 83 | Tendance soutenue | 2.317 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2023-04-02 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | KBC | KBC | 2023-08-20 | 86 | Tendance soutenue | 2.667 | 1.000 |  |
| marque_generique_neobanques | ING | ING | 2023-08-27 | 69 | Pic isolé | 1.821 | 1.000 |  |
| marque_generique_neobanques | KBC | KBC | 2023-08-27 | 94 | Tendance soutenue | 3.603 | 1.000 |  |
| marque_generique_neobanques | ING | ING | 2024-03-24 | 87 | Pic isolé | 4.002 | 1.000 |  |
| marque_generique_neobanques | ING | ING | 2024-08-25 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| marque_generique_neobanques | ING | ING | 2024-09-01 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| marque_generique_neobanques | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.304 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2024-12-15 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | bunq | 2025-03-16 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | bunq | bunq | 2025-05-25 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-08-17 | 12 | Tendance soutenue | 2.742 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-08-24 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2025-09-14 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-11-02 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-11-23 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2025-11-23 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-11-30 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-12-14 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2025-12-28 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-01-11 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-01-18 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2026-02-15 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-03-15 | 10 | Tendance soutenue | 1.976 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-03-22 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-04-05 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-04-12 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-04-19 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-03 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-10 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-17 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-05-31 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-06-07 | 10 | Tendance soutenue | 1.976 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-07-05 | 9 | Pic isolé | 1.593 | 1.000 |  |
| marque_generique_neobanques | bunq | bunq | 2026-07-26 | 1 | Pic isolé | 5.302 | 0.038 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-02 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-09 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-16 | 10 | Tendance soutenue | 1.976 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-08-30 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-09-06 | 9 | Tendance soutenue | 1.593 | 1.000 |  |
| marque_generique_neobanques | Revolut | Revolut | 2026-09-13 | 19 | Tendance soutenue | 5.424 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2021-09-26 | 76 | Pic isolé | 2.67 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2021-12-12 | 72 | Pic isolé | 2.82 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2021-12-26 | 66 | Tendance soutenue | 2.175 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-01-02 | 70 | Tendance soutenue | 2.605 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-01-30 | 69 | Pic isolé | 2.497 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-02-27 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2022-02-27 | 76 | Pic isolé | 2.67 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-06 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-20 | 61 | Tendance soutenue | 1.637 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-03-27 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-04-03 | 64 | Tendance soutenue | 1.96 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-04-24 | 73 | Tendance soutenue | 2.927 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-05-01 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2022-05-01 | 73 | Pic isolé | 2.306 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-05-29 | 60 | Tendance soutenue | 1.53 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-05 | 60 | Tendance soutenue | 1.53 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-12 | 61 | Tendance soutenue | 1.637 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-19 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-06-26 | 68 | Tendance soutenue | 2.39 | 1.000 |  |
| marque_generique_traditionnelles | KBC | KBC | 2022-06-26 | 78 | Tendance soutenue | 1.732 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-03 | 69 | Tendance soutenue | 2.497 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2022-07-03 | 68 | Pic isolé | 1.7 | 1.000 |  |
| marque_generique_traditionnelles | KBC | KBC | 2022-07-03 | 83 | Tendance soutenue | 2.317 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-10 | 61 | Tendance soutenue | 1.637 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-07-31 | 69 | Tendance soutenue | 2.497 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-07 | 66 | Tendance soutenue | 2.175 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-21 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-08-28 | 64 | Tendance soutenue | 1.96 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-04 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-11 | 62 | Tendance soutenue | 1.745 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-18 | 65 | Tendance soutenue | 2.067 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2022-09-25 | 63 | Tendance soutenue | 1.852 | 1.000 |  |
| marque_generique_traditionnelles | Argenta | Argenta | 2023-08-20 | 62 | Tendance soutenue | 9.206 | 1.000 |  |
| marque_generique_traditionnelles | KBC | KBC | 2023-08-20 | 86 | Tendance soutenue | 2.667 | 1.000 |  |
| marque_generique_traditionnelles | Argenta | Argenta | 2023-08-27 | 52 | Tendance soutenue | 6.556 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2023-08-27 | 69 | Pic isolé | 1.821 | 1.000 |  |
| marque_generique_traditionnelles | KBC | KBC | 2023-08-27 | 94 | Tendance soutenue | 3.603 | 1.000 |  |
| marque_generique_traditionnelles | BNP Paribas Fortis | BNP Paribas Fortis | 2024-01-21 | 81 | Pic isolé | 3.787 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2024-03-24 | 87 | Pic isolé | 4.002 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-09 | 50 | Tendance soutenue | 4.965 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-16 | 38 | Tendance soutenue | 2.912 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-23 | 34 | Tendance soutenue | 2.228 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-06-30 | 34 | Tendance soutenue | 2.228 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-07-07 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-07-14 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2024-08-25 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| marque_generique_traditionnelles | Argenta | Argenta | 2024-09-01 | 45 | Pic isolé | 4.7 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-09-01 | 38 | Tendance soutenue | 2.912 | 1.000 |  |
| marque_generique_traditionnelles | ING | ING | 2024-09-01 | 74 | Tendance soutenue | 2.427 | 1.000 |  |
| marque_generique_traditionnelles | KBC | KBC | 2024-09-01 | 100 | Pic isolé | 4.304 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-09-08 | 33 | Tendance soutenue | 2.057 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-09-29 | 30 | Pic isolé | 1.544 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-12-15 | 32 | Pic isolé | 1.886 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2024-12-29 | 30 | Pic isolé | 1.544 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-03-23 | 31 | Tendance soutenue | 1.715 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-03-30 | 33 | Tendance soutenue | 2.057 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-06-29 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| marque_generique_traditionnelles | Crelan | Crelan | 2025-07-06 | 32 | Tendance soutenue | 1.886 | 1.000 |  |
| pret_hypothecaire | prêt hypothécaire ING | ING | 2021-12-05 | 71 | Pic isolé | 9.541 |  |  |
| pret_hypothecaire | KBC hypothecair krediet | KBC | 2021-12-12 | 100 | Pic isolé | 11.541 |  |  |
| pret_hypothecaire | KBC hypothecair krediet | KBC | 2023-11-12 | 71 | Pic isolé | 8.164 |  |  |
| pret_hypothecaire | KBC hypothecair krediet | KBC | 2024-09-01 | 67 | Pic isolé | 7.698 |  |  |
| pret_hypothecaire | prêt hypothécaire ING | ING | 2025-05-25 | 75 | Pic isolé | 10.085 |  |  |
| pret_hypothecaire | ING hypothecair krediet | ING | 2025-12-14 | 69 | Pic isolé | 9.396 |  |  |
| pret_hypothecaire | prêt hypothécaire ING | ING | 2026-01-25 | 60 | Pic isolé | 8.046 |  |  |
| pret_hypothecaire | ING hypothecair krediet | ING | 2026-04-19 | 96 | Pic isolé | 13.106 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire ING | ING | 2021-12-05 | 61 | Pic isolé | 9.546 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire CBC | CBC | 2024-04-14 | 100 | Pic isolé | 13.906 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire CBC | CBC | 2024-08-25 | 59 | Pic isolé | 8.17 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire ING | ING | 2025-05-25 | 64 | Pic isolé | 10.022 |  |  |
| pret_hypothecaire_cbc | ING hypothecair krediet | ING | 2025-12-14 | 59 | Pic isolé | 9.327 |  |  |
| pret_hypothecaire_cbc | prêt hypothécaire ING | ING | 2026-01-25 | 52 | Pic isolé | 8.121 |  |  |
| pret_hypothecaire_cbc | ING hypothecair krediet | ING | 2026-04-19 | 83 | Pic isolé | 13.156 |  |  |
