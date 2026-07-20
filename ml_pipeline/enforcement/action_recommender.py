ACTION_MAP = {

    "Traffic/Roads": [
        "Deploy traffic police",
        "Restrict heavy vehicles",
        "Implement traffic diversion",
        "Increase public transport frequency"
    ],

    "Industry": [
        "Inspect industrial units",
        "Verify stack emissions",
        "Check pollution-control equipment",
        "Review environmental compliance"
    ],

    "Construction/Dust": [
        "Dust suppression",
        "Water sprinkling",
        "Cover exposed materials",
        "Inspect construction site compliance"
    ]
}


def get_action(source: str) -> str:

    source = str(source).strip()

    if source not in ACTION_MAP:
        return "Investigate source"

    return ACTION_MAP[source][0]