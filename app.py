import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Chocolate Umpire Date Availability Application")

# Initialize Firebase connection (assuming st.secrets exists)
firebase_creds = st.secrets["firebase_service_account"].to_dict()
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Extract umpire names and available dates.
umpire_names = ["Select an umpire"] + [record["legal_name"] for record in st.secrets["dataset_record"]["data_record"]]
available_dates = [record["date"] for record in st.secrets["available_dates"]["data_record"]]

# Initialize session state for navigation if not already set.
if 'page' not in st.session_state:
    st.session_state.page = 'data_entry'

# Define the main data entry screen.
def data_entry():
    col1, col2 = st.columns(2)
    
    with col1:
        selected_name = st.selectbox("Select an umpire", umpire_names, index=0)
    
    # Only show rest of UI if a valid umpire is selected.
    if selected_name != "Select an umpire":
        # Use the selected umpire's name as the document ID.
        doc_ref = db.collection("chocolateumpire").document(selected_name)
        doc = doc_ref.get()
        existing_dates = doc.to_dict().get("Dates", []) if doc.exists else []
    
        with col2:
            selected_dates = st.multiselect("Select date(s)", available_dates, default=existing_dates)
        
        if selected_name != "Abigail":
            if st.button("Save"):
                # Save the user's data.
                doc_ref.set({
                    "Umpire": selected_name,
                    "Dates": selected_dates
                })
                st.success("Data saved successfully!")
                st.session_state.page = 'confirmation'
                st.rerun()
        else:
            # For Abigail, display the admin password input.
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
                        # For each available date, mark "X" if the umpire selected it.
                        for date in available_dates:
                            row[date] = "X" if date in umpire_dates else ""
                        data.append(row)
                    df = pd.DataFrame(data)
                    
                    # Write DataFrame to an Excel file in memory.
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name="Availability")
                        workbook  = writer.book
                        worksheet = writer.sheets["Availability"]
        
                        # Create a format for headers: bold, centered, with a background color, and a border.
                        header_format = workbook.add_format({
                            'bold': True,
                            'align': 'center',
                            'valign': 'vcenter',
                            'bg_color': '#D7E4BC',  # light green background; change as needed
                            'border': 1
                        })
                        # Create a default format for all cells: center aligned.
                        cell_format = workbook.add_format({
                            'align': 'center',
                            'valign': 'vcenter'
                        })
        
                        # Set the column width to 35 and apply the default cell format.
                        for i, col in enumerate(df.columns):
                            worksheet.set_column(i, i, 35, cell_format)
                            # Overwrite the header cell with header_format if there's content.
                            if col:
                                worksheet.write(0, i, col, header_format)
                            else:
                                worksheet.write(0, i, col, cell_format)
        
                        # Determine the data range for conditional formatting.
                        # Data rows start at row 1 (since row 0 is the header) through row index len(df)
                        num_rows = len(df)
                        num_cols = len(df.columns)
        
                        # Define a format for even rows with a light gray background and border.
                        even_format = workbook.add_format({
                            'bg_color': '#F2F2F2',  # light gray background; adjust as needed
                            'border': 1,
                            'align': 'center',
                            'valign': 'vcenter'
                        })
                        # Define a format for odd rows with just the border.
                        odd_format = workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'valign': 'vcenter'
                        })
        
                        # Apply conditional formatting to even rows (Excel rows with even numbers)
                        worksheet.conditional_format(1, 0, num_rows, num_cols - 1, {
                            'type': 'formula',
                            'criteria': '=MOD(ROW(),2)=0',
                            'format': even_format
                        })
                        # Apply conditional formatting to odd rows (Excel rows with odd numbers)
                        worksheet.conditional_format(1, 0, num_rows, num_cols - 1, {
                            'type': 'formula',
                            'criteria': '=MOD(ROW(),2)=1',
                            'format': odd_format
                        })
        
                    buffer.seek(0)
        
                    st.download_button(
                        label="Download Excel File",
                        data=buffer,
                        file_name="umpire_availability.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                        # [Your Excel report generation code goes here]
                        # For brevity, that part is omitted in this snippet.
                else:
                    st.error("Incorrect password.")
    else:
        with col2:
            st.multiselect("Select date(s)", available_dates, default=[])
        st.write("Please select an umpire.")

# Define the confirmation screen.
def confirmation():
    st.header("Review Your Submission")
    st.write("Your data has been saved. If everything looks correct, press 'Save & End Session'.")
    # Provide an option to go back if the user needs to change something.
    if st.button("Go Back"):
        st.session_state.page = 'data_entry'
        st.rerun()
    # Provide an option to finish the session.
    if st.button("Save & End Session"):
        st.session_state.page = 'final'
        st.rerun()

# Define the final screen.
def final():
    st.header("Session Ended")
    st.write("All results saved, please close your browser.")
    # Optionally, disable further inputs by not rendering anything else.

# Render the appropriate page.
if st.session_state.page == 'data_entry':
    data_entry()
elif st.session_state.page == 'confirmation':
    confirmation()
elif st.session_state.page == 'final':
    final()
