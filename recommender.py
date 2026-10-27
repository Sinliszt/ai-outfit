from itertools import product
from collections import Counter

# Scores are design heuristics. Fashion is subjective, so treat these as editable defaults.
OCCASION_FORMALITY = {
    "Casual": 1.5,
    "School": 2.5,
    "Party": 3.0,
    "Dinner": 3.5,
    "Formal event": 4.8,
}

NEUTRALS = {"black", "white", "grey", "beige", "cream", "brown", "navy"}
COLOUR_FAMILIES = {
    "blue": {"blue", "light blue", "navy", "denim blue"},
    "green": {"green", "olive"},
    "red": {"red", "pink"},
    "purple": {"purple", "pink"},
    "earth": {"beige", "cream", "brown", "olive"},
}
STYLE_COMPATIBILITY = {
    "Minimalist": {"Minimalist", "Smart casual", "Formal", "Casual", "Preppy"},
    "Casual": {"Casual", "Sporty", "Streetwear", "Minimalist", "Vintage"},
    "Streetwear": {"Streetwear", "Casual", "Sporty"},
    "Smart casual": {"Smart casual", "Minimalist", "Formal", "Preppy", "Casual"},
    "Formal": {"Formal", "Smart casual", "Minimalist", "Preppy"},
    "Vintage": {"Vintage", "Bohemian", "Casual", "Minimalist"},
    "Sporty": {"Sporty", "Casual", "Streetwear"},
    "Preppy": {"Preppy", "Smart casual", "Formal", "Minimalist"},
    "Bohemian": {"Bohemian", "Vintage", "Casual"},
}


def _normalise_colour(item):
    return str(item.get("colour", "Other")).strip().lower()


def colour_score(items):
    """Return a heuristic 0-100 score for a set of clothing colours."""
    colours = [_normalise_colour(item) for item in items]
    unique = set(colours)
    if len(unique) <= 1:
        return 94

    neutral_count = sum(c in NEUTRALS for c in colours)
    non_neutrals = [c for c in colours if c not in NEUTRALS]
    score = 70

    # Neutral colours usually combine easily with one another and with accent colours.
    if neutral_count >= len(colours) - 1:
        score += 18
    elif neutral_count >= 1:
        score += 10

    # Avoid penalising a coherent palette with repeated colours.
    if len(unique) <= 2:
        score += 8
    elif len(unique) == 3:
        score += 3
    else:
        score -= min(18, (len(unique) - 3) * 6)

    # Give a small boost when colours are in a related family.
    for family in COLOUR_FAMILIES.values():
        if len(set(non_neutrals) & family) >= 2:
            score += 5
            break

    # Multicolour/patterned items make colour prediction less certain.
    if "multicolour" in unique or "other" in unique:
        score -= 5

    return max(35, min(100, int(round(score))))


def occasion_score(items, occasion):
    target = OCCASION_FORMALITY.get(occasion, 3)
    levels = [int(item.get("formality", 3)) for item in items]
    if not levels:
        return 0
    average = sum(levels) / len(levels)
    distance = abs(average - target)
    consistency_penalty = max(0, max(levels) - min(levels) - 2) * 4
    return max(0, min(100, int(round(100 - distance * 24 - consistency_penalty))))


def style_score(items, preferred_style="Any"):
    styles = [str(item.get("style", "Casual")) for item in items]
    if not styles:
        return 0

    # Pairwise compatibility: a mixed style can still work, but several clashes lower the score.
    pair_scores = []
    for i in range(len(styles)):
        for j in range(i + 1, len(styles)):
            a, b = styles[i], styles[j]
            if a == b:
                pair_scores.append(100)
            elif b in STYLE_COMPATIBILITY.get(a, set()) or a in STYLE_COMPATIBILITY.get(b, set()):
                pair_scores.append(82)
            else:
                pair_scores.append(52)
    consistency = sum(pair_scores) / len(pair_scores) if pair_scores else 85

    if preferred_style and preferred_style != "Any":
        matching = sum(1 for style in styles if style == preferred_style) / len(styles)
        consistency = 0.7 * consistency + 0.3 * matching * 100

    return int(round(consistency))


def preference_score(items, ratings):
    """Use ratings from prior recommendations; otherwise return a neutral starting score."""
    if not ratings:
        return 60
    item_names = {item.get("name", "") for item in items}
    # Ratings are keyed by outfit combination; a direct rating match is used by the caller.
    # This function is a neutral fallback until an exact prior combination is found.
    return 60


def _outfit_key(items):
    return "|".join(sorted(str(item.get("id", item.get("name", ""))) for item in items))


def _make_combinations(wardrobe):
    tops = [x for x in wardrobe if x.get("category") == "Top"]
    bottoms = [x for x in wardrobe if x.get("category") == "Bottom"]
    dresses = [x for x in wardrobe if x.get("category") == "Dress"]
    shoes = [x for x in wardrobe if x.get("category") == "Shoes"]
    outerwear = [x for x in wardrobe if x.get("category") == "Outerwear"]
    accessories = [x for x in wardrobe if x.get("category") == "Accessory"]

    combinations = []
    # Main outfit structures.
    for top, bottom, shoe in product(tops, bottoms, shoes):
        combinations.append([top, bottom, shoe])
    for dress, shoe in product(dresses, shoes):
        combinations.append([dress, shoe])

    # Add optional outerwear/accessories, but cap optional variations to avoid huge lists.
    base_combinations = list(combinations)
    for outfit in base_combinations:
        if outerwear:
            # Include one optional outerwear variation.
            for layer in outerwear[:4]:
                combinations.append(outfit + [layer])
        if accessories:
            for accessory in accessories[:4]:
                combinations.append(outfit + [accessory])
        if outerwear and accessories:
            for layer, accessory in product(outerwear[:3], accessories[:3]):
                combinations.append(outfit + [layer, accessory])

    # Deduplicate combinations by item ids.
    unique = {}
    for outfit in combinations:
        unique[_outfit_key(outfit)] = outfit
    return list(unique.values())


def score_outfit(items, occasion="Casual", preferred_style="Any", ratings=None):
    ratings = ratings or {}
    key = _outfit_key(items)
    c_score = colour_score(items)
    o_score = occasion_score(items, occasion)
    s_score = style_score(items, preferred_style)

    # Personal feedback on this exact combination, if available. Otherwise use a neutral prior.
    rated = ratings.get(key)
    p_score = int(rated) * 20 if rated else 60

    total = round(0.35 * c_score + 0.30 * o_score + 0.20 * s_score + 0.15 * p_score)
    explanation_parts = []
    if c_score >= 85:
        explanation_parts.append("the colours form a cohesive palette")
    elif c_score >= 70:
        explanation_parts.append("the colours are reasonably coordinated")
    else:
        explanation_parts.append("the colour combination is more experimental")
    if o_score >= 85:
        explanation_parts.append(f"the formality suits a {occasion.lower()} occasion")
    elif o_score >= 65:
        explanation_parts.append(f"the formality is a reasonable match for {occasion.lower()}")
    else:
        explanation_parts.append(f"the formality may not be ideal for {occasion.lower()}")
    if s_score >= 80:
        explanation_parts.append("the styles work well together")
    if rated:
        explanation_parts.append(f"you previously rated this combination {rated}/5")
    explanation = "Recommended because " + ", and ".join(explanation_parts) + "."

    return {
        "key": key,
        "items": items,
        "score": max(0, min(100, int(total))),
        "breakdown": {
            "colour": c_score,
            "occasion": o_score,
            "style": s_score,
            "preference": p_score,
        },
        "explanation": explanation,
    }


def generate_ranked_outfits(wardrobe, occasion="Casual", preferred_style="Any", ratings=None, limit=3):
    """Generate complete combinations, score them and return the top-ranked outfits."""
    if not wardrobe:
        return []
    ratings = ratings or {}
    combinations = _make_combinations(wardrobe)
    ranked = [
        score_outfit(items, occasion=occasion, preferred_style=preferred_style, ratings=ratings)
        for items in combinations
    ]
    ranked.sort(key=lambda result: (result["score"], result["breakdown"]["preference"]), reverse=True)
    return ranked[:limit]
