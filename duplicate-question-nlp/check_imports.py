import sys

checks = [
    ("pandas", "pandas"),
    ("numpy", "numpy"),
    ("matplotlib", "matplotlib.pyplot"),
    ("seaborn", "seaborn"),
    ("scipy", "scipy.sparse"),
    ("re", "re"),
    ("collections", "collections.Counter"),
    ("nltk", "nltk"),
    ("nltk_tokenize", "nltk.tokenize"),
    ("nltk_corpus", "nltk.corpus"),
    ("gensim", "gensim.models"),
    ("sklearn_tfidf", "sklearn.feature_extraction.text"),
    ("sklearn_lr", "sklearn.linear_model"),
    ("sklearn_svm", "sklearn.svm"),
    ("sklearn_model_selection", "sklearn.model_selection"),
    ("sklearn_metrics", "sklearn.metrics"),
    ("data_loader", "data_loader")
]

for name, mod in checks:
    try:
        __import__(mod)
        print(f"OK: {mod}")
    except Exception as e:
        print(f"ERR: {mod} -> {e}")

# Try downloading NLTK resources (quiet)
try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    print('NLTK downloads attempted (punkt, stopwords).')
except Exception as e:
    print(f'NLTK download error -> {e}')

print('Import check finished.')
