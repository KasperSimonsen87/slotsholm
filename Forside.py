import streamlit as st
from docx import Document as DocxDocument
import io
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="Slotsholmifikatoren",
    page_icon="👋",
    layout="wide",
)

# Overskrift og hjælpetekst
st.title('🦜🔗 Slotsholmifikatoren')

introhjaelpetekst = '''I UFM skal alle forklæder følge Slotsholmsmetoden. 
                    Brug det nedenstående værktøj til at uploade et notat og få et udkast til forklæde. '''

st.markdown(introhjaelpetekst)


# Funktion til at konvertere Word til tekst
def docx_to_text(file):
    doc = DocxDocument(file)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return ' '.join(full_text)
    
result = []

# Kald til OpenAI's API
def generate_response(txt, formaal):
    # Instantier sprogmodel
    llm = ChatOpenAI(temperature=0, 
                 model_name='gpt-3.5-turbo',
                 openai_api_key=openai_api_key)
    
    # Lav rekursiv tekstsplit - summary of summaries
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, 
                                                   chunk_overlap=400, 
                                                   separators=[" ", ",", "\n"])
    docs = text_splitter.create_documents([txt])
    
    # Map-prompt til at lave præliminære summaries
    map_prompt = """
    Skriv et koncist resumé af følgende tekst:
    "{text}"
    RESUMÉ:
    """
    map_prompt_template = PromptTemplate(template=map_prompt, input_variables=["text"])

    
    # Lav prompt
    combine_prompt = """
    Lav et resumé af den følgende tekst afgrænset af triple backquotes.
    Resuméet skal overholde følgende regler:
    Der skal være fire afsnit: Indledning, Indstilling, Baggrund og Videre proces. Afsnittene skal være formateret som overskrifter via Markdown (.md).
    Under Videre proces skal det fremgå, om modtageren på baggrund af resumeet skal {formaal}.
    ```{text}```
    RESUMÉ AF TEKSTEN:
    """

    # Kombiner prompt
    combine_prompt_template = PromptTemplate(template=combine_prompt, 
                                             input_variables=["text", "formaal"]
                                             )
    print(combine_prompt_template)
    
    # Text summarization
    summary_chain = load_summarize_chain(llm=llm,
                                         chain_type='map_reduce',
                                         map_prompt=map_prompt_template,
                                         combine_prompt=combine_prompt_template,
                                         verbose=True
                                         )
    
    return summary_chain.run({'input_documents': docs, 
                              'formaal': formaal.lower()})



# Form-elementer og logik til upload af notat 
with st.form('Upload notat'):
    # Vælg formål med forklædet
    formaal = st.radio("Skal modtageren efter endt læsning vide, beslutte eller handle? 👇",
                       ('Vide', 'Beslutte', 'Handle'),
                       horizontal=True,
                       )


    # Fileuploader
    uploaded_file = st.file_uploader("Vælg notat", 
                                     type='docx',
                                     )
    # Upload-knap
    submitted = st.form_submit_button('Generer forklæde', type='primary')

    # Ved klik på knap
    if submitted:
        if uploaded_file is not None:
            with st.spinner('Slotsholmificering in progress 😎'):
                docx_file = io.BytesIO(uploaded_file.getbuffer())
                rawtext = docx_to_text(docx_file)
                response = generate_response(rawtext, formaal)
                result.append(response)

if len(result):
    st.header('Udkast til forklæde')
    st.info(result[0])

# Resultat