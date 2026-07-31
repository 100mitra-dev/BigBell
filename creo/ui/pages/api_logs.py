import json

import streamlit as st


def format_preview(text) -> tuple[str, str]:
    """Pretty-print a response if it is a JSON blob (optionally fenced)."""
    if text is None:
        return "", ""
    if not isinstance(text, str):
        try:
            return json.dumps(text, indent=2, ensure_ascii=False), "json"
        except (TypeError, ValueError):
            return str(text), ""
    if not text:
        return "", ""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.dumps(json.loads(cleaned), indent=2, ensure_ascii=False), "json"
    except (json.JSONDecodeError, ValueError, TypeError):
        return text, ""


st.title("API Debug Logs")
st.caption("Detailed logs of LLM API calls")

logs = st.session_state.get("api_logs", [])

if not logs:
    st.info("No API calls logged yet. Enable debug logging in Settings and make an AI request.")
else:
    c1, c2 = st.columns([6, 1])
    with c2:
        if st.button("Clear all", icon=":material/delete_sweep:", type="primary", width="stretch"):
            from creo.utils.debug_logging import clear_logs
            clear_logs()
            st.rerun()

    for i, log in enumerate(reversed(logs)):
        icon = ":material/check_circle:" if log.get("success") else ":material/error:"
        color = "green" if log.get("success") else "red"
        label = "Success" if log.get("success") else "Failed"

        with st.container(border=True):
            cols = st.columns([1, 2, 2, 1, 1])
            with cols[0]:
                st.markdown(f"**{log.get('provider', '?')}**")
            with cols[1]:
                st.markdown(f"`{log.get('model', '?')}`")
            with cols[2]:
                st.caption(log.get("timestamp", ""))
            with cols[3]:
                st.badge(label, icon=icon, color=color)
            with cols[4]:
                st.caption(f"{log.get('duration_ms', 0)}ms")

            with st.expander("Request / Response", icon=":material/code:"):
                req_tab, res_tab, err_tab = st.tabs(["Request", "Response", "Error"])
                with req_tab:
                    st.code(log.get("request_preview", ""), wrap_lines=True)
                with res_tab:
                    pretty, lang = format_preview(log.get("response_preview", ""))
                    st.code(pretty, language=lang or None, wrap_lines=True)
                with err_tab:
                    err = log.get("error")
                    if err:
                        st.code(err, wrap_lines=True)
                    else:
                        st.caption("No error")
