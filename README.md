# Context Based Wordlist Generation

A modular tool for generating and managing wordlists used in dictionary attacks and security audits.

## Usage

The tool supports two transformation modes: rule-based (similar to hashcat) and AI-powered generation.

## Requirements

- Google AI [API key](https://aistudio.google.com/apikey) (for AI mode)
- [uv](https://github.com/astral-sh/uv) package manager
- Rust toolchain (for building the transformation engine)

## Commands

**Rule-based wordlist generation:**

```bash
# Basic usage with default settings
uv run cbwg.py -p passwords.txt -r resources/rules

# With custom configuration
uv run cbwg.py -p data.txt -r resources/rules --parser-config resources/config_files/parser_config.yml -o custom_wordlist
```

**AI-powered generation:**

```bash
# Using API key directly
uv run cbwg.py -ai -p context.txt --api-key your_api_key
```

Example context file (`context.txt`):

```
CompanyName
password
login
2024
secure
database
server
```

Example output:

```
CompanyName2024
admin123
password!
adminpassword
CompanyNameAdmin
login2024
securepassword
databaseadmin
serverlogin
CompanyName123
admin2024
```

### Configuration Files

The tool supports YAML configuration files for fine-tuning behavior:

**Parser Configuration** (`parser_config.yml`):

```yaml
min_length: 3
max_length: 20
pattern: "[a-zA-Z0-9]+"
include_numbers: true
preserve_case: false
exclude_words: ["the", "and", "or"]
```

**Source Configuration** (`source_config.yml`):

```yaml
binary_mode: false
encoding: "utf-8"
chunk_size: 4096
```

**Rule Engine Configuration** (`rule_config.yml`):

```yaml
rules_path: "resources/rules"
batch_size: 10000
verbose_logging: false
```

### Environment Variables

You can set the Google API key as an environment variable:

```bash
export GOOGLE_API_KEY="your_api_key_here"
uv run cbwg.py -ai -p input.txt
```

For hashcat rules path:

```bash
export HASHCAT_RULES_PATH="/path/to/rules"
uv run cbwg.py -p input.txt
```

## Development

### Installation

To set up the development environment, sync dependencies using:

```bash
uv sync
```

### Formatting and Linting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting.

To check for linting issues:

```bash
uvx ruff check
```

To automatically format the code:

```bash
uvx ruff format
```

### Package Management

Package management is handled using [uv](https://github.com/astral-sh/uv). Refer to the official documentation for additional commands and usage details.

### Testing

To run tests:

```bash
uv run pytest
```
