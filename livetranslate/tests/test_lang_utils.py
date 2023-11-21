from livetranslate.lang_utils import merge

def test_merge():
    assert merge(
            "la zona oeste de Rio de Janeiro fue construido como",
            "de Janeiro fue construido como si fuera una especie de",
            ) == ("la zona oeste de Rio de Janeiro fue construido como si fuera una especie de", True)


    assert merge(
            "la zona oeste de Rio de Janeiro fue construido como",
            "como si fuera una especie de",
            ) == ("la zona oeste de Rio de Janeiro fue construido como si fuera una especie de", True)


    assert merge(
            "la zona oeste de Rio de Janeiro fue construido como",
            "si fuera una especie de",
            ) == ("si fuera una especie de", False)
