import streamlit as st
import pandas as pd
import uuid

from creo.services.creator_service import CreatorService
from creo.services.campaign_service import CampaignService
from creo.services.follow_up_service import FollowUpNoteService
from creo.services.assignment_service import AssignmentService, STATUS_LABELS, STATUS_COLORS, AssignmentStatus
from creo.models import FollowUpNote
from creo.utils.helpers import days_until, today_str
import logging

logger = logging.getLogger(__name__)

if "cs" not in st.session_state:
    st.session_state.cs = CreatorService()
if "cams" not in st.session_state:
    st.session_state.cams = CampaignService()
if "fns" not in st.session_state:
    st.session_state.fns = FollowUpNoteService()
if "asvc" not in st.session_state:
    st.session_state.asvc = AssignmentService()
cs = st.session_state.cs
cams = st.session_state.cams
fns = st.session_state.fns
asvc = st.session_state.asvc

st.title("Follow-ups")
st.caption("Deadline tracking, deliverable management, and campaign notes")
try:

    active = cams.get_active_campaigns()
    overdue = sum(1 for c in active if days_until(c.deadline) < 0)
    due_soon = sum(1 for c in active if 0 <= days_until(c.deadline) <= 7)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active campaigns", len(active))
    col2.metric("Overdue", overdue, delta_color="inverse")
    col3.metric("Due soon (7 days)", due_soon)
    col4.metric("Total assignments", len(asvc.assignments))

    tab1, tab2, tab3 = st.tabs(["Campaign deadlines", "Pending deliverables", "Campaign notes"])

    with tab1:
        for campaign in sorted(active, key=lambda c: c.deadline):
            d = days_until(campaign.deadline)
            color, label = ("#E74C3C", "Overdue") if d < 0 else ("#F39C12", "Critical") if d <= 3 else ("#E67E22", "Due soon") if d <= 7 else ("#3498DB", "Approaching") if d <= 14 else ("#2ECC71", "On track")
            icon = ":material/error:" if d < 0 else ":material/schedule:" if d <= 7 else ":material/check_circle:"

            with st.container(border=True):
                st.markdown(f"**{campaign.title}** — *{campaign.brand}*")
                st.caption(f"Assigned: {len(campaign.assigned_creators)} creators | Budget: ₹{campaign.budget:,.0f}")

                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    st.markdown(f"**Deadline:** {campaign.deadline} ({d} days)")
                with c2:
                    st.markdown(f"{icon} **{label}**")
                with c3:
                    if st.button("Send reminder", key=f"fu_{campaign.id}", icon=":material/send:"):
                        names = [cs.get_by_id(cid).name for cid in campaign.assigned_creators if cs.get_by_id(cid)]
                        if names:
                            st.success(f":material/check: Reminder sent to {', '.join(names)}")
                        else:
                            st.info("No creators assigned to this campaign.")

    with tab2:
        wk_filter = st.selectbox("Workflow status", ["All", "matched", "invited", "accepted", "brief_sent", "content_received", "approved", "rejected"], label_visibility="collapsed")

        deliverables = []
        for campaign in active:
            for assignment in asvc.get_for_campaign(campaign.id):
                creator = cs.get_by_id(assignment.creator_id)
                if not creator:
                    continue
                if wk_filter != "All" and assignment.status.value != wk_filter:
                    continue
                d = days_until(campaign.deadline)
                deadline_status = "Overdue" if d < 0 else "Pending" if d <= 7 else "On track"
                wk_label = STATUS_LABELS.get(assignment.status, assignment.status.value)
                deliverables.append({
                    "Creator": creator.name,
                    "Campaign": campaign.title,
                    "Deadline": campaign.deadline,
                    "Days left": d,
                    "Deadline status": deadline_status,
                    "Workflow": wk_label,
                })

        if deliverables:
            df = pd.DataFrame(deliverables)
            st.dataframe(df, hide_index=True, column_config={
                "Days left": st.column_config.NumberColumn(width="small"),
            })

            c1, c2 = st.columns(2)
            with c1:
                if st.button("Send reminders to all overdue", type="primary", icon=":material/notifications:"):
                    overdue_items = [d for d in deliverables if d["Days left"] < 0]
                    if overdue_items:
                        st.success(f":material/check: Reminders sent to {len(overdue_items)} creators")
                    else:
                        st.info("No overdue deliverables found.")
            with c2:
                if active:
                    sample = active[0]
                    msg = f"Hi team! Reminder about the upcoming deadline for **{sample.title}** ({sample.brand}). Please submit deliverables by {sample.deadline}. Reach out if you need support!"
                    st.code(msg, language="text")
        else:
            st.info("No deliverables matching this filter.", icon=":material/inbox:")

    with tab3:
        st.markdown("**Add a note for any campaign**")

        with st.form("add_note_form"):
            c_opts = sorted([(c.id, f"{c.title} ({c.brand})") for c in active], key=lambda x: x[1])
            selected_camp = st.selectbox("Campaign", options=c_opts, format_func=lambda x: x[1])
            note_text = st.text_area("Note", placeholder="Enter follow-up note, update, or reminder...")
            submitted = st.form_submit_button("Save note", type="primary", icon=":material/save:")
            if submitted and selected_camp and note_text:
                fns.add(FollowUpNote(
                    id=str(uuid.uuid4()),
                    campaign_id=selected_camp[0],
                    note=note_text,
                    created_at=today_str(),
                ))
                st.success("Note saved")
                st.rerun()

        st.divider()

        all_notes = fns.notes
        if not all_notes:
            st.info("No notes yet. Add your first campaign note above.", icon=":material/edit_note:")
        else:
            for note in sorted(all_notes, key=lambda n: n.created_at, reverse=True):
                campaign = cams.get_by_id(note.campaign_id)
                camp_label = f"{campaign.title} ({campaign.brand})" if campaign else "Unknown"
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"**{camp_label}**  \n:material/calendar_today: {note.created_at}")
                        st.write(note.note)
                    with c2:
                        if st.button("Delete", key=f"del_note_{note.id}", icon=":material/delete:"):
                            fns.delete(note.id)
                            st.rerun()

except Exception as e:
    st.error(f"Something went wrong: {e}")
    logger.exception("Error in follow_ups")