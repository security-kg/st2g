def test_spacy_install():
    import spacy
    nlp = spacy.load("en_core_web_sm")
    # If failed, try to run: "python3 -m spacy download en_core_web_sm"
