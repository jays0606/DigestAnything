# Gemini Prompting Strategies

*Prompt design* is the process of creating prompts, or natural language requests,
that elicit accurate, high quality responses from a language model.

## Clear and specific instructions

### Input types

| **Input type** | **Example** |
|---|---|
| Question | "What's a good name for a flower shop?" |
| Task | "Give me a simple list of camping essentials" |
| Entity | "Classify these items as [large, small]" |
| Completion | Provide partial content for the model to complete |

### Constraints

Specify any constraints on reading the prompt or generating a response.

### Response format

You can give instructions that specify the format of the response (table,
bulleted list, paragraph, etc.).

## Zero-shot vs few-shot prompts

- **Zero-shot:** No examples provided
- **Few-shot:** Include examples showing the model what correct output looks like

Recommendations:
- Always include few-shot examples in your prompts
- Use specific and varied examples
- Ensure consistent formatting across all examples

### Optimal number of examples

Models can often pick up on patterns using a few examples. Too many examples may
cause overfitting.

## Add context

Include instructions and information the model needs to solve a problem, instead
of assuming it has all required information.

## Break down prompts into components

1. **Break down instructions:** Create one prompt per instruction
2. **Chain prompts:** Sequential steps where output becomes input for next step
3. **Aggregate responses:** Perform different parallel tasks and aggregate results

## Model parameters

1. **Max output tokens:** Maximum tokens in the response
2. **Temperature:** Controls randomness in token selection. For Gemini 3, keep at default 1.0
3. **topK:** How many top tokens to consider
4. **topP:** Cumulative probability threshold for token selection
5. **stop_sequences:** Sequences that tell the model to stop generating

## Gemini 3 Specific

### Core prompting principles

- **Be precise and direct:** State your goal clearly
- **Use consistent structure:** XML-style tags or Markdown headings
- **Define parameters:** Explicitly explain ambiguous terms
- **Control output verbosity:** Explicitly request detailed responses if needed
- **Prioritize critical instructions:** Place essential constraints at the beginning
- **Structure for long contexts:** Context first, instructions at the end
- **Anchor context:** Use transition phrases like "Based on the information above..."

### Gemini 3 Flash strategies

- **Current day accuracy:**
  ```
  For time-sensitive user queries that require up-to-date information, you
  MUST follow the provided current time (date and year) when formulating
  search queries in tool calls. Remember it is 2026 this year.
  ```

- **Knowledge cutoff accuracy:**
  ```
  Your knowledge cutoff date is January 2025.
  ```

### Enhancing reasoning and planning

**Explicit planning:**
```
Before providing the final answer, please:
1. Parse the stated goal into distinct sub-tasks.
2. Check if the input information is complete.
3. Create a structured outline to achieve the goal.
```

**Self-critique:**
```
Before returning your final response, review your generated output against the user's original constraints.
1. Did I answer the user's *intent*, not just their literal words?
2. Is the tone authentic to the requested persona?
```

### Structured prompting examples

**XML example:**
```xml
<role>
You are a helpful assistant.
</role>

<constraints>
1. Be objective.
2. Cite sources.
</constraints>

<context>
[Insert User Input Here]
</context>

<task>
[Insert the specific user request here]
</task>
```

**Markdown example:**
```markdown
# Identity
You are a senior solution architect.

# Constraints
- No external libraries allowed.
- Python 3.11+ syntax only.

# Output format
Return a single code block.
```

## Agentic workflows

When designing prompts for agents, consider:

### Reasoning and strategy
- **Logical decomposition:** How thoroughly the model analyzes constraints
- **Problem diagnosis:** Depth of analysis when identifying causes
- **Information exhaustiveness:** Trade-off between thoroughness and speed

### Execution and reliability
- **Adaptability:** How the model reacts to new data
- **Persistence and Recovery:** Degree of self-correction attempts
- **Risk Assessment:** Logic for evaluating consequences

### Interaction and output
- **Ambiguity handling:** When to make assumptions vs. ask for clarification
- **Verbosity:** Volume of text generated alongside tool calls
- **Precision and completeness:** Required fidelity of the output

### System instruction template for agents

```
You are a very strong reasoner and planner. Use these critical instructions:

Before taking any action, you must proactively plan and reason about:

1) Logical dependencies and constraints
2) Risk assessment
3) Abductive reasoning and hypothesis exploration
4) Outcome evaluation and adaptability
5) Information availability
6) Precision and Grounding
7) Completeness
8) Persistence and patience
9) Inhibit your response: only take action after all reasoning is completed
```
