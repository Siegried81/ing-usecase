"""Banking Campaigns Comparator - analysis toolkit.

The feature dictionary (config/feature_dictionary.yaml) is the source of truth.
Everything in this package is derived from it so that the schema, the validator
and the documentation cannot drift apart.
"""

from comparator.dictionary import Feature, FeatureDictionary, load_dictionary

__all__ = ["Feature", "FeatureDictionary", "load_dictionary"]
__version__ = "0.1.0"
