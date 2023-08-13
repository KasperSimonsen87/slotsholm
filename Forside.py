import streamlit as st
import slotsholm_helperfunctions as sh
import slotsholm_gpt_functions as gpt

import sys
import io
import time

st.set_page_config(
    page_title="Forklæd-o-matic",
    page_icon="📄",
    layout="wide",
)

with st.sidebar:
    temperature = st.slider(
    'Select temperature',
    0.0, 1.0, 0.0, 0.01)


# Overskrift og hjælpetekst
st.title('📝💪Forklæd-o-matic ')
introhjaelpetekst = '''I UFM skal alle forklæder følge Slotsholmsmetoden.
                        Brug det nedenstående værktøj til at uploade et notat og få et udkast til forklæde. 
                        Udkastet kan du bruge som inspiration til det endelige forklæde.'''
st.markdown(introhjaelpetekst)

# Vælg formål med forklædet
formaal = st.radio("Skal modtageren efter endt læsning vide, beslutte eller handle? 👇",
                    ('Vide', 'Beslutte', 'Handle'),
                    horizontal=True,
                    )
if formaal == 'Beslutte':
    formaalstekst = st.text_input('Angiv kort hvad læseren skal beslutte')
elif formaal == 'Handle':
    formaalstekst = st.text_input('Angiv kort hvad læseren skal gøre')
elif formaal == 'Vide':
    formaalstekst = 'Punktet er alene til orientering.'

videre_proces_tekst = st.text_input('Beskriv kort - eventuelt i stikordsform - den videre proces')

# Fileuploader
uploaded_file = st.file_uploader("Vælg notat", 
                                    type='docx',
                                    )
result = []
submitted = st.button('Generer forklæde', type='primary')



# Ved klik på upload-knap
if submitted:
    if uploaded_file is not None:
        with st.spinner('Konverterer Word-fil'):
            try: 
                docx_file = io.BytesIO(uploaded_file.getbuffer())
                txt = sh.docx_to_text(docx_file)
            except:
                st.error("Konverteringen af Word-filen mislykkedes")
                sys.exit(1)
        
        with st.spinner('Tæller antal tokens'):
            try:
                txtLength = sh.num_tokens_from_string(txt, "gpt-3.5-turbo")
            except:
                st.error("Kunne ikke tælle antal tokens")
                sys.exit(1)

        if txtLength > 10000:
            with st.spinner('Teksten er for lang. Genererer resume som 😓'):
                try:
                    doc = gpt.generate_summary(txt)
                except:
                    st.error('Genereringen af resumé mislykkedes')
                    sys.exit(1)
        else:
            doc = txt

        with st.spinner('Genererer kant-kontekst-konklusion 😬'):
            kant_kontekst_konklusion = gpt.generate_kant_kontekst_konklusion(doc, formaal, formaalstekst, temperature)
            result = []
            result.append(kant_kontekst_konklusion)
            kant_kontekst_konklusion = dict(result[0])

        with st.spinner('Genererer sagsfremstilling 🙂'):
            sagsfremstilling = gpt.generate_sagsfremstilling(doc, kant_kontekst_konklusion["kant_kontekst"], temperature)
            result = []
            result.append(sagsfremstilling)
            sagsfremstilling = dict(result[0])

        with st.spinner('Genererer videre proces 😍'):
            videre_proces = gpt.generate_videre_proces(kant_kontekst_konklusion["kant_kontekst"], sagsfremstilling["sagsfremstilling"], videre_proces_tekst, temperature)
            result = []
            result.append(videre_proces)
            videre_proces = dict(result[0])


    else:
        st.error('Husk at uploade en fil, før du klikker upload', icon="🚨")


if len(result):
    download = st.button('Download forklæde', type='secondary')

    st.header('Kant-kontekst-konklusion')
    st.write(kant_kontekst_konklusion["kant_kontekst"], kant_kontekst_konklusion["konklusion"])

    st.header('Sagsfremstilling')
    st.write(sagsfremstilling["sagsfremstilling"])

    st.header('Videre proces')
    st.write(videre_proces["videre_proces"])
