//! Integration tests for the transformation engine
//!
//! These tests verify that the rule application system correctly transforms
//! input words according to Hashcat rule specifications.

use _core::engine::run;

#[test]
fn test_basic_transform_rules() {
    let rules = vec![
        "l".to_string(),    // lowercase
        "u".to_string(),    // uppercase
        "c".to_string(),    // capitalize
        "C".to_string(),    // invert capitalization
        "t".to_string(),    // toggle case
    ];
    
    let words = vec![
        "Password123".to_string(),
        "EXAMPLE".to_string(),
        "mixed".to_string(),
    ];
    
    let results = run(rules, words).unwrap();
    
    // Expected transformed words based on rules
    let expected = vec![
        "password123".to_string(),  // l -> Password123 -> password123
        "example".to_string(),      // l -> EXAMPLE -> example
        "mixed".to_string(),        // l -> mixed -> mixed (already lowercase)

        "PASSWORD123".to_string(),  // u -> Password123 -> PASSWORD123
        "EXAMPLE".to_string(),      // u -> EXAMPLE -> EXAMPLE (already uppercase)
        "MIXED".to_string(),        // u -> mixed -> MIXED
        
        "Password123".to_string(),  // c -> Password123 -> Password123 (already capitalized)
        "Example".to_string(),      // c -> EXAMPLE -> Example
        "Mixed".to_string(),        // c -> mixed -> Mixed
        
        "pASSWORD123".to_string(),  // C -> Password123 -> pASSWORD123
        "eXAMPLE".to_string(),      // C -> EXAMPLE -> eXAMPLE
        "Mixed".to_string(),        // C -> mixed -> mIXED
        
        "PaSsWoRd123".to_string(),  // t -> Password123 -> PaSsWoRd123
        "example".to_string(),      // t -> EXAMPLE -> example
        "MIXED".to_string(),        // t -> mixed -> MIXED
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_character_manipulation_rules() {
    let rules = vec![
        "$1".to_string(),      // append "1"
        "^A".to_string(),      // prepend "A"
        "sab".to_string(),     // replace "a" with "b"
        "[".to_string(),       // truncate left
        "]".to_string(),       // truncate right
        "@a".to_string(),      // purge all "a"
    ];
    
    let words = vec![
        "password".to_string(),
        "apple".to_string(),
    ];
    
    let results = run(rules, words).unwrap();
    
    let expected = vec![
        "password1".to_string(),    // $1 -> password -> password1
        "apple1".to_string(),       // $1 -> apple -> apple1
        
        "Apassword".to_string(),    // ^A -> password -> Apassword
        "Aapple".to_string(),       // ^A -> apple -> Aapple
        
        "pbssword".to_string(),     // sab -> password -> pbssword
        "bpple".to_string(),        // sab -> apple -> bpple
        
        "assword".to_string(),      // [ -> password -> assword
        "pple".to_string(),         // [ -> apple -> pple
        
        "passwor".to_string(),      // ] -> password -> passwor
        "appl".to_string(),         // ] -> apple -> appl
        
        "pssword".to_string(),      // @a -> password -> pssword
        "pple".to_string(),         // @a -> apple -> pple
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_position_based_rules() {
    let rules = vec![
        "T0".to_string(),       // toggle case at position 0
        "D1".to_string(),       // delete character at position 1
        "'3".to_string(),       // truncate to 3 characters
        "z2".to_string(),       // duplicate first character twice
        "Z1".to_string(),       // duplicate last character once
    ];
    
    let words = vec![
        "password".to_string(),
        "admin".to_string(),
    ];
    
    let results = run(rules, words).unwrap();
    
    let expected = vec![
        "Password".to_string(),     // T0 -> password -> Password
        "Admin".to_string(),        // T0 -> admin -> Admin
        
        "pssword".to_string(),      // D1 -> password -> pssword
        "amin".to_string(),         // D1 -> admin -> amin
        
        "pas".to_string(),          // '3 -> password -> pas
        "adm".to_string(),          // '3 -> admin -> adm
        
        "pppassword".to_string(),   // z2 -> password -> pppassword
        "aaadmin".to_string(),      // z2 -> admin -> aaadmin
        
        "passwordd".to_string(),    // Z1 -> password -> passwordd
        "adminn".to_string(),       // Z1 -> admin -> adminn
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_range_based_rules() {
    let rules = vec![
        "x1:3".to_string(),     // extract 3 characters from position 1 
        "O2:4".to_string(),     // omit 4 characters from position 2
        "*0:5".to_string(),     // swap characters at positions 0 and 5
    ];
    
    let words = vec![
        "password".to_string(), 
        "security".to_string(),
    ];
    
    let results = run(rules, words).unwrap();
    
    let expected = vec![
        "ass".to_string(),           // x1:3 -> password -> ass (extraction)
        "ecu".to_string(),           // x1:3 -> security -> ecu (extraction)
        
        "pard".to_string(),         // O2:4 -> password -> paord (omission)
        "sety".to_string(),         // O2:4 -> security -> seity (omission)
        
        "oasswprd".to_string(),      // *0:5 -> password -> oasswprd (swap)
        "iecursty".to_string(),      // *0:5 -> security -> iecursty (swap)
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_duplication_and_reversal_rules() {
    let rules = vec![
        "d".to_string(),      // duplicate entire word
        "p2".to_string(),     // duplicate word twice
        "f".to_string(),      // reflect the word
        "r".to_string(),      // reverse the word
        "{".to_string(),      // rotate left
        "}".to_string(),      // rotate right
        "y2".to_string(),     // duplicate first 2 characters
        "Y1".to_string(),     // duplicate last 1 character
    ];
    
    let words = vec!["abc".to_string()];
    
    let results = run(rules, words).unwrap();
    
    let expected = vec![
        "abcabc".to_string(),     // d -> abc -> abcabc
        "abcabcabc".to_string(),  // p2 -> abc -> abcabcabc
        "abccba".to_string(),     // f -> abc -> abccba
        "cba".to_string(),        // r -> abc -> cba
        "bca".to_string(),        // { -> abc -> bca (rotate left)
        "cab".to_string(),        // } -> abc -> cab (rotate right)
        "ababc".to_string(),      // y2 -> abc -> ababc
        "abcc".to_string(),       // Y1 -> abc -> abcc
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_reject_rules() {
    let rules = vec![
        "<5".to_string(),       // reject if length > 5
        ">3".to_string(),       // reject if length < 3
        "_4".to_string(),       // reject if length != 4
        "!a".to_string(),       // reject if contains 'a'
        "/p".to_string(),       // reject if doesn't contain 'p'
        "(a".to_string(),       // reject if doesn't start with 'a'
        ")e".to_string(),       // reject if doesn't end with 'e'
    ];
    
    let words = vec![
        "pass".to_string(),     // length 4, contains 'a' and 'p', starts with 'p', ends with 's'
        "apple".to_string(),    // length 5, contains 'a' and 'p', starts with 'a', ends with 'e'
        "password".to_string(), // length 8, contains 'a' and 'p', starts with 'p', ends with 'd'
        "ab".to_string(),       // length 2, contains 'a', starts with 'a', ends with 'b'
        "test".to_string(),     // length 4, doesn't contain 'a', doesn't start with 'a', doesn't end with 'e'
    ];
    
    let results = run(rules, words).unwrap();
    
    // Expected results based on rejection rules
    let expected = vec![
        // <5 (reject if length > 5) - only "pass", "apple", "ab" will pass
        "pass".to_string(), 
        "apple".to_string(),
        "ab".to_string(),
        "test".to_string(),
        
        // >3 (reject if length < 3) - "pass", "apple", "password" will pass
        "pass".to_string(),
        "apple".to_string(),
        "password".to_string(),
        "test".to_string(),
        
        // _4 (reject if length != 4) - only "pass" and "test" will pass
        "pass".to_string(),
        "test".to_string(),
        
        // !a (reject if contains 'a') - "test" will pass
        "test".to_string(),
        
        // /p (reject if doesn't contain 'p') - "pass", "apple", "password" will pass
        "pass".to_string(),
        "apple".to_string(),
        "password".to_string(),
        
        // (a (reject if doesn't start with 'a') - "apple", "ab" will pass
        "apple".to_string(),
        "ab".to_string(),
        
        
        // )e (reject if doesn't end with 'e') - only "apple" will pass
        "apple".to_string(),
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_complex_rule_combinations() {
    let rules = vec![
        "l$1".to_string(),                  // lowercase, then append "1"
        "u]d".to_string(),                  // uppercase, truncate right, duplicate
        "c[o0l".to_string(),                // capitalize, truncate left, overwrite 0 with 'l', lowercase
    ];
    
    let words = vec![
        "Password".to_string(),
        "USER".to_string(),
    ];
    
    let results = run(rules, words).unwrap();
    
    let expected = vec![
        "password1".to_string(),           // l$1 -> Password -> password -> password1
        "user1".to_string(),               // l$1 -> USER -> user -> user1
        
        "PASSWORPASSWOR".to_string(),     // u]d -> Password -> PASSWORD -> PASSWOR -> PASSWORDPASSWOR
        "USEUSE".to_string(),            // u]d -> USER -> USER -> USE ->  USERUSEU
        
        "lssword".to_string(),            // c[o0l -> Password -> Password -> assword -> lssword
        "ler".to_string(),                // c[o0l -> USER -> User -> ser -> ler
    ];
    
    assert_eq!(results, expected);
}

#[test]
fn test_error_handling() {
    let invalid_rules = vec![
        "#".to_string(),         // non-existent rule
        "x".to_string(),         // missing range parameter
        "T".to_string(),         // missing position parameter
    ];
    
    let words = vec!["password".to_string()];
    
    // The function should still return a result, but it might be empty
    // or contain error messages depending on implementation
    let results = run(invalid_rules, words).unwrap();
    
    // Expecting empty results since all rules are invalid
    assert!(results.is_empty());
}