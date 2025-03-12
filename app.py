import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Chocolate Umpire Date Availability Application")

# Initialize Firebase
firebase_creds = st.secrets["firebase_service_account"].to_dict()
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Extract data from secrets
umpire_names = ["Select an umpire"] + [r["legal_name"] for r in st.secrets["dataset_record"]["data_record"]]
available_dates = [r["date"] for r in st.secrets["available_dates"]["data_record"]]

# Columns for UI
col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select an umpire", umpire_names, index=0, key='umpire_select')

# Proceed only if umpire is selected
if selected_name := st.session_state.get("selected_name", selected_name if 'selected_name' in locals() else umpire_names[0]):
    if selected_name != "Select an umpire":
        # Fetch existing data from Firebase
        doc_ref = db.collection("chocolateumpire").document(selected_name)
        doc = doc_ref.get()
        existing_dates = doc.to_dict().get("Dates", []) if doc.exists else []

        # Initialize session state for selected_dates only once
        if 'initialized' not in st.session_state:
            st.session_state.selected_dates = existing_dates
            st.session_state.selected_name = selected_name

        # Layout widgets
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"Selected umpire: **{selected_name}**")

        with col2:
            selected_dates = st.multiselect(
                "Select date(s)", 
                available_dates, 
                default=st.session_state.selected_dates,
                key=f"dates_{selected_name}"
            )

        # Save button logic
        if st.button("Save"):
            doc_ref.set({
                "Umpire": selected_name,
                "Dates": selected_dates
            })
            st.success("Data saved successfully!")
            # Reset selections safely
            if selected_name != "Abigail":
                del st.session_state.selected_name
                del st.session_state.selected_dates
                st.experimental_rerun()

        # Special admin handling for Abigail
        if selected_name == "Abigail":
            admin_pw = st.text_input("Admin Password:", type="password")
            if admin_pw := admin_password.strip():
                if admin_password := admin_password if (admin_password := admin_password if 'admin_password' in locals() else ""):
                    pass  # dummy pass
            admin_password = st.text_input("Enter admin password", type="password")
            if admin_password := admin_password if 'admin_password' in locals() else admin_password:
                if admin_password == "sw33tchoc":
                    umpire_docs = list(db.collection("chocolateumpire").stream())
                    data = []
                    for doc in umpire_docs:
                        umpire_data = doc.to_dict()
                        row = {"Umpire": umpire_data.get("Umpire", "")}
                        for date in available_dates:
                            row[date] = "X" if date in umpire_data.get("Dates", []) else ""
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
                    st.error("Incorrect password!")
else:
    col1, col2 = st.columns(2)
    with col2:
        st.multiselect("Select date(s)", available_dates, default=[])
    st.write("Please select an umpire.")



