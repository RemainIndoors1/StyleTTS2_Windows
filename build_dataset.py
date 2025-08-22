import os
import random
import subprocess
import unicodedata
import re

# Input and output file paths
input_file = 'Path/to/metadata.csv'

def phonemize_with_espeak(text):
    result = subprocess.run(
        ['espeak-ng', '-q', '--ipa=3', text],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    # Combine lines into one
    ipa_raw = result.stdout.strip().replace('\n', ' ').replace('\r', ' ')

    # Normalize and remove invisible characters (like ZERO WIDTH JOINER)
    ipa_clean = unicodedata.normalize('NFKD', ipa_raw)
    ipa_clean = ''.join(c for c in ipa_clean if not unicodedata.category(c).startswith('C'))

    # Collapse multiple spaces
    ipa_clean = ' '.join(ipa_clean.split())

    return ipa_clean

def phonemize_line(line):
    parts = line.strip().split('|')
    if len(parts) != 3:
        return None
    wav, text, speaker_id = parts
    
    # replacing asterisks with em dash to cover pause after footnote in asterisks
    # example: "*smiles brightly* I'm very happy to see you" should become "smiles brightly— I'm very happy to see you"
    text = text.replace('* ', '— ')
    text = text.replace(' *', ' ')
    text = re.sub(r'^[\*]', '', text.strip)
    text = re.sub(r'[\*]$', '', text)

    text = text.replace('"', '')
    text = text.replace('’', "'") # replace invalid utf-8 apostrophe
    text = text.replace('​', '') # zero-width space whitespace character
    text = text.replace('&', ' and ') # convert ampersand to and for pronunciation
    text = text.replace("%", " percent") # convert percent to spoken word
    text = text.replace("  ", " ") # get rid of double spaces
    text = text.replace("...", "…") # convert three periods to ellipsis
    
    chunks = re.split(r'([^\w\s\']+)', text)

    phonemized_chunks = []
    for chunk in chunks:
        if re.match(r'([\w\s\']+)', chunk.strip()):
            phonemized_chunk = phonemize_with_espeak(chunk.strip())
            phonemized_chunks.append(phonemized_chunk)
        elif len(chunk.strip()) > 0:
            phonemized_chunks.append(chunk.strip())

    phonemes = ' '.join(phonemized_chunks)

    return f"{wav}|{phonemes.strip()}|{speaker_id}"

with open(input_file, 'r', encoding='utf-8') as f:
   lines = [line.strip() for line in f if "|" in line]
   split_idx = int(len(lines) * 0.9)
   random.shuffle(lines)

with open("Data/train_list.txt", "w", encoding="utf-8") as f:
   for line in lines[:split_idx]:
       phonemized = phonemize_line(line)
       f.write(f"{phonemized}\n")

with open("Data/val_list.txt", "w", encoding="utf-8") as f:
   for line in lines[split_idx:]:
       phonemized = phonemize_line(line)
       f.write(f"{phonemized}\n")
