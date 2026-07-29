import pandas as pd
from io import StringIO
from typing import Optional

from creo.models import Creator, Campaign, Payment, PlatformInfo, CreatorStatus


def export_creators_to_csv(creators: list[Creator]) -> str:
    rows = []
    for c in creators:
        rows.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone or "",
            "primary_niche": c.primary_niche,
            "secondary_niches": "; ".join(c.secondary_niches),
            "primary_language": c.primary_language,
            "secondary_languages": "; ".join(c.secondary_languages),
            "content_quality_score": c.content_quality_score,
            "profile_completeness": c.profile_completeness,
            "avg_engagement_rate": c.avg_engagement_rate,
            "status": c.status.value,
            "total_campaigns_completed": c.total_campaigns_completed,
            "total_earnings": c.total_earnings,
            "notes": c.notes or "",
            "platforms": "; ".join(f"{p}:@{info.handle}" for p, info in c.platforms.items()),
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def import_creators_from_csv(csv_content: str) -> list[Creator]:
    df = pd.read_csv(StringIO(csv_content))
    creators = []
    for _, row in df.iterrows():
        platforms = {}
        if pd.notna(row.get("platforms")):
            for entry in str(row["platforms"]).split("; "):
                if ":" in entry and "@" in entry:
                    parts = entry.split(":@")
                    platform_name = parts[0]
                    handle = parts[1] if len(parts) > 1 else ""
                    if platform_name:
                        platforms[platform_name] = PlatformInfo(handle=handle, followers=0)

        secondary_niches = [s.strip() for s in str(row.get("secondary_niches", "")).split(";") if s.strip()]
        secondary_languages = [s.strip() for s in str(row.get("secondary_languages", "")).split(";") if s.strip()]

        creator = Creator(
            id=str(row.get("id", "")),
            name=str(row.get("name", "")),
            email=str(row.get("email", "")),
            phone=str(row.get("phone", "")) if pd.notna(row.get("phone")) else None,
            primary_niche=str(row.get("primary_niche", "")),
            secondary_niches=secondary_niches,
            primary_language=str(row.get("primary_language", "")),
            secondary_languages=secondary_languages,
            platforms=platforms,
            content_quality_score=float(row.get("content_quality_score", 0)),
            profile_completeness=float(row.get("profile_completeness", 0)),
            avg_engagement_rate=float(row.get("avg_engagement_rate", 0)),
            status=CreatorStatus(str(row.get("status", "pending"))),
            total_campaigns_completed=int(row.get("total_campaigns_completed", 0)),
            total_earnings=float(row.get("total_earnings", 0)),
            notes=str(row.get("notes", "")) if pd.notna(row.get("notes")) else None,
        )
        creators.append(creator)
    return creators


def export_campaigns_to_csv(campaigns: list[Campaign]) -> str:
    rows = []
    for c in campaigns:
        rows.append({
            "id": c.id,
            "title": c.title,
            "brand": c.brand,
            "description": c.description,
            "budget": c.budget,
            "deadline": c.deadline,
            "status": c.status,
            "target_niches": "; ".join(c.target_niches),
            "target_languages": "; ".join(c.target_languages),
            "requirements": "; ".join(c.requirements),
            "assigned_creators": "; ".join(c.assigned_creators),
            "created_at": c.created_at,
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def import_campaigns_from_csv(csv_content: str) -> list[Campaign]:
    df = pd.read_csv(StringIO(csv_content))
    campaigns = []
    for _, row in df.iterrows():
        campaign = Campaign(
            id=str(row.get("id", "")),
            title=str(row.get("title", "")),
            brand=str(row.get("brand", "")),
            description=str(row.get("description", "")),
            budget=float(row.get("budget", 0)),
            deadline=str(row.get("deadline", "")),
            status=str(row.get("status", "active")),
            target_niches=[s.strip() for s in str(row.get("target_niches", "")).split(";") if s.strip()],
            target_languages=[s.strip() for s in str(row.get("target_languages", "")).split(";") if s.strip()],
            requirements=[s.strip() for s in str(row.get("requirements", "")).split(";") if s.strip()],
            assigned_creators=[s.strip() for s in str(row.get("assigned_creators", "")).split(";") if s.strip()],
            created_at=str(row.get("created_at", "")),
        )
        campaigns.append(campaign)
    return campaigns


def export_payments_to_csv(payments: list[Payment]) -> str:
    rows = []
    for p in payments:
        rows.append({
            "id": p.id,
            "creator_id": p.creator_id,
            "campaign_id": p.campaign_id,
            "amount": p.amount,
            "status": p.status,
            "due_date": p.due_date,
            "notes": p.notes or "",
        })
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def import_payments_from_csv(csv_content: str) -> list[Payment]:
    df = pd.read_csv(StringIO(csv_content))
    payments = []
    for _, row in df.iterrows():
        payment = Payment(
            id=str(row.get("id", "")),
            creator_id=str(row.get("creator_id", "")),
            campaign_id=str(row.get("campaign_id", "")),
            amount=float(row.get("amount", 0)),
            status=str(row.get("status", "pending")),
            due_date=str(row.get("due_date", "")),
            notes=str(row.get("notes", "")) if pd.notna(row.get("notes")) else None,
        )
        payments.append(payment)
    return payments
