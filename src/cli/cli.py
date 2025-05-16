import argparse
import os
#import json

from src.sources.file import FileSource
from src.parsers.text import TextParser
from src.transformers.rules import RuleTransformer

def main():
    parser = argparse.ArgumentParser(description="CLI for the cbwg Wordlist Generator")
    
    parser.add_argument('-p', type=list, nargs='*', required=True, help="Path to the input file/s")
    parser.add_argument('-r', type=str, help="Path to the directory with .rule file/s")
    parser.add_argument('--source-config', type=str, help="Path to the file containing the source config")
    parser.add_argument('--parser-config', type=str, help="Path to the file containing parser config")
    parser.add_argument('--trans-engine-config', type=str, help="Path to the file containing transformation engine config")

    args = parser.parse_args()

    paths = [''.join(p) for p in args.p]

    
    if args.source_config:
        config = parse_config(args.source_config, "source")
        if config:
            source_config = config
        source = FileSource(paths, source_config)
    else:
        source = FileSource(paths)

    if args.parser_config:
        config = parse_config(args.source_config, "parser")
        if config:
            parser_config = config
            text = TextParser(parser_config)
    else:
        text = TextParser()

    if args.trans_engine_config:
        config = parse_config(args.source_config, "engine")
        if config:
            rule_config = config
        transformer = RuleTransformer(rule_config)
    elif args.r:
        rule_config = {"rules_path" : args.r}
        transformer = RuleTransformer(rule_config)
    else:
        transformer = RuleTransformer()
    
    
    words = []
    for data in source.get_data():
        for word in text.parse(data):
            words.append(word)
    results = list(transformer.transform(words))
    for i in range(0, 30):
        print(results[i])
    
    

    
    
    
# def parse_config_source(filename):
#     with open("r", filename) as file:
#         config = {}
#         for line in file:
#             line = line.strip(" ")
#             index = line.index("=")
#             key = line[:index]
#             value = line[index + 1:]
#             if not validate(key, value, "source"):
#                 return False
#             else:
#                 config[key] = value

def parse_config(filename, type):
    config = {}
    with open("r", filename) as file:
        for line in file:
            line = line.strip(" ")
            index = line.index("=")
            key = line[:index]
            value = line[index + 1:]
            validate_result = validate(key, type) 
            if validate_result:
                match validate_result:
                    case 2:
                        config[key] = bool(value)
                    case 1:
                        config[key] = value # already a string
                    case 2:
                        config[key] = int(value)
            else:
                return None
    return config
        
            

def validate(key, config_type):
    # dicts, for casting: 2 - boolean, 1 - string, 0 - int
    allowed_source = {"binary_mode" : 2, "encoding" : 1, "chunk_size" : 0}
    allowed_parser = ["min_length", "max_length", "pattern", "include_numbers", "preserve_case", "exclude_words"]
    allowed_rule = ["rules_path", "batch_size", "verbose_logging", "rules"]
    match config_type:
        case "source":
            if key not in allowed_source:
                return None
            return allowed_source[key]                      

        case "parser":
            return False if key not in  allowed_parser else True
        
        case "rule":
            return False if key not in  allowed_rule else True

        case _:
            return False
        

if __name__ == "__main__":
    main()