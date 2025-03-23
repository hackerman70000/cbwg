use winnow::prelude::*;
use winnow::Parser;
use winnow::ascii::dec_uint;
use winnow::token::{one_of,any,literal};
use winnow::combinator::{dispatch,empty,fail,alt,separated,repeat,terminated,eof};

use crate::lang::*;



fn range_parser_delim(input: &mut &str) -> ModalResult<(usize, usize)> {
    separated(2,dec_uint::<_,usize,_>, ':').parse_next(input).map(|v: Vec<usize>| (v[0], v[1]))
}

fn range_parse_raw(input: &mut &str) -> ModalResult<(usize,usize)> {
   repeat(2, one_of('0'..='9')).parse_next(input).map(|v: Vec<char>| (v[0].to_digit(10).unwrap() as usize, v[1].to_digit(10).unwrap() as usize))
}

fn range_parser(input: &mut &str) -> ModalResult<(usize, usize)> {
    alt((range_parser_delim, range_parse_raw, fail)).parse_next(input)
}

pub fn parse_rule(input: &mut &str) -> ModalResult<Rule> {
    dispatch! { any;
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
        'o' => (any, dec_uint).map(|(c, i): (char, usize)| Rule::Transform(TransformRule::Overwrite(i, c.to_string()))),
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

pub fn parse_line(input: &mut &str) -> ModalResult<Vec<Rule>> {
    terminated(repeat(0.., parse_rule), alt((literal('\n'), eof))).parse_next(input)
}