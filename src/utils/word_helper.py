## word_helper.py
# import 
from docx import Document



def extract_docx(path):
    doc = Document(path)

    doc_para = []
    for para in doc.paragraphs:
        doc_para.append(para.text)

    return doc_para 