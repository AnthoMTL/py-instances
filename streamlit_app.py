import streamlit as st

st.title('Atkins Data Crunching App')

# Full example of using the with notation
st.header('1. Project creation')
# st.subheader('Coffee machine')

with st.form('my_form'):
#    st.write('**Order your coffee**')
    
    # Input widgets
    project_name = st.text_input('Enter your username:', max_chars=10)
    vm_size = st.selectbox('Choose your VM size', ['Small', 'Medium', 'Large'])
#    coffee_roast_val = st.selectbox('Coffee roast', ['Light', 'Medium', 'Dark'])
#    brewing_val = st.selectbox('Brewing method', ['Aeropress', 'Drip', 'French press', 'Moka pot', 'Siphon'])
#    serving_type_val = st.selectbox('Serving format', ['Hot', 'Iced', 'Frappe'])
    vm_numbers = st.select_slider('How many VMs do you need', ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'])
#    owncup_val = st.checkbox('Bring own cup')
    
    # Every form must have a submit button
    submitted = st.form_submit_button('Submit')

""" if submitted:
    st.markdown(f'''
        ☕ You have ordered:
        - Coffee bean: `{coffee_bean_val}`
        - Coffee roast: `{coffee_roast_val}`
        - Brewing: `{brewing_val}`
        - Serving type: `{serving_type_val}`
        - Milk: `{milk_val}`
        - Bring own cup: `{owncup_val}`
        ''')
else:
    st.write('☝️ Place your order!') """


""" # Short example of using an object notation
st.header('2. Example of object notation')

form = st.form('my_form_2')
selected_val = form.slider('Select a value')
form.form_submit_button('Submit')

st.write('Selected value: ', selected_val) """