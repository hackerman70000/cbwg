
use pyo3::prelude::*;
pub mod lang;
pub mod parser;
pub mod engine;

#[pyfunction]
pub fn run(rules: Vec<String>, words: Vec<String>) -> PyResult<Vec<String>> {
    engine::run(rules, words).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run, m)?)?;
    Ok(())
}
