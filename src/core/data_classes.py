## base_data.py
# import
from pydantic import BaseModel, Field
from typing import List, Dict, Optional       #


# -------------------------
# METADATA
# -------------------------
class BaseMeta(BaseModel):
    n_words: int = Field(default_factory=int) # "n.a."
    n_chars: int = Field(default_factory=int)
    n_tokens: int = Field(default_factory=int)

    has_hyphen: bool = Field(default_factory=bool)
    end_hyphen: bool  = Field(default_factory=bool)
    has_punct: bool = Field(default_factory=bool)
    ends_sentence: bool = Field(default_factory=bool)


class ElementMeta(BaseMeta):
    element_type: str = Field(default_factory=str)
    language: str = Field(default_factory=str)
    level: int = Field(default_factory=int)
    token_id: int | List[int] = Field(default_factory=int)
    element_id: int = Field(default_factory=int)
    list_type: str = Field(default_factory=str)
    context: Dict = Field(default_factory=dict)


class SpanMeta(BaseModel): 
    x_start: float = Field(default_factory=float)
    x_end: float = Field(default_factory=float)
    y_start: float = Field(default_factory=float)
    y_end: float = Field(default_factory=float)

    size: float = Field(default_factory=float)
    alpha: float = Field(default_factory=float)
    flags: List = Field(default_factory=list)
    font: str = Field(default_factory=str)
    color: List = Field(default_factory=list)


class WordMeta(SpanMeta):
    is_bold: bool = Field(default_factory=bool)


class TextWordMeta(BaseModel):
    word_no: int = Field(default_factory=int)
    line_no: int = Field(default_factory=int)
    block_no: int = Field(default_factory=int) 


class DocumentMeta(BaseMeta):
    pass


class LineMeta(BaseMeta):
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
    fonts: List[str] = Field(default_factory=list)
    font_sizes: List[float] = Field(default_factory=list)
    font_size_mean: float = Field(default_factory=float)
    font_size_max: float = Field(default_factory=float)
    alpha_mean: float = Field(default_factory=float)


class TextLineMeta(BaseMeta):
    pass


class TextBlockMeta(BaseMeta):
    pass


class BulletMeta(BaseModel):
    bullet_id: int = Field(default_factory=int)
    char: str = Field(default_factory=str)
    bbox: List = Field(default_factory=list)
    origin: str = Field(default_factory=str)


class PageMeta(BaseModel):
    height: float = Field(default_factory=float)
    width: float = Field(default_factory=float)


class DrawMeta(BaseModel):
    drawing_id: int = Field(default_factory=int)
    fill: str = Field(default_factory=str)
    color: str = Field(default_factory=str)
    width: float = Field(default_factory=float)
    draw_type: str = Field(default_factory=str)
    n_items: int = Field(default_factory=int)
    bbox: List = Field(default_factory=list)


class GraphMeta(BaseModel):
    graph_type: str = Field(default_factory=str)
    page_no: int = Field(default_factory=int)
    drawings: List[DrawMeta] = Field(default_factory=list)
    bullets: List[BulletMeta] = Field(default_factory=list)

# -------------------------
# LEAF_ELEMENTS 
# -------------------------
class BaseLeaf(BaseModel):
    text: str = Field(default_factory=str)


class Word(BaseLeaf):
    meta: Optional[WordMeta | TextWordMeta] = Field(default_factory=WordMeta)


class Span(BaseLeaf):
    pass


class Graphic(BaseLeaf):
    elements: List[Word]  = Field(default_factory=list)
    meta: GraphMeta  = Field(default_factory=GraphMeta)

# -------------------------
# CONTAINER_ELEMENTS 
# -------------------------
class BaseContainer(BaseLeaf):
    structure_level: str
    elements: List[Word] = Field(default_factory=list)
    meta: BaseMeta = Field(
                    default_factory=BaseMeta
                    )


class Line(BaseContainer):
    structure_level: str = "line"
    line_type: str = Field(default_factory=str)
    meta: LineMeta = Field(default_factory=LineMeta)


class TextLine(BaseContainer):
    structure_level: str = "text_line"
    line_type: str = Field(default_factory=str)
    meta: TextLineMeta = Field(default_factory=TextLineMeta)


class Element(BaseContainer):
    structure_level: str = "element"
    meta: ElementMeta  = Field(default_factory=ElementMeta)
    elements: List[Word]  = Field(default_factory=list)
    # language: str  = Field(default_factory=str)


class TextBlock(BaseContainer):
    structure_level: str = "text_block"
    meta: TextBlockMeta  = Field(default_factory=TextBlockMeta)
    elements: List[Line]  = Field(default_factory=list)


class Document(BaseContainer):
    structure_level: str = "document"
    elements: List[Word]  = Field(default_factory=list)
    meta: DocumentMeta  = Field(default_factory=DocumentMeta)

# class Blocks()


# -------------------------
# SUMMARIES
# -------------------------

# class LineExtract:
#     text = str
#     elements: List = []
#     meta: LineMeta

class DocumentExtract(BaseModel):
    doc_type: str   #  = "txt",
    doc_name: str
    text: str   #  = text,
    elements: List  = Field(default_factory=list)
    meta: DocumentMeta  = Field(default_factory=DocumentMeta)
    non_text: List  = Field(default_factory=list)


class PageExtract(DocumentExtract):
    page_no: int  = Field(default_factory=int)
    meta: PageMeta  = Field(default_factory=PageMeta)



