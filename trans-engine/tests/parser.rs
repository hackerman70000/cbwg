//! Integration tests for the parser module, with more comprehensive test cases
//! to ensure all parsing rules are correctly implemented and validated.
//! 
//! The tests are written in a way that they can be run in parallel, as they are
//! independent of each other.
//!

use _core::lang::{Rule, TransformRule, RejectRule, Rotation, Truncate};
use _core::parser::parse_line;

#[test]
fn parse_basic_transform_rules() {
    let mut input = "luc";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Lowercase),
        Rule::Transform(TransformRule::Uppercase),
        Rule::Transform(TransformRule::Capitalize),
    ]);
}

#[test]
fn parse_append_prepend_rules() {
    let mut input = "$1^A";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Append("1".to_string())),
        Rule::Transform(TransformRule::Prepend("A".to_string())),
    ]);
}

#[test]
fn parse_rules_with_numeric_parameters() {
    let mut input = "T2D3'4";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::ToggleCase(Some(2))),
        Rule::Transform(TransformRule::Delete(3)),
        Rule::Transform(TransformRule::Truncate(Truncate::To(4))),
    ]);
}

#[test]
fn parse_range_based_rules() {
    let mut input = "x1:5O37*2:4";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Extract(1, 5)),
        Rule::Transform(TransformRule::Omit(3, 7)),
        Rule::Transform(TransformRule::Swap(2, 4)),
    ]);
}

#[test]
fn parse_multi_digit_ranges() {
    let mut input = "x10:15O25:30*11:14";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Extract(10, 15)),
        Rule::Transform(TransformRule::Omit(25, 30)),
        Rule::Transform(TransformRule::Swap(11, 14)),
    ]);
}
#[test]
fn parse_multi_digit_ranges_without_separator() {
    let mut input = "x1015O2530*1114";
    let result = parse_line(&mut input);
    assert!(result.is_err());
}


#[test]
fn parse_character_manipulation_rules() {
    let mut input = "sabk{r}";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Replace("a".to_string(), "b".to_string())),
        Rule::Transform(TransformRule::SwapFront),
        Rule::Transform(TransformRule::Rotate(Rotation::Left)),
        Rule::Transform(TransformRule::Reverse),
        Rule::Transform(TransformRule::Rotate(Rotation::Right)),
    ]);
}

#[test]
fn parse_duplication_rules() {
    let mut input = "dqfz3Z2y4Y5";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Duplicate(None)),
        Rule::Transform(TransformRule::DuplicateAll),
        Rule::Transform(TransformRule::Reflect),
        Rule::Transform(TransformRule::DuplicateFirst(3)),
        Rule::Transform(TransformRule::DuplicateLast(2)),
        Rule::Transform(TransformRule::DuplicateFirstBlock(4)),
        Rule::Transform(TransformRule::DuplicateLastBlock(5)),
    ]);
}

#[test]
fn parse_ascii_manipulation_rules() {
    let mut input = "+1-2.3,4L2R3";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::AsciiIncrement(1)),
        Rule::Transform(TransformRule::AsciiDecrement(2)),
        Rule::Transform(TransformRule::ReplaceWithNext(3)),
        Rule::Transform(TransformRule::ReplaceWithPrev(4)),
        Rule::Transform(TransformRule::BitwiseShiftLeft(2)),
        Rule::Transform(TransformRule::BitwiseShiftRight(3)),
    ]);
}

#[test]
fn parse_truncate_rules() {
    let mut input = "[]'5";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Truncate(Truncate::Left)),
        Rule::Transform(TransformRule::Truncate(Truncate::Right)),
        Rule::Transform(TransformRule::Truncate(Truncate::To(5))),
    ]);
}

#[test]
fn parse_reject_rules() {
    let mut input = "<8>3_6!a/b(c)d=2e%3f";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Reject(RejectRule::LongerThan(8)),
        Rule::Reject(RejectRule::ShorterThan(3)),
        Rule::Reject(RejectRule::NotEqualTo(6)),
        Rule::Reject(RejectRule::Contains("a".to_string())),
        Rule::Reject(RejectRule::NotContains("b".to_string())),
        Rule::Reject(RejectRule::NotStartsWith("c".to_string())),
        Rule::Reject(RejectRule::NotEndsWith("d".to_string())),
        Rule::Reject(RejectRule::NotEqualAt(2, "e".to_string())),
        Rule::Reject(RejectRule::ContainsLessThan(3, "f".to_string())),
    ]);
}

#[test]
fn parse_no_op_rule() {
    let mut input = ":";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![Rule::NoOp]);
}

#[test]
fn parse_complex_rule_combination() {
    let mut input = "luct$1^A[D2x1:3O45sa!";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Lowercase),
        Rule::Transform(TransformRule::Uppercase),
        Rule::Transform(TransformRule::Capitalize),
        Rule::Transform(TransformRule::ToggleCase(None)),
        Rule::Transform(TransformRule::Append("1".to_string())),
        Rule::Transform(TransformRule::Prepend("A".to_string())),
        Rule::Transform(TransformRule::Truncate(Truncate::Left)),
        Rule::Transform(TransformRule::Delete(2)),
        Rule::Transform(TransformRule::Extract(1, 3)),
        Rule::Transform(TransformRule::Omit(4, 5)),
        Rule::Transform(TransformRule::Replace("a".to_string(), "!".to_string())),
    ]);
}

#[test]
fn parse_multiple_lines() {
    let mut input = "lu\nc";
    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Lowercase),
        Rule::Transform(TransformRule::Uppercase),
    ]);

    let result = parse_line(&mut input).unwrap();
    assert_eq!(result, vec![
        Rule::Transform(TransformRule::Capitalize),
    ]);
}

#[test]
fn parse_empty_line() {
    let mut input = "\n";
    let result = parse_line(&mut input).unwrap();
    assert!(result.is_empty());
}

#[test]
fn parse_whitespace_handling() {
    // Note: In hashcat, whitespace is not allowed in rules, but our parser should handle it
    let mut input = "l u\tc";
    let result = parse_line(&mut input);
    // The parser should either fail or treat 'u' and 'c' as parameters to 'l'
    // Depending on your implementation, adjust this assertion
    assert!(result.is_err() || result.unwrap() != vec![
        Rule::Transform(TransformRule::Lowercase),
        Rule::Transform(TransformRule::Uppercase),
        Rule::Transform(TransformRule::Capitalize),
    ]);
}


#[test]
fn parse_nonexistent_rules() {
    let mut input = "luc|";
    let result = parse_line(&mut input);
    assert!(result.is_err());


    if let Err(ref e) = result {
        assert!(e.to_string().starts_with("Parsing Error"));
    }
}

#[test]
fn parse_non_ascii_rules() {
    let mut input = "lüc";
    let result = parse_line(&mut input);
    assert!(result.is_err());


    if let Err(ref e) = result {
        assert!(e.to_string().contains("Parsing Error"));
    }
}