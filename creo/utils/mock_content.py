import random


def mock_recent_posts(creator, count: int = 5) -> list[dict]:
    """Deterministic mock recent posts for a creator's application review.

    Posts are derived from the creator's id so the same creator always gets the
    same mock feed. Each post targets a linked platform (instagram/youtube/etc).
    """
    rng = random.Random(f"posts::{creator.id}")
    platforms = list(creator.platforms.keys()) or ["instagram"]
    niche = creator.primary_niche or "creator"
    engagement = max(0.5, creator.avg_engagement_rate)

    templates = {
        "Gaming": [
            "First look at {game} gameplay — full review dropping soon!",
            "Ranked up to {rank} tonight, absolutely clutch.",
            "New loadout guide: {item} is broken this patch.",
            "Streaming {game} at 9PM, come hang out!",
            "Best moments from last night's squad — watch till the end.",
        ],
        "Beauty & Makeup": [
            "Everyday glam tutorial with the {palette} palette.",
            "Skincare routine for glowing skin — part 1 of 3.",
            "Rating viral makeup trends, some are a hard no.",
            "Easy festival look using only {budget} products.",
            "Unboxing the new {brand} collection, so excited!",
        ],
        "Fitness & Wellness": [
            "Full body workout you can do at home — no equipment.",
            "What I eat in a day: {meals} meals to hit protein goals.",
            "Morning mobility routine to fix your posture.",
            "Cardio vs strength: which burns more fat?",
            "Day {n} of my 90-day transformation challenge.",
        ],
        "Fashion": [
            "OOTD: {outfit} perfect for a casual coffee date.",
            "Streetwear haul from {store}, budget friendly picks.",
            "5 ways to style the same {item}.",
            "Fall capsule wardrobe essentials.",
            "Rate my outfit from 1-10 in the comments!",
        ],
        "Food & Cooking": [
            "Easy {recipe} recipe in under 20 minutes.",
            "Restaurant review: {place} — worth the hype?",
            "Home-cooked meal prep for the week.",
            "Secret ingredient that makes {dish} amazing.",
            "Street food tour in {city}, part 2.",
        ],
    }
    niche_templates = templates.get(niche, [
        "Quick update for you all — more coming soon!",
        "Behind the scenes of today's shoot.",
        "What should I post next? Drop ideas below.",
        "Appreciate all the support on the latest video.",
        "Collaboration announcement — guess who?",
    ])

    posts = []
    for i in range(count):
        platform = platforms[i % len(platforms)]
        info = creator.platforms.get(platform)
        base_followers = max(1, info.followers if info else 0)
        likes = int(base_followers * (engagement / 100) * rng.uniform(0.5, 1.2))
        comments = int(likes * rng.uniform(0.02, 0.06))
        caption = rng.choice(niche_templates)
        caption = caption.format(
            game="VALORANT", rank="Diamond", item="new meta",
            palette="Neutral Nudes", budget="3", brand="Lakmé",
            meals="4", outfit="oversized blazer", store="Zara",
            recipe="chicken stir-fry", place="Sagar Gare",
            dish="butter chicken", city="Mumbai", n=i + 3,
        )
        posts.append({
            "platform": platform,
            "caption": caption,
            "likes": likes,
            "comments": comments,
            "posted_at": f"{i * 3 + 1} days ago",
        })
    return posts
