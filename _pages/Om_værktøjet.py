import streamlit as st


st.markdown("# Page 2 ❄️")
st.sidebar.markdown("# Page 2 ❄️")
with st.form(key='my_form'):
    option = st.radio(
        'Select an option:',
        ('Option 1', 'Option 2'))

    if option == 'Option 1':
        input_text = st.text_input('Input text for Option 1')
    elif option == 'Option 2':
        input_text = st.text_input('Input text for Option 2')

    submit_button = st.form_submit_button(label='Submit')
    if submit_button:
        st.write(f'You selected {option} and entered {input_text}')
