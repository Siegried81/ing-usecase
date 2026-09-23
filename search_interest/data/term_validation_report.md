# Rapport de validation des termes — extension six banques

Genere par collectors/term_resolver.py. Ne modifie jamais config.PRODUCTS - sert de base a la revue humaine avant mise a jour manuelle (phase 2).

## Convention de langue neutre

Aucune convention neutre existante n'a ete trouvee (les termes CBC/app_mobile existants sont tous étiquetés `en` par defaut). Valeur retenue pour les nouveaux termes neutres (topics de marque, noms d'application) : `multi`.

## Marques (phase 1A)

| Banque | Rang | Terme | Type | Titre topic | Type topic | Couverture | Moyenne | Verdict |
|---|---|---|---|---|---|---|---|---|
| ARGENTA | 1 | /m/03lmky | topic | Argenta | Banque | 1.000 | 44.46 | info_only |
| ARGENTA | 2 | /m/04ry8n | topic | Banco Bilbao Vizcaya Argentaria | Banque | 0.498 | 0.50 | info_only |
| ARGENTA | 3 | /g/1tgn_zf3 | topic | Argenta Lede | Banque à Lede, Belgique | 0.000 | 0.00 | info_only |
| ARGENTA | 4 | /g/11bzvzx7yc | topic | Argenta Bank en Verzekering | Banque à Renaix, Belgique | 0.000 | 0.00 | info_only |
| ARGENTA | 5 | Argenta | string |  |  | 1.000 | 43.48 | info_only |
| ARGENTA | 1 | /m/03lmky | topic | Argenta | Banque | 1.000 | 44.46 | selected |
| BNPPF | 1 | /m/07sc3dj | topic | BNP Paribas Fortis | Banque | 1.000 | 56.70 | info_only |
| BNPPF | 2 | /g/1tcvh6w3 | topic | BNP Paribas Fortis | Banque à Waremme, Belgique | 0.000 | 0.00 | info_only |
| BNPPF | 3 | /g/1tdq08j9 | topic | BNP Paribas Fortis | Banque à Hasselt, Belgique | 0.000 | 0.00 | info_only |
| BNPPF | 4 | /g/1tyktjdz | topic | BNP Paribas Fortis | Banque à Ans, Belgique | 0.000 | 0.00 | info_only |
| BNPPF | 5 | BNP Paribas Fortis | string |  |  | 1.000 | 20.91 | info_only |
| BNPPF | 1 | /m/07sc3dj | topic | BNP Paribas Fortis | Banque | 1.000 | 56.70 | selected |
| BUNQ | 1 | bunq | string |  |  | 0.713 | 39.38 | info_only |
| BUNQ | 1 | bunq | string |  |  | 0.713 | 39.38 | selected |
| CRELAN | 1 | /m/0h4w6d | topic | Crelan | Banque | 1.000 | 37.67 | info_only |
| CRELAN | 2 | Crelan | string |  |  | 1.000 | 38.15 | info_only |
| CRELAN | 2 | Crelan | string |  |  | 1.000 | 38.15 | selected |
| ING | 1 | /m/01hlqz | topic | Groupe ING | Compagnie | 1.000 | 58.09 | info_only |
| ING | 2 | ING | string |  |  | 1.000 | 59.32 | info_only |
| KBC | 1 | /m/0g4dpgt | topic | KBC Group N.V. | Groupe financier | 0.808 | 16.46 | info_only |
| KBC | 2 | /m/06t05x | topic | KBC Bank | Banque | 1.000 | 40.62 | info_only |
| KBC | 3 | /g/1tfptf4z | topic | KBC | Banque à Gand, Belgique | 0.000 | 0.00 | info_only |
| KBC | 4 | /g/1trttjnw | topic | KBC | Banque à Beerse, Belgique | 0.000 | 0.00 | info_only |
| KBC | 5 | KBC | string |  |  | 1.000 | 63.67 | info_only |
| N26 | 1 | /g/11c1p5t9vb | topic | N26 | Banque | 0.985 | 12.60 | info_only |
| N26 | 2 | /g/11c2prkfpn | topic | N26 Bank AG | Banque à Berlin, Allemagne | 0.011 | 0.07 | info_only |
| N26 | 3 | N26 | string |  |  | 0.989 | 12.41 | info_only |
| N26 | 1 | /g/11c1p5t9vb | topic | N26 | Banque | 0.985 | 12.60 | selected |
| REVOLUT | 1 | /g/11clggwh1c | topic | Revolut | Société de services financiers | 1.000 | 23.47 | info_only |
| REVOLUT | 2 | Revolut | string |  |  | 1.000 | 21.84 | info_only |
| REVOLUT | 2 | Revolut | string |  |  | 1.000 | 21.84 | selected |

## Controle informatif ING / KBC (chaine brute vs topic)

| Banque | Rang | Terme | Type | Titre topic | Type topic | Couverture | Moyenne |
|---|---|---|---|---|---|---|---|
| ING | 1 | /m/01hlqz | topic | Groupe ING | Compagnie | 1.000 | 58.09 |
| ING | 2 | ING | string |  |  | 1.000 | 59.32 |
| KBC | 1 | /m/0g4dpgt | topic | KBC Group N.V. | Groupe financier | 0.808 | 16.46 |
| KBC | 2 | /m/06t05x | topic | KBC Bank | Banque | 1.000 | 40.62 |
| KBC | 3 | /g/1tfptf4z | topic | KBC | Banque à Gand, Belgique | 0.000 | 0.00 |
| KBC | 4 | /g/1trttjnw | topic | KBC | Banque à Beerse, Belgique | 0.000 | 0.00 |
| KBC | 5 | KBC | string |  |  | 1.000 | 63.67 |

## Fiches produit x slots (phase 1B)

| Fiche | Banque | Langue | Terme retenu | Couverture | Moyenne | Verdict | Flags |
|---|---|---|---|---|---|---|---|
| app_mobile_argenta | ARGENTA | multi | Argenta app | 0.877 | 5.00 | selected | asymmetric |
| app_mobile_bnppf | BNPPF | multi | easy banking app | 0.713 | 3.57 | selected | asymmetric |
| app_mobile_bunq | BUNQ | multi | bunq app | 0.000 | 0.00 | dropped |  |
| app_mobile_crelan | CRELAN | multi | Crelan app | 0.345 | 1.91 | selected_low_coverage | asymmetric |
| app_mobile_n26 | N26 | multi | N26 app | 0.008 | 0.03 | dropped |  |
| app_mobile_revolut | REVOLUT | multi | Revolut app | 0.103 | 0.47 | dropped |  |
| assurance_habitation_argenta | ARGENTA | fr | assurance habitation Argenta | 0.004 | 0.38 | dropped |  |
| assurance_habitation_argenta | ARGENTA | nl | Argenta brandverzekering | 0.019 | 0.87 | dropped |  |
| assurance_habitation_bnppf | BNPPF | fr | assurance habitation BNP | 0.008 | 0.34 | dropped |  |
| assurance_habitation_bnppf | BNPPF | nl | BNP woningverzekering | 0.000 | 0.00 | dropped |  |
| assurance_habitation_crelan | CRELAN | fr | assurance habitation Crelan | 0.008 | 0.46 | dropped |  |
| assurance_habitation_crelan | CRELAN | nl | Crelan woningverzekering | 0.004 | 0.38 | dropped |  |
| carte_credit_argenta | ARGENTA | fr | Argenta mastercard | 0.172 | 5.18 | dropped |  |
| carte_credit_argenta | ARGENTA | nl | Argenta kredietkaart | 0.096 | 3.17 | dropped |  |
| carte_credit_bnppf | BNPPF | fr | BNP visa | 0.743 | 32.84 | selected | broad_fallback,asymmetric |
| carte_credit_bnppf | BNPPF | nl | BNP kredietkaart | 0.004 | 0.01 | dropped |  |
| carte_credit_bunq | BUNQ | fr | carte de crédit bunq | 0.000 | 0.00 | dropped |  |
| carte_credit_bunq | BUNQ | nl | bunq kredietkaart | 0.004 | 0.11 | dropped |  |
| carte_credit_crelan | CRELAN | fr | Crelan visa | 0.318 | 11.84 | selected_low_coverage | broad_fallback,asymmetric |
| carte_credit_crelan | CRELAN | nl | Crelan kredietkaart | 0.008 | 0.23 | dropped |  |
| compte_a_vue_argenta | ARGENTA | fr | compte Argenta | 0.253 | 7.01 | selected_low_coverage | broad_fallback,asymmetric |
| compte_a_vue_argenta | ARGENTA | nl | Argenta rekening | 0.736 | 22.17 | selected | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNPPF | fr | compte BNP | 1.000 | 37.14 | selected | broad_fallback,asymmetric |
| compte_a_vue_bnppf | BNPPF | nl | BNP rekening | 0.268 | 11.66 | selected_low_coverage | broad_fallback,asymmetric |
| compte_a_vue_bunq | BUNQ | fr | compte bunq | 0.008 | 0.21 | dropped |  |
| compte_a_vue_bunq | BUNQ | nl | bunq rekening | 0.008 | 0.48 | dropped |  |
| compte_a_vue_crelan | CRELAN | fr | compte Crelan | 0.230 | 10.39 | dropped |  |
| compte_a_vue_crelan | CRELAN | nl | Crelan rekening | 0.084 | 4.49 | dropped |  |
| compte_a_vue_n26 | N26 | fr | compte N26 | 0.034 | 1.41 | dropped |  |
| compte_a_vue_n26 | N26 | nl | N26 zichtrekening | 0.004 | 0.21 | dropped |  |
| compte_a_vue_revolut | REVOLUT | fr | compte Revolut | 0.479 | 23.03 | selected_low_coverage | broad_fallback,asymmetric |
| compte_a_vue_revolut | REVOLUT | nl | Revolut rekening | 0.057 | 1.82 | dropped |  |
| compte_epargne_argenta | ARGENTA | fr | compte épargne Argenta | 0.019 | 0.14 | dropped |  |
| compte_epargne_argenta | ARGENTA | nl | Argenta spaarrekening | 0.575 | 8.97 | selected |  |
| compte_epargne_bnppf | BNPPF | fr | épargne BNP | 0.054 | 1.58 | dropped |  |
| compte_epargne_bnppf | BNPPF | nl | BNP spaarrekening | 0.249 | 8.93 | dropped |  |
| compte_epargne_bunq | BUNQ | fr | compte épargne bunq | 0.004 | 0.12 | dropped |  |
| compte_epargne_bunq | BUNQ | nl | bunq spaarrekening | 0.011 | 0.11 | dropped |  |
| compte_epargne_crelan | CRELAN | fr | épargne Crelan | 0.011 | 0.10 | dropped |  |
| compte_epargne_crelan | CRELAN | nl | Crelan spaarrekening | 0.077 | 2.34 | dropped |  |
| compte_epargne_n26 | N26 | fr | compte épargne N26 | 0.004 | 0.15 | dropped |  |
| compte_epargne_n26 | N26 | nl | N26 sparen | 0.004 | 0.10 | dropped |  |
| compte_epargne_revolut | REVOLUT | fr | compte épargne Revolut | 0.008 | 0.11 | dropped |  |
| compte_epargne_revolut | REVOLUT | nl | Revolut spaarrekening | 0.015 | 0.39 | dropped |  |
| compte_professionnel_argenta | ARGENTA | fr | Argenta indépendant | 0.008 | 0.46 | dropped |  |
| compte_professionnel_argenta | ARGENTA | nl | Argenta zakelijke rekening | 0.008 | 0.29 | dropped |  |
| compte_professionnel_bnppf | BNPPF | fr | compte professionnel BNP | 0.011 | 0.55 | dropped |  |
| compte_professionnel_bnppf | BNPPF | nl | BNP zakelijk | 0.004 | 0.23 | dropped |  |
| compte_professionnel_bunq | BUNQ | en | bunq Business | 0.011 | 1.02 | dropped |  |
| compte_professionnel_bunq | BUNQ | fr | compte pro bunq | 0.008 | 0.53 | dropped |  |
| compte_professionnel_crelan | CRELAN | fr | compte pro Crelan | 0.008 | 0.44 | dropped |  |
| compte_professionnel_crelan | CRELAN | nl | Crelan zelfstandige | 0.004 | 0.02 | dropped |  |
| compte_professionnel_n26 | N26 | en | N26 Business | 0.008 | 0.50 | dropped |  |
| compte_professionnel_n26 | N26 | fr | compte pro N26 | 0.004 | 0.26 | dropped |  |
| compte_professionnel_revolut | REVOLUT | en | Revolut Business | 0.195 | 9.85 | dropped |  |
| compte_professionnel_revolut | REVOLUT | fr | compte pro Revolut | 0.008 | 0.49 | dropped |  |
| epargne_pension_argenta | ARGENTA | fr | Argenta pension | 0.065 | 3.63 | dropped |  |
| epargne_pension_argenta | ARGENTA | nl | Argenta pensioensparen | 0.188 | 10.39 | dropped |  |
| epargne_pension_bnppf | BNPPF | fr | BNP pension | 0.625 | 32.23 | selected | broad_fallback,asymmetric |
| epargne_pension_bnppf | BNPPF | nl | BNP pensioensparen | 0.019 | 1.19 | dropped |  |
| epargne_pension_crelan | CRELAN | fr | Crelan pension | 0.034 | 1.92 | dropped |  |
| epargne_pension_crelan | CRELAN | nl | Crelan pensioen | 0.015 | 1.10 | dropped |  |
| investissement_courtage_argenta | ARGENTA | fr | investir Argenta | 0.004 | 0.28 | dropped |  |
| investissement_courtage_argenta | ARGENTA | nl | Argenta beleggen | 0.050 | 2.66 | dropped |  |
| investissement_courtage_bnppf | BNPPF | fr | investir BNP | 0.011 | 0.59 | dropped |  |
| investissement_courtage_bnppf | BNPPF | nl | BNP beleggen | 0.015 | 0.70 | dropped |  |
| investissement_courtage_bunq | BUNQ | en | bunq stocks | 0.008 | 0.43 | dropped |  |
| investissement_courtage_bunq | BUNQ | fr | investir bunq | 0.004 | 0.21 | dropped |  |
| investissement_courtage_bunq | BUNQ | nl | bunq beleggen | 0.004 | 0.25 | dropped |  |
| investissement_courtage_crelan | CRELAN | fr | investir Crelan | 0.000 | 0.00 | dropped |  |
| investissement_courtage_crelan | CRELAN | nl | Crelan beleggen | 0.015 | 0.63 | dropped |  |
| investissement_courtage_n26 | N26 | en | N26 invest | 0.004 | 0.19 | dropped |  |
| investissement_courtage_n26 | N26 | fr | investir N26 | 0.004 | 0.21 | dropped |  |
| investissement_courtage_n26 | N26 | nl | N26 beleggen | 0.004 | 0.36 | dropped |  |
| investissement_courtage_revolut | REVOLUT | en | Revolut stocks | 0.008 | 0.18 | dropped |  |
| investissement_courtage_revolut | REVOLUT | fr | investir Revolut | 0.015 | 0.45 | dropped |  |
| investissement_courtage_revolut | REVOLUT | nl | Revolut beleggen | 0.011 | 0.43 | dropped |  |
| pret_hypothecaire_argenta | ARGENTA | fr | prêt hypothécaire Argenta | 0.004 | 0.33 | dropped |  |
| pret_hypothecaire_argenta | ARGENTA | nl | Argenta hypotheek | 0.023 | 1.64 | dropped |  |
| pret_hypothecaire_bnppf | BNPPF | fr | crédit hypothécaire BNP | 0.031 | 1.76 | dropped |  |
| pret_hypothecaire_bnppf | BNPPF | nl | BNP woonkrediet | 0.023 | 1.39 | dropped |  |
| pret_hypothecaire_crelan | CRELAN | fr | prêt hypothécaire Crelan | 0.011 | 0.53 | dropped |  |
| pret_hypothecaire_crelan | CRELAN | nl | Crelan hypotheek | 0.011 | 0.64 | dropped |  |

## Fiches et slots supprimes

Fiches entierement supprimees (tous les slots sous le seuil plancher) :

- `compte_professionnel_bnppf`
- `compte_epargne_bnppf`
- `investissement_courtage_bnppf`
- `assurance_habitation_bnppf`
- `pret_hypothecaire_bnppf`
- `compte_professionnel_argenta`
- `investissement_courtage_argenta`
- `carte_credit_argenta`
- `epargne_pension_argenta`
- `assurance_habitation_argenta`
- `pret_hypothecaire_argenta`
- `compte_professionnel_crelan`
- `compte_a_vue_crelan`
- `compte_epargne_crelan`
- `investissement_courtage_crelan`
- `epargne_pension_crelan`
- `assurance_habitation_crelan`
- `pret_hypothecaire_crelan`
- `compte_professionnel_revolut`
- `compte_epargne_revolut`
- `investissement_courtage_revolut`
- `app_mobile_revolut`
- `compte_professionnel_n26`
- `compte_a_vue_n26`
- `compte_epargne_n26`
- `investissement_courtage_n26`
- `app_mobile_n26`
- `compte_professionnel_bunq`
- `compte_a_vue_bunq`
- `compte_epargne_bunq`
- `investissement_courtage_bunq`
- `app_mobile_bunq`
- `carte_credit_bunq`

Slots individuels supprimes (fiche conservee avec les autres slots) :

- `carte_credit_bnppf` / slot `nl`
- `epargne_pension_bnppf` / slot `nl`
- `compte_epargne_argenta` / slot `fr`
- `carte_credit_crelan` / slot `nl`
- `compte_a_vue_revolut` / slot `nl`

## Fiches marque et contexte (section 4.3, appels de controle)

| Fiche | Banque | Langue | Terme | Couverture | Moyenne |
|---|---|---|---|---|---|
| contexte_fusion_crelan_axa | CRELAN | en | AXA Bank | 0.701 | 1.39 |
| contexte_fusion_crelan_axa | ING | en | ING | 1.000 | 62.33 |
| contexte_fusion_crelan_axa | CRELAN | fr | AXA Banque | 0.625 | 0.79 |
| contexte_fusion_crelan_axa | CRELAN | multi | Crelan | 1.000 | 24.18 |
| contexte_integration_bnppf_bpost | BNPPF | en | bpost bank | 0.563 | 1.10 |
| contexte_integration_bnppf_bpost | ING | en | ING | 1.000 | 62.33 |
| contexte_integration_bnppf_bpost | BNPPF | fr | bpost banque | 0.590 | 1.64 |
| contexte_integration_bnppf_bpost | BNPPF | multi | /m/07sc3dj | 1.000 | 52.85 |
| marque_generique_neobanques | ING | en | ING | 1.000 | 54.36 |
| marque_generique_neobanques | KBC | en | KBC | 1.000 | 63.66 |
| marque_generique_neobanques | BUNQ | multi | bunq | 0.038 | 0.04 |
| marque_generique_neobanques | N26 | multi | /g/11c1p5t9vb | 0.828 | 0.84 |
| marque_generique_neobanques | REVOLUT | multi | Revolut | 1.000 | 4.81 |
| marque_generique_traditionnelles | ING | en | ING | 1.000 | 54.36 |
| marque_generique_traditionnelles | KBC | en | KBC | 1.000 | 63.66 |
| marque_generique_traditionnelles | ARGENTA | multi | /m/03lmky | 1.000 | 27.40 |
| marque_generique_traditionnelles | BNPPF | multi | /m/07sc3dj | 1.000 | 46.10 |
| marque_generique_traditionnelles | CRELAN | multi | Crelan | 1.000 | 21.11 |

## Duree observee

- Phase 1A (marques) : 0.0 min
- Phase 1B (fiches produit) : 76.5 min
- Fiches marque/contexte : 4.1 min
- Total : 80.5 min

## Nombre de fiches produit resolues (non supprimees) : 10
