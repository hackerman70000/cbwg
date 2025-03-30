
use parser::parse_line;
use pyo3::prelude::*;
mod lang;
mod parser;
mod transforms;

// TODO: fix arrow typing

#[pyfunction]
pub fn run(rules: Vec<String>, words: Vec<String>) -> PyResult<Vec<String>> {
    // We can call py.allow_threads to ensure the GIL is released during our
    // operations
    // This example just wraps `arrow_select::take::take`
    let mut output_array: Vec<String> = Vec::new();
    for element in rules.iter() {
        match parse_line(&mut element.to_string().as_str()) {
            Ok(rule) => {
                for values in words.iter() {
                    // perf issue: clone is expensive
                    match lang::Rule::run_all(rule.clone(), values.to_string()) {
                        Some(result) => output_array.push(result),
                        None => {}
                    }
                }
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
