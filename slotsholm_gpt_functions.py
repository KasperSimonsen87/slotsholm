from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import load_prompt
from langchain.prompts import PromptTemplate
from langchain.chains import SequentialChain
from langchain.chains import LLMChain

# Indlæs miljøvariabler (secrets) - streamlit online
load_dotenv()

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
                                        chain_type='map_reduce', 
                                        map_prompt=map_prompt_template,
                                        combine_prompt=combine_prompt_template,
                                        verbose=True,
                                        )
    # Returner referat af teksten
    return summary_chain.run({'input_documents': docs})





def generate_kant_kontekst_konklusion(doc, formaal, formaalstekst, usertemperature):
    # Instantier sprogmodel
    llm = ChatOpenAI(temperature=usertemperature, 
                        model_name='gpt-3.5-turbo-16k',
                        openai_api_key=openai_api_key)

    # Dette er en LLMChain til at lave kant og kontekst-sætningen ift. Slotsholmsmetoden med et notat som input.
    #llm = OpenAI(temperature=.7)
    kant_kontekst_template = """
    Du skal nu lave et ultrakort resumé af teksten nedenfor indkapslet i triple backquotes (```) ved hjælp af Slotsholmmetoden.

    Ifølge Slotsholmmetoden skal resuméet MAKSIMALT fylde 2 sætninger, kantsætning og kontekstsætning:
    - Den første sætning er kantsætningen og skal besvare hvad tekstens ærinde er. Hvad er den konkrete anledning til at man henvender sig? Er et produkt klar til godkendelse? Skal vi reagere på noget, der er sket? Skal vi forholde os til en ny tanke, har vi produceret en ny analyse, eller har vi forfattet endnu en rutinemæssig statusrapport?  
    - Derefter følger kontekstsætningen. Kontekstsætningen kvalificerer kantsætningen med en vurdering af hvad er der på spil. Den fortæller i hvilket lys kantsætningen skal ses. Sætningen flager graden af business as usual, opmærksomhedsbehov eller drama.

    De to sætninger må ikke gentage hinanden.  
    Nedenfor er nogle eksempler på resuméer der overholder Slotsholmsmetoden:
    - Der er behov for, at styrelsen genovervejer sin tolkning af reglerne for udbetaling i landbrugsstøtteordninger (BICES). Et nyligt afholdt møde med EU-kommissionen har afdækket, at der er uoverensstemmelse mellem partneres forståelse af udbetalingsreglerne, hvorfor der inden for få dage vil komme bud på plan for videre forløb.
    - Dette dokument afklarer, om der juridisk er krav om udbud ved køb af nye overvågningskameraer. Loven tillader at vi køber uden udbud hvis vi fastholder nuværende pris og tekniske krav til systemet, og vi kan hvis vi ønsker det, fortsætte med Flexcom som leverandør.
    - Dagsorden til kvartalsmøde med Rigspolitiets juridiske afdeling er klar. Programmet indeholder alene punkter af rutinemæssig karakter, herunder en orientering om jubilæumsskriftet.
    - Budgettet til hjemtagning af færdigbehandlede patienter kan med fordel varigt reduceres med 1,2 mio. kr. Der er et mindreforbrug i forlængelse af en række tiltag fra Sundhedsforvaltningen, som betyder, at færdigbehandlede patienter venter færre dage på hospitalerne.
    - Det er muligt at foretage en digitalisering, oprydning og udsmidning af personalearkivet. Ressourceforbruget ved en sådan oprydning vurderes at være uforholdsmæssigt stort i forhold til den potentielle værdiskabelse, og et alternativ er at arkivet flyttes til et fjernlager, hvor det kan destrueres efter udløbet af forældelsesfristen på fem år.    

    Lav resumé ifølge Slotsholmsmetoden af følgende tekst: ```{doc}```
    """
    kant_kontekst_prompt_template = PromptTemplate(input_variables=["doc"], template=kant_kontekst_template)
    kant_kontekst_chain = LLMChain(llm=llm, prompt=kant_kontekst_prompt_template, output_key="kant_kontekst")


    # Dette er en LLMChain til at lave konklusionssætningen.
    #llm = OpenAI(temperature=.7)
    konklusion_template = """
    Du er ved at skrive konklusionssætningen af et resumé af den følgende tekst:
    ```{doc}````

    Resuméet lyder som følger: {kant_kontekst}.
    Du skal nu skrive konklusionssætningen. 
    Konklusionssætningen beskriver hvad slutmodtageren skal med dokumentet: Skal slutmodtageren vide, beslutte eller handle? 
    Tag udgangspunkt i disse gode eksempler på konklusionssætninger:
    - Notatet er alene til orientering
    - Det skal besluttes, om dagsordenen kan godkendes
    - Det skal besluttes, om budgetændringen kan godkendes
    - Notatet er til orientering for indkøbskontoret
    - Det skal besluttes hvilken løsning der vælges.

    Skriveren har oplyst, at tekstens konklusion er som følger: {formaal}. {formaalstekst}

    Konklusionssætning:
    """
    konklusion_prompt_template = PromptTemplate(input_variables=["doc", "kant_kontekst", "formaal", "formaalstekst"], template=konklusion_template)
    konklusion_chain = LLMChain(llm=llm, prompt=konklusion_prompt_template, output_key="konklusion")

    overall_chain = SequentialChain(
        chains=[kant_kontekst_chain, konklusion_chain],
        input_variables=["doc", "formaal", "formaalstekst"],
        # Here we return multiple variables
        output_variables=["kant_kontekst","konklusion"],
        verbose=True)

    return overall_chain({"doc":doc, "formaal": formaal, "formaalstekst": formaalstekst})






def generate_sagsfremstilling(doc, kant_kontekst, usertemperature):
    # Instantier sprogmodel
    llm = ChatOpenAI(temperature=usertemperature, 
                        model_name='gpt-3.5-turbo-16k',
                        openai_api_key=openai_api_key)


    # This is an LLMChain to the sagsfremstilling.
    #llm = OpenAI(temperature=.7)
    sagsfremstilling_template = """
    Du skal nu lave et resumé af et notat fra et ministerium.
    Der er allerede lavet et kort resumé: ```{kant_kontekst}````
    Du skal i resuméet ikke gentage, men udbygge udsagnene fra ovenstående resumé med flere, relevante detaljer. 
    Dit svar må maks være på 100 tokens.
    Resuméet må ikke indeholde overskrifter.
    Tekst: ```{doc}```
    """

    sagsfremstilling_prompt_template = PromptTemplate(input_variables=["doc", "kant_kontekst"], template=sagsfremstilling_template)
    sagsfremstilling_chain = LLMChain(llm=llm, prompt=sagsfremstilling_prompt_template, output_key="sagsfremstilling")

    overall_chain = SequentialChain(
        chains=[sagsfremstilling_chain],
        input_variables=["doc", "kant_kontekst"],
        # Here we return multiple variables
        output_variables=["sagsfremstilling"],
        verbose=True)

    return overall_chain({"doc":doc, "kant_kontekst": kant_kontekst})



def generate_videre_proces(kant_kontekst, sagsfremstilling, videre_proces_tekst, usertemperature):
    # Instantier sprogmodel
    llm = ChatOpenAI(temperature=usertemperature, 
                        model_name='gpt-3.5-turbo-16k',
                        openai_api_key=openai_api_key)


    # This is an LLMChain to the sagsfremstilling.
    #llm = OpenAI(temperature=.7)
    videre_proces_template = """
    Baggrund: ```{kant_kontekst}````
    Yderligere baggrund: ```{sagsfremstilling}````
    Du skal nu skrive en kort tekst på MAKSIMALT 50 ord om den videre proces om sagen ovenover.
    Sagsbehandleren har angivet at følgende skal ske: ```{videre_proces_tekst}```
    Videre proces:
    """

    videre_proces_prompt_template = PromptTemplate(input_variables=["sagsfremstilling", "kant_kontekst", "videre_proces_tekst"], template=videre_proces_template)
    videre_proces_chain = LLMChain(llm=llm, prompt=videre_proces_prompt_template, output_key="videre_proces")

    overall_chain = SequentialChain(
        chains=[videre_proces_chain],
        input_variables=["kant_kontekst", "sagsfremstilling", "videre_proces_tekst"],
        # Here we return multiple variables
        output_variables=["videre_proces"],
        verbose=True)

    return overall_chain({"kant_kontekst":kant_kontekst, "sagsfremstilling": sagsfremstilling, "videre_proces_tekst": videre_proces_tekst})