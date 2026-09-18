"""Campaign catalog - source of truth, mirrors config.PRODUCTS as the seed
data for load_campaigns.py.

Belgian press research plus information supplied directly by the user.
None of the source material included a `language`, `agency`, `channels` or
`source_url` value per campaign, so:
- `language` is inferred from known brand/market conventions (KBC = Flemish
  brand hence NL; "KBC Brussels" sub-brand = bilingual Brussels hence FR+NL;
  CBC = Walloon brand hence FR; ING = national operator hence FR+NL) unless
  the campaign's own name is unambiguous in one language. These are
  reasonable defaults, not confirmed values - flagged here for review.
- `agency`, `channels`, `source_url` are left null; no data was supplied.

`start_date` / `end_date` are stored at the precision actually known from
the source (YYYY, YYYY-MM, YYYY-Qn or YYYY-MM-DD) rather than padded to a
fake full date - see date_utils.parse_precision_window for how this is
turned into a match window.

`target_fiches` lists product_id values from config.PRODUCTS, or None. Per
the brief, target_fiches is normally empty for brand/sponsoring/csr
campaigns (their reach is judged on marque_generique only). "Level up your
banking" is a deliberate exception: it is type='brand' but the source gives
explicit target fiches (a repositioning that concretely touches specific
everyday-banking products), so campaigns/scoring.py selects fiches based on
whether target_fiches is populated, not on campaign_type.
"""

CAMPAIGNS = [
    # --- KBC ---
    # "Lancement de Kate (assistante digitale)" (2021-05-05) removed: entirely
    # before the Trends data window (2021-09-12), never scorable, dropped
    # rather than kept as permanent dead weight in the catalog.
    {
        "bank": "KBC",
        "name": "KBC Brussels - campagne Kate locale",
        "language": "FR+NL",
        "start_date": "2021-08-25",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "brand",
        "target_fiches": None,
        "notes": "A la limite/hors fenetre Trends egalement.",
    },
    {
        "bank": "KBC",
        "name": "Kate Coin (premiere monnaie digitale)",
        "language": "NL",
        "start_date": "2022-06-16",
        "end_date": None,
        "date_confidence": "exact",
        "campaign_type": "product",
        "target_fiches": ["app_mobile", "app_mobile_cbc"],
        "notes": (
            "Rapprochement deja valide manuellement : pics sur CBC Mobile (19/06), "
            "KBC Touch (26/06-10/07), marque KBC (26/06, 03/07)."
        ),
    },
    {
        "bank": "KBC",
        "name": "KBC Brussels - repositionnement \"Plan B\"",
        "language": "FR+NL",
        "start_date": "2022-07",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "brand",
        "target_fiches": None,
        "notes": "Date precise incertaine.",
    },
    {
        "bank": "KBC",
        "name": "\"Vivre plus durablement\" (developpement durable)",
        "language": "FR+NL",
        "start_date": "2023-03",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "brand",
        "target_fiches": None,
        "notes": None,
    },
    {
        "bank": "KBC",
        "name": "KBC Brussels - \"Bruxelles bat au rythme de vos projets\" (lancement plateforme)",
        "language": "FR+NL",
        "start_date": "2024-08",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "brand",
        "target_fiches": None,
        "notes": None,
    },
    {
        "bank": "KBC",
        "name": "KBC Brussels - activation renovation (tram, un an apres le lancement ci-dessus)",
        "language": "FR+NL",
        "start_date": "2025-08-27",
        "end_date": None,
        "date_confidence": "exact",
        "campaign_type": "product",
        "target_fiches": ["assurance_habitation"],
        "notes": "Rapprochement deja repere : pic \"KBC brandverzekering\" le 31/08/2025.",
    },
    {
        "bank": "KBC",
        "name": "KBC Commercial Banking - \"Ondernemen zonder grenzen\"",
        "language": "NL",
        "start_date": "2025-Q4",
        "end_date": None,
        "date_confidence": "month_only",
        "campaign_type": "product",
        "target_fiches": ["compte_professionnel"],
        "notes": "Date precise inconnue, probablement nov-dec 2025.",
    },
    {
        "bank": "KBC",
        "name": "Kate Coins - unification du systeme (\"Je kan meer met Kate Coins\")",
        "language": "NL",
        "start_date": "2025-10-16",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "product",
        "target_fiches": ["app_mobile"],
        "notes": "Date deduite de metadonnees, pas d'un texte explicite - a verifier si possible.",
    },
    {
        "bank": "KBC",
        "name": "\"De Warmste Week\" (campagne solidaire)",
        "language": "NL",
        "start_date": "2025-12-09",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "csr",
        "target_fiches": None,
        "notes": None,
    },
    {
        "bank": "KBC",
        "name": "\"No stress. Kate it.\"",
        "language": "NL",
        "start_date": "2026-05-21",
        "end_date": None,
        "date_confidence": "exact",
        "campaign_type": "product",
        "target_fiches": ["app_mobile"],
        "notes": None,
    },

    # --- CBC ---
    # "Plan d'Expansion 2.0" (2020-02) removed: entirely before the Trends
    # data window, never scorable.
    {
        "bank": "CBC",
        "name": "Plan \"Impact27\"",
        "language": "FR",
        "start_date": "2025-02",
        "end_date": None,
        "date_confidence": "month_only",
        "campaign_type": "brand",
        "target_fiches": None,
        "notes": "\"Debut 2025\" dans la source.",
    },
    # "CBC Assurances se mobilise pour vous" (start_date "2025", year only)
    # removed: too imprecise to window, never scorable.
    {
        "bank": "CBC",
        "name": "\"La banque des Wallons ambitieux\"",
        "language": "FR",
        "start_date": "2025-09",
        "end_date": None,
        "date_confidence": "month_only",
        "campaign_type": "brand",
        "target_fiches": None,
        "notes": (
            "Pourrait etre une page de contenu evergreen plutot qu'une campagne media "
            "datee - a verifier, exclure du scoring si c'est le cas."
        ),
    },

    # --- ING ---
    {
        "bank": "ING",
        "name": "Campagne \"pouce\" (app ING Banking)",
        "language": "FR+NL",
        "start_date": "2022-04",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "product",
        "target_fiches": ["app_mobile", "app_mobile_cbc"],
        "notes": None,
    },
    {
        "bank": "ING",
        "name": "Renouvellement partenariat URBSFA (Diables Rouges/Red Flames, jusqu'en 2028)",
        "language": "FR+NL",
        "start_date": "2022-09",
        "end_date": None,
        "date_confidence": "month_only",
        "campaign_type": "sponsoring",
        "target_fiches": None,
        "notes": None,
    },
    {
        "bank": "ING",
        "name": "Digitalisation des Diables Rouges",
        "language": "FR+NL",
        "start_date": "2023-01",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "sponsoring",
        "target_fiches": None,
        "notes": None,
    },
    {
        "bank": "ING",
        "name": "Publicite produit d'investissement \"jusqu'a 15% de rendement\" (controverse Test-Achats)",
        "language": "FR+NL",
        "start_date": "2025-06",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "product",
        "target_fiches": ["investissement_courtage"],
        "notes": "Fenetre floue, possiblement en cours depuis plusieurs mois avant sa mediatisation le 30/09/2025.",
    },
    {
        "bank": "ING",
        "name": "\"Lancez-vous comme un lion\"",
        "language": "FR+NL",
        "start_date": "2026-01-13",
        "end_date": "2026-02-28",
        "date_confidence": "exact",
        "campaign_type": "product",
        "target_fiches": ["compte_professionnel"],
        "notes": None,
    },
    {
        "bank": "ING",
        "name": "\"Her Goal, Your Club\" (Coupe du Monde)",
        "language": "FR+NL",
        "start_date": "2026-06",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "sponsoring",
        "target_fiches": None,
        "notes": "Date de bilan connue (13/07/2026) mais campagne reellement active pendant le Mondial, donc plutot juin 2026.",
    },
    {
        "bank": "ING",
        "name": "\"Need it? Lease it!\"",
        "language": "FR+NL",
        "start_date": "2026-08-19",
        "end_date": None,
        "date_confidence": "approximate",
        "campaign_type": "product",
        "target_fiches": ["compte_professionnel"],
        "notes": (
            "Incoherence de date entre sources : 19/08 (presse pub) vs 27/08 "
            "(newsroom ING) - documentee, non tranchee arbitrairement."
        ),
    },
    {
        "bank": "ING",
        "name": "Remboursement frais BCE pour entrepreneurs",
        "language": "FR+NL",
        "start_date": "2026-09-04",
        "end_date": None,
        "date_confidence": "exact",
        "campaign_type": "product",
        "target_fiches": ["compte_professionnel"],
        "notes": None,
    },
    {
        "bank": "ING",
        "name": (
            "\"Level up your banking\" (repositionnement international, 8 pays, "
            "nouveaux forfaits ING Go/More/Extra/Max)"
        ),
        "language": "FR+NL",
        "start_date": "2026-09-05",
        "end_date": None,
        "date_confidence": "exact",
        "campaign_type": "brand",
        "target_fiches": [
            "compte_a_vue", "compte_a_vue_cbc",
            "compte_epargne", "compte_epargne_cbc",
            "assurance_habitation", "assurance_habitation_cbc",
            "compte_professionnel", "compte_professionnel_cbc",
        ],
        "notes": (
            "Rapprochement deja repere et tres net : tendances soutenues sur plusieurs "
            "fiches ING du 30/08 au 13/09/2026. Cible tous les produits du quotidien, "
            "d'ou le mapping large."
        ),
    },
]
