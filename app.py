import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Chocolate Umpire Date Availability Application")

# Initialize Firebase connection
firebase_creds = st.secrets["firebase_service_account"].to_dict()
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Extract umpire names and dates from secrets
umpire_names = ["Select an umpire"] + [r["legal_name"] for r in st.secrets["dataset_record"]["data_record"]]
available_dates = [r["date"] for r in st.secrets["available_dates"]["data_record"]]

# Set default state for widgets
if "selected_name" not in st.session_state:
    st.session_state.selected_name = "Select an umpire"
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []

# Columns layout
col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select an umpire", umpire_names, key="selected_name")

if selected_name != "Select an umpire":
    doc_ref = db.collection("chocolateumpire").document(selected_name)
    doc = doc_ref.get()
    existing_dates = doc.to_dict().get("Dates", []) if doc.exists else []

    with col2:
        selected_dates = st.multiselect("Select date(s)", available_dates, default=existing_dates)

    # Save data button
    if st.button("Save"):
        doc_ref.set({"Umpire": selected_name, "Dates": selected_dates})
        st.success("Data saved successfully!")
        # Clear selections after save for non-admin users
        if selected_name != "Abigail":
            st.session_state.selected_name = "Select an umpire"
            st.session_state.selected_dates = []
            st.experimental_rerun()

    # Admin password and Excel report functionality for Abigail
    if selected_name == "Abigail":
        admin_password = st.text_input("Enter admin password", type="password")
        if admin_password:
            if admin_password == "sw33tchoc":
                umpire_docs = list(db.collection("chocolateumpire").stream())
                data = []
                for doc in umpire_docs:
                    umpire_data = doc.to_dict()
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
    with col2:
        st.multiselect("Select date(s)", available_dates, default=[])
    st.write("Please select an umpire.")


