## data_classes_wiki.py
# import

from pydantic import BaseModel, Field


# class WikiLink(BaseModel):
#     # pass
#     text: str
#     url: str
#     link_type: Literal


# class WikiInfoBox(BaseModel):
#     # pass
#     title: str
#     fields: Dict


# class WikiTable(BaseModel):
#     # pass
#     rows: List
#     header: List
#     captions: List
#     raw_html: str


# class WikiCitationReference(BaseModel):
#     id: int
#     target: str


# class WikiSection(BaseLeaf):
#     text: str
#     title: str
#     level: int
#     parent: str
#     meta: Dict



# -------------------------
# METADATA
# -------------------------
# class BaseMeta(BaseModel):
#     n_words: int = Field(default_factory=int) # "n.a."
#     n_chars: int = Field(default_factory=int)
#     n_tokens: int = Field(default_factory=int)

#     has_hyphen: bool = Field(default_factory=bool)
#     end_hyphen: bool  = Field(default_factory=bool)
#     has_punct: bool = Field(default_factory=bool)
#     ends_sentence: bool = Field(default_factory=bool)

# class Parameter(BaseModel):
#     action: str = Field(default_factory=str)
#     list: str = Field(default_factory=str)
#     format


class WikiPageMeta(BaseModel):
    page_id: int = Field(default_factory=int)
    wordcount: int = Field(default_factory=int)
    timestamp: str = Field(default_factory=str)


class ResultItem(BaseModel):
    title: str = Field(default_factory=str)
    page_id: int | None = Field(default=None)
    snippet: str = Field(default_factory=str)
    word_count: int | None = Field(default_factory=None)
    timestamp: str = Field(default_factory=str)


class SearchResult(BaseModel):
    query: str = Field(default_factory=str)
    params: dict = Field(default_factory=dict)
    results: list[ResultItem] = Field(default_factory=list)
    suggestion: str | None = Field(default_factory=str)
    suggestion_hits: int | None = Field(default_factory=int)
    #
    # list


class WikiPage(BaseModel):
    title: str = Field(default_factory=str)
    text: str = Field(default_factory=str)
    meta: WikiPageMeta = Field(default_factory=WikiPageMeta)


# class WikiLink(BaseModel):
#     # pass
#     text: str
#     url: str
#     link_type: Literal


# class WikiInfoBox(BaseModel):
#     # pass
#     title: str
#     fields: Dict


# class WikiTable(BaseModel):
#     # pass
#     rows: List
#     header: List
#     captions: List
#     raw_html: str


# class WikiCitationReference(BaseModel):
#     id: int
#     target: str


# class WikiSection(BaseLeaf):
#     text: str
#     title: str
#     level: int
#     parent: str
#     meta: Dict


"""


class WikiPage(BaseLeaf):
    page_title: str
    text: str
    sections: List[WikiSection]
    meta: Optional[WikiPageMeta]
    
"""
