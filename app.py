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

# Extract umpire names and add a placeholder as the first option.
umpire_names = ["Select an umpire"] + [record["legal_name"] for record in st.secrets["dataset_record"]["data_record"]]

# Extract available dates from secrets.
available_dates = [record["date"] for record in st.secrets["available_dates"]["data_record"]]

# Initialize session state for selected umpire and dates.
if "selected_name" not in st.session_state:
    st.session_state.selected_name = "Select an umpire"
if "selected_dates" not in st.session_state:
    st.session_state.selected_dates = []

# Create two columns for layout.
col1, col2 = st.columns(2)

with col1:
    # Use the session state value as default.
    selected_name = st.selectbox(
        "Select an umpire",
        umpire_names,
        index=umpire_names.index(st.session_state.selected_name),
        key="selected_name"
    )

if selected_name != "Select an umpire":
    # Use the selected umpire's name as the document ID.
    doc_ref = db.collection("chocolateumpire").document(selected_name)
    doc = doc_ref.get()
    
    # Retrieve previously selected dates from Firestore if available.
    if doc.exists:
        existing_dates = doc.to_dict().get("Dates", [])
        st.session_state.selected_dates = existing_dates  # update session state
    else:
        existing_dates = st.session_state.selected_dates

    with col2:
        selected_dates = st.multiselect(
            "Select date(s)",
            available_dates,
            default=existing_dates,
            key="selected_dates"
        )

    # Save button to update or create the document.
    if st.button("Save"):
        doc_ref.set({
            "Umpire": selected_name,
            "Dates": selected_dates
        })
        st.success("Data saved successfully!")
        
        # For umpires other than Abigail, clear the selections and rerun the app.
        if selected_name != "Abigail":
            st.session_state.selected_name = "Select an umpire"
            st.session_state.selected_dates = []
            st.experimental_rerun()
    
    # If the selected umpire is Abigail, show admin options.
    if selected_name == "Abigail":
        admin_password = st.text_input("Enter admin password to generate report", type="password")
        if admin_password:
            if admin_password == "sw33tchoc":
                st.success("Password correct. Generating Excel report...")
                # Retrieve all umpire documents.
                umpire_docs = list(db.collection("chocolateumpire").stream())
                data = []
                for doc in umpire_docs:
                    doc_data = doc.to_dict()
                    umpire = doc_data.get("Umpire", "")
                    umpire_dates = doc_data.get("Dates", [])
                    row = {"Umpire": umpire}
                    # Mark an "X" for each available date if selected.
                    for date in available_dates:
                        row[date] = "X" if date in umpire_dates else ""
                    data.append(row)
                df = pd.DataFrame(data)
                
                # Write DataFrame to an Excel file in memory.
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    df.to_excel(writer, index=False, sheet_name="Availability")
                buffer.seek(0)
                
                st.download_button(
                    label="Download Excel File",
                    data=buffer,
                    file_name="umpire_availability.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Incorrect password.")
else:
    with col2:
        st.multiselect("Select date(s)", available_dates, default=[])
    st.write("Please select an umpire.")


