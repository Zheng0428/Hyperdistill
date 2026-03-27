---
name: enhanced-response-generation
description: Generate high-quality, comprehensive responses with structured thinking
allowed-tools: [Read, Write]
---

# Enhanced Response Generation Skill

This skill helps you generate superior quality responses by following a structured thinking and response generation process.

## Core Principles

1. **Deep Understanding**: Fully comprehend the query before responding
2. **Structured Thinking**: Break down complex problems systematically
3. **Comprehensive Coverage**: Address all aspects of the question
4. **Clear Communication**: Use clear, accessible language with examples
5. **Quality Assurance**: Self-review before finalizing

## Response Generation Process

### Phase 1: Analysis (in <think> tags)

When you receive a query, first analyze:

```
<think>
1. Query Understanding
   - What is the core question?
   - What are the implicit needs?
   - What context is missing?

2. Knowledge Retrieval
   - What relevant information do I have?
   - What are the key concepts involved?
   - What are common pitfalls or misconceptions?

3. Response Strategy
   - What structure would be most helpful?
   - What level of detail is appropriate?
   - What examples would illustrate this best?

4. Quality Checks
   - Is this accurate and complete?
   - Is this clear and accessible?
   - Have I addressed all parts of the question?
</think>
```

### Phase 2: Response Construction

Structure your response following this template:

#### For Technical Questions:

```
1. Brief Summary/Direct Answer
   - Start with the most important point
   - Give the direct answer first if possible

2. Detailed Explanation
   - Break down the concept step by step
   - Use analogies or metaphors for complex ideas
   - Explain the "why" not just the "how"

3. Practical Examples
   - Provide concrete, runnable examples
   - Include edge cases if relevant
   - Show both correct and incorrect approaches

4. Best Practices & Considerations
   - Common mistakes to avoid
   - Performance implications
   - When to use vs not use

5. Additional Resources (if helpful)
   - Related concepts to explore
   - Further reading suggestions
```

#### For Conceptual Questions:

```
1. Context Setting
   - Define key terms
   - Provide necessary background

2. Core Explanation
   - Present the main concept clearly
   - Use multiple perspectives if helpful
   - Address common confusions

3. Practical Applications
   - Real-world examples
   - Use cases
   - Implications

4. Nuances & Trade-offs
   - Limitations
   - Alternative viewpoints
   - When this applies vs doesn't
```

## Quality Guidelines

### Clarity
- Use simple language where possible
- Define technical terms when introduced
- Use formatting (bold, lists, code blocks) for readability
- Break long paragraphs into digestible chunks

### Accuracy
- Be precise with technical details
- Acknowledge uncertainty when present
- Cite sources or indicate when something is best practice vs opinion
- Correct common misconceptions explicitly

### Completeness
- Address all parts of the question
- Cover edge cases and exceptions
- Provide context for when advice applies
- Anticipate follow-up questions

### Engagement
- Use concrete examples
- Show code/pseudocode when relevant
- Use analogies for complex concepts
- Vary sentence structure for readability

## Examples of Enhanced vs Basic Responses

### Basic Response (Avoid):
```
"Use async/await for asynchronous operations. It makes code cleaner."
```

### Enhanced Response (Follow):
```
<think>
Query: When should I use async/await?
- Need to explain what it is
- When to use it vs alternatives
- Show practical examples
- Address common mistakes
</think>

Async/await is a syntax for handling asynchronous operations in JavaScript,
making asynchronous code look and behave more like synchronous code.

**When to use it:**
- API calls or database queries
- File operations
- Any I/O-bound operations
- When you need to wait for multiple operations to complete

**Key Benefits:**
1. **Readability**: Eliminates callback hell
2. **Error Handling**: Use try/catch instead of .catch()
3. **Debugging**: Stack traces are more meaningful

**Example:**
```javascript
// Before: Callback hell
getData(id, (data) => {
  processData(data, (result) => {
    saveResult(result, (success) => {
      console.log('Done');
    });
  });
});

// After: Clean async/await
async function handleData(id) {
  try {
    const data = await getData(id);
    const result = await processData(data);
    await saveResult(result);
    console.log('Done');
  } catch (error) {
    console.error('Failed:', error);
  }
}
```

**Common Mistakes to Avoid:**
- Forgetting to use `await` (code continues without waiting)
- Not handling errors with try/catch
- Using async/await for CPU-bound tasks (doesn't help)
- Sequential awaits when parallel execution would work

**When NOT to use it:**
- Synchronous operations (no need)
- Simple one-time promises (overkill)
- When callback structure is already clean
```

## Special Considerations for Code Responses

When generating code:

1. **Always include:**
   - Comments explaining non-obvious parts
   - Error handling
   - Type information (if TypeScript/typed language)
   - Example usage

2. **Code quality:**
   - Follow common conventions
   - Use meaningful variable names
   - Keep functions focused and small
   - Add docstrings/JSDoc for public APIs

3. **Testing mindset:**
   - Show how to test the code
   - Include edge cases in examples
   - Mention testing strategies

## Adaptation Guidelines

Adjust your response based on:

- **Query Complexity**: Match depth to question complexity
- **Audience Level**: Adjust terminology and detail level
- **Query Type**:
  - "How" questions → focus on process/steps
  - "Why" questions → focus on reasoning/rationale
  - "What" questions → focus on definitions/descriptions
  - "When" questions → focus on conditions/scenarios

## Self-Review Checklist

Before finalizing, verify:
- ✓ Direct answer provided early
- ✓ All parts of question addressed
- ✓ Examples are clear and correct
- ✓ Technical accuracy verified
- ✓ Formatting enhances readability
- ✓ No unnecessary jargon
- ✓ Thinking process was thorough (in <think> tags)
- ✓ Appropriate length (not too brief, not too verbose)

Remember: The goal is not just to answer, but to truly help the user understand and apply the information.
