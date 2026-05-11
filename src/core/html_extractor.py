## html_extractor.py
# import
from pathlib import Path
from bs4 import BeautifulSoup as bs
import requests 
from dataclasses import dataclass, field
from typing import List

from src.core.base_extractor import BaseExtractor
from src.core.data_classes import (Element, ElementMeta, 
                                   Word, Document,
                                   DocumentExtract)
from src.utils.text_file_helper import read_text_file


@dataclass
class HMTLExtractor(BaseExtractor):

    relevant_tags: List = field(default_factory=list)


    def extract_html(
                    self, 
                    extract_config, 
                    f_path=None,
                    url=None
                    ):
        from src.core.memory import session

        self.logger = session.logger

        # parser = extract_config["html_parser"]
        parser = "html.parser"  # "lxml"
        if f_path is not None:
            # data_src == "file":
            file = read_text_file(f_path)

            soup = bs(file, parser)

        elif url is not None:
            # data_src == "file":
            page = requests.get(url, timeout=10)

            soup = bs(page.content, parser)

        # extract_approach = extract_config["extract_approach"]
        self.relevant_tags = extract_config["extraction_tags"]
        
        root = (soup.find("div", class_="container") 
                or soup.body 
                or soup)

        elements = self._extract_elements(root)

        elements_clean = []
        for element in elements:

            words_clean = []
            for word in element.text.split():
                words_clean.append(
                            Word(
                                text = self._clean_word_token(word)
                                ))

            txt_clean = " ".join([w.text for w in words_clean])
            
            element_new = self.enricher._add_basic_metadata(txt_clean, 
                                                     words_clean, 
                                                     Element())
            
            element_new.meta.element_type = element.meta.element_type

            elements_clean.append(
                            element_new
                            )

        text_clean = "\n\n".join([ele.text for ele in elements_clean])
        doc_info = self.enricher._add_basic_metadata(text_clean,
                                               elements_clean,
                                               Document())

        return DocumentExtract(
                            doc_type = "md",
                            doc_name = Path(f_path).name, 
                            text = doc_info.text,
                            elements = doc_info.elements,
                            meta = doc_info.meta
                            )



    def _is_inside_relevant_parent(self, tag):
        return tag.find_parent(
                        ["p", "ul", "ol", "pre", "table"]
                        ) is not None

    
    def _extract_elements(self, root) -> List[Element]:

        extract = []
        current_headings = {}
        idx = 0
        for tag in root.find_all(
                                self.relevant_tags,
                                recursive=True
                                ):

            # protection against duplicates
            if (tag.name in ["code", "li"] 
                and self._is_inside_relevant_parent(tag)):
                continue
            
            if tag.name == "p":      # paragraph
                extract.append(
                            Element(
                                text = tag.get_text(" ", 
                                                    strip=True),
                                meta = ElementMeta(
                                    element_type = "paragraph",
                                    element_id = idx,
                                    context = dict(current_headings)
                                    )
                                )
                            )
                idx += 1
    
            elif tag.name.startswith("h"):
                # in ["h1", "h2", "h3",
                            #   "h4", "h5", "h6"]:      # heading
                level = int(tag.name[1]) 

                current_headings[level] = tag.get_text(" ", 
                                                       strip=True)

                # tiefere Headings löschen
                for k in list(current_headings):
                    if k > level:
                        del current_headings[k]

                extract.append(
                            Element(
                                text = current_headings[level],
                                meta = ElementMeta(
                                    element_type = "paragraph",
                                    element_id = idx,
                                    level = level
                                    )
                                )
                            )
                idx += 1
        
            elif tag.name in ["ul", "ol"]:      # un-/ordered list
                extract.append(
                            Element(
                                text = tag.get_text(" ", strip=True),
                                meta = ElementMeta(
                                    element_type = "bullets_list",
                                    element_id = idx,
                                    list_type = "ordered" if tag.name == "ol" else "unordered"
                                    )
                                )
                            )
                idx += 1

            elif tag.name == "pre":       # code_block
                code = tag.get_text("\n", strip=False)
                code_tag = tag.find("code")
                lang = None
                
                if code_tag:
                    classes = code_tag.get("class", [])
                    lang = next((c.replace("language-", "") 
                                 for c in classes 
                                 if c.startswith("language-")), 
                                 None)


                extract.append(
                            Element(
                                text = tag.get_text(" ", strip=True),
                                meta = ElementMeta(
                                    element_type = "code",
                                    element_id = idx,
                                    language = lang,
                                    context = dict(current_headings)
                                    )
                                )
                            )
                idx += 1

            elif tag.name == "table":       
                extract.append(
                            Element(
                                text = tag.get_text(" ", strip=True),
                                meta = ElementMeta(
                                    element_type = "table",
                                    element_id = idx
                                    )
                                )
                            )
                idx += 1

            elif tag.name == "img":       # image
                extract.append(
                            Element(
                                text = tag.get_text(" ", strip=True),
                                meta = ElementMeta(
                                    element_type = "image",
                                    element_id = idx
                                    )
                                )
                            )
                idx += 1

            elif tag.name == "href":       # external link
                extract.append(
                            Element(
                                text = tag.get_text(" ", strip=True),
                                meta = ElementMeta(
                                    element_type = "link_reference",
                                    element_id = idx
                                    )
                                )
                            )
                idx += 1

            else: 
                self.logger.info("Tag of element does not match with a relevant tag:\t%s",
                           tag.name)

        return extract
    

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