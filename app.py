import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Chocolate Umpire Date Availability Application")

# Firebase initialization
firebase_creds = st.secrets["firebase_service_account"].to_dict()
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Load umpire names and dates from secrets
umpire_names = ["Select an umpire"] + [r["legal_name"] for r in st.secrets["dataset_record"]["data_record"]]
available_dates = [r["date"] for r in st.secrets["available_dates"]["data_record"]]

# UI Layout
col1, col2 = st.columns(2)

# Select umpire
with col1:
    selected_name = st.selectbox("Select an umpire", umpire_names, key="umpire_selector")

# Proceed if a valid umpire is selected
if selected_name != "Select an umpire":
    doc_ref = db.collection("chocolateumpire").document(selected_name)
    doc = doc_ref.get()

    # Get existing dates from Firestore
    existing_dates = doc.to_dict().get("Dates", []) if doc.exists else []

    # Multiselect for dates with existing dates pre-selected
    with col2:
        selected_dates = st.multiselect(
            "Select date(s)", 
            available_dates, 
            default=existing_dates, 
            key=f"dates_{selected_name}"
        )

    # Button to save selections
    if st.button("Save"):
        doc_ref = db.collection("chocolateumpire").document(selected_name)
        doc_ref.set({"Umpire": selected_name, "Dates": selected_dates})
        st.success("Data saved successfully!")

        # Clear the selection after saving, except for Abigail
        if selected_name != "Abigail":
            # Clear the widget values indirectly via rerun:
            st.session_state[f"dates_{selected_name}"] = []
            st.session_state["selected_name"] = "Select an umpire"
            st.experimental_rerun()

    # Admin functionality if Abigail selected
    if selected_name == "Abigail":
        admin_password = st.text_input("Enter admin password:", type="password", key="admin_password")

        if admin_password := admin_password.strip():
            if admin_password == "sw33tchoc":
                umpire_docs = list(db.collection("chocolateumpire").stream())
                data = []
                for ump_doc in umpire_docs:
                    umpire_data = ump_doc.to_dict()
                    row = {"Umpire": umpire_data.get("Umpire", "")}
                    umpire_dates = umpire_data.get("Dates", [])
                    for date in available_dates:
                        row[date] = "X" if date in umpire_dates else ""
                    data.append(row)
                df = pd.DataFrame(data)

                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Availability")
                buffer.seek(0)

                st.download_button(
                    "Download Umpire Availability",
                    data=buffer,
                    file_name="umpire_availability.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
else:
    # If no umpire selected
    with col2:
        st.multiselect("Select date(s)", available_dates)
    st.write("Please select an umpire.")



