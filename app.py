import streamlit as st

# Extract umpire names and add a placeholder as the first option.
umpire_names = ["Select an umpire"] + [record["legal_name"] for record in st.secrets["dataset_record"]["data_record"]]

# Extract available dates from secrets.
available_dates = [record["date"] for record in st.secrets["available_dates"]["data_record"]]

# Create two columns for layout.
col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select an umpire", umpire_names, index=0)

with col2:
    selected_dates = st.multiselect("Select date(s)", available_dates)

# Display the selections.
if selected_name == "Select an umpire":
    st.write("Please select an umpire.")
else:
    st.write(f"You selected: **{selected_name}**")

if selected_dates:
    st.write(f"Selected date(s): {', '.join(selected_dates)}")
else:
    st.write("No date selected.")
