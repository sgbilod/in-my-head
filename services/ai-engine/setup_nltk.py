"""
Download required NLTK data for chunking service.
"""

import nltk
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_nltk_data():
    """Download all required NLTK datasets."""
    
    print("\n" + "=" * 70)
    print("DOWNLOADING NLTK DATA")
    print("=" * 70 + "\n")
    
    datasets = [
        'punkt',  # Sentence tokenizer
        'punkt_tab',  # Punkt tokenizer models (new format)
        'averaged_perceptron_tagger',  # POS tagger
        'stopwords',  # Stop words
    ]
    
    for dataset in datasets:
        try:
            print(f"📥 Downloading {dataset}...")
            nltk.download(dataset, quiet=False)
            print(f"✅ {dataset} downloaded successfully\n")
        except Exception as e:
            print(f"❌ Failed to download {dataset}: {e}\n")
    
    print("=" * 70)
    print("✅ NLTK DATA DOWNLOAD COMPLETE")
    print("=" * 70 + "\n")
    
    # Verify installation
    print("🔍 Verifying installation...")
    try:
        from nltk.tokenize import sent_tokenize, word_tokenize
        
        test_text = "This is a test. It has two sentences."
        sentences = sent_tokenize(test_text)
        words = word_tokenize(test_text)
        
        print(f"  ✅ Sentence tokenization: {len(sentences)} sentences")
        print(f"  ✅ Word tokenization: {len(words)} words")
        print("\n✅ NLTK is ready to use!")
        
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")


if __name__ == "__main__":
    download_nltk_data()
