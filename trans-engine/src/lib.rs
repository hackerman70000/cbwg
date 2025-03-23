use arrow::pyarrow::ToPyArrow;
use arrow_array::iterator::ArrayIter;
use arrow_array::run_iterator::RunArrayIter;
use arrow_array::types::Utf8Type;
use arrow_array::{Array, ArrayRef, PrimitiveArray, StringArray};
use arrow_schema::DataType;
use parser::parse_line;
use pyo3::prelude::*;
use pyo3_arrow::error::PyArrowResult;
use pyo3_arrow::PyArray;

mod lang;
mod parser;
mod transforms;

// TODO: fix arrow typing

#[pyfunction]
pub fn run(py: Python, rules: PyArray, words: PyArray) -> PyArrowResult<PyObject> {
    // We can call py.allow_threads to ensure the GIL is released during our
    // operations
    // This example just wraps `arrow_select::take::take`
    let mut output_array: Vec<String> = Vec::new();
    let rules_array = rules.to_arro3(py);
    let words_array = words.to_arro3(py);
    for element in rules_array.iter() {
        match parse_line(&mut element.to_string().as_str()) {
            Ok(rule) => {
                for values in words_array.iter() {
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
    Ok(StringArray::from(output_array).to_data().to_pyarrow(py)?)
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run, m)?)?;
    Ok(())
}
