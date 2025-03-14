import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
from io import BytesIO
from xlsxwriter.utility import xl_col_to_name

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
            
                        # Create header format.
                        header_format = workbook.add_format({
                            'bold': True,
                            'align': 'center',
                            'valign': 'vcenter',
                            'bg_color': '#D7E4BC',  # light green background
                            'border': 1
                        })
                        # Create a default cell format that includes center alignment, border, and text wrap.
                        cell_format = workbook.add_format({
                            'align': 'center',
                            'valign': 'vcenter',
                            'border': 1,
                            'text_wrap': True
                        })
            
                        # Apply header formatting and set the column widths (applied once).
                        for i, col in enumerate(df.columns):
                            worksheet.write(0, i, col, header_format)
                            worksheet.set_column(i, i, 35, cell_format)
            
                        # Determine the data range.
                        # Note: The header is row 0; data rows start at row 1.
                        num_rows = len(df)  # data rows count (not including header)
                        num_cols = len(df.columns)

                        # Define format for cells containing "X".
                        x_format = workbook.add_format({
                            'bg_color': '#FFC7CE',  # light red background for "X"
                            'border': 1,
                            'align': 'center',
                            'valign': 'vcenter'
                        })
                        
                        # Apply the "X" rule after the alternating rules so it overrides them.
                        worksheet.conditional_format(1, 0, num_rows, num_cols - 1, {
                            'type': 'formula',
                            'criteria': '=TRIM(UPPER(A2))="X"',
                            'format': x_format
                        })
            
            
                        # Define alternating row formats.
                        even_format = workbook.add_format({
                            'bg_color': '#F2F2F2',  # light gray background for even rows
                            'border': 1,
                            'align': 'center',
                            'valign': 'vcenter'
                        })
                        odd_format = workbook.add_format({
                            'border': 1,
                            'align': 'center',
                            'valign': 'vcenter'
                        })
                        
                        # Apply alternating row conditional formatting.
                        worksheet.conditional_format(1, 0, num_rows, num_cols - 1, {
                            'type': 'formula',
                            'criteria': '=MOD(ROW(),2)=0',
                            'format': even_format
                        })
                        worksheet.conditional_format(1, 0, num_rows, num_cols - 1, {
                            'type': 'formula',
                            'criteria': '=MOD(ROW(),2)=1',
                            'format': odd_format
                        })
                        

                        # Freeze the top row and first column.
                        worksheet.freeze_panes(1, 1)
            
                        # Enable an auto filter on the header row.
                        worksheet.autofilter(0, 0, num_rows, num_cols - 1)
            
                        # Page setup: landscape and fit columns to one page width.
                        worksheet.set_landscape()
                        worksheet.fit_to_pages(1, 0)
            
                    buffer.seek(0)
                    st.download_button(label="Download Excel File",data=buffer,file_name="umpire_availability.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


                    uploaded_file = st.file_uploader("Upload your umpire availability Excel file", type=["xlsx"])
                    if uploaded_file is not None:
                        # Read the uploaded file.
                        df = pd.read_excel(uploaded_file)
                        # Replace NaN/INF with empty strings.
                        df = df.fillna('')
                        
                        if "Umpire" not in df.columns:
                            st.error("The uploaded file must contain a column named 'Umpire'.")
                        else:
                            # Group non-Umpire columns by field (location).
                            # Expect headers in the format: "MM-DD-YYYY at TIME at LOCATION"
                            location_to_columns = {}
                            for col in df.columns:
                                if col == "Umpire":
                                    continue
                                parts = col.split(" at ")
                                if len(parts) >= 3:
                                    date_str = parts[0]      # e.g. "03-30-2025"
                                    time_str = parts[1]      # e.g. "1pm"
                                    location = parts[2]      # e.g. "Gelder"
                                    try:
                                        dt = datetime.strptime(date_str, "%m-%d-%Y")
                                        # Simplify date to "M-D" (e.g. "3-30")
                                        simple_date = f"{dt.month}-{dt.day}"
                                    except Exception as e:
                                        simple_date = date_str
                                    if location not in location_to_columns:
                                        location_to_columns[location] = []
                                    # Store the original column name and the simplified date.
                                    location_to_columns[location].append((col, simple_date))
                                else:
                                    # If header doesn't match, group under "Other"
                                    if "Other" not in location_to_columns:
                                        location_to_columns["Other"] = []
                                    location_to_columns["Other"].append((col, col))
                            
                            # Create an Excel file with one sheet that contains tables for each field.
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                                workbook = writer.book
                                worksheet = workbook.add_worksheet("Field Assignments")
                                
                                # Define common formats.
                                title_format = workbook.add_format({
                                    'bold': True,
                                    'font_size': 14
                                })
                                header_format = workbook.add_format({
                                    'bold': True,
                                    'bg_color': '#D7E4BC',  # light green
                                    'border': 1,
                                    'align': 'center',
                                    'valign': 'vcenter'
                                })
                                cell_format = workbook.add_format({
                                    'border': 1,
                                    'align': 'center',
                                    'valign': 'vcenter'
                                })
                                
                                current_row = 0  # starting row in output sheet
                                
                                # For each field, write a table if there is at least one assignment.
                                for location, cols in location_to_columns.items():
                                    # Create a temporary DataFrame for this field.
                                    df_field = df[["Umpire"] + [col for (col, _) in cols]].copy()
                                    
                                    # Filter rows: keep only rows with at least one "X" in any of these columns.
                                    def has_assignment(row):
                                        for col, _ in cols:
                                            if str(row[col]).strip().upper() == "X":
                                                return True
                                        return False
                                    df_field = df_field[df_field.apply(has_assignment, axis=1)]
                                    
                                    # Skip if no assignments for this field.
                                    if df_field.empty:
                                        continue
                                    
                                    # Write the field title.
                                    worksheet.write(current_row, 0, f"Field: {location}", title_format)
                                    current_row += 1
                                    
                                    # Write header row.
                                    headers = ["Umpire"] + [simple_date for (_, simple_date) in cols]
                                    header_row = current_row
                                    for col_index, header in enumerate(headers):
                                        worksheet.write(header_row, col_index, header, header_format)
                                    current_row += 1
                                    
                                    # Data rows start here.
                                    data_start_row = current_row
                                    for _, row in df_field.iterrows():
                                        worksheet.write(current_row, 0, row["Umpire"], cell_format)
                                        for j, (orig_col, _) in enumerate(cols, start=1):
                                            value = row[orig_col]
                                            worksheet.write(current_row, j, value, cell_format)
                                        current_row += 1
                                    data_end_row = current_row - 1  # last data row index
                                    
                                    # Write summary row with COUNTIF formulas.
                                    summary_row = current_row
                                    worksheet.write(summary_row, 0, "Total", cell_format)
                                    for j in range(1, len(headers)):
                                        # Convert column index j to Excel column letter.
                                        col_letter = xl_col_to_name(j)
                                        # Excel rows are 1-indexed. Data rows are from (data_start_row+1) to (data_end_row+1).
                                        start_excel = data_start_row + 1
                                        end_excel = data_end_row + 1
                                        formula = f'=COUNTIF({col_letter}{start_excel}:{col_letter}{end_excel}, "X")'
                                        worksheet.write_formula(summary_row, j, formula, cell_format)
                                    current_row += 1
                                    
                                    # Leave one blank row between tables.
                                    current_row += 1
                                
                                # Optional: Set column widths for readability.
                                worksheet.set_column(0, 0, 20)  # Umpire column
                                max_cols = max([len(cols) for cols in location_to_columns.values()], default=0)
                                for i in range(1, max_cols + 1):
                                    worksheet.set_column(i, i, 12)
                                
                                writer.close()
                            output.seek(0)
                            
                            st.download_button(
                                label="Download Field Assignments Report",
                                data=output,
                                file_name="Field_Assignments_Report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
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
