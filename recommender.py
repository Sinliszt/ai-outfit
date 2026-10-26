import random


def generate_outfit(wardrobe, occasion):
    tops = [
        item for item in wardrobe
        if item["category"] == "Top"
    ]
    bottoms = [
        item for item in wardrobe
        if item["category"] == "Bottom"
    ]
    dresses = [
        item for item in wardrobe
        if item["category"] == "Dress"
    ]
    shoes = [
        item for item in wardrobe
        if item["category"] == "Shoes"
    ]
    outerwear = [
        item for item in wardrobe
        if item["category"] == "Outerwear"
    ]
    outfits = []

    for top in tops:
        for bottom in bottoms:
            for shoe in shoes:
                outfit = [top, bottom, shoe]
                outfits.append(outfit)

    for dress in dresses:
        for shoe in shoes:
            outfit = [dress, shoe]
            outfits.append(outfit)

    if not outfits:
        return None

    chosen_outfit = random.choice(outfits)

    return chosen_outfit