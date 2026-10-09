## docx_extractor.py
# import
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# from docx import Document
# from docx.oxml.table import CT_Tbl
# from docx.oxml.text.paragraph import CT_P
# from docx.table import Table
# from docx.text.paragraph import Paragraph

# import streamlit as st
from returns.result import Result, Success

from src.model_parsing.base_classes_parsing import (
    BulletItem,
    BulletList,
    Code,
    DocumentExtract,
    DOCXImageMeta,
    Element,
    Heading,
    HeadingMeta,
    Image,
    Quote,
    RawDocument,
    TableCell,
    TableMeta,
    TableObject,
    TableRow,
    TextBlock,
    Word,
    WordMeta,
)
from src.model_parsing.base_extractor import BaseExtractor
from src.utils.dict_helper import save_dict


@dataclass
class DOCXCleanExtractor(BaseExtractor):
    mode: Literal["brief", "long"] = "brief"
    bullets: list = field(default_factory=list, init=False)

    def setup(self):
        self.mode = self.extract_config.tbl_text_mode

    def extract(self, f_path: str) -> Result[DocumentExtract, str]:
        doc = Document(f_path)

        blocks = list(self._iter_block_items(doc))

        self.logger.info("Length 'blocks': %s", len(blocks))

        blocks_all = []
        for idx, block in enumerate(blocks):
            next_block = blocks[idx + 1] if idx + 1 < len(blocks) else None

            bullet_next = (
                isinstance(next_block, Paragraph)
                and next_block.style.name == "Aufzählung"
            )

            # for idx, block in enumerate(self._iter_block_items(doc)):

            # bullet_next = (
            #         idx < len(doc.paragraphs) - 1
            #         and doc.paragraphs[idx+1].style.name == "Aufzählung"
            #         )

            # if block.container_type == "heading":
            #     # is_heading(block):
            #     level = self._get_heading_level(block.style.name)
            #     current_context = current_context[:level - 1]
            #     current_context.append(block.text)

            if isinstance(block, Paragraph):
                # heading / normal / bullet parsing

                images = self._extract_images_from_paragraph(block, idx)

                if images:
                    blocks.extend(images)

                if block.text.strip():
                    parsed = self._extract_paragraph(
                        para=block, para_idx=idx, bullet_next=bullet_next
                    )

                    if parsed is not None:
                        blocks_all.append(parsed)
                    else:
                        self.logger.info(
                            "Skipped paragraph idx=%s style=%r text=%r",
                            idx,
                            block.style.name,
                            block.text[:80],
                        )

            elif isinstance(block, Table):
                # table parsing
                parsed = self._extract_table(
                    tbl=block,
                    tbl_idx=idx,
                    # bullet_next=""
                )

                if parsed is not None:
                    blocks_all.append(parsed)
                else:
                    self.logger.info(
                        "Skipped paragraph idx=%s style=%r text=%r",
                        idx,
                        block.style.name,
                        block.text[:80],
                    )
            else:
                self.logger.info("Unknown block type: ", type(block))

        # tables = self._extract_table(doc)

        # text_clean = "\n\n".join([p.text for p in para_clean])

        # doc_info.elements.extend(tables)
        # doc_info = self.enricher.enrich

        self.logger.info("Length 'blocks_all': %s", len(blocks_all))

        doc_info = self._add_head_context(blocks_all)  # doc_info

        save_path = Path(f"{self.save_folder}/{self.save_name}_info")
        save_dict(
            data=doc_info.model_dump(
                mode="json",
                serialize_as_any=True,
            ),
            path=save_path,
        )

        return Success(
            DocumentExtract(
                doc_type="docx",
                doc_name=self.doc_name,
                text=doc_info.text,
                # tables=tables,
                elements=doc_info.elements,
                meta=doc_info.meta,
            )
        )

    def _iter_block_items(self, doc: Document):
        body = doc.element.body

        for child in body.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, doc)

            elif isinstance(child, CT_Tbl):
                yield Table(child, doc)

    def _paragraph_has_image(self, p: Paragraph):
        return bool(p._element.xpath(".//w:drawing | .//w:pict"))

    def _add_head_context(
        self,
        elements: list,
        # doc_info: RawDocument
    ) -> RawDocument:
        elements_sorted = sorted(elements, key=lambda e: e.container_id)

        text = []
        current_context = []
        # blocks = []

        for ele in elements_sorted:
            c_type = ele.container_type
            content = ele.text or None
            # ).strip()

            if content is None:
                continue

            if c_type == "heading":
                level = ele.meta.level or 1

                # alle Headings gleicher oder tieferer Ebene entfernen
                current_context = current_context[: level - 1]
                current_context.append(content)

                prefix = "#" * level
                text.append(f"{prefix} {content}")

            elif c_type in [
                "bullet_list",
                "code",
                "image",
                "quote",
                "table",
                "text_block",
            ]:
                ele.context = current_context.copy()

                # if c_type == "bullet_list":
                #     text.append(content)
                # else:
                text.append(content)

                # blocks.append(ele)

        # doc_info.text =
        # doc_info.elements = elements_sorted #  blocks

        return RawDocument(elements=elements_sorted, text="\n\n".join(text))

    # {
    #         "text": "\n\n".join(text),
    #         "blocks": blocks,
    #     }

    # headings = []
    # non_heads = []
    # for para in doc_info:
    #     if para.container_type == "heading":
    #         headings.append(para)

    #     else:
    #         non_heads.append(para)

    # heads_sorted = sorted(headings,
    #                      key=lambda p: p.container_id)
    # non_heads_sorted = sorted(non_heads,
    #                      key=lambda p: p.container_id)

    # text = []
    # idx = 0
    # relevant_heads = []
    # head_lvl = None

    # for idx, para in enumerate(para_sorted):
    #     if para.container_type == "heading":
    #         if not head_lvl:
    #             # or para.meta.level <= head_lvl:
    #             relevant_heads = []

    #         relevant_heads[head_lvl]

    #     else:
    #         para.context = relevant_heads

    # return

    def _is_code_paragraph(self, para) -> bool:
        style = para.style.name.lower()

        if "code" in style:
            return True

        fonts = {run.font.name for run in para.runs if run.font.name}

        monospace_fonts = {"consolas", "courier new", "menlo", "monaco"}
        return any(f.lower() in monospace_fonts for f in fonts)

    def _is_quote(self, para) -> bool:
        style = para.style.name.lower()
        return any(x in style for x in ["quote", "zitat"])

    def _get_heading_level(self, style_name: str) -> int:
        match = re.search(r"\d+", style_name)
        return int(match.group()) if match else 1

    def _extract_images_from_paragraph(
        self, para: Paragraph, para_idx: int
    ) -> list[Image]:
        images = []

        drawings = para._element.xpath(".//w:drawing | .//w:pict")

        for img_idx, drawing in enumerate(drawings):
            blips = drawing.xpath(".//a:blip")

            size = self._get_image_size_emu(drawing)

            for blip in blips:
                r_id = blip.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )

                if not r_id:
                    continue

                image_part = para.part.related_parts[r_id]
                image_bytes = image_part.blob
                content_type = image_part.content_type  # z.B. image/png

                img_suffix = content_type.split("/")[-1]

                file_name = f"image_{self.save_name}.{img_suffix}"

                save_path = f"{self.save_folder}/{file_name}"

                Path(save_path).write_bytes(image_bytes)

                src = ""
                alt = ""

                images.append(
                    Image(
                        text=f"[IMAGE]({src or alt or 'text missing'})",
                        img_idx=img_idx,
                        container_id=para_idx,
                        meta=DOCXImageMeta(
                            alt=alt,
                            src=src,
                            folder=self.save_folder,
                            img_name=file_name,
                            byte_size=len(image_bytes),
                            img_suffix=img_suffix,
                            relationship_id=r_id,
                            width_cm=size.get("width_cm"),
                            height_cm=size.get("height_cm"),
                        ),
                    )
                )

        return images

    def _get_image_size_emu(self, drawing):
        extent = drawing.xpath(".//wp:extent")
        if not extent:
            return None

        cx = int(extent[0].get("cx"))
        cy = int(extent[0].get("cy"))

        return {
            "width_emu": cx,
            "height_emu": cy,
            "width_cm": cx / 360000,
            "height_cm": cy / 360000,
        }

    def _extract_paragraph(self, para, para_idx: int, bullet_next: bool):
        # para_all = []
        # container_id = 0

        # for idx, p in enumerate(doc.paragraphs):

        p_text = para.text.strip()

        p_elements = []
        for word in p_text.split():
            p_elements.append(Word(text=word, meta=WordMeta()))
        temp_info = self.enricher._add_basic_metadata(
            text=p_text, leaf_info=p_elements, info_obj=Element()
        )

        match para.style.name:
            # case style if self._is_horizontal_rule(para):
            #     return HorizontalRule(...)

            case style if style.startswith("Heading") or style.startswith(
                "Überschrift"
            ):
                # para_all.append(
                return Heading(
                    meta=HeadingMeta(level=self._get_heading_level(style)),
                    text=temp_info.text,
                    elements=temp_info.elements,
                    container_id=para_idx,
                )

            case style if self._is_quote(para):
                # "quote" in style.lower() or "zitat" in style.lower():
                return Quote(
                    text=f"'{temp_info.text}'",
                    elements=temp_info.elements,
                    container_id=para_idx,
                )

            case style if self._is_code_paragraph(para):
                return Code(
                    text=temp_info.text,
                    elements=temp_info.elements,
                    container_id=para_idx,
                    # meta = CodeMeta(
                    # )
                )

            case "Aufzählung":
                self.bullets.append(
                    BulletItem(text=temp_info.text, elements=temp_info.elements)
                )

                if not bullet_next:
                    # para_all.append(

                    bullet_list = BulletList(
                        elements=self.bullets.copy(),
                        text="\n".join(b.text for b in self.bullets),
                        #  + "\n",
                        container_id=para_idx,
                    )
                    self.bullets = []

                    return bullet_list

                    # container_id += 1
                    # bullets = []

            case "Normal":
                if p_text:
                    # para_all.append(
                    return TextBlock(
                        text=temp_info.text,
                        elements=temp_info.elements,
                        container_id=para_idx,
                    )

            case _:
                self.logger.warning(
                    "Unsupported DOCX style '%s' in paragraph %d",
                    para.style.name,
                    para_idx,
                )

        return None

    def _create_row_text(self, cells_all: list):
        """
        'long' - e.g.:
        Beteiligungsart: führt durch
        Kürzel: D
        Name: Anreicher

        'brief' - e.g.:
        führt durch | D | Anreicher
        """
        if self.mode == "long":
            row_text = ""
            for cell in cells_all:
                row_text += f"{cell.col_name}:\t{cell.text}\n"

        elif self.mode == "brief":
            row_text = "\t|\t".join(c.text for c in cells_all)

        else:
            self.logger.warning("Unknown 'table parsing mode': %s", self.mode)

        return row_text

    def _create_table_text(self, rows_all: list):
        if self.mode == "long":
            table_text = ""
            for row in rows_all:
                table_text += f"[Row #{row.row_id}]:\n{row.text}\n\n"

        elif self.mode == "brief":
            table_text = "\n".join(f"[Row #{r.row_id}]:\t{r.text}" for r in rows_all)

        else:
            self.logger.warning("Unknown 'table parsing mode': %s", self.mode)

        return table_text

    def _is_header_row(self, rows: list[TableRow]) -> bool:
        if not rows:
            return False

        # first = [cell.text.strip() for cell in rows[0]]
        # rest = [[cell.text.strip() for cell in row] for row in rows[1:]]

        # if not any(first):
        #     return False

        # # Ausschluss: erste Zeile sieht wie normale Datenzeile aus
        # data_like_terms = {"D", "B", "I", "V", "PV"}
        # if any(c_text in data_like_terms for c_text in first):
        #     return False

        # # Positiv: typische Header-Wörter
        # header_terms = {
        #     "nr", "nr.", "nummer",
        #     "beschreibung", "kürzel", "name",
        #     "datum", "version",
        #     "beteiligungsart",
        #     "änderung", "änderungen",
        # }

        # normalized = {c_text.lower().strip(":") for c_text in first}
        # if normalized & header_terms:
        #     return True

        # # Positiv: erste Zeile kurz, nachfolgende Zeilen länger
        # first_len = sum(len(c_text) for c_text in first)
        # rest_len = max(
        #     (sum(len(c_text) for c_text in row) for row in rest),
        #     default=0,
        # )

        # if first_len < 80 and rest_len > first_len * 2:
        #     return True

        # return False

        return True

    def _extract_table(self, tbl, tbl_idx: int) -> TableObject:
        # for tbl_idx, tbl in enumerate(doc.tables):
        # col_names_all = []

        rows_all = []
        for row_idx, row in enumerate(tbl.rows):
            cells_all = []
            for cell_idx, cell in enumerate(row.cells):
                # if row_idx == 0:
                #     col_names_all.append(cell.text)

                cell_info = TableCell(
                    text=cell.text,
                    # col_name = (headers[cell_idx] if has_header
                    #             and cell_idx < len(headers) else "")
                    # col_names_all[cell_idx],
                    # row_name = "",
                    col_idx=cell_idx,
                    row_idx=row_idx,
                )

                cells_all.append(self.enricher.enrich_table_cell(cell_info))

            # if len(cells_all) > 0:
            #     if row_idx == 0:
            #         row_text = col_names_all.copy()
            #     else:
            #         row_text = self._create_row_text(cells_all)
            # else:
            #     row_text = ""

            rows_all.append(
                TableRow(
                    row_id=row_idx,
                    elements=cells_all,
                    # is_header = self._is_header_row(cells_all),
                    has_empty_cells=any(not c.text.strip for c in cells_all),
                    # text = row_text
                )
            )

        has_header = self._is_header_row(rows_all)

        if has_header:
            header = rows_all[0]

            # for cell in header.elements:
            header.is_header = True

            col_names = [cell.text for cell in header.elements]

            for row in rows_all[1:]:
                for cell in row.elements:
                    cell.col_name = col_names[cell.col_idx]

                row.is_header = False
                row.text = self._create_row_text(row.elements)

                # cell.text = self._create_row_text(cells_all)
        else:
            col_names = []

            # [cell.text.strip() for cell in tbl.rows[0].cells]

        # if has_header:headers = [cell.text.strip() for cell in tbl.rows[0].cells]
        # tables_all.append(
        return TableObject(
            container_id=tbl_idx,
            text=self._create_table_text(rows_all) if len(rows_all) > 0 else "",
            elements=rows_all,
            meta=TableMeta(
                n_rows=len(tbl.rows),
                n_cols=max(len(row.cells) for row in tbl.rows),
                # len(tbl.columns),
                has_header=has_header,
                col_names=col_names,
                # any(r.is_header for r in rows_all),
                has_empty_cells=any(r.has_empty_cells for r in rows_all),
                title="",
            ),
            # tbl_rows --> row.cells --> cell.text
        )

        # curl -I https://lightning.ai/me/compute

        # self.logger.info(f"table #{idx}:\n", tbl)
