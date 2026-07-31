import streamlit as st


PLATFORM_META = {
    "youtube": {
        "label": "subscribers",
        "url": lambda h: f"https://www.youtube.com/{h}",
        "icon": ":material/play_circle:",
    },
    "instagram": {
        "label": "followers",
        "url": lambda h: f"https://www.instagram.com/{h}",
        "icon": ":material/photo_camera:",
    },
    "twitter": {
        "label": "followers",
        "url": lambda h: f"https://x.com/{h}",
        "icon": ":material/tag:",
    },
    "twitch": {
        "label": "followers",
        "url": lambda h: f"https://www.twitch.tv/{h}",
        "icon": ":material/videocam:",
    },
    "tiktok": {
        "label": "followers",
        "url": lambda h: f"https://www.tiktok.com/@{h}",
        "icon": ":material/music_video:",
    },
    "linkedin": {
        "label": "followers",
        "url": lambda h: f"https://www.linkedin.com/in/{h}",
        "icon": ":material/work:",
    },
    "facebook": {
        "label": "followers",
        "url": lambda h: f"https://www.facebook.com/{h}",
        "icon": ":material/forum:",
    },
    "github": {
        "label": "followers",
        "url": lambda h: f"https://github.com/{h}",
        "icon": ":material/code:",
    },
    "snapchat": {
        "label": "followers",
        "url": lambda h: f"https://www.snapchat.com/add/{h}",
        "icon": ":material/ghost:",
    },
    "threads": {
        "label": "followers",
        "url": lambda h: f"https://www.threads.net/@{h}",
        "icon": ":material/forum:",
    },
    "pinterest": {
        "label": "followers",
        "url": lambda h: f"https://www.pinterest.com/{h}",
        "icon": ":material/image:",
    },
}


def platform_url(platform: str, handle: str) -> str | None:
    meta = PLATFORM_META.get((platform or "").lower())
    if not meta:
        return None
    clean = (handle or "").strip().lstrip("@").replace(" ", "")
    if not clean:
        return None
    return meta["url"](clean)


def platform_follower_label(platform: str) -> str:
    return PLATFORM_META.get((platform or "").lower(), {}).get("label", "followers")


def platform_icon(platform: str) -> str:
    return PLATFORM_META.get((platform or "").lower(), {}).get("icon", ":material/link:")


def handle_display(handle: str) -> str:
    return handle.strip() if handle.startswith("@") else f"@{handle}"


def platform_link_markdown(platform: str, handle: str, followers: int) -> str:
    display = handle_display(handle)
    url = platform_url(platform, handle)
    link = f"[{display}]({url})" if url else f"`{display}`"
    return (
        f"{platform_icon(platform)} **{platform.title()}** {link} "
        f"\u00b7 {int(followers or 0):,} {platform_follower_label(platform)}"
    )


def render_platform_grid(platforms: dict):
    """Render each platform as a small bordered card with a clickable handle.

    `platforms` maps platform name -> object with `.handle`, `.followers`, `.verified`
    (or a dict with the same keys).
    """
    if not platforms:
        return
    items = list(platforms.items())
    for start in range(0, len(items), 4):
        cols = st.columns(len(items[start : start + 4]))
        for col, (name, info) in zip(cols, items[start : start + 4]):
            handle = getattr(info, "handle", None)
            followers = getattr(info, "followers", 0)
            verified = getattr(info, "verified", False)
            if isinstance(info, dict):
                handle = info.get("handle", "")
                followers = info.get("followers", 0)
                verified = info.get("verified", False)
            with col:
                st.markdown(f"{platform_icon(name)} **{name.title()}**")
                url = platform_url(name, handle or "")
                display = handle_display(handle or "")
                st.markdown(f"[{display}]({url})" if url else f"`{display}`")
                st.caption(
                    f"{int(followers or 0):,} {platform_follower_label(name)}"
                    + (" \u00b7 :material/verified:" if verified else "")
                )
