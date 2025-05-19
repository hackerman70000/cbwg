use rayon::prelude::*;

use crate::parser::parse_line;
use crate::lang::Rule;

pub fn run(rules: Vec<String>, words: Vec<String>) -> Result<Vec<String>, String> {
    // We can call py.allow_threads to ensure the GIL is released during our
    // operations
    // This example just wraps `arrow_select::take::take`
    let mut output_array: Vec<String> = Vec::new();
    for element in rules.iter() {
        match parse_line(&mut element.to_string().as_str()) {
            Ok(parsed_rules) => {

                let rules_slice = &Rule::simplify(parsed_rules)[..];

                // Parallel processing of words
                let thread_results: Vec<String> = words.par_iter()
                    .filter_map(|values| {
                        // perf issue: clone is expensive
                        Rule::run_all(rules_slice, values.to_string())
                    })
                    .collect();

                output_array.extend(thread_results);
            }
            Err(e) => {
                println!("Error: {}", e);
            }
        }
    }
    
    Ok(output_array)
}