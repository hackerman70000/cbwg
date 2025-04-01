#![no_main]
use arbitrary;

use libfuzzer_sys::fuzz_target;
extern crate _core;


#[derive(Clone, Debug, arbitrary::Arbitrary)]
pub struct RulesAndWords {
    rules: Vec<String>,
    words: Vec<String>,
}

fuzz_target!(|data: RulesAndWords| {
    let _ = _core::engine::run(data.rules, data.words);
});
