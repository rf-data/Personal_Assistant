# !!! - docling --> AI-focused document processing library

from docling.document_converter import DocumentConverter

converter = DocumentConverter()

result = converter.convert("annual_report.pdf")

document = result.document
markdown = document.export_to_markdown()
json_data = document.export_to_dict()
