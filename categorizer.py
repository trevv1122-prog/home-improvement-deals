"""
Categorizer Module.
Automatically separates scraped products into structured home improvement departments
using pattern recognition, keyword tokenization, brand heuristics, and taxonomy mapping.
"""

import re
from typing import Tuple

# Canonical department definitions
CATEGORIES = [
    "Tools & Hardware",
    "Appliances",
    "Lawn & Garden",
    "Electrical & Lighting",
    "Plumbing",
    "Building Materials",
    "Paint & Supplies",
    "Kitchen & Bath",
    "Storage & Organization",
    "Smart Home & Electronics",
]

# High-precision keyword patterns for categorization
CATEGORY_RULES = {
    "Tools & Hardware": [
        r"\b(drill|impact driver|saw|circular saw|miter saw|table saw|router|sander|grinder|nailer|wrench|ratchet|socket set|pliers|hammer|screwdriver|drill bit|tool kit|dewalt|milwaukee|makita|ryobi|craftsman|stanley|screws|bolts|fasteners|brackets|hinges|anchors|toolbox|workbench)\b",
    ],
    "Appliances": [
        r"\b(refrigerator|fridge|freezer|dishwasher|washer|dryer|laundry|range|oven|cooktop|microwave|range hood|ice maker|beverage cooler|air conditioner|portable ac|dehumidifier|whirlpool|samsung|lg|ge appliances|maytag|kitchenaid|bosch)\b",
    ],
    "Lawn & Garden": [
        r"\b(mower|lawn mower|riding mower|trimmer|string trimmer|weed eater|leaf blower|chainsaw|hedger|pressure washer|garden hose|sprinkler|fertilizer|mulch|soil|planter|plant|grass seed|patio furniture|pergola|grill|pellet grill|smoker|ego|toro|greenworks|ryobi outdoor|scotts|traeger|weber)\b",
    ],
    "Electrical & Lighting": [
        r"\b(ceiling fan|chandelier|vanity light|pendant light|flush mount|outdoor lighting|flood light|sconce|recessed light|led bulb|breaker|panel|wire|romex|conduit|outlet|receptacle|switch|dimmer|surge protector|generator|extension cord|lutron|leviton|eaton|square d|hunter|hampton bay|progress lighting)\b",
    ],
    "Plumbing": [
        r"\b(toilet|faucet|sink|shower head|tub|bathtub|water heater|tankless|sump pump|garbage disposal|pvc|pex|pipe|valve|drain|flapper|moen|delta|kohler|american standard|glacier bay|rheem|insinkerator)\b",
    ],
    "Building Materials": [
        r"\b(lumber|plywood|drywall|sheetrock|insulation|roofing|shingle|decking|siding|concrete|mortar|cement|rebar|flashing|ventilation|framing|stud|composite deck|owens corning|quikrete|trex|timbertech)\b",
    ],
    "Paint & Supplies": [
        r"\b(paint|primer|stain|sealer|polyurethane|spray paint|roller|brush|paint sprayer|tray|drop cloth|painters tape|sandpaper|caulk|putty|behr|glidden|valspar|minwax|sherwin|purdy|frog tape|dap)\b",
    ],
    "Kitchen & Bath": [
        r"\b(kitchen cabinet|countertop|backsplash|bath vanity|medicine cabinet|shower door|kitchen sink|granite|quartz|tile|subway tile|grout|kraftmaid|hickory|allen\s*\+\s*roth|home decorators)\b",
    ],
    "Storage & Organization": [
        r"\b(shelving unit|wire shelf|garage storage|cabinet storage|bin|tote|closet system|shoe rack|utility cart|pegboard|hooks|rubbermaid|sterilite|husky|craftsman storage)\b",
    ],
    "Smart Home & Electronics": [
        r"\b(smart thermostat|video doorbell|security camera|smart lock|nest|ring|arlo|schlage smart|august lock|wyze|smart plug|wifi extender|sensor|smoke detector|first alert)\b",
    ],
}


def categorize_product(title: str, raw_category: str = "", brand: str = "") -> Tuple[str, str]:
    """
    Categorize a product by examining raw retailer category, title, and brand.
    Returns (Category, SubCategory).
    """
    text_corpus = f"{title} {raw_category} {brand}".lower()

    # Direct match on raw category if present
    for cat in CATEGORIES:
        if cat.lower() in raw_category.lower():
            return cat, extract_sub_category(title, cat)

    # Keyword regex scanning with scoring
    scored_categories = []
    for cat, patterns in CATEGORY_RULES.items():
        score = 0
        for pattern in patterns:
            matches = re.findall(pattern, text_corpus, flags=re.IGNORECASE)
            score += len(matches)
        if score > 0:
            scored_categories.append((cat, score))

    if scored_categories:
        # Sort by match frequency
        scored_categories.sort(key=lambda x: x[1], reverse=True)
        primary_cat = scored_categories[0][0]
        return primary_cat, extract_sub_category(title, primary_cat)

    # Fallback default
    return "Tools & Hardware", "General Hardware"


def extract_sub_category(title: str, category: str) -> str:
    """Derive a friendly sub-category label."""
    title_lower = title.lower()

    if category == "Tools & Hardware":
        if any(w in title_lower for w in ["drill", "impact", "driver", "hammer drill"]):
            return "Drills & Drivers"
        if any(w in title_lower for w in ["saw", "blade", "miter", "circular"]):
            return "Saws & Woodworking"
        if any(w in title_lower for w in ["wrench", "socket", "ratchet", "pliers"]):
            return "Hand Tools"
        if any(w in title_lower for w in ["combo kit", "tool kit"]):
            return "Power Tool Combo Kits"
        return "Power Tools & Accessories"

    if category == "Appliances":
        if any(w in title_lower for w in ["fridge", "refrigerator", "freezer"]):
            return "Refrigeration"
        if any(w in title_lower for w in ["washer", "dryer", "laundry"]):
            return "Washers & Dryers"
        if any(w in title_lower for w in ["range", "cooktop", "oven", "microwave"]):
            return "Cooking Appliances"
        return "Major Appliances"

    if category == "Lawn & Garden":
        if any(w in title_lower for w in ["mower", "tractor"]):
            return "Lawn Mowers"
        if any(w in title_lower for w in ["blower", "trimmer", "chainsaw", "edger"]):
            return "Outdoor Power Equipment"
        if any(w in title_lower for w in ["grill", "smoker", "bbq"]):
            return "Grills & Outdoor Cooking"
        return "Yard Care & Landscaping"

    if category == "Electrical & Lighting":
        if any(w in title_lower for w in ["fan", "ceiling fan"]):
            return "Ceiling Fans"
        if any(w in title_lower for w in ["chandelier", "pendant", "vanity light", "sconce"]):
            return "Indoor Lighting"
        if any(w in title_lower for w in ["generator", "inverter"]):
            return "Generators & Power"
        return "Electrical Fixtures & Wiring"

    if category == "Plumbing":
        if any(w in title_lower for w in ["faucet", "shower"]):
            return "Faucets & Showerheads"
        if any(w in title_lower for w in ["water heater", "tankless"]):
            return "Water Heaters"
        if any(w in title_lower for w in ["toilet", "bidet"]):
            return "Toilets & Parts"
        return "Pipes & Fixtures"

    return "General"
