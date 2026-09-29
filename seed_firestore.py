from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-15689d1f930e"
db = firestore.Client(project=PROJECT_ID)

destinations = [
    {
        "id": "kyoto-japan",
        "name": "Kyoto",
        "country": "Japan",
        "best_season": "Spring / Autumn",
        "style": "Culture & Nature",
        "avg_daily_budget_usd": 150,
        "description": "Historic city famed for thousands of classical Buddhist temples, gardens, imperial palaces, and traditional wooden houses.",
        "top_attractions": ["Fushimi Inari Taisha", "Kinkaku-ji (Golden Pavilion)", "Arashiyama Bamboo Grove"],
    },
    {
        "id": "reykjavik-iceland",
        "name": "Reykjavik",
        "country": "Iceland",
        "best_season": "Winter (Aurora) / Summer (Midnight Sun)",
        "style": "Adventure & Nature",
        "avg_daily_budget_usd": 220,
        "description": "Coastal capital known for geothermal wonders, volcanic landscapes, dramatic waterfalls, and Northern Lights.",
        "top_attractions": ["Blue Lagoon", "Golden Circle", "Hallgrimskirkja"],
    },
    {
        "id": "rome-italy",
        "name": "Rome",
        "country": "Italy",
        "best_season": "Spring / Autumn",
        "style": "Food & History",
        "avg_daily_budget_usd": 170,
        "description": "Vibrant metropolis with nearly 3,000 years of globally influential art, architecture, and world-class cuisine.",
        "top_attractions": ["Colosseum", "Vatican Museums", "Pantheon"],
    },
    {
        "id": "banff-canada",
        "name": "Banff National Park",
        "country": "Canada",
        "best_season": "Summer / Winter",
        "style": "Outdoors & Hiking",
        "avg_daily_budget_usd": 190,
        "description": "Stunning Canadian Rockies park with turquoise glacial lakes, towering peaks, and abundant wildlife.",
        "top_attractions": ["Lake Louise", "Moraine Lake", "Banff Gondola"],
    }
]

for d in destinations:
    doc_ref = db.collection("destinations").document(d["id"])
    doc_ref.set(d)
    print(f"Seeded destination: {d['name']}")

print("Firestore seeding complete!")
