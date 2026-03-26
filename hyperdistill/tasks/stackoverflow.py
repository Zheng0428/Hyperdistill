"""
StackOverflow Enhancement task.

Reads raw StackOverflow Q&A data (Post_Title, Post_Body, Post_Tags, Answers, Comments),
constructs a prompt to enhance the Q&A into higher difficulty, more comprehensive content,
and parses the YAML-formatted response.

Source data: /volume/pt-coder/users/tuney/pretrain_data/stackoverflow/matched_output_10.jsonl
"""

import json
from typing import Any, Dict, List, Optional

from .base import BaseTask
from .registry import TaskRegistry


SYSTEM_PROMPT = """You are a StackOverflow data enhancement expert.

## Core Objective

Transform raw StackOverflow Q&A data into a **higher difficulty, more comprehensive** technical question.

**Key Requirements**:
1. **Code based on actual needs**: Decide whether code snippets are needed based on the question's nature
   - Implementation questions: Must include code examples showing the problem
   - Concept explanation questions: May not need code, focus on clear technical description
   - Tool usage questions: Decide whether to show configurations or commands as needed
2. **Technical transformation**: Concretize abstract questions into more professional technical questions
3. **Real scenarios**: Based on actual technical scenarios and application cases"""


USER_PROMPT_TEMPLATE = """## Input Data

Below is the raw StackOverflow question data in JSON format:

```json
{source_json}
```

## Your Task

Transform this raw StackOverflow Q&A into a higher difficulty, more comprehensive technical question.

### Workflow

1. **Deep understanding of raw data**
   - Extract key information from `Post_Body` and `Answers` list
   - Analyze core technical points and difficulty level of the question
   - Identify tech stack, concepts, and application scenarios involved
   - **Understand answers**: Raw data may contain multiple answers with different solutions or perspectives; use them to understand the problem better and enrich the question context
   - Identify the accepted answer (`Post_AcceptedAnswerId` correspondence) and other high-score answers
   - **Value comment information**:
     * `Comments` under the question may contain clarifications and supplementary explanations
     * `Comments` under each answer may contain important technical details, edge cases, potential issue warnings
     * Integrate key information from comments into the enhanced question
   - Note: Need to handle HTML tags, extract plain text and code blocks

2. **Elevate difficulty and completeness**
   - Increase depth and complexity of the question
   - Add more technical details and professional terminology
   - Introduce real engineering scenarios and constraints
   - Consider multiple dimensions: performance, security, maintainability, etc.

3. **Generate enhanced question**
   - **Title**: More specific, more professional, reflecting increased difficulty
   - **Question body**: Clearly describe problem background, specific difficulties, and expected solution standards
   - **Optional**: Include code examples showing the problem (if helpful for illustration)

4. **Maintain technical accuracy**
   - Ensure all code syntax is correct
   - Follow coding conventions of target language
   - Verify accuracy of technical concepts

## Output Format

**CRITICAL**: Your output MUST be a YAML code block. Generate YAML format output with the following fields:

```yaml
enhanced_question:
  title: "Enhanced question title"
  body: "Enhanced question body (Markdown format)"
  contains_code: true
enhancement_notes:
  explanation: "Brief explanation of key improvements and technical transformation strategy (2-3 sentences)"
```

**Important Notes**:
- **CRITICAL: Output MUST be a YAML code block** wrapped in ```yaml ... ```
- **Question only**: Generate only the enhanced question; do NOT generate an answer
- **Utilize comment information**: Extract key technical details from `Comments`
- **Code decision**: Implementation/debugging questions may include code showing the problem; concept/architecture questions optional
- **Maintain authenticity**: Enhance based on original question's core intent
- **No extra commentary**: Only output the YAML code block, no explanation before or after it"""


@TaskRegistry.register
class StackOverflowTask(BaseTask):
    name = "stackoverflow"

    def get_id(self, item: Dict[str, Any]) -> str:
        return str(item["id"])

    def get_id_fields(self) -> Optional[List[str]]:
        """Use id field as the ID."""
        return ["id"]

    def build_messages(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        # Build a clean source JSON with relevant fields for the prompt
        user_prompt = USER_PROMPT_TEMPLATE.replace("{source_json}", str(item))

        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
    def process_result(
        self,
        item: Dict[str, Any],
        content: str,
        thinking: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        item["response"] = content
        item["thinking"] = thinking
        return item

    def validate_item(self, item: Dict[str, Any]) -> bool:
        return "id" in item

    