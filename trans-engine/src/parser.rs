//! Parser for Hashcat rule-based attack syntax.
//!
//! This module implements a parser for Hashcat rule files, which are used for rule-based password
//! cracking attacks. Hashcat rules consist of a series of commands that define transformations
//! to be applied to password candidates.
//!
//! The parser uses the `winnow` crate to efficiently parse rule syntax into structured data
//! that can be used by the transformation engine to apply the rules to input words.
//!
//! ## Rule Format
//!
//! Hashcat rules consist of single-character commands, often followed by parameters.
//! For example:
//!
//! - `$1` appends character '1'
//! - `^A` prepends character 'A'
//! - `c` capitalizes the first letter
//!
use winnow::prelude::*;
use winnow::Parser;
use winnow::ascii::dec_uint;
use winnow::token::{one_of,any,literal,rest};
use winnow::combinator::{dispatch,empty,fail,alt,separated,repeat,terminated,eof};

use crate::lang::*;

/// Parses a range in the format `N:M` where N and M are decimal integers separated by a colon.
/// 
/// Returns a tuple of two usize values representing the start and end positions of the range.
/// 
/// # Examples
/// 
/// ```
/// # use crate::_core::parser::range_parser_delim;
/// let mut input = "1:5";
/// assert_eq!(range_parser_delim(&mut input), Ok((1, 5)));
/// 
/// let mut input = "10:20";
/// assert_eq!(range_parser_delim(&mut input), Ok((10, 20)));
/// ```
pub fn range_parser_delim(input: &mut &str) -> ModalResult<(usize, usize)> {
    separated(2,dec_uint::<_,usize,_>, ':').parse_next(input).map(|v: Vec<usize>| (v[0], v[1]))
}

/// Parses a range consisting of exactly two digits with no separator.
/// 
/// Converts each digit to a number and returns them as a tuple. For example,
/// "12" would be parsed as (1, 2).
/// 
/// # Examples
/// 
/// ```
/// # use crate::_core::parser::range_parse_raw;
/// let mut input = "12";
/// assert_eq!(range_parse_raw(&mut input), Ok((1, 2)));
/// ```
/// ```
/// # use crate::_core::parser::range_parse_raw;
/// let mut input = "05";
/// assert_eq!(range_parse_raw(&mut input), Ok((0, 5)));
/// ```
pub fn range_parse_raw(input: &mut &str) -> ModalResult<(usize,usize)> {
   repeat(2, one_of('0'..='9')).parse_next(input).map(|v: Vec<char>| (v[0].to_digit(10).unwrap() as usize, v[1].to_digit(10).unwrap() as usize))
}

/// Parses a range using either delimiter format (N:M) or raw format (NM).
/// 
/// First attempts to parse using the `range_parser_delim` function (N:M format).
/// If that fails, it tries the `range_parse_raw` function (NM format).
/// Returns a tuple of two usize values representing the range bounds.
/// 
/// # Examples
/// 
/// Delimited format:
/// ```
/// # use crate::_core::parser::range_parser;
/// let mut input = "1:5";
/// assert_eq!(range_parser(&mut input), Ok((1, 5)));
/// ```
/// Raw format:
/// ```
/// # use crate::_core::parser::range_parser;
/// let mut input = "25";
/// assert_eq!(range_parser(&mut input), Ok((2, 5)));
/// ```
///
/// Handles larger numbers in delimited format
/// ```
/// # use crate::_core::parser::range_parser;
/// let mut input = "10:20";
/// assert_eq!(range_parser(&mut input), Ok((10, 20)));
/// ```
pub fn range_parser(input: &mut &str) -> ModalResult<(usize, usize)> {
    alt((range_parser_delim, range_parse_raw, fail)).parse_next(input)
}

/// Parses a single Hashcat rule command from the input string.
///
/// This function recognizes all standard Hashcat rule commands and maps them to the appropriate 
/// `Rule` enum variant. It consumes the command character and any parameters from the input string.
///
/// # Supported Commands
///
/// ## Transform Rules:
/// - `:` - No operation
/// - `l` - Convert to lowercase
/// - `u` - Convert to uppercase
/// - `c` - Capitalize first letter
/// - `C` - Invert capitalization of first letter
/// - `t` - Toggle case of all characters
/// - `T[N]` - Toggle case of character at position N
/// - `r` - Reverse the entire word
/// - `d` - Duplicate entire word
/// - `p[N]` - Duplicate word N times
/// - `f` - Reflect the word
/// - `{` - Rotate word left
/// - `}` - Rotate word right
/// - `$[C]` - Append character C
/// - `^[C]` - Prepend character C
/// - `[` - Truncate from left (remove first char)
/// - `]` - Truncate from right (remove last char)
/// - `D[N]` - Delete character at position N
/// - `x[N:M]` or `x[NM]` - Extract characters from positions N to M
/// - `O[N:M]` or `O[NM]` - Omit characters from positions N to M
/// - `i[C][N]` - Insert character C at position N
/// - `o[C][N]` - Overwrite character at position N with C
/// - `'[N]` - Truncate to N characters
/// - `s[A][B]` - Replace character A with B
/// - `@[C]` - Purge all instances of character C
/// - `z[N]` - Duplicate first character N times
/// - `Z[N]` - Duplicate last character N times
/// - `q` - Duplicate the entire word
/// - `k` - Swap first two characters
/// - `K` - Swap last two characters
/// - `*[N:M]` or `*[NM]` - Swap characters at positions N and M
/// - `L[N]` - Bitwise shift left by N
/// - `R[N]` - Bitwise shift right by N
/// - `+[N]` - Increment ASCII value of character at position N
/// - `-[N]` - Decrement ASCII value of character at position N
/// - `.[N]` - Replace character at position N with next character
/// - `,[N]` - Replace character at position N with previous character
/// - `y[N]` - Duplicate first N characters
/// - `Y[N]` - Duplicate last N characters
///
/// ## Reject Rules:
/// - `<[N]` - Reject if word length is greater than N
/// - `>[N]` - Reject if word length is less than N
/// - `_[N]` - Reject if word length is not equal to N
/// - `![C]` - Reject if word contains character C
/// - `/[C]` - Reject if word does not contain character C
/// - `([C]` - Reject if word does not start with character C
/// - `)[C]` - Reject if word does not end with character C
/// - `=[N][C]` - Reject if character at position N is not C
/// - `%[N][C]` - Reject if word contains fewer than N instances of character C
///
/// # Returns
///
/// A `ModalResult<Rule>` containing either the parsed rule or an error.
///
/// # Examples
///
/// Parse a lowercase rule:
/// ```
/// # use crate::_core::parser::parse_rule;
/// # use crate::_core::lang::{Rule, TransformRule};
/// 
/// let mut input = "l";
/// assert_eq!(parse_rule(&mut input), Ok(Rule::Transform(TransformRule::Lowercase)));
/// ```
///
/// Parse an append rule:
/// ```
/// # use crate::_core::parser::parse_rule;
/// # use crate::_core::lang::{Rule, TransformRule};
/// 
/// let mut input = "$1";
/// assert_eq!(parse_rule(&mut input), Ok(Rule::Transform(TransformRule::Append("1".to_string()))));
/// ```
/// 
/// Parse a rotate rule:
/// ```
/// # use crate::_core::parser::parse_rule;
/// # use crate::_core::lang::{Rule, TransformRule, Rotation};
/// 
/// let mut input = "{";
/// assert_eq!(parse_rule(&mut input), Ok(Rule::Transform(TransformRule::Rotate(Rotation::Left))));
/// ```
/// Parse a reject rule:
/// ```
/// # use crate::_core::parser::parse_rule;
/// # use crate::_core::lang::{Rule, RejectRule};
/// 
/// let mut input = "<8";
/// assert_eq!(parse_rule(&mut input), Ok(Rule::Reject(RejectRule::LongerThan(8))));
/// ```
pub fn parse_rule(input: &mut &str) -> ModalResult<Rule> {
    dispatch! { any;
        '#' => rest.value(Rule::NoOp),
        ':' => empty.value(Rule::NoOp),
        'l' => empty.value(Rule::Transform(TransformRule::Lowercase)),
        'u' => empty.value(Rule::Transform(TransformRule::Uppercase)),
        'c' => empty.value(Rule::Transform(TransformRule::Capitalize)),
        'C' => empty.value(Rule::Transform(TransformRule::InvertCapitalize)),
        't' => empty.value(Rule::Transform(TransformRule::ToggleCase(None))),
        'T' => dec_uint.map(|n| Rule::Transform(TransformRule::ToggleCase(Some(n)))),
        'r' => empty.value(Rule::Transform(TransformRule::Reverse)),
        'd' => empty.value(Rule::Transform(TransformRule::Duplicate(None))),
        'p' => dec_uint.map(|n| Rule::Transform(TransformRule::Duplicate(Some(n)))),
        'f' => empty.value(Rule::Transform(TransformRule::Reflect)),
        '{' => empty.value(Rule::Transform(TransformRule::Rotate(Rotation::Left))),
        '}' => empty.value(Rule::Transform(TransformRule::Rotate(Rotation::Right))),
        '$' => any.map(|c: char| Rule::Transform(TransformRule::Append(c.to_string()))),
        '^' => any.map(|c: char| Rule::Transform(TransformRule::Prepend(c.to_string()))),
        '[' => empty.value(Rule::Transform(TransformRule::Truncate(Truncate::Left))),
        ']' => empty.value(Rule::Transform(TransformRule::Truncate(Truncate::Right))),
        'D' => dec_uint.map(|i| Rule::Transform(TransformRule::Delete(i))),
        'x' => range_parser.map(|r| Rule::Transform(TransformRule::Extract(r.0,r.1))),
        'O' => range_parser.map(|r| Rule::Transform(TransformRule::Omit(r.0,r.1))),
        'i' => (any, dec_uint).map(|(c, i): (char, usize)| Rule::Transform(TransformRule::Insert(i, c.to_string()))),
        'o' => (dec_uint, any).map(|(i, c): (usize, char)| Rule::Transform(TransformRule::Overwrite(i, c.to_string()))),
        '\'' => dec_uint.map(|n| Rule::Transform(TransformRule::Truncate(Truncate::To(n)))),
        's' => (any,any).map(|(a,b): (char,char)| Rule::Transform(TransformRule::Replace(a.to_string(), b.to_string()))),
        '@' => any.map(|c: char| Rule::Transform(TransformRule::Purge(c.to_string()))),
        'z' => dec_uint.map(|n| Rule::Transform(TransformRule::DuplicateFirst(n))),
        'Z' => dec_uint.map(|n| Rule::Transform(TransformRule::DuplicateLast(n))),
        'q' => empty.value(Rule::Transform(TransformRule::DuplicateAll)),
        // hashcat-specific transformations
        'k' => empty.value(Rule::Transform(TransformRule::SwapFront)),
        'K' => empty.value(Rule::Transform(TransformRule::SwapBack)),
        '*' => range_parser.map(|r| Rule::Transform(TransformRule::Swap(r.0,r.1))),
        'L' => dec_uint.map(|i| Rule::Transform(TransformRule::BitwiseShiftLeft(i))),
        'R' => dec_uint.map(|i| Rule::Transform(TransformRule::BitwiseShiftRight(i))),
        '+' => dec_uint.map(|i| Rule::Transform(TransformRule::AsciiIncrement(i))),
        '-' => dec_uint.map(|i| Rule::Transform(TransformRule::AsciiDecrement(i))),
        '.' => dec_uint.map(|i| Rule::Transform(TransformRule::ReplaceWithNext(i))),
        ',' => dec_uint.map(|i| Rule::Transform(TransformRule::ReplaceWithPrev(i))),
        'y' => dec_uint.map(|n| Rule::Transform(TransformRule::DuplicateFirstBlock(n))),
        'Y' => dec_uint.map(|n| Rule::Transform(TransformRule::DuplicateLastBlock(n))),

        // reject rules
        '<' => dec_uint.map(|n| Rule::Reject(RejectRule::LongerThan(n))),
        '>' => dec_uint.map(|n| Rule::Reject(RejectRule::ShorterThan(n))),
        '_' => dec_uint.map(|n| Rule::Reject(RejectRule::NotEqualTo(n))),
        '!' => any.map(|c: char| Rule::Reject(RejectRule::Contains(c.to_string()))),
        '/' => any.map(|c: char| Rule::Reject(RejectRule::NotContains(c.to_string()))),
        '(' => any.map(|c: char| Rule::Reject(RejectRule::NotStartsWith(c.to_string()))),
        ')' => any.map(|c: char| Rule::Reject(RejectRule::NotEndsWith(c.to_string()))),
        '=' => (dec_uint, any).map(|(i, c): (usize, char)| Rule::Reject(RejectRule::NotEqualAt(i, c.to_string()))),
        '%' => (dec_uint, any).map(|(n, c): (usize, char)| Rule::Reject(RejectRule::ContainsLessThan(n, c.to_string()))),
        _ => fail::<_, Rule, _>,
    }.parse_next(input)
}

/// Parses a series of Hashcat rules from the input string.
/// 
/// Simply calls the `parse_rule` function repeatedly until the input string is exhausted or a newline is reached.
/// Returns a vector of `Rule` enum variants.
/// 
/// # Examples
/// 
/// Parse a series of rules:
/// ```
/// # use crate::_core::parser::parse_line;
/// # use crate::_core::lang::{Rule, TransformRule};
/// 
/// let mut input = "lu$1";
/// assert_eq!(parse_line(&mut input), Ok(vec![
///     Rule::Transform(TransformRule::Lowercase),
///     Rule::Transform(TransformRule::Uppercase),
///     Rule::Transform(TransformRule::Append("1".to_string()))
/// ]));
/// ```
/// 
/// Interrupt parsing at a newline:
/// ```
/// # use crate::_core::parser::parse_line;
/// # use crate::_core::lang::{Rule, TransformRule};
/// 
/// let mut input = "lu$1\nl";
/// assert_eq!(parse_line(&mut input), Ok(vec![
///    Rule::Transform(TransformRule::Lowercase),
///    Rule::Transform(TransformRule::Uppercase),
///    Rule::Transform(TransformRule::Append("1".to_string()))
/// ]));
/// ```
pub fn parse_line(input: &mut &str) -> ModalResult<Vec<Rule>> {
    terminated(repeat(0.., parse_rule), alt((literal('\n'), eof))).parse_next(input)
}