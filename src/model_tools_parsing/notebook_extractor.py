## notebook_extractor.py
# import
# import sys
import re

# from bs4 import NavigableString # , Tag
# import requests
from dataclasses import dataclass, field
from returns.result import Failure, Result, Success

# import html
from pathlib import Path

# from markdown_it import MarkdownIt
import markdown
from bs4 import BeautifulSoup as bs

from src.model_classes_parsing.base_classes_parsing import (
    Cell,
    CellMeta,
    Document,
    DocumentExtract,
    Word,
)

from src.model_tools_parsing.feature_enricher import FeatureEnricher
from src.model_tools_parsing.html_extractor import HTMLCleanExtractor

from src.core.memory import ParseContext
# Element, ElementMeta,
# from src.utils.text_file_helper import read_html_file
# from src.utils.path_helper import shorten_path
from src.utils.dict_helper import load_dict, save_dict


# @dataclass
class NoteBookCleanExtractor(HTMLCleanExtractor):

    nb_language: str = field(default_factory=str)
    
    def __init__(self, 
                 enricher: FeatureEnricher, 
                 parse_context: ParseContext):
        
        self.doc_name = parse_context.run_id
        self.enricher = enricher
        self.extract_config = parse_context.parse_settings.json_nb
        self.extraction_tags = parse_context.general_settings.json_nb.extraction_tags
        self.header = parse_context.header

        self.logger = parse_context.logger
        self.parser = self.extract_config.parser
        self.save_folder = parse_context.save_folder
        self.save_name = parse_context.save_name
        self.text_type = parse_context.text_type

        return 


    def extract(
            self, 
            f_path: str
            ) -> Result[DocumentExtract, str]:

        self.logger.info("Starting extraction by NotebookCleanExtractor")

        nb = load_dict(f_path)

        nb_name = nb.get("name", {})
        self.nb_language = (
            nb.get("content", {})
            .get("metadata", {})
            .get("kernelspec", {})
            .get("language")
        )

        if nb_name.split(".")[-1] != "ipynb":
            self.logger.error(
                "Provided json-file did not match the expected structure. No value or invalid for 'name':\t%s",
                nb,
            )
            return Failure("Provided json-file did not match the expected structure. No value or invalid for 'name'")

        nb_cells = nb.get("content", {}).get("cells")
        assert nb_cells is not None

        cells = self._extract_cells(nb_cells)

        self.logger.info("Number of cells in notebook:\t%s", 
                         len(cells))

        cells_clean = []
        for cell in cells:
            # text_clean = self._clean_text(element.text)

            if cell.cell_type == "code_block":
                cells_clean.append(self._prepare_code_cell(cell))

            else:
                cells_clean.append(self._prepare_md_cell(cell))

        text_clean = "\n\n".join([cell.text for cell in cells_clean])
        doc_info = self.enricher._add_basic_metadata(
                                            text_clean, 
                                            cells_clean, 
                                            Document()
                                        )

        save_path = Path(f"{self.save_folder}/{self.save_name}")
        save_dict(data=doc_info.model_dump(
                            mode="json",
                            serialize_as_any=True,
                            ), 
                path=save_path)
        
        return Success(
                DocumentExtract(
                    doc_type="json_nb",
                    doc_name=Path(f_path).name,
                    text=doc_info.text,
                    elements=doc_info.elements,
                    meta=doc_info.meta,
        ))

    def _prepare_code_cell(self, 
                           cell):

        words_clean = []
        for word in re.findall(r"\S+|\n", cell.text):
            # element.text.split():   # text_clean.split():

            words_clean.append(
                            Word(
                                text=self._clean_word_token(word)
                            ))

        txt_clean = cell.text

        cell_new = self.enricher._add_basic_metadata(
                                                txt_clean, 
                                                words_clean, 
                                                cell
                                                )

        # cell_new.cell_type = cell.cell_type

        # self.logger.info("Finished 'prepare_code_cell'.\nNumber of word = %s\ncell_meta:\n%s",
        #                  len(words_clean),
        #                  cell_new)

        self.logger.info(
            "Finished 'prepare_code_cell'.\nNumber of elements = %s\ncell_text:\n%s",
            len(words_clean),
            cell_new.text[:100] if cell_new.text else None,
        )
        return cell_new


    def _prepare_md_cell(self, 
                         cell):
         # "lxml"

        # md = MarkdownIt()

        html = markdown.markdown(
            cell.text, 
            extensions=[
                    "fenced_code", 
                    "tables", 
                    "nl2br"
                    ]
        )
        soup = bs(html, 
                  self.parser)

        # elements = self._differentiate_text(tokens)

        elements = self._extract_elements(soup)
        self.logger.info("Extracted %s elements from markdown cell", len(elements))

        elements_clean = []
        for element in elements:

            if (hasattr(element, "container_type") 
                and element.container_type != "code"):
                e_txt_clean = self._clean_text(element.text)
            
            elif (hasattr(element, "leaf_type") 
                and element.leaf_type != "code"):
                e_txt_clean = self._clean_text(element.text)
            
            else:
                e_txt_clean = element.text

            words_clean = []
            for word in re.findall(r"\S+|\n", e_txt_clean):
                words_clean.append(
                            Word(
                                text=self._clean_word_token(word)
                                ))

            # if element.meta.element_type != "code":
            #     e_txt_clean = self._clean_text(element.text)

            # else:
            #     e_txt_clean = element.text

            
            element_new = self.enricher._add_basic_metadata(
                e_txt_clean, words_clean, element
            )

            # element_new.meta.element_type = element.meta.element_type

            elements_clean.append(element_new)

        cell.elements = elements_clean

        txt_clean = "\n".join([e.text for e in cell.elements])

        cell_new = self.enricher._add_basic_metadata(txt_clean, elements_clean, cell)

        # cell_new.meta.cell_type = cell.meta.cell_type

        # words_clean = []
        # for word in re.findall(r"\S+|\n", cell.text):
        #     # element.text.split():   # text_clean.split():

        #     words_clean.append(
        #                     Word(
        #                         text = self._clean_word_token(word)
        #                         ))

        # txt_clean = cell.text

        # cell_new = self.enricher._add_basic_metadata(
        #                                         txt_clean,
        #                                         words_clean,
        #                                         cell
        #                                         )

        # cell_new.meta.cell_type = cell.meta.cell_type

        self.logger.info(
            "Finished 'prepare_md_cell'.\nNumber of elements = %s\ncell_text:\n%s",
            len(elements_clean),
            cell_new.text[:100] if cell_new.text else None,
        )

        return cell_new

        # for i, e in enumerate(elements[:10]):
        #     self.logger.info(
        #         "[Element %s] type=%s | len=%s | preview=%s",
        #         i,
        #         getattr(e.meta, "element_type", None),
        #         len(e.text) if e.text else 0,
        #         repr(e.text[:100]) if e.text else None
        #     )
        # sys.exit()

    def _clean_text(self, text: str) -> str:
        # text = html.unescape(text)

        # Mehrfache Leerzeichen
        text = re.sub(r"[ \t]+", " ", text)

        # Mehrfache Leerzeilen
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Spaces vor newline
        text = re.sub(r" +\n", "\n", text)

        text = text.replace('\\"', '"')
        text = text.replace("\\n", "\n")
        text = re.sub(r'\\(?!n|t|"|u)', "", text)

        # text = re.sub(r"(\\\\n)", "\n", text)
        # text = re.sub(r'(\\\")', '"', text)
        # text = text.replace('\\"', '"')
        # text = text.replace('\\n', '\n')

        return text

    def _extract_cells(
                    self, 
                    cells: list[dict]
                    ) -> list[Cell]:
        extract = []
        idx = 0

        for cell in cells:
            c_type = cell.get("cell_type")
            assert c_type is not None

            c_text = cell.get("source")
            assert c_text is not None

            if isinstance(c_text, list):
                c_text = "".join(c_text)

            self.logger.info(
                "[Cell #%s] cell_type | len_cell_text:\t%s | %s\nContent:\t%s",
                idx,
                c_type,
                len(c_text),
                c_text[:20],
            )

            if c_type == "code":
                # language = ""

                # try:
                #     c_text = c_text.encode().decode(
                #                         "unicode_escape"
                #                         )
                # except Exception:
                #     pass

                extract.append(
                    Cell(
                        text=c_text,
                        cell_type="code_block",
                        cell_id=idx,
                        meta=CellMeta(
                            language=self.nb_language,
                        ),
                    )
                )
                idx += 1

            elif c_type == "markdown":
                # hi = ""
                extract.append(
                    Cell(
                        text=c_text, 
                        cell_type="md_block", 
                        cell_id=idx,
                        meta=CellMeta()
                        )
                )
                idx += 1

            else:
                self.logger.error(
                    "Found cell of unknown type:\t%s\nContent:\n%s",
                    c_type,
                    c_text[:500],
                )

        return extract


# # On importe la librairie spaCy\n
# import spacy \n\n
# # On charge le mod\u00e8le\n
# nlp = spacy.load(\"fr_core_news_md\")\n\n
# # On cr\u00e9e la cha\u00eene de caract\u00e8res\n
# string = \"Bonjour @canal, j'esp\u00e8re que vous allez bien.\"\n\n
# # On transforme la cha\u00eene de caract\u00e8res en doc\n
# doc = nlp(string)\n\n
# # On affiche chacun des tokens de la cha\u00eene de caract\u00e8res\n
# for mot in doc:\n
#     print(mot.text)\n\n

# # De fa\u00e7on \u00e9quivalente print(mot) nous donne le m\u00eame r\u00e9sultat

# def _extract_elements(
#                     self,
#                     cell: str
#                     ) -> List[Element]:


#     current_headings = {}

#     return extract


# def _parse_inline(self, tag):

#     parts = []

#     for child in tag.children:

#         # normaler Text
#         if isinstance(child, NavigableString):

#             text = str(child)

#             if child.name not in ["code", "p"]:
#                 text = text.replace("\n", " ")

#             parts.append(text)

#         # inline code
#         elif child.name == "code":

#             code = child.get_text()

#             try:
#                 code = bytes(code, "utf-8").decode(
#                                             "unicode_escape"
#                                             )
#             except Exception:
#                 pass

#             parts.append(f"{code}")       # strip=True

#         # links
#         elif child.name == "a":

#             text = self._parse_inline(child)
#             href = child.get("href", "")

#             parts.append(f"[{text}]({href})")

#         # elif child.name == "image":

#         #     text = self._parse_inline(child)
#         #     # href = child.get("href", "")

#         #     parts.append(f"[image]({text})")

#         # bold
#         elif child.name in ["strong", "b"]:

#             parts.append(
#                 f"**{self._parse_inline(child)}**"
#             )

#         # italic
#         elif child.name in ["em", "i"]:

#             parts.append(
#                 f"*{self._parse_inline(child)}*"
#                 )

#         elif child.name == "li":
#             parts.append(
#                 f"\n- {self._parse_inline(child)}\n"
#                 )

#         elif child.name == "br":
#             parts.append("\n")

#         else:
#             parts.append(
#                 self._parse_inline(child)
#                 # child.get_text(" ", strip=True)
#                 )

#     return "".join(parts)   # .strip()


# def _extract_elements_from_soup(self, soup):
#     extract_elements = self.extract_config["extract_elements"]

#     extract = {}
#     if "paragraph" in extract_elements:
#         extract["para"] = self._extract_paragraphs(soup)

#     if "image" in extract_elements:
#         extract["img"] = self._extract_images(soup)

#     if "table" in extract_elements:
#         extract["table"] = self._extract_tables(soup)

#     if "list" in extract_elements:
#         extract["list"] = self._extract_lists(soup)
#         # CAVE: ORDERED vs. UNORDERED

#     if "link" in extract_elements:
#         extract["link"] = self._extract_links(soup)

#     return extract

# element_by_id = soup.find('div', id= 'main-content')
# element_by_class = soup.find('div', class_= 'content')
# element_by_attrs = soup.find('div', attrs={'class': 'content', 'data-lang': 'en'})

# print("element_by_id : ",element_by_id.text)
# print("element_by_class : ",element_by_class.text)
# print("element_by_attrs : ",element_by_attrs.text)


# url = 'https://en.wikipedia.org/wiki/Alan_Turing'
# page = requests.get(url)
# soup = bs(page.content, "lxml")
# print(soup)

# code_source = '''
# <html>
#   <body>
#     <h1 id="first"> Title 1 </h1>
#     <div id="main-content"> Unique main content </div>
#     <div class="content"> Initial content </div>
#     <div class="content" data-lang="en"> A second English content </div>
#     <h1 id="second"> Title 2 </h1>
#     <ul id="lists">
#         <li class="chip"> Element 1 </li>
#         <li class="chip"> Element 2 </li>
#         <li class="chip"> Element 3 </li>
#     </ul>
#     <div>
#         <p class="paragraph"> A new paragraph </p>
#     </div>
#   </body>
# </html>
# '''

# soup = bs(code_source, 'html.parser')
# element_by_id = soup.find('div', id= 'main-content')
# element_by_class = soup.find('div', class_= 'content')
# element_by_attrs = soup.find('div', attrs={'class': 'content', 'data-lang': 'en'})

# print("element_by_id : ",element_by_id.text)
# print("element_by_class : ",element_by_class.text)
# print("element_by_attrs : ",element_by_attrs.text)
