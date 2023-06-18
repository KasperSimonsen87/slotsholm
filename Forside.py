import streamlit as st
from docx import Document as DocxDocument
import io
import os
from dotenv import load_dotenv
import tiktoken
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import load_prompt
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# Indlæs miljøvariabler (secrets)
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

def num_tokens_from_string(string: str, encoding_model: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_model)
    num_tokens = len(encoding.encode(string))
    return num_tokens


# Kald til OpenAI's API
def generate_summary(txt):
    # Instantier sprogmodel
    llm4k = ChatOpenAI(temperature=0, 
                model_name='gpt-3.5-turbo',
                openai_api_key=openai_api_key)
    
    # Lav rekursiv tekstsplit - summary of summaries
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, 
                                                chunk_overlap=100, 
                                                separators=[" ", ",", "\n"])
    docs = text_splitter.create_documents([txt])
    
    # Map-prompt til at lave præliminære summaries
    map_prompt_template = load_prompt("prompts/map_prompt.json")
    
    # Kombiner prompt
    combine_prompt_template = load_prompt("prompts/combine_prompt.json")
    
    # Text summarization
    summary_chain = load_summarize_chain(llm=llm4k,
                                        chain_type='map_reduce', #'map_reduce'
                                        map_prompt=map_prompt_template,
                                        combine_prompt=combine_prompt_template,
                                        verbose=True,
                                        )
    # Returner referat af teksten
    return summary_chain.run({'input_documents': docs})

def generate_response(txt, formaal, input_text):

    txtLength = num_tokens_from_string(txt, "gpt-3.5-turbo")
    print('Antal tokens i resumeer: ', txtLength)

    if txtLength > 10000:
        try:
            docs = generate_summary(txt)
        except Exception as e:
            return(e.message, e.args)
    else:
        docs = txt

    # Instantier sprogmodel
    llm16k = ChatOpenAI(temperature=0, 
                 model_name='gpt-3.5-turbo-16k',
                 openai_api_key=openai_api_key)

    template = """Du er en hjælpsom assistent, der altid følger Slotsholmmetoden."""
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)

    human_template = """
    Du skal nu lave en kort opsummering af teksten nedenfor indkapslet i triple backquotes (```) ved hjælp af Slotsholmmetoden.
    Ifølge Slotsholmmetoden skal opsummeringen MAKSIMALT fylde 3 sætninger:
    - Den første sætning er kantsætningen og skal besvare hvad tekstens ærinde er. Hvad er den konkrete anledning til at man henvender sig? Er et produkt klar til godkendelse? Skal vi reagere på noget, der er sket? Skal vi forholde os til en ny tanke, har vi produceret en ny analyse, eller har vi forfattet endnu en rutinemæssig statusrapport?  
    - Derefter følger kontekstsætningen. Kontekstsætningen kvalificerer kantsætningen med en vurdering af hvad er der på spil. Den fortæller i hvilket lys kantsætningen skal ses. Sætningen flager graden af business as usual, opmærksomhedsbehov eller drama.
    - Til sidst følger konklusionssætningen, der beskriver hvad slutmodtageren skal med dokumentet: Skal slutmodtageren vide, beslutte eller handle? Skriveren har oplyst, at tekstens konklusion er som følger: {formaal}
    Her følger 3 eksempler på gode besvarelser på irrelevante tekster, der overholder kravene:
    - Der er behov for at styrelsen genovervejer sin tolkning af reglerne for udbetaling i landbrugsstøtteordningen (BICES). Et nyligt afholdt møde med EU-Kommissionen har afdækket, at der er uoverensstemmelse mellem parternes forståelse af udbetalingsreglerne, hvorfor der inden for få dage vil komme bud på plan for videre forløb. Notatet er alene til orientering.
    - Dagsordenen til kvartalsmøde med Rigspolitiets juridiske afdeling er klar. Programmet indeholder alene punkter af rutinemæssig karakter, herunder en orientering om jubilæumsskriftet. Det skal besluttes, om dagsordenen kan godkendes.
    - Budgettet til hjemtagning af færdigbehandlede patienter kan med fordel varigt reduceres med 1,2 mio. kr. Der er et mindreforbrug i forlængelse af en række tiltag fra Sundhedsforvaltningen, som betyder, at færdigbehandlede patienter venter færre dage på hospitalerne. Det skal besluttes, om budgetændringen kan godkendes.
    Herunder følger teksten:
    ```{text}````
    """
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    slotsholm_chain = LLMChain(llm=llm16k, prompt=chat_prompt, verbose=True)


    # Text summarization
    #kant_kontekst_konklusion = load_prompt("prompts/kant_kontekst_konklusion.json")

    return slotsholm_chain.run({'text': docs,
                                'formaal': input_text})




# Form-elementer og logik til upload af notat 

# Vælg formål med forklædet
formaal = st.radio("Skal modtageren efter endt læsning vide, beslutte eller handle? 👇",
                    ('Vide', 'Beslutte', 'Handle'),
                    horizontal=True,
                    )

if formaal == 'Beslutte':
    input_text = st.text_input('Angiv kort hvad læseren skal beslutte')
elif formaal == 'Handle':
    input_text = st.text_input('Angiv kort hvad læseren skal gøre')
elif formaal == 'Vide':
    input_text = 'Punktet er alene til orientering.'

# Fileuploader
uploaded_file = st.file_uploader("Vælg notat", 
                                    type='docx',
                                    )
# Upload-knap
submitted = st.button('Generer forklæde', type='primary')

# Ved klik på knap
if submitted:
    if uploaded_file is not None:
        with st.spinner('Slotsholmificering in progress 😎'):
            docx_file = io.BytesIO(uploaded_file.getbuffer())
            rawtext = docx_to_text(docx_file)
            response = generate_response(rawtext, formaal, input_text)
            result.append(response)

if len(result):
    st.header('Udkast til forklæde')
    st.info(result)

# Resultat