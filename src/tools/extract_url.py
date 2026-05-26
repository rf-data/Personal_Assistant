def extract_url(url: str, enricher, save: bool = True):
    for u in url:
        session_state.save_folder = Path(f"{data_processed}/html_files/extracted")
        session_state.save_name = f"{now}_{u}_extracted"

        extractor = HTMLCleanExtractor(enricher=feat_enricher)

        html_extract = extract_html_file(extractor, u, save=True)

        # assemble_config = run_config.get(f"{text_type}_assembly", {})

        if run_config.get("assemble_as_md"):
            # text = html_extract.text

            save_name = "url_md"
            assembler = BaseAssembler()
            text = assembler.create_md_from_extract(html_extract.model_dump())
            # text = md(text)
            save_text_file(text, save_name, session_state.save_folder)
