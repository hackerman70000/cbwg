
use parser::parse_line;
use rayon::prelude::*;
use pyo3::prelude::*;
pub mod lang;
pub mod parser;
pub mod transforms;

#[pyfunction]
pub fn run(rules: Vec<String>, words: Vec<String>) -> PyResult<Vec<String>> {
    // We can call py.allow_threads to ensure the GIL is released during our
    // operations
    // This example just wraps `arrow_select::take::take`
    let mut output_array: Vec<String> = Vec::new();
    for element in rules.iter() {
        match parse_line(&mut element.to_string().as_str()) {
            Ok(parsed_rules) => {

                let rules_slice = &lang::Rule::simplify(parsed_rules)[..];

                // Parallel processing of words
                let thread_results: Vec<String> = words.par_iter()
                    .filter_map(|values| {
                        // perf issue: clone is expensive
                        lang::Rule::run_all(rules_slice, values.to_string())
                    })
                    .collect();

                output_array.extend(thread_results);
            }
            Err(e) => {
                println!("Error: {}", e);
            }
        }
    }
    
    // TODO: remove copying here too
    Ok(output_array)
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run, m)?)?;
    Ok(())
}
