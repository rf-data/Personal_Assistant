## classes_html_parsing.py
# import
from typing import (
    Literal,
    Dict
)

from pydantic import Field  # BaseModel, 

from src.model_classes_parsing.base_classes_parsing import (BaseLeaf,
                                                    # BaseContainer,
                                                    Element, 
                                                    HeadingMeta, 
                                                    ImageMeta)

# -------------------------
# LEAF_ELEMENTS
# -------------------------
class TextNode(BaseLeaf):
    leaf_type: Literal["text_node"] = "text_node"
    inline_elements: list = Field(default_factory=list)


class CodeNode(TextNode):
    leaf_type: Literal["code_node"] = "code_node"


class LinkNode(TextNode):
    leaf_type: Literal["link_node"] = "link_node"
    href: str


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


class OtherNode(TextNode):
    leaf_type: Literal["other_node"] = "other_node"


# -------------------------
# CONTAINER_ELEMENTS
# -------------------------
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


class LinkPreview(Link):
    container_type: Literal["link_preview_node"] = "link_preview_node"


class BlockQuote(Element):
    container_type: Literal["block_quote"] = "block_quote" 
