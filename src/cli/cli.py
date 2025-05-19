import argparse
from pathlib import Path
import yaml
from typing import Optional, Dict
import re
import sys

from src.sources.file import FileSource
from src.parsers.text import TextParser
from src.transformers.rules import RuleTransformer
from src.transformers.llm.transformer import LLMTransformer

def main():
    parser = argparse.ArgumentParser(description="CLI for the cbwg Wordlist Generator. " \
    "You can chose whether you want to generate a wordlost using an AI client (-ai), or using a local " \
    "hashCat-like transformer. You can provide some options to the transformer from the CLI. " \
    "For fine-tuning, create .yml config files for each component.",
    epilog="For detailed configuration options, visit README")
    
    parser.add_argument('-ai', action='store_true', help="Generating a wordlist using an AI client")
    parser.add_argument('--api-key', type=str, help="API key to use for AI client")
    parser.add_argument('--ai-config', type=str, help="Path to the file containing config file fot the AI client. If none provided, environment variable \"GOOGLE_API_KEY\" is used")

    parser.add_argument('-p', type=list, nargs='*', required=True, help="Path to the input file/s")    
    parser.add_argument('-r', type=str, help="Path to the directory with .rule file/s")
    parser.add_argument('--source-config', type=str, help="Path to the file containing the source config")
    parser.add_argument('--parser-config', type=str, help="Path to the file containing parser config")
    parser.add_argument('--trans-engine-config', type=str, help="Path to the file containing transformation engine config")
    parser.add_argument('-o', type=str, default="stdout", help="Type of epected output. \"Filename\" is the name a .txt file will be given")

    args = parser.parse_args()

    paths = [''.join(p) for p in args.p]
    paths = [Path(p) for p in paths]

    if args.ai:
        if args.ai_config:
            config = parse_config(args.ai_config, "ai")
            if config:
                transformer = LLMTransformer(config)
            else:
                exit()
        elif args.api_key:
            transformer = LLMTransformer({"api_key": args.api_key})        
        lines = []
        for path in paths:
            with open(path, 'r', encoding='utf-8') as file:
                for line in file:
                    lines.append(line.strip())
        
        results = transformer.transform(lines)
        write_output(args.o, results)

    else:
        if args.source_config:
            path = Path(args.source_config)
            config = parse_config(path, "source")
            if config:
                source = FileSource(paths, config)
            else:
                exit()
        else:
            source = FileSource(paths)

        if args.parser_config:
            path = Path(args.parser_config)
            config = parse_config(path, "parser")
            if config:
                parser_config = config
                text = TextParser(parser_config)
            else:
                exit()
        else:
            text = TextParser()

        if args.trans_engine_config:
            path = Path(args.trans_engine_config)
            config = parse_config(path, "engine")
            if config:
                rule_config = config
                transformer = RuleTransformer(rule_config)
            else:
                exit()
        elif args.r:
            path = Path(args.r)
            rule_config = {"rules_path" : path}
            transformer = RuleTransformer(rule_config)
        else:
            transformer = RuleTransformer()
        
        words = []
        for data in source.get_data():
            for word in text.parse(data):
                words.append(word)
        results = list(transformer.transform(words))
        write_output(args.o, results)

def write_output(args, list):
    if args == "stdout":
        print("stdout")
        output = sys.stdout
    else:
        output = open(f'{args}.txt', 'w', encoding='utf-8')      
    try:
        for el in list:
            output.write(el + '\n')
    finally:
        if output is not sys.stdout:
            output.close()

def parse_config(filename, type) -> Optional[Dict]:
    with open(filename, 'r') as file:
        dict = yaml.safe_load(file)
    return dict if validate_dict(dict, type) else None

            

def validate_dict(dict, config_type) -> bool:
    if not isinstance(dict, Dict):
        raise ValueError

    # dicts, for casting: 0 - int, 1 - string, 2 - boolean, 3 - list, 4 - regex
    allowed_source = {"binary_mode" : 2, "encoding" : 1, "chunk_size" : 0}
    allowed_parser = {"min_length" : 0, "max_length" : 0, "pattern" : 4, "include_numbers" : 2, "preserve_case" : 2, "exclude_words" : 3}
    allowed_engine = {"rules_path" : 1, "batch_size" : 0, "verbose_logging" : 2, "rules" : 3}
    allowed_ai = {"api_key": 1, "model_name": 1, "prompt_path": 1, "system_instruction": 1, "batch_size": 0, "max_retries": 0, "verbose_logging": 2}
    match config_type:
        case "source":
            for key in dict:
                if key not in allowed_source or not validate_value(dict[key], allowed_source[key]):
                    print("Error location: source config file")
                    return False
            return True

        case "parser":
            for key in dict:
                if key not in allowed_parser or not validate_value(dict[key], allowed_parser[key]):
                    print("Error location: parser config file")
                    return False
            return True
        
        case "engine":
            for key in dict:
                if key not in allowed_engine or not validate_value(dict[key], allowed_engine[key]):
                    print("Error location: transformation engine config file")
                    return False
            return True
        
        case "ai":
            for key in dict:
                if key not in allowed_ai or not validate_value(dict[key], allowed_ai[key]):
                    print("Error location: ai config file")
                    return False
            return True
        
        # no default needed
        
def validate_value(value, code):
    match code:
        case 0:
            if isinstance(value, int):
                return True 
            else:
                print_type_error("integer")
                return False
        case 1:
            if isinstance(value, str):
                return True 
            else:
                print_type_error("string")
                return False
        case 2:
            if isinstance(value, bool):
                return True 
            else:
                print_type_error("bool")
                return False
        case 3:
            if isinstance(value, list):
                return True 
            else:
                print_type_error("list")
                return False
        case 4:
            if not isinstance(value, str):
                print_type_error("string")
                return False
            else:
                try:
                    re.compile(value)
                    return True
                except re.error:
                    print("Error in argument. Invalid regex!")
                    return False
                
def print_type_error(var_type):
    print(f'Error in argument. Expected: {var_type}')          

if __name__ == "__main__":
    main()