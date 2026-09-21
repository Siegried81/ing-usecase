# Fiches campagnes — rapprochement avec les anomalies Trends

Une section par campagne cataloguée (KBC, CBC, ING) : métadonnées, anomalies Trends rapprochées dans la fenêtre d'attribution, et score d'efficacité détaillé. Voir `campaigns_comparison.md` pour la synthèse agrégée KBC vs CBC vs ING.

**Fenêtre d'attribution** : `[start_date, start_date + 21 jours]` (étendue à `end_date + 21 jours` si connue). **Fiches interrogées** : `target_fiches` + `marque_generique` de la banque, ou `marque_generique` seul pour les campagnes `brand`/`sponsoring`/`csr` sans `target_fiches`. **Score** : `Σ (poids_type × min(score_deviation, 10))` par anomalie rapprochée (poids 2 pour tendance soutenue, 1 pour pic isolé), avec un facteur ×0.3 sur les anomalies possiblement dues à une confusion saisonnière (motif large observé la même semaine chez une autre banque sans campagne active), une contribution partagée entre campagnes dont les fenêtres se chevauchent sur une même anomalie, puis un bonus de largeur ×(1 + 0.1×(N_fiches-1)).

## KBC

### KBC Brussels - campagne Kate locale

- **Période** : 2021-08-25 (confiance : approximate) — **Type** : Image de marque — **Langue** : FR+NL
- **Notes** : A la limite/hors fenetre Trends egalement.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### Kate Coin (premiere monnaie digitale)

- **Période** : 2022-06-16 (confiance : exact) — **Type** : Produit — **Langue** : NL
- **Fiches ciblées** : app_mobile, app_mobile_cbc
- **Notes** : Rapprochement deja valide manuellement : pics sur CBC Mobile (19/06), KBC Touch (26/06-10/07), marque KBC (26/06, 03/07).

**7 anomalie(s) rapprochée(s)**

| Terme | Banque | Date | Type | Score déviation | Délai | Confusion saisonnière | Campagnes concurrentes | Contribution |
|---|---|---|---|---|---|---|---|---|
| CBC Mobile | CBC | 2022-06-19 | Pic isolé | 3.21 | +3 j | Oui | - | 0.963 |
| KBC Mobile | KBC | 2022-06-26 | Pic isolé | 2.466 | +10 j | Oui | - | 0.74 |
| KBC Touch | KBC | 2022-06-26 | Tendance soutenue | 1.754 | +10 j | Oui | - | 1.052 |
| KBC | KBC | 2022-06-26 | Tendance soutenue | 2.085 | +10 j | Oui | - | 1.251 |
| KBC Touch | KBC | 2022-07-03 | Tendance soutenue | 2.24 | +17 j | Oui | - | 1.344 |
| CBC Mobile | CBC | 2022-07-03 | Pic isolé | 3.21 | +17 j | Oui | - | 0.963 |
| KBC | KBC | 2022-07-03 | Tendance soutenue | 1.972 | +17 j | Oui | 1 | 0.592 |

**Score** : 8.2858 (brut 6.9048 × bonus de largeur 1.2, 3 fiche(s) touchée(s), 7 anomalie(s) sous confusion saisonnière)

### KBC Brussels - repositionnement "Plan B"

- **Période** : 2022-07 (confiance : approximate) — **Type** : Image de marque — **Langue** : FR+NL
- **Notes** : Date precise incertaine.

**1 anomalie(s) rapprochée(s)**

| Terme | Banque | Date | Type | Score déviation | Délai | Confusion saisonnière | Campagnes concurrentes | Contribution |
|---|---|---|---|---|---|---|---|---|
| KBC | KBC | 2022-07-03 | Tendance soutenue | 1.972 | +2 j | Oui | 1 | 0.592 |

**Score** : 0.5916 (brut 0.5916 × bonus de largeur 1.0, 1 fiche(s) touchée(s), 1 anomalie(s) sous confusion saisonnière)

### "Vivre plus durablement" (developpement durable)

- **Période** : 2023-03 (confiance : approximate) — **Type** : Image de marque — **Langue** : FR+NL

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### KBC Brussels - "Bruxelles bat au rythme de vos projets" (lancement plateforme)

- **Période** : 2024-08 (confiance : approximate) — **Type** : Image de marque — **Langue** : FR+NL

**1 anomalie(s) rapprochée(s)**

| Terme | Banque | Date | Type | Score déviation | Délai | Confusion saisonnière | Campagnes concurrentes | Contribution |
|---|---|---|---|---|---|---|---|---|
| KBC | KBC | 2024-09-01 | Pic isolé | 4.12 | +31 j | Oui | - | 1.236 |

**Score** : 1.236 (brut 1.236 × bonus de largeur 1.0, 1 fiche(s) touchée(s), 1 anomalie(s) sous confusion saisonnière)

### KBC Brussels - activation renovation (tram, un an apres le lancement ci-dessus)

- **Période** : 2025-08-27 (confiance : exact) — **Type** : Produit — **Langue** : FR+NL
- **Fiches ciblées** : assurance_habitation
- **Notes** : Rapprochement deja repere : pic "KBC brandverzekering" le 31/08/2025.

**1 anomalie(s) rapprochée(s)**

| Terme | Banque | Date | Type | Score déviation | Délai | Confusion saisonnière | Campagnes concurrentes | Contribution |
|---|---|---|---|---|---|---|---|---|
| KBC brandverzekering | KBC | 2025-08-31 | Pic isolé | 4.15 | +4 j | Non | - | 4.15 |

**Score** : 4.15 (brut 4.15 × bonus de largeur 1.0, 1 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### Kate Coins - unification du systeme ("Je kan meer met Kate Coins")

- **Période** : 2025-10-16 (confiance : approximate) — **Type** : Produit — **Langue** : NL
- **Fiches ciblées** : app_mobile
- **Notes** : Date deduite de metadonnees, pas d'un texte explicite - a verifier si possible.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "De Warmste Week" (campagne solidaire)

- **Période** : 2025-12-09 (confiance : approximate) — **Type** : RSE/solidaire — **Langue** : NL

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### KBC Commercial Banking - "Ondernemen zonder grenzen"

- **Période** : 2025-Q4 (confiance : month_only) — **Type** : Produit — **Langue** : NL
- **Fiches ciblées** : compte_professionnel
- **Notes** : Date precise inconnue, probablement nov-dec 2025.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "No stress. Kate it."

- **Période** : 2026-05-21 (confiance : exact) — **Type** : Produit — **Langue** : NL
- **Fiches ciblées** : app_mobile

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

## CBC

### Plan "Impact27"

- **Période** : 2025-02 (confiance : month_only) — **Type** : Image de marque — **Langue** : FR
- **Notes** : "Debut 2025" dans la source.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "La banque des Wallons ambitieux"

- **Période** : 2025-09 (confiance : month_only) — **Type** : Image de marque — **Langue** : FR
- **Notes** : Pourrait etre une page de contenu evergreen plutot qu'une campagne media datee - a verifier, exclure du scoring si c'est le cas.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

## ING

### Campagne "pouce" (app ING Banking)

- **Période** : 2022-04 (confiance : approximate) — **Type** : Produit — **Langue** : FR+NL
- **Fiches ciblées** : app_mobile, app_mobile_cbc

**1 anomalie(s) rapprochée(s)**

| Terme | Banque | Date | Type | Score déviation | Délai | Confusion saisonnière | Campagnes concurrentes | Contribution |
|---|---|---|---|---|---|---|---|---|
| ING | ING | 2022-05-01 | Pic isolé | 1.754 | +30 j | Oui | - | 0.526 |

**Score** : 0.5262 (brut 0.5262 × bonus de largeur 1.0, 1 fiche(s) touchée(s), 1 anomalie(s) sous confusion saisonnière)

### Renouvellement partenariat URBSFA (Diables Rouges/Red Flames, jusqu'en 2028)

- **Période** : 2022-09 (confiance : month_only) — **Type** : Sponsoring — **Langue** : FR+NL

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### Digitalisation des Diables Rouges

- **Période** : 2023-01 (confiance : approximate) — **Type** : Sponsoring — **Langue** : FR+NL

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### Publicite produit d'investissement "jusqu'a 15% de rendement" (controverse Test-Achats)

- **Période** : 2025-06 (confiance : approximate) — **Type** : Produit — **Langue** : FR+NL
- **Fiches ciblées** : investissement_courtage
- **Notes** : Fenetre floue, possiblement en cours depuis plusieurs mois avant sa mediatisation le 30/09/2025.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "Lancez-vous comme un lion"

- **Période** : 2026-01-13 → 2026-02-28 (confiance : exact) — **Type** : Produit — **Langue** : FR+NL
- **Fiches ciblées** : compte_professionnel

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "Her Goal, Your Club" (Coupe du Monde)

- **Période** : 2026-06 (confiance : approximate) — **Type** : Sponsoring — **Langue** : FR+NL
- **Notes** : Date de bilan connue (13/07/2026) mais campagne reellement active pendant le Mondial, donc plutot juin 2026.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "Need it? Lease it!"

- **Période** : 2026-08-19 (confiance : approximate) — **Type** : Produit — **Langue** : FR+NL
- **Fiches ciblées** : compte_professionnel
- **Notes** : Incoherence de date entre sources : 19/08 (presse pub) vs 27/08 (newsroom ING) - documentee, non tranchee arbitrairement.

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### Remboursement frais BCE pour entrepreneurs

- **Période** : 2026-09-04 (confiance : exact) — **Type** : Produit — **Langue** : FR+NL
- **Fiches ciblées** : compte_professionnel

Aucune anomalie rapprochée dans la fenêtre d'attribution.

**Score** : 0.0 (brut 0.0 × bonus de largeur 1.0, 0 fiche(s) touchée(s), 0 anomalie(s) sous confusion saisonnière)

### "Level up your banking" (repositionnement international, 8 pays, nouveaux forfaits ING Go/More/Extra/Max)

- **Période** : 2026-09-05 (confiance : exact) — **Type** : Image de marque — **Langue** : FR+NL
- **Fiches ciblées** : compte_a_vue, compte_a_vue_cbc, compte_epargne, compte_epargne_cbc, assurance_habitation, assurance_habitation_cbc, compte_professionnel, compte_professionnel_cbc
- **Notes** : Rapprochement deja repere et tres net : tendances soutenues sur plusieurs fiches ING du 30/08 au 13/09/2026. Cible tous les produits du quotidien, d'ou le mapping large.

**11 anomalie(s) rapprochée(s)**

| Terme | Banque | Date | Type | Score déviation | Délai | Confusion saisonnière | Campagnes concurrentes | Contribution |
|---|---|---|---|---|---|---|---|---|
| assurance habitation ING | ING | 2026-09-06 | Tendance soutenue | 14.444 | +1 j | Oui | - | 6.0 |
| assurance habitation ING | ING | 2026-09-06 | Tendance soutenue | 11.402 | +1 j | Oui | - | 6.0 |
| ING zichtrekening | ING | 2026-09-06 | Pic isolé | 1.63 | +1 j | Oui | - | 0.489 |
| compte à vue ING | ING | 2026-09-06 | Tendance soutenue | 2.05 | +1 j | Oui | - | 1.23 |
| ING zichtrekening | ING | 2026-09-06 | Tendance soutenue | 1.596 | +1 j | Oui | - | 0.958 |
| compte à vue ING | ING | 2026-09-06 | Tendance soutenue | 1.568 | +1 j | Oui | - | 0.941 |
| compte épargne ING | ING | 2026-09-06 | Tendance soutenue | 2.633 | +1 j | Oui | - | 1.58 |
| compte épargne ING | ING | 2026-09-06 | Tendance soutenue | 2.491 | +1 j | Oui | - | 1.495 |
| ING zichtrekening | ING | 2026-09-13 | Tendance soutenue | 2.186 | +8 j | Non | - | 4.372 |
| compte épargne ING | ING | 2026-09-13 | Tendance soutenue | 2.633 | +8 j | Non | - | 5.266 |
| compte épargne ING | ING | 2026-09-13 | Tendance soutenue | 3.806 | +8 j | Non | - | 7.612 |

**Score** : 53.9127 (brut 35.9418 × bonus de largeur 1.5, 6 fiche(s) touchée(s), 8 anomalie(s) sous confusion saisonnière)
