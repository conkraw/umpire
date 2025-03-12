import streamlit as st

# Extract umpire names from the secrets file.
names = [record["legal_name"] for record in st.secrets["dataset_record"]["data_record"]]

# Extract available dates from secrets by iterating over the data_record list.
available_dates = [record["date"] for record in st.secrets["available_dates"]["data_record"]]

# Create two columns for layout.
col1, col2 = st.columns(2)

with col1:
    selected_name = st.selectbox("Select an umpire", names)

with col2:
    selected_date = st.selectbox("Select a date", available_dates)

# Display the selected values.
st.write(f"You selected: **{selected_name}** to umpire on **{selected_date}**")
