import argparse
import os

from src.sources.file import FileSource
from src.parsers.text import TextParser
from src.transformers.rules import RuleTransformer

def parse_multiple_values(value):
    if not value:
        return []
    
    if isinstance (value, list):
        values = value

    return values

def main():
    parser = argparse.ArgumentParser(description="CLI for the cbwg Wordlist Generator")
    
    parser.add_argument('-i', type=list, nargs='*', help="Path to the input file/s")
    parser.add_argument('-rules', type=str, help="Path to the directory with .rule file/s")
    parser.add_argument('--input-config', type=str, )
    args = parser.parse_args()

    print(args.i[0])

if __name__ == "__main__":
    main()