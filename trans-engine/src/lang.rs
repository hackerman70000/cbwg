use itertools::Itertools;

#[derive(Debug, Clone, PartialEq, PartialOrd, Eq, Ord, Hash)]
pub enum Rule {
    /// Passthrough
    /// example: p@assW0rd -> p@assW0rd
    NoOp,
    /// Transform the input string using given rule
    Transform(TransformRule),
    /// Reject the input string if it matches the given rule
    Reject(RejectRule),
    /// End the rule chain
    End,
}


#[derive(Debug, Clone, PartialEq, PartialOrd, Eq, Ord, Hash)]
pub enum TransformRule {
    // John the Ripper/passwords pro rules
    /// Lowercase the entire input string
    /// example: p@ssW0rd -> p@ssw0rd
    Lowercase,
    /// Uppercase the entire input string
    /// example: p@ssW0rd -> P@SSW0RD
    Uppercase,
    /// Capitalize the first letter of the input string, lowercase the rest
    /// example: p@ssW0rd -> P@ssw0rd
    Capitalize,
    /// Lowercase the first letter of the input string, uppercase the rest
    /// example: p@ssW0rd -> p@SSW0RD
    InvertCapitalize,
    /// Toggle the case of the input string
    /// example: p@ssW0rd -> P@SSw0RD
    /// example(N=4):  p@ssW0rd -> p@ssw0rd
    /// example(N=6):  p@ssW0rd -> p@ssW0Rd 
    ToggleCase(Option<usize>),
    /// Reverse the input string
    /// example: p@ssW0rd -> dr0Wss@p
    Reverse,
    /// Duplicate the input string n times (once if n is None)
    /// example: p@ssW0rd -> p@ssW0rdp@ssW0rd
    /// example(N=2):  p@ssW0rd -> p@ssW0rdp@ssW0rdp@ssW0rd
    Duplicate(Option<usize>),
    /// Duplicate the input string reversed
    /// example: p@ssW0rd -> p@ssW0rddr0Wss@p
    Reflect,
    /// Rotate the input string left or right
    /// example(Left): p@ssW0rd -> @ssW0rdp
    /// example(Right): p@ssW0rd -> dp@ssW0r
    Rotate(Rotation),
    /// Append a string to the input string
    /// example(123): p@ssW0rd -> p@ssW0rd123
    Append(String),
    /// Prepend a string to the input string
    /// example(123): p@ssW0rd -> 123p@ssW0rd
    Prepend(String),
    /// Delete a character at the given index
    /// example(3): p@ssW0rd -> p@sW0rd
    Delete(usize),
    Extract(usize, usize),
    Omit(usize, usize),
    Insert(usize, String),
    Overwrite(usize, String),
    Truncate(Truncate),
    Replace(String, String),
    Purge(String),
    DuplicateFirst(usize),
    DuplicateLast(usize),
    DuplicateAll,
    // TODO: memory?

    // hashcat rules
    SwapFront,
    SwapBack,
    Swap(usize, usize),
    BitwiseShiftLeft(usize),
    BitwiseShiftRight(usize),
    AsciiIncrement(usize),
    AsciiDecrement(usize),
    ReplaceWithNext(usize),
    ReplaceWithPrev(usize),
    DuplicateFirstBlock(usize),
    DuplicateLastBlock(usize),
    // TODO: titlecase rules
}

#[derive(Debug, Clone, PartialEq, PartialOrd, Eq, Ord, Hash)]
pub enum Truncate {
    Left,
    Right,
    To(usize)
}

#[derive(Debug, Copy, Clone, PartialEq, PartialOrd, Eq, Ord, Hash)]
pub enum Rotation {
    Left,
    Right,
}

#[derive(Debug, Clone,  PartialEq, PartialOrd, Eq, Ord, Hash)]
pub enum RejectRule {
    ShorterThan(usize),
    LongerThan(usize),
    NotEqualTo(usize),
    Contains(String),
    NotContains(String),
    NotStartsWith(String),
    NotEndsWith(String),
    NotEqualAt(usize, String),
    ContainsLessThan(usize, String),
}


impl Rule {
    pub fn simplify(rules: Vec<Rule>) -> Vec<Rule> {
        basic_simplify(rules)
    }
    pub fn run(&self, input: String) -> Option<String> {
        match self {
            Rule::NoOp => Some(input),
            Rule::Transform(rule) => Some(rule.run(input)),
            // TODO: add run
            Rule::Reject(rule) => rule.run(input),
            Rule::End => Some(input),
        }
    }
    pub fn run_all<'a>(rules: impl  IntoIterator<Item = &'a Rule>, input: String) -> Option<String> {
        let mut output = Some(input);
        for rule in rules {
            output = rule.run(output.unwrap());
            if output.is_none() {
                return None;
            }
        }
        output
    }
}
impl TransformRule {
    pub fn run(&self, input: String) -> String {
        match self {
            TransformRule::Lowercase => input.to_lowercase(),
            TransformRule::Uppercase => input.to_uppercase(),
            TransformRule::Capitalize => {
                let mut chars = input.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => first.to_uppercase().collect::<String>() + chars.as_str().to_lowercase().as_str(),
                }
            },
            TransformRule::InvertCapitalize => {
                let mut chars = input.chars();
                match chars.next() {
                    None => String::new(),
                    Some(first) => first.to_lowercase().collect::<String>() + chars.as_str().to_uppercase().as_str(),
                }
            },
            TransformRule::ToggleCase(n) => {
                match n {
                    Some(n) => {
                        input.char_indices().map(|(i, c)| {
                            if i == *n {
                                if c.is_uppercase() {
                                    c.to_lowercase().next().unwrap()
                                } else {
                                    c.to_uppercase().next().unwrap()
                                }
                            } else {
                                c
                            }
                        }).collect()
                    },
                    None => input.chars().map(|c| {
                        if c.is_uppercase() {
                            c.to_lowercase().next().unwrap()
                        } else {
                            c.to_uppercase().next().unwrap()
                        }
                    }).collect()
                }
            },
            TransformRule::Reverse => input.chars().rev().collect(),
            TransformRule::Duplicate(n) => input.repeat(1 + n.unwrap_or(1) as usize),
            TransformRule::Reflect => input.chars().chain(input.chars().rev()).collect(),
            TransformRule::Rotate(rotation) => {
                match rotation {
                    Rotation::Left => {
                        let mut chars = input.chars();
                        let first = chars.next().unwrap();
                        chars.collect::<String>() + &first.to_string()
                    },
                    Rotation::Right => {
                        let mut chars = input.chars().rev();
                        let first = chars.next().unwrap();
                        first.to_string() + &chars.rev().collect::<String>()
                    },
                }
            },
            TransformRule::Append(s) => input + s,
            TransformRule::Prepend(s) => s.to_owned() + &input,
            TransformRule::Swap(a, b) => {
                let range =  (a.min(b), a.max(b));
                input.chars().enumerate().map(|(i, c)| {
                    if i == *range.0 {
                        input.chars().nth(*range.1).unwrap()
                    } else if i == *range.1 {
                        input.chars().nth(*range.0).unwrap()
                    } else {
                        c
                    }
                }).collect()
            },
            TransformRule::Delete(n) => {
                input.chars().take(*n).chain(input.chars().skip(*n + 1)).collect()
            },
            TransformRule::Extract(a, b) => {
                input.chars().skip(*a).take(*b).collect()
            },
            TransformRule::Omit(a, b) => {
                input.chars().take(*a).chain(input.chars().skip(*a+*b)).collect()
            },
            TransformRule::Insert(n, s) => {
                input.chars().take(*n).chain(s.chars()).chain(input.chars().skip(*n)).collect()
            },
            TransformRule::Overwrite(n, s) => {
                input.chars().take(*n).chain(s.chars()).chain(input.chars().skip(*n + s.len())).collect()
            },
            TransformRule::Truncate(n) => {
                match n {
                    Truncate::Left => input.chars().skip(1).collect(),
                    Truncate::Right => input.chars().take(input.len() - 1).collect(),
                    Truncate::To(n) => input.chars().take(*n).collect(),
                }
            },
            TransformRule::Replace(a, b) => input.replace(a, b),
            TransformRule::Purge(s) => input.replace(s, ""),
            TransformRule::DuplicateFirst(n) => match input.chars().next() {
                Some(first) => first.to_string().repeat(*n) + &input,
                None => input,
            },
            TransformRule::DuplicateLast(n) => match input.chars().rev().next() {
                Some(last) => input + &last.to_string().repeat(*n),
                None => input,
            },
            TransformRule::DuplicateAll => {
                input.chars().interleave(input.chars()).collect()
            },
            TransformRule::SwapFront => {
                let mut chars = input.chars();
                let first = chars.next().unwrap();
                let second = chars.next().unwrap();
                second.to_string() + &first.to_string() + &chars.collect::<String>()
            },
            TransformRule::SwapBack => {
                let mut chars = input.chars().rev();
                let first = chars.next().unwrap();
                let second = chars.next().unwrap();
                chars.rev().collect::<String>() + &first.to_string() + &second.to_string()
            },
            TransformRule::BitwiseShiftLeft(n) => {
                input.chars().map(|c| {
                    let mut c = c as u8;
                    c = c << *n;
                    c as char
                }).collect()
            },
            TransformRule::BitwiseShiftRight(n) => {
                input.chars().map(|c| {
                    let mut c = c as u8;
                    c = c >> *n;
                    c as char
                }).collect()
            },
            TransformRule::AsciiIncrement(n) => {
                input.chars().map(|c| {
                    let mut c = c as u8;
                    c = c.wrapping_add(*n as u8);
                    c as char
                }).collect()
            },
            TransformRule::AsciiDecrement(n) => {
                input.chars().map(|c| {
                    let mut c = c as u8;
                    c = c.wrapping_sub(*n as u8);
                    c as char
                }).collect()
            },
            TransformRule::ReplaceWithNext(n) => {
                input.chars().enumerate().map(|(i, c)| {
                    if i == *n {
                        input.chars().nth(i + 1).unwrap()
                    } else {
                        c
                    }
                }).collect()
            },
            TransformRule::ReplaceWithPrev(n) => {
                input.chars().enumerate().map(|(i, c)| {
                    if i == *n {
                        input.chars().nth(i - 1).unwrap()
                    } else {
                        c
                    }
                }).collect()
            },
            TransformRule::DuplicateFirstBlock(n) => 
                input.chars().take(*n).collect::<String>() + &input
            ,
            TransformRule::DuplicateLastBlock(n) => {
                let last = input.chars().rev().take(*n).collect::<Vec<char>>().iter().rev().collect::<String>();
                input + &last
            },
        }
    }
}

impl RejectRule {
    pub fn run(&self, input: String) -> Option<String> {
        match self {
            RejectRule::ShorterThan(n) => {
                if input.len() >= *n {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::LongerThan(n) => {
                if input.len() <= *n {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::NotEqualTo(n) => {
                if input.len() == *n {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::Contains(s) => {
                if !input.contains(s) {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::NotContains(s) => {
                if input.contains(s) {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::NotStartsWith(s) => {
                if input.starts_with(s) {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::NotEndsWith(s) => {
                if input.ends_with(s) {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::NotEqualAt(n, s) => {
                if input.chars().skip(*n).take(s.len()).collect::<String>() == *s {
                    Some(input)
                } else {
                    None
                }
            },
            RejectRule::ContainsLessThan(n, s) => {
                if input.matches(s).count() >= *n {
                    Some(input)
                } else {
                    None
                }
            },
        }
    }
}



fn basic_simplify(rules: Vec<Rule>) -> Vec<Rule> {
    rules
        .into_iter()
        .filter(|rule| match rule {
            Rule::NoOp => false,
            _ => true,
        })
        .coalesce(|prev, current| {
            match (prev, current) {
                // remove noops
                (Rule::NoOp, current) => Ok(current),
                (
                    Rule::Transform(TransformRule::Append(a)),
                    Rule::Transform(TransformRule::Append(b)),
                ) => Ok(Rule::Transform(TransformRule::Append(a + &b))),
                (
                    Rule::Transform(TransformRule::Prepend(a)),
                    Rule::Transform(TransformRule::Prepend(b)),
                ) => Ok(Rule::Transform(TransformRule::Prepend(b + &a))),
                (
                    Rule::Transform(TransformRule::DuplicateLast(a)),
                    Rule::Transform(TransformRule::DuplicateLast(b)),
                ) => Ok(Rule::Transform(TransformRule::DuplicateLast(a + b))),
                (
                    Rule::Transform(TransformRule::DuplicateFirst(a)),
                    Rule::Transform(TransformRule::DuplicateLast(b)),
                ) => Ok(Rule::Transform(TransformRule::DuplicateFirst(a + b))),
                (
                    Rule::Transform(TransformRule::Lowercase),
                    Rule::Transform(TransformRule::Lowercase),
                ) => Ok(Rule::Transform(TransformRule::Lowercase)),
                (
                    Rule::Transform(TransformRule::Uppercase),
                    Rule::Transform(TransformRule::Uppercase),
                ) => Ok(Rule::Transform(TransformRule::Uppercase)),
                (
                    Rule::Transform(TransformRule::Capitalize),
                    Rule::Transform(TransformRule::Capitalize),
                ) => Ok(Rule::Transform(TransformRule::Capitalize)),
                (
                    Rule::Transform(TransformRule::InvertCapitalize),
                    Rule::Transform(TransformRule::InvertCapitalize),
                ) => Ok(Rule::Transform(TransformRule::InvertCapitalize)),
                (
                    Rule::Transform(TransformRule::ToggleCase(a)),
                    Rule::Transform(TransformRule::ToggleCase(b)),
                ) if a == b => Ok(Rule::NoOp),
                (
                    Rule::Transform(TransformRule::Reverse),
                    Rule::Transform(TransformRule::Reverse),
                ) => Ok(Rule::NoOp),
                (prev, current) => Err((prev, current)),
            }
        })
        .collect()
}
