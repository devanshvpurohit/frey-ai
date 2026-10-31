"""
FREY AI - Multi-Crop Plant Disease Taxonomy & Registry
Authoritative metadata for plant species, diseases, healthy classifications,
and management recommendations.

Supports:
- Mendeley Multi-Crop Disease Dataset (DOI: 10.17632/6243z8r6t6.1): Banana, Cauliflower, Chilli, Groundnut, Radish (30 classes)
- PlantDoc Dataset: Apple, Tomato, Potato, Corn, Grape, etc.
"""

from typing import Dict, Any, List, Optional

# Primary Mendeley 30-class taxonomy
MENDELEY_30_CLASSES: List[Dict[str, Any]] = [
    {
        "id": 0,
        "raw_name": "banana_bract_mosaic_virus",
        "crop": "Banana",
        "disease": "Bract Mosaic Virus",
        "is_healthy": False,
        "display_name": "Banana — Bract Mosaic Virus",
        "scientific_name": "Banana bract mosaic virus (BBrMV)",
        "recommendation": "Eradicate and burn infected plants. Disinfect machetes and pruning knives. Control aphid vectors using neem oil.",
    },
    {
        "id": 1,
        "raw_name": "banana_cordana",
        "crop": "Banana",
        "disease": "Cordana Leaf Spot",
        "is_healthy": False,
        "display_name": "Banana — Cordana Leaf Spot",
        "scientific_name": "Cordana musae",
        "recommendation": "Prune decaying leaves. Ensure proper spacing to enhance air movement. Apply protectant mancozeb or chlorothalonil.",
    },
    {
        "id": 2,
        "raw_name": "banana_healthy",
        "crop": "Banana",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Banana — Healthy Leaf",
        "scientific_name": "Musa acuminata",
        "recommendation": "Foliage and pseudostem are vigorous. Maintain balanced nitrogen-potassium feeding and routine de-suckering.",
    },
    {
        "id": 3,
        "raw_name": "banana_insectpest",
        "crop": "Banana",
        "disease": "Insect Pest Damage",
        "is_healthy": False,
        "display_name": "Banana — Insect Pest Damage",
        "scientific_name": "Cosmopolites sordidus / Thrips",
        "recommendation": "Inspect pseudostem base for banana weevil borer galleries. Deploy pheromone traps and entomopathogenic nematodes.",
    },
    {
        "id": 4,
        "raw_name": "banana_moko",
        "crop": "Banana",
        "disease": "Moko Disease (Bacterial Wilt)",
        "is_healthy": False,
        "display_name": "Banana — Moko Bacterial Wilt",
        "scientific_name": "Ralstonia solanacearum race 2",
        "recommendation": "CRITICAL: Quarantine pathogen. Uproot and burn infected mats. Bag male flower buds to prevent insect vector transmission.",
    },
    {
        "id": 5,
        "raw_name": "banana_panama",
        "crop": "Banana",
        "disease": "Panama Disease (Fusarium Wilt)",
        "is_healthy": False,
        "display_name": "Banana — Panama Fusarium Wilt",
        "scientific_name": "Fusarium oxysporum f. sp. cubense",
        "recommendation": "Soil-borne fungal wilt. Prevent soil/water movement from infected block. Replant with resistant somaclones.",
    },
    {
        "id": 6,
        "raw_name": "banana_pestalotiopsis",
        "crop": "Banana",
        "disease": "Pestalotiopsis Leaf Spot",
        "is_healthy": False,
        "display_name": "Banana — Pestalotiopsis Leaf Spot",
        "scientific_name": "Pestalotiopsis microspora",
        "recommendation": "Apply preventive copper oxychloride. Remove severely spotted lower leaves before the onset of the monsoon.",
    },
    {
        "id": 7,
        "raw_name": "banana_sigatoka",
        "crop": "Banana",
        "disease": "Black Sigatoka",
        "is_healthy": False,
        "display_name": "Banana — Black Sigatoka",
        "scientific_name": "Pseudocercospora fijiensis",
        "recommendation": "Apply systemic triazole or strobilurin fungicides in rotation with agricultural mineral oil. Strip diseased leaf tips promptly.",
    },
    {
        "id": 8,
        "raw_name": "banana_yb_sigatoka",
        "crop": "Banana",
        "disease": "Yellow Sigatoka",
        "is_healthy": False,
        "display_name": "Banana — Yellow Sigatoka",
        "scientific_name": "Pseudocercospora musae",
        "recommendation": "De-leaf lower infected canopies. Improve field drainage and apply preventive copper hydroxide sprays.",
    },
    {
        "id": 9,
        "raw_name": "cauliflower_Blackrot",
        "crop": "Cauliflower",
        "disease": "Black Rot",
        "is_healthy": False,
        "display_name": "Cauliflower — Black Rot",
        "scientific_name": "Xanthomonas campestris pv. campestris",
        "recommendation": "Hot-water seed treatment (50°C for 25 min). Spray copper hydroxide bactericide. Practice 3-year non-brassica crop rotation.",
    },
    {
        "id": 10,
        "raw_name": "cauliflower_bacterial _spot _rot",
        "crop": "Cauliflower",
        "disease": "Bacterial Spot & Soft Rot",
        "is_healthy": False,
        "display_name": "Cauliflower — Bacterial Soft Rot",
        "scientific_name": "Pectobacterium carotovorum",
        "recommendation": "Avoid overhead irrigation during curding. Prevent mechanical damage during hoeing. Disinfect harvesting tools.",
    },
    {
        "id": 11,
        "raw_name": "cauliflower_downy_mildew",
        "crop": "Cauliflower",
        "disease": "Downy Mildew",
        "is_healthy": False,
        "display_name": "Cauliflower — Downy Mildew",
        "scientific_name": "Hyaloperonospora brassicae",
        "recommendation": "Apply metalaxyl-mancozeb or fosetyl-aluminum. Avoid evening watering and reduce plant density for aeration.",
    },
    {
        "id": 12,
        "raw_name": "cauliflower_healthy",
        "crop": "Cauliflower",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Cauliflower — Healthy Foliage",
        "scientific_name": "Brassica oleracea var. botrytis",
        "recommendation": "Healthy curd and waxy foliage. Maintain uniform soil moisture and boron supplementation to prevent hollow stem.",
    },
    {
        "id": 13,
        "raw_name": "chilli_anthracnose",
        "crop": "Chilli",
        "disease": "Anthracnose (Dieback / Fruit Rot)",
        "is_healthy": False,
        "display_name": "Chilli — Anthracnose Fruit Rot",
        "scientific_name": "Colletotrichum capsici",
        "recommendation": "Spray azoxystrobin or difenoconazole. Remove dried mummified fruit twigs. Use disease-free certified seeds.",
    },
    {
        "id": 14,
        "raw_name": "chilli_healthy",
        "crop": "Chilli",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Chilli — Healthy Leaf",
        "scientific_name": "Capsicum annuum",
        "recommendation": "Vigorous dark green foliage. Maintain balanced drip fertigation and periodic whitefly/thrips scouting.",
    },
    {
        "id": 15,
        "raw_name": "chilli_leafcurl",
        "crop": "Chilli",
        "disease": "Leaf Curl Virus",
        "is_healthy": False,
        "display_name": "Chilli — Leaf Curl Virus",
        "scientific_name": "Chilli leaf curl virus (ChiLCV)",
        "recommendation": "Whitefly-vectored geminivirus. Install yellow sticky traps. Spray acetamiprid or thiamethoxam to control whitefly populations.",
    },
    {
        "id": 16,
        "raw_name": "chilli_leafspot",
        "crop": "Chilli",
        "disease": "Cercospora Leaf Spot",
        "is_healthy": False,
        "display_name": "Chilli — Cercospora Leaf Spot",
        "scientific_name": "Cercospora capsici",
        "recommendation": "Spray mancozeb or carbendazim at first onset of circular frog-eye lesions. Deep bury crop residues post-harvest.",
    },
    {
        "id": 17,
        "raw_name": "chilli_whitefly",
        "crop": "Chilli",
        "disease": "Whitefly Infestation",
        "is_healthy": False,
        "display_name": "Chilli — Whitefly Infestation",
        "scientific_name": "Bemisia tabaci",
        "recommendation": "Release encarsia parasitoid wasps or chrysoperla. Spray insecticidal soap or 2% neem oil to suppress egg laying.",
    },
    {
        "id": 18,
        "raw_name": "chilli_yellowish",
        "crop": "Chilli",
        "disease": "Yellow Mosaic & Chlorosis",
        "is_healthy": False,
        "display_name": "Chilli — Yellowing / Chlorosis",
        "scientific_name": "Pepper yellow mosaic virus / Micro-nutrient deficiency",
        "recommendation": "Apply chelated zinc and iron foliar sprays. Test soil for root-knot nematode damage.",
    },
    {
        "id": 19,
        "raw_name": "groundnut_early_leaf_spot",
        "crop": "Groundnut",
        "disease": "Early Leaf Spot (Tikka)",
        "is_healthy": False,
        "display_name": "Groundnut — Early Leaf Spot",
        "scientific_name": "Cercospora arachidicola",
        "recommendation": "Apply chlorothalonil or tebuconazole starting 35-40 days after sowing. Rotate with maize or sorghum.",
    },
    {
        "id": 20,
        "raw_name": "groundnut_early_rust",
        "crop": "Groundnut",
        "disease": "Early Rust",
        "is_healthy": False,
        "display_name": "Groundnut — Early Rust",
        "scientific_name": "Puccinia arachidis",
        "recommendation": "Spray hexaconazole or propiconazole at appearance of orange-brown pustules on underside of leaves.",
    },
    {
        "id": 21,
        "raw_name": "groundnut_healthy",
        "crop": "Groundnut",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Groundnut — Healthy Leaf",
        "scientific_name": "Arachis hypogaea",
        "recommendation": "Strong vegetative canopy. Ensure calcium/gypsum availability at pegging stage for pod development.",
    },
    {
        "id": 22,
        "raw_name": "groundnut_late_leaf_spot",
        "crop": "Groundnut",
        "disease": "Late Leaf Spot",
        "is_healthy": False,
        "display_name": "Groundnut — Late Leaf Spot",
        "scientific_name": "Cercosporidium personatum",
        "recommendation": "Apply systemic strobilurin + triazole tank-mix. Harvest promptly at maturity to avoid pod shedding.",
    },
    {
        "id": 23,
        "raw_name": "groundnut_nutrition_deficiency",
        "crop": "Groundnut",
        "disease": "Nutrient Deficiency",
        "is_healthy": False,
        "display_name": "Groundnut — Nutrient Deficiency",
        "scientific_name": "Iron / Zinc Deficiency",
        "recommendation": "Soil test pH. Apply foliar zinc sulfate (0.5%) and ferrous sulfate (1.0%) with lime to correct chlorosis.",
    },
    {
        "id": 24,
        "raw_name": "groundnut_rust",
        "crop": "Groundnut",
        "disease": "Rust Pustules",
        "is_healthy": False,
        "display_name": "Groundnut — Rust",
        "scientific_name": "Puccinia arachidis",
        "recommendation": "Apply wettable sulfur or triadimefon fungicide. Avoid excessive plant density in humid conditions.",
    },
    {
        "id": 25,
        "raw_name": "radish_black_leaf_spot",
        "crop": "Radish",
        "disease": "Black Leaf Spot",
        "is_healthy": False,
        "display_name": "Radish — Black Leaf Spot",
        "scientific_name": "Alternaria raphani",
        "recommendation": "Hot-water seed treatment (50°C for 20 min). Apply iprodione or mancozeb sprays at 10-day intervals.",
    },
    {
        "id": 26,
        "raw_name": "radish_downey_mildew",
        "crop": "Radish",
        "disease": "Downy Mildew",
        "is_healthy": False,
        "display_name": "Radish — Downy Mildew",
        "scientific_name": "Peronospora parasitica",
        "recommendation": "Spray copper oxychloride or cymoxanil. Improve furrow drainage and weed management to reduce relative humidity.",
    },
    {
        "id": 27,
        "raw_name": "radish_flea_beetle",
        "crop": "Radish",
        "disease": "Flea Beetle Damage",
        "is_healthy": False,
        "display_name": "Radish — Flea Beetle Shot-Holes",
        "scientific_name": "Phyllotreta cruciferae",
        "recommendation": "Deploy floating row covers over young seedlings. Dust with diatomaceous earth or apply pyrethrin spray.",
    },
    {
        "id": 28,
        "raw_name": "radish_healthy",
        "crop": "Radish",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Radish — Healthy Leaf",
        "scientific_name": "Raphanus sativus",
        "recommendation": "Foliage is crisp and uniform. Maintain consistent soil moisture to prevent root cracking.",
    },
    {
        "id": 29,
        "raw_name": "radish_mosaic",
        "crop": "Radish",
        "disease": "Radish Mosaic Virus",
        "is_healthy": False,
        "display_name": "Radish — Mosaic Virus",
        "scientific_name": "Radish mosaic virus (RaMV)",
        "recommendation": "Aphid-borne comovirus. Rogue out infected stunted plants. Disinfect field tools with trisodium phosphate.",
    },
]

# Backward compatibility alias
PLANTDOC_CLASSES = MENDELEY_30_CLASSES
CLASSES = MENDELEY_30_CLASSES

# Lookups
BY_ID: Dict[int, Dict[str, Any]] = {entry["id"]: entry for entry in MENDELEY_30_CLASSES}
BY_RAW_NAME: Dict[str, Dict[str, Any]] = {
    entry["raw_name"].lower().strip(): entry for entry in MENDELEY_30_CLASSES
}


def get_taxonomy_entry(identifier: Any) -> Optional[Dict[str, Any]]:
    """Retrieve taxonomy entry by class integer ID or raw string name."""
    if isinstance(identifier, int):
        return BY_ID.get(identifier)
    if isinstance(identifier, str):
        cleaned = identifier.lower().strip()
        if cleaned in BY_RAW_NAME:
            return BY_RAW_NAME[cleaned]
        for k, v in BY_RAW_NAME.items():
            if cleaned == k.replace("_", " "):
                return v
    return None


def parse_prediction(
    class_id: int,
    confidence: float,
    bbox: List[int],
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Enrich raw detection output with agricultural metadata.
    
    IMPORTANT AG-NOTE: Confidence score represents the neural network's
    classification probability, NOT the biological severity or progression
    of the disease.
    """
    tax = get_taxonomy_entry(class_id)
    if not tax:
        return {
            "class_id": class_id,
            "crop": "Unknown",
            "disease": "Unclassified",
            "is_healthy": False,
            "display_name": f"Class {class_id}",
            "confidence": round(float(confidence), 3),
            "confidence_percent": f"{round(confidence * 100, 1)}%",
            "bbox": bbox,
            "timestamp": timestamp,
            "recommendation": "Species not in registry. Inspect plant manually.",
            "severity_disclaimer": "Confidence reflects model certainty, not biological severity.",
        }

    return {
        "class_id": class_id,
        "crop": tax["crop"],
        "disease": tax["disease"],
        "is_healthy": tax["is_healthy"],
        "display_name": tax["display_name"],
        "scientific_name": tax.get("scientific_name", ""),
        "confidence": round(float(confidence), 3),
        "confidence_percent": f"{round(confidence * 100, 1)}%",
        "bbox": bbox,
        "timestamp": timestamp,
        "recommendation": tax.get("recommendation", "Continue routine monitoring."),
        "severity_disclaimer": "Confidence reflects classification probability, not disease severity.",
    }


def list_supported_crops() -> List[str]:
    """Returns sorted list of all crops currently supported."""
    crops = set(entry["crop"] for entry in MENDELEY_30_CLASSES)
    return sorted(list(crops))


def get_all_classes() -> List[Dict[str, Any]]:
    """Returns all 30 base classes."""
    return MENDELEY_30_CLASSES
