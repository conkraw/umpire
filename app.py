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
umpire_names = ["Select an umpire"] + [record["legal_name"] for record in st.secrets["dataset_record"]["data_record"]]
available_dates = [record["date"] for record in st.secrets["available_dates"]["data_record"]]

# Streamlit session state initialization
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []

# Columns layout
col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select an umpire", umpire_names, index=0)

# Firestore interaction
if selected_name != "Select an umpire":
    doc_ref = db.collection("chocolateumpire").document(selected_name)
    doc = doc_ref.get()

    # Load existing dates if present
    if doc.exists:
        existing_dates = doc.to_dict().get("Dates", [])
    else:
        existing_dates = []

    # Initialize multiselect values only if umpire changes
    if "last_selected_umpire" not in st.session_state or st.session_state.last_umpire != selected_name:
        st.session_state.selected_dates = existing_dates

    # Columns for layout
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Selected umpire: **{selected_name}**")

    with col2:
        selected_dates = st.multiselect(
            "Select date(s)", available_dates, default=existing_dates, key="selected_dates"
        )

    # Save button
    if st.button("Save"):
        doc_ref.set({"Umpire": selected_name, "Dates": selected_dates})
        st.success("Data saved successfully!")

        # Clear selections (except Abigail)
        if selected_name != "Abigail":
            st.session_state.selected_dates = []
            st.session_state.selected_name = "Select an umpire"
            st.experimental_rerun()

    # Abigail's admin Excel generation
    if selected_name == "Abigail":
        password = st.text_input("Enter admin password:", type="password")
        if password:
            if password == "sw33tchoc":
                umpire_docs = list(db.collection("chocolateumpire").stream())
                data = []
                for ump_doc in umpire_docs:
                    umpire_data = umpire_docs = umpire_docs = [doc.to_dict() for doc in umpire_docs]
                # create DataFrame
                records = []
                for umpire_record in umpire_docs:
                    umpire_data = umpire_record.to_dict()
                    row = {"Umpire": umpire_data.get("Umpire", "")}
                    dates_chosen = umpire_data.get("Dates", [])
                    for date in available_dates:
                        row[date] = "X" if date in dates_chosen else ""
                    data.append(row)

                df = pd.DataFrame(data)

                # Save to Excel in memory
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Availability")
                buffer = buffer.getvalue()

                st.download_button(
                    label="Download Umpire Availability",
                    data=buffer,
                    file_name="umpire_availability.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.error("Incorrect password!")

else:
    st.write("Please select an umpire.")



