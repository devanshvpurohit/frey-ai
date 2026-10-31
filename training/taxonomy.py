"""
FREY AI - Multi-Crop Plant Disease Taxonomy & Registry
Authoritative metadata for plant species, diseases, healthy classifications,
and management recommendations.
"""

from typing import Dict, Any, List, Optional

# Canonical PlantDoc 29-class taxonomy
PLANTDOC_CLASSES: List[Dict[str, Any]] = [
    {
        "id": 0,
        "raw_name": "Apple Scab Leaf",
        "crop": "Apple",
        "disease": "Apple Scab",
        "is_healthy": False,
        "display_name": "Apple — Scab",
        "scientific_name": "Venturia inaequalis",
        "recommendation": "Prune infected shoots, apply copper-based or sulfur fungicides during early budding. Avoid overhead watering.",
    },
    {
        "id": 1,
        "raw_name": "Apple leaf",
        "crop": "Apple",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Apple — Healthy Leaf",
        "scientific_name": "Malus domestica",
        "recommendation": "Leaf tissue appears normal. Maintain standard orchard monitoring and nutrition.",
    },
    {
        "id": 2,
        "raw_name": "Apple rust leaf",
        "crop": "Apple",
        "disease": "Cedar Apple Rust",
        "is_healthy": False,
        "display_name": "Apple — Rust",
        "scientific_name": "Gymnosporangium juniperi-virginianae",
        "recommendation": "Apply targeted fungicide at pink-bud stage. Remove nearby eastern red cedar galls within 500m.",
    },
    {
        "id": 3,
        "raw_name": "Bell_pepper leaf",
        "crop": "Bell Pepper",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Bell Pepper — Healthy Leaf",
        "scientific_name": "Capsicum annuum",
        "recommendation": "Normal foliage. Maintain balanced drip irrigation and balanced NPK fertilizer.",
    },
    {
        "id": 4,
        "raw_name": "Bell_pepper leaf spot",
        "crop": "Bell Pepper",
        "disease": "Bacterial Spot",
        "is_healthy": False,
        "display_name": "Bell Pepper — Bacterial Spot",
        "scientific_name": "Xanthomonas campestris pv. vesicatoria",
        "recommendation": "Apply copper bactericide + mancozeb. Avoid working among wet foliage. Rotate with non-solanaceous crops.",
    },
    {
        "id": 5,
        "raw_name": "Blueberry leaf",
        "crop": "Blueberry",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Blueberry — Healthy Leaf",
        "scientific_name": "Vaccinium corymbosum",
        "recommendation": "Canopy is healthy. Maintain acidic soil pH (4.5–5.2) and adequate mulch.",
    },
    {
        "id": 6,
        "raw_name": "Cherry leaf",
        "crop": "Cherry",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Cherry — Healthy Leaf",
        "scientific_name": "Prunus avium",
        "recommendation": "Foliage in good condition. Inspect regularly for powdery mildew or leaf spot symptoms.",
    },
    {
        "id": 7,
        "raw_name": "Corn Gray leaf spot",
        "crop": "Corn (Maize)",
        "disease": "Gray Leaf Spot",
        "is_healthy": False,
        "display_name": "Corn — Gray Leaf Spot",
        "scientific_name": "Cercospora zeae-maydis",
        "recommendation": "Apply strobilurin or triazole fungicides before VT tasseling stage if disease pressure is high.",
    },
    {
        "id": 8,
        "raw_name": "Corn leaf blight",
        "crop": "Corn (Maize)",
        "disease": "Northern Leaf Blight",
        "is_healthy": False,
        "display_name": "Corn — Northern Leaf Blight",
        "scientific_name": "Exserohilum turcicum",
        "recommendation": "Use resistant hybrids. Deep tillage to bury residue and timely foliar fungicide spray.",
    },
    {
        "id": 9,
        "raw_name": "Corn rust leaf",
        "crop": "Corn (Maize)",
        "disease": "Common Rust",
        "is_healthy": False,
        "display_name": "Corn — Common Rust",
        "scientific_name": "Puccinia sorghi",
        "recommendation": "Scout lower canopy. Fungicide applications rarely needed unless severe on susceptible inbreds.",
    },
    {
        "id": 10,
        "raw_name": "grape leaf",
        "crop": "Grape",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Grape — Healthy Leaf",
        "scientific_name": "Vitis vinifera",
        "recommendation": "Vines appear healthy. Maintain canopy training for airflow and sun penetration.",
    },
    {
        "id": 11,
        "raw_name": "grape leaf black rot",
        "crop": "Grape",
        "disease": "Black Rot",
        "is_healthy": False,
        "display_name": "Grape — Black Rot",
        "scientific_name": "Guignardia bidwellii",
        "recommendation": "Apply myclobutanil or mancozeb from pre-bloom to 4 weeks post-bloom. Remove mummified berries.",
    },
    {
        "id": 12,
        "raw_name": "Peach leaf",
        "crop": "Peach",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Peach — Healthy Leaf",
        "scientific_name": "Prunus persica",
        "recommendation": "Foliage clear. Prepare for dormant copper application for peach leaf curl prevention.",
    },
    {
        "id": 13,
        "raw_name": "Potato leaf",
        "crop": "Potato",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Potato — Healthy Leaf",
        "scientific_name": "Solanum tuberosum",
        "recommendation": "Healthy foliage. Monitor weekly for early and late blight lesions.",
    },
    {
        "id": 14,
        "raw_name": "Potato leaf early blight",
        "crop": "Potato",
        "disease": "Early Blight",
        "is_healthy": False,
        "display_name": "Potato — Early Blight",
        "scientific_name": "Alternaria solani",
        "recommendation": "Apply protectant fungicides (chlorothalonil/mancozeb). Avoid plant moisture stress and nitrogen deficiency.",
    },
    {
        "id": 15,
        "raw_name": "Potato leaf late blight",
        "crop": "Potato",
        "disease": "Late Blight",
        "is_healthy": False,
        "display_name": "Potato — Late Blight",
        "scientific_name": "Phytophthora infestans",
        "recommendation": "URGENT: High contagion risk. Apply systemic fungicide (metalaxyl or cymoxanil). Destroy infected cull piles.",
    },
    {
        "id": 16,
        "raw_name": "Raspberry leaf",
        "crop": "Raspberry",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Raspberry — Healthy Leaf",
        "scientific_name": "Rubus idaeus",
        "recommendation": "Healthy bramble foliage. Prune old fruited floricanes to enhance aeration.",
    },
    {
        "id": 17,
        "raw_name": "Soyabean leaf",
        "crop": "Soybean",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Soybean — Healthy Leaf",
        "scientific_name": "Glycine max",
        "recommendation": "Crop foliage is vigorous. Scout periodically for frogeye leaf spot and downy mildew.",
    },
    {
        "id": 18,
        "raw_name": "Squash Powdery mildew leaf",
        "crop": "Squash",
        "disease": "Powdery Mildew",
        "is_healthy": False,
        "display_name": "Squash — Powdery Mildew",
        "scientific_name": "Podosphaera xanthii",
        "recommendation": "Apply potassium bicarbonate, neem oil, or strobilurin. Ensure proper plant spacing for sunlight.",
    },
    {
        "id": 19,
        "raw_name": "Strawberry leaf",
        "crop": "Strawberry",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Strawberry — Healthy Leaf",
        "scientific_name": "Fragaria × ananassa",
        "recommendation": "Healthy runner and crown foliage. Keep fruit off moist soil with clean straw mulch.",
    },
    {
        "id": 20,
        "raw_name": "Tomato Early blight leaf",
        "crop": "Tomato",
        "disease": "Early Blight",
        "is_healthy": False,
        "display_name": "Tomato — Early Blight",
        "scientific_name": "Alternaria solani",
        "recommendation": "Prune lower leaves touching soil. Spray copper or mancozeb at first sign of concentric lesions.",
    },
    {
        "id": 21,
        "raw_name": "Tomato Septoria leaf spot",
        "crop": "Tomato",
        "disease": "Septoria Leaf Spot",
        "is_healthy": False,
        "display_name": "Tomato — Septoria Leaf Spot",
        "scientific_name": "Septoria lycopersici",
        "recommendation": "Remove affected bottom leaves immediately. Apply chlorothalonil or copper fungicide weekly.",
    },
    {
        "id": 22,
        "raw_name": "Tomato leaf",
        "crop": "Tomato",
        "disease": "Healthy",
        "is_healthy": True,
        "display_name": "Tomato — Healthy Leaf",
        "scientific_name": "Solanum lycopersicum",
        "recommendation": "Vigorous foliage. Support vines with stakes or cages to maintain distance from ground pathogens.",
    },
    {
        "id": 23,
        "raw_name": "Tomato leaf bacterial spot",
        "crop": "Tomato",
        "disease": "Bacterial Spot",
        "is_healthy": False,
        "display_name": "Tomato — Bacterial Spot",
        "scientific_name": "Xanthomonas perforans",
        "recommendation": "Apply copper + mancozeb bactericide tank-mix. Sanitize equipment and avoid handling damp foliage.",
    },
    {
        "id": 24,
        "raw_name": "Tomato leaf late blight",
        "crop": "Tomato",
        "disease": "Late Blight",
        "is_healthy": False,
        "display_name": "Tomato — Late Blight",
        "scientific_name": "Phytophthora infestans",
        "recommendation": "CRITICAL: Fast-spreading water mold. Remove heavily infected plants. Apply chlorothalonil, mandipropamid or cymoxanil.",
    },
    {
        "id": 25,
        "raw_name": "Tomato leaf mosaic virus",
        "crop": "Tomato",
        "disease": "Mosaic Virus",
        "is_healthy": False,
        "display_name": "Tomato — Mosaic Virus",
        "scientific_name": "Tobacco mosaic virus (TMV)",
        "recommendation": "No chemical cure. Remove and burn infected plants. Disinfect tools with 10% bleach solution. Wash hands after handling tobacco.",
    },
    {
        "id": 26,
        "raw_name": "Tomato leaf yellow virus",
        "crop": "Tomato",
        "disease": "Yellow Leaf Curl Virus",
        "is_healthy": False,
        "display_name": "Tomato — Yellow Leaf Curl",
        "scientific_name": "TYLCV (transmitted by Bemisia tabaci)",
        "recommendation": "Control whitefly vector with insecticidal soap or yellow sticky cards. Use reflective silver mulches.",
    },
    {
        "id": 27,
        "raw_name": "Tomato mold leaf",
        "crop": "Tomato",
        "disease": "Leaf Mold",
        "is_healthy": False,
        "display_name": "Tomato — Leaf Mold",
        "scientific_name": "Passalora fulva",
        "recommendation": "Reduce greenhouse humidity below 85%. Increase ventilation and apply preventive copper sprays.",
    },
    {
        "id": 28,
        "raw_name": "Tomato two spotted spider mites leaf",
        "crop": "Tomato",
        "disease": "Two-Spotted Spider Mite",
        "is_healthy": False,
        "display_name": "Tomato — Spider Mite Damage",
        "scientific_name": "Tetranychus urticae",
        "recommendation": "Apply horticultural oil, neem spray, or release predatory mites (Phytoseiulus persimilis).",
    },
]

# Additional extensible crops configuration
EXTENSION_CROPS: Dict[str, Dict[str, Any]] = {
    "Rice": {
        "scientific_name": "Oryza sativa",
        "supported_conditions": ["Healthy", "Blast", "Brown Spot", "Bacterial Leaf Blight", "Sheath Blight"],
    },
    "Wheat": {
        "scientific_name": "Triticum aestivum",
        "supported_conditions": ["Healthy", "Stripe Rust", "Leaf Rust", "Powdery Mildew", "Septoria Nodorum"],
    },
    "Cotton": {
        "scientific_name": "Gossypium hirsutum",
        "supported_conditions": ["Healthy", "Bacterial Blight", "Leaf Curl Virus", "Alternaria Leaf Spot"],
    },
    "Chilli": {
        "scientific_name": "Capsicum frutescens",
        "supported_conditions": ["Healthy", "Anthracnose", "Leaf Curl Virus", "Cercospora Leaf Spot"],
    },
    "Maize": {
        "scientific_name": "Zea mays",
        "supported_conditions": ["Healthy", "Common Rust", "Northern Leaf Blight", "Gray Leaf Spot"],
    },
}

# Index lookups
BY_ID: Dict[int, Dict[str, Any]] = {entry["id"]: entry for entry in PLANTDOC_CLASSES}
BY_RAW_NAME: Dict[str, Dict[str, Any]] = {
    entry["raw_name"].lower().strip(): entry for entry in PLANTDOC_CLASSES
}


def get_taxonomy_entry(identifier: Any) -> Optional[Dict[str, Any]]:
    """Retrieve taxonomy entry by class integer ID or raw string name."""
    if isinstance(identifier, int):
        return BY_ID.get(identifier)
    if isinstance(identifier, str):
        cleaned = identifier.lower().strip()
        # Direct match
        if cleaned in BY_RAW_NAME:
            return BY_RAW_NAME[cleaned]
        # Partial match
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
            "display_name": f"Unknown Class {class_id}",
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
        "recommendation": tax.get("recommendation", "Continue monitoring."),
        "severity_disclaimer": "Confidence reflects classification probability, not disease severity.",
    }


def list_supported_crops() -> List[str]:
    """Returns sorted list of all crops currently supported in FREY AI."""
    crops = set(entry["crop"] for entry in PLANTDOC_CLASSES)
    crops.update(EXTENSION_CROPS.keys())
    return sorted(list(crops))


def get_all_classes() -> List[Dict[str, Any]]:
    """Returns all 29 base classes."""
    return PLANTDOC_CLASSES
