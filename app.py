import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

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

# Create two columns for layout.
col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select an umpire", umpire_names, index=0)

# Only show the date selection if a valid umpire is selected.
if selected_name != "Select an umpire":
    # Use the selected umpire's name as the document ID.
    doc_ref = db.collection("chocolateumpire").document(selected_name)
    doc = doc_ref.get()
    
    # If the document exists, get the previously selected dates.
    if doc.exists:
        existing_dates = doc.to_dict().get("Dates", [])
    else:
        existing_dates = []

    with col2:
        # Use multiselect with default values if they exist.
        selected_dates = st.multiselect("Select date(s)", available_dates, default=existing_dates)

    # When the user clicks Save, update the Firebase document.
    if st.button("Save"):
        # Set the document with the umpire name and selected dates.
        doc_ref.set({
            "Umpire": selected_name,
            "Dates": selected_dates
        })
        st.success("Data saved successfully!")
else:
    with col2:
        # If no umpire is selected, show an empty multiselect.
        st.multiselect("Select date(s)", available_dates, default=[])
    st.write("Please select an umpire.")

