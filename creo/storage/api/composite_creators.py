import hashlib
import logging
from typing import Optional

from creo.storage.base import CreatorRepository
from creo.models import Creator

logger = logging.getLogger(__name__)


class CompositeCreatorRepository(CreatorRepository):
    """Merges creators from multiple sources into a unified, deduplicated pool.

    Implements the "Centralized Data Pipeline" stage: profiles fetched from
    Meta Marketplace, Modash, Instagram, and the local JSON store are
    deduplicated by a content fingerprint (name + primary platform handle)
    and merged into unified creator records. The local store has priority on
    writeable fields; external sources fill in gaps.
    """

    def __init__(self, sources: list[CreatorRepository] | None = None):
        from creo.storage.json.creator_repo import JsonCreatorRepository
        self._sources: list[CreatorRepository] = sources if sources is not None else [
            JsonCreatorRepository(),
        ]

    @property
    def sources(self) -> list[CreatorRepository]:
        return self._sources

    @property
    def use_real_api(self) -> bool:
        return any(getattr(s, "use_real_api", False) for s in self._sources)

    def _fingerprint(self, creator: Creator) -> str:
        """Generate a deduplication key from name + primary handle."""
        handles = [p.handle.lower() for p in creator.platforms.values() if p.handle]
        handle_str = handles[0] if handles else ""
        raw = f"{creator.name.lower()}|{handle_str}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def list_all(self) -> list[Creator]:
        """List all creators from all sources, deduplicated and merged."""
        seen: dict[str, Creator] = {}
        for source in self._sources:
            for creator in source.list_all():
                fp = self._fingerprint(creator)
                if fp in seen:
                    # Merge the new profile into the existing one — external
                    # sources only fill fields that are empty on the local record.
                    existing = seen[fp]
                    for plat_name, plat_info in creator.platforms.items():
                        if plat_name not in existing.platforms:
                            existing.platforms[plat_name] = plat_info
                    if not existing.region and creator.region:
                        existing.region = creator.region
                    if existing.total_earnings == 0.0 and creator.total_earnings > 0:
                        existing.total_earnings = creator.total_earnings
                    if existing.total_campaigns_completed == 0 and creator.total_campaigns_completed > 0:
                        existing.total_campaigns_completed = creator.total_campaigns_completed
                else:
                    seen[fp] = creator
        result = list(seen.values())
        logger.debug(
            "CompositeCreatorRepository: %d creators from %d sources, %d after dedup",
            sum(len(s.list_all()) for s in self._sources),
            len(self._sources),
            len(result),
        )
        return result

    def get_by_id(self, creator_id: str) -> Optional[Creator]:
        for source in self._sources:
            creator = source.get_by_id(creator_id)
            if creator:
                return creator
        return None

    def add(self, creator: Creator):
        """Adds to the first writeable source (the local JSON repo)."""
        for source in self._sources:
            try:
                source.add(creator)
                return
            except NotImplementedError:
                continue
        raise NotImplementedError("No writeable source available to add creator")

    def delete(self, creator_id: str):
        """Deletes from the first writeable source."""
        for source in self._sources:
            try:
                source.delete(creator_id)
                return
            except NotImplementedError:
                continue
        raise NotImplementedError("No writeable source available to delete creator")

    def save_all(self, creators: list[Creator]):
        """Persists to the first writeable source."""
        for source in self._sources:
            try:
                source.save_all(creators)
                return
            except NotImplementedError:
                continue
        raise NotImplementedError("No writeable source available to save creators")

    def add_source(self, source: CreatorRepository):
        """Register an additional reader source for discovery."""
        if source not in self._sources:
            self._sources.append(source)

    def clear_sources(self):
        """Reset to only the local JSON store."""
        from creo.storage.json.creator_repo import JsonCreatorRepository
        self._sources = [JsonCreatorRepository()]
