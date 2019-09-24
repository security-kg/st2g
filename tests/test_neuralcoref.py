import pytest
from pprint import pprint


@pytest.mark.skip(reason="Won't work with my binaries.")
def test_neuralcoref_with_spacy():
    import spacy
    nlp = spacy.load('en_core_web_sm')

    # Add neural coref to SpaCy's pipe
    import neuralcoref
    neuralcoref.add_to_pipe(nlp)

    # You're done. You can now use NeuralCoref as you usually manipulate a SpaCy document annotations.
    doc = nlp(u'My sister has a dog. She loves him.')

    print(doc._.has_coref)
    print(doc._.coref_clusters)
