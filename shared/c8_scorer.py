"""Linear scorer: value of a move = sum of weight * feature for the current mode."""
from .c7_features import FEATURE_NAMES


def mode_weights(params, mode):
    """{feature: weight} of one mode, read from the params."""
    weights = {}
    for name in FEATURE_NAMES[mode]:
        key = mode + '_' + name
        weights[name] = params[key]
    return weights


def linear_score(features, weights):
    """Sum of weight * feature; a weighted feature missing from features counts as 0."""
    total = 0.0
    for name, weight in weights.items():
        value = features.get(name, 0.0)
        total += weight * value
    return total
