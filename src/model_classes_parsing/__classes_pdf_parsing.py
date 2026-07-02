## data_classes_parsing.py
# import
from typing import (
    Annotated,  #
    Literal,
    List,
    Dict
)

from pydantic import BaseModel, Field

from src.model_classes_parsing.base_classes_parsing import (
                                                BaseLeaf,
                                                BaseContainer,
                                                PageExtract,
                                                Graphics,
                                                Image
                                                )

# -------------------------
# METADATA
# -------------------------


# -------------------------
# LEAF_ELEMENTS
# -------------------------

# -------------------------
# CONTAINER_ELEMENTS
# -------------------------

"""
class BaseMeta(BaseModel):
    n_words: int = Field(default_factory=int)  # "n.a."
    n_chars: int = Field(default_factory=int)
    n_tokens: int = Field(default_factory=int)

    has_hyphen: bool = Field(default_factory=bool)
    end_hyphen: bool = Field(default_factory=bool)
    has_punct: bool = Field(default_factory=bool)
    ends_sentence: bool = Field(default_factory=bool)


class ElementMeta(BaseMeta):
    # element_type: str = Field(default_factory=str)
    # token_id: int | list[int] = Field(default_factory=int)
    # element_id: int = Field(default_factory=int)
    context: dict = Field(default_factory=dict)


class HeadingMeta(ElementMeta):
    # element_type: str = "heading"
    level: int = Field(default_factory=int)


class ListMeta(ElementMeta):
    # element_type: str = "list"
    list_type: str = Field(default_factory=str)


class CodeMeta(ElementMeta):
    # element_type: str = "code"
    language: str = Field(default_factory=str)


class ImageMeta(ElementMeta):
    # element_type: str = "image"
    src: str = Field(default_factory=str)
    downloadable: bool | None = Field(default=None)
    alt: str = Field(default_factory=str)
    style: str = Field(default_factory=str)
    text_file: str = Field(default_factory=str)
    folder: str = Field(default_factory=str)
    image_file: str = Field(default_factory=str)


class CellMeta(BaseMeta):
    language: str | list[str] = Field(default_factory=str)


class SpanMeta(BaseModel):
    x_start: float = Field(default_factory=float)
    x_end: float = Field(default_factory=float)
    y_start: float = Field(default_factory=float)
    y_end: float = Field(default_factory=float)

    size: float = Field(default_factory=float)
    alpha: float = Field(default_factory=float)
    flags: int = Field(default_factory=int)
    # List = Field(default_factory=list)
    font: str = Field(default_factory=str)
    color: int = Field(default_factory=int)
    # List = Field(default_factory=list)


class WordMeta(SpanMeta):
    is_bold: bool = Field(default_factory=bool)


class TextWordMeta(BaseModel):
    word_no: int = Field(default_factory=int)
    line_no: int = Field(default_factory=int)
    block_no: int = Field(default_factory=int)


class DocumentMeta(BaseMeta):
    pass


class LineMeta(BaseMeta):
    column: int | None = Field(default=None)
    line_type: str | None = Field(default_factory=str)
    # text_body_id: int | None = Field(default=None)
    # bullet_id: int | None = Field(default=None)

    x_start_min: float = Field(default_factory=float)
    y_start_min: float = Field(default_factory=float)
    y_start_mean: float = Field(default_factory=float)
    x_end_max: float = Field(default_factory=float)
    y_end_max: float = Field(default_factory=float)
    height: float = Field(default_factory=float)
    rel_height: float = Field(default_factory=float)
    width: float = Field(default_factory=float)
    rel_width: float = Field(default_factory=float)
    rel_start: float = Field(default_factory=float)

    is_wide: bool = Field(default_factory=bool)

    is_bold_rel: float = Field(default_factory=float)
    fonts: list[str] = Field(default_factory=list)
    font_sizes: list[float] = Field(default_factory=list)
    font_size_mean: float = Field(default_factory=float)
    font_size_max: float = Field(default_factory=float)
    alpha_mean: float = Field(default_factory=float)


class TextLineMeta(BaseMeta):
    pass


class TextBlockMeta(LineMeta):
    pass


class BulletMeta(BaseModel):
    # bullet_id: int = Field(default_factory=int)
    char: str = Field(default_factory=str)
    bbox: list = Field(default_factory=list)
    origin: str = Field(default_factory=str)


class PageMeta(BaseModel):
    height: float = Field(default_factory=float)
    width: float = Field(default_factory=float)
    median_font_size: float = Field(default_factory=float)
    max_font_size: float = Field(default_factory=float)
    fonts: list[str] = Field(default_factory=list)
    is_bold_rel: float = Field(default_factory=float)
    left_indent: float = Field(default_factory=float)
    right_indent: float = Field(default_factory=float)


class DrawingMeta(BaseModel):
    # drawing_id: int = Field(default_factory=int)
    fill: str = Field(default_factory=str)
    color: str = Field(default_factory=str)
    width: float = Field(default_factory=float)
    draw_type: str = Field(default_factory=str)
    n_items: int = Field(default_factory=int)
    bbox: list = Field(default_factory=list)


class WikiPageMeta(BaseModel):
    # page_id: int = Field(default_factory=int)
    wordcount: int = Field(default_factory=int)
    timestamp: str = Field(default_factory=str)


# class WikiPageMeta(BaseModel):
#     source: str = "wikipedia"
#     url: str
#     # chunk_id: int
#     n_tokens: int


# -------------------------
# LEAF_ELEMENTS
# -------------------------
class BaseLeaf(BaseModel):
    leaf_id: int|None = None 
    leaf_type: str
    text: str = Field(default_factory=str)
    meta: ElementMeta
    markups: List[dict] = Field(default_factory=list)


class TextNode(BaseLeaf):
    leaf_type: Literal["text_node"] = "text_node"
    inline_elements: list = Field(default_factory=list)


class CodeNode(TextNode):
    leaf_type: Literal["code_node"] = "code_node"


class LinkNode(TextNode):
    leaf_type: Literal["link_node"] = "link_node"
    href: str


class LinkPreviewNode(TextNode):
    leaf_type: Literal["link_preview_node"] = "link_preview_node"


class ImageNode(TextNode):
    leaf_type: Literal["image_node"] = "image_node"
    src: str = ""
    alt: str = ""
    meta: ImageMeta
    meta_from_html: Dict = {}


class CiteNode(TextNode):
    leaf_type: Literal["cite_node"] = "cite_node"
    href: str


class BulletNode(TextNode):
    leaf_type: Literal["bullet_node"] = "bullet_node"


class BlockQuoteNode(TextNode):
    leaf_type: Literal["block_quote"] = "block_quote" 


class OtherNode(TextNode):
    leaf_type: Literal["other_node"] = "other_node"


class Word(BaseLeaf):
    leaf_type: Literal["word"] = "word"
    meta: WordMeta | TextWordMeta | None = Field(default_factory=WordMeta)


class Span(BaseLeaf):
    leaf_type: Literal["span"] = "span"
    meta: SpanMeta | None = Field(default_factory=SpanMeta)


class Bullet(BaseLeaf):
    leaf_type: Literal["bullet"] = "bullet"
    meta: BulletMeta | None = Field(default_factory=BulletMeta)


class Drawing(BaseLeaf):
    leaf_type: Literal["drawing"] = "drawing"
    meta: DrawingMeta | None = Field(default_factory=DrawingMeta)


class Image(BaseLeaf):
    leaf_type: Literal["image"] = "image"
    meta: ImageMeta | None = Field(default_factory=ImageMeta)


class ResultItem(BaseModel):
    leaf_type: Literal["result_item"] = "result_item"
    title: str = Field(default_factory=str)
    page_id: int | None = Field(default=None)
    snippet: str = Field(default_factory=str)
    word_count: int | None = Field(default=None)
    timestamp: str = Field(default_factory=str)

    #
    # list

"""
# class WikiPage(BaseModel):
#     title: str = Field(default_factory=str)
#     text:  str = Field(default_factory=str)
#     meta: WikiPageMeta = Field(default_factory=WikiPageMeta)


# class GraphMeta(BaseModel):
#     graph_type: str = Field(default_factory=str)
#     page_no: int = Field(default_factory=int)
#     drawings: List[DrawMeta] = Field(default_factory=list)
#     bullets: List[BulletMeta] = Field(default_factory=list)


# class Image(BaseLeaf):
#     # elements: List[Word]  = Field(default_factory=list)
#     meta: ImageMeta  = Field(default_factory=ImageMeta)

"""
# -------------------------
# CONTAINER_ELEMENTS
# -------------------------
class BaseContainer(BaseModel):
    container_type: str
    container_id: int|None = None
    text: str = Field(default_factory=str)
    elements: list[Word] = Field(default_factory=list)
    meta: BaseMeta = Field(default_factory=BaseMeta)


class Line(BaseContainer):
    container_type: Literal["line"] = "line"
    # elements: List[Word] = Field(default_factory=list)
    # line_type: str = Field(default_factory=str)
    meta: LineMeta = Field(default_factory=LineMeta)


class LineSplit(BaseContainer):
    container_type: Literal["line_split"] = "line_split"
    # line_type: str = Field(default_factory=str)
    meta: LineMeta = Field(default_factory=LineMeta)


class LineGroup(BaseContainer):
    container_type: Literal["line_group"] = "line_group"
    line_type: str = Field(default_factory=str)
    meta: LineMeta = Field(default_factory=LineMeta)


class TextLine(BaseContainer):
    container_type: Literal["text_line"] = "text_line"
    line_type: str = Field(default_factory=str)
    meta: TextLineMeta = Field(default_factory=TextLineMeta)


class Element(BaseContainer):
    container_type: Literal["element"] = "element"
    meta: ElementMeta | None = Field(default_factory=ElementMeta)
    elements: list[Word | Image] = Field(default_factory=list)
    inline_elements: list = Field(default_factory=list)
    # language: str  = Field(default_factory=str)


class Paragraph(Element):
    container_type: Literal["paragraph"] = "paragraph"


class BulletList(Element):
    container_type: Literal["bullet_list"] = "bullet_list"


class Heading(Element):
    container_type: Literal["heading"] = "heading"
    meta: HeadingMeta | None = Field(default_factory=HeadingMeta)


class Link(Element):
    container_type: Literal["link"] = "link"
    extern: bool = Field(default=False)
# class Paragraph(Element):
#     container_type: Literal["paragraph"] = "paragraph"
#     meta: Optional[HeadingMeta]  = Field(default_factory=HeadingMeta)


class Code(Element):
    container_type: Literal["code"] = "code"
    # elements: List[Word]  = Field(default_factory=list)
    meta: CodeMeta = Field(default_factory=CodeMeta)


class Graphics(BaseContainer):
    container_type: Literal["graphics"] = "graphics"
    # elements: List[Word]  = Field(default_factory=list)
    drawings: list[Drawing] = Field(default_factory=list)
    bullets: list[Bullet] = Field(default_factory=list)


class Cell(BaseContainer):
    container_type: Literal["cell"] = "cell"
    cell_type: Literal["code_block", "md_block", ""] = ""  # Field(default=tr)
    cell_id: int = Field(default_factory=int)
    meta: CellMeta = Field(default_factory=CellMeta)
    elements: list[Word | Element] = Field(default_factory=list)
    # language: str  = Field(default_factory=str)


class TextBlock(BaseContainer):
    container_type: Literal["text_block"] = "text_block"
    meta: TextBlockMeta = Field(default_factory=TextBlockMeta)
    elements: list[LineGroup] = Field(default_factory=list)


class Document(BaseContainer):
    container_type: Literal["document"] = "document"
    elements: list[Word] = Field(default_factory=list)
    meta: DocumentMeta = Field(default_factory=DocumentMeta)


class CollectionItem(BaseContainer):
    container_type: Literal["collection_item"] = "collection_item"
    doc_name: str = Field(default_factory=str)
    page: int = Field(default_factory=int)
    text_bodies: list[dict] = Field(default_factory=list)
    headings: list[dict] = Field(default_factory=list)
    text: str = Field(default_factory=str)
    text_merged: str = Field(default_factory=str)


class SearchResult(BaseContainer):
    container_type: Literal["search_result"] = "search_result"
    query: str = Field(default_factory=str)
    params: dict = Field(default_factory=dict)
    elements: list[ResultItem] = Field(default_factory=list)
    suggestion: str | None = Field(default_factory=str)
    suggestion_hits: int | None = Field(default_factory=int)

"""
# class Blocks()


# -------------------------
# SUMMARIES
# -------------------------

# class LineExtract:
#     text = str
#     elements: List = []
#     meta: LineMeta

"""
class DocumentExtract(BaseModel):
    doc_type: Literal["",
                      "md",
                      "html",
                      "html_apollo",
                      "pdf",
                      "txt",
                      "json_nb"] = Field(default="")
    doc_name: str
    text: str  #  = text,
    elements: List = Field(default_factory=list)
    meta: DocumentMeta = Field(default_factory=DocumentMeta)
    non_text: List = Field(default_factory=list)
    # foot_notes: List  = Field(default_factory=list)
    # headings: List  = Field(default_factory=list)


class PageExtract(DocumentExtract):
    page_no: int = Field(default_factory=int)
    meta: PageMeta = Field(default_factory=PageMeta)
    # graphics: Graphics = Field(default_factory=Graphics)
    # images: List[Image] = Field(default_factory=List)
    # non_text: List  = Field(default_factory=list)
    # foot_notes: List  = Field(default_factory=list)
    # headings: List  = Field(default_factory=list)
    # header_footer: List  = Field(default_factory=list)
    # text_bodies: List  = Field(default_factory=list)

"""
"""
line_types = Annotated[LineSplit | Line | LineGroup, 
                       Field(discriminator="meta_type")]

container_types = Annotated[
    Document | Line | LineSplit | Element | Heading | TextBlock | Code,
    Field(discriminator="meta_type"),
]
"""
#
