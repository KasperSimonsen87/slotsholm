# Funktion til at konvertere Word til tekst
from docx import Document as DocxDocument
def docx_to_text(file):
    '''Returns ASCII text of an inputted Word document'''
    doc = DocxDocument(file)
    full_text = []
    for paragraph in doc.paragraphs:
        full_text.append(paragraph.text)
    return ' '.join(full_text)
    

# Funktion til at tælle tokens i en tekststreng
import tiktoken
def num_tokens_from_string(string: str, encoding_model: str) -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_model)
    num_tokens = len(encoding.encode(string))
    return num_tokens