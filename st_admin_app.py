# --- streamlit_app.py: minimal integration ---

# 1) Add to the frontend.pages import:
#
#     F_p0_ingestion_admin,
#
# 2) Add a new division to the global radio:
#
#     "Admin",
#
# 3) Extend PROJECT_MAP:
#
#     "Admin": ("Admin", "Ingestion"),
#
# 4) Add the sidebar branch:
#
#     elif st.session_state.page == "Admin":
#         st.subheader("Admin")
#         st.radio(
#             "Admin tool",
#             options=["Ingestion"],
#             key="subpage",
#             label_visibility="collapsed",
#         )
#
# 5) Add routing:
#
#     elif page == "Admin":
#         if sub == "Ingestion":
#             F_p0_ingestion_admin.show()
