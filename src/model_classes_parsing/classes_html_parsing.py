## classes_html_parsing.py
# import
from typing import Literal

from pydantic import Field  # BaseModel,

from src.model_classes_parsing.base_classes_parsing import (
    BaseLeaf,
    # BaseContainer,
    ImageMeta,
)


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
    meta_from_html: dict = {}


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
