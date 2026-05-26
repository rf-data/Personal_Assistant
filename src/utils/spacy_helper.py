## spacy_helper.py
# imports
import spacy


def load_spacy_model(lang_model: str):  # "en_core_web_sm"
    try:
        return spacy.load(lang_model)
    except OSError:
        from spacy.cli import download

        download(lang_model)
        return spacy.load(lang_model)


def remove_stop_words():

    return
