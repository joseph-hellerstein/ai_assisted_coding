# AI-Assisted Python Programming: Course Outline

This document provides brief descriptions of the content of lectures.

1. Course introduction and old school software engineering
   1. Course learning objectives.
   2. AI/ML background
      1. History
      2. Key concepts in neural networks
      3. Capabilities and limitations of LLMs
      4. AI ethics
   3. Old school software engineering
      1. Agile programming: specify, implement/test, evaluate
      2. Documentation: overall spec, module, function/method
      3. Design
      4. Tests: what is a test; writing tests; coverage; not flakey; pytest

2. Running example
   1. Description of the survey manager
      1. Survey authoring
      2. Survey taking
      3. Survey analysis
   2. ``Dash`` overview
   3. A simple ``Dash`` application
   4. HTML
   5. ``callbacks``

3. Basics of AI-Assists
   1. Architecture and terminology
      1. AI model
      2. Tokens
      3. Context
      4. Harness
      5. Agents, skills (and where *.md files live)
      6. Tools
   2. Claude on-boarding
      1. Installing the Anthropic extension in VSCode
      2. The sidebar chat interface
      3. Running /init
   3. Chat interface
   4. AI review and iterate implementation
   5. Prompting skills

4. AI assisted code review

5. AI-Assisted implementation of unit tests

6. Assisted small feature implementation
   1. Scope: function/method or small refactor
   2. Use case 1: Complete a partial implementation
      1. Implementation may have comments in sections and errors in others.
   3. Use case 2: AI creates from scratch
      1. Write function doc
      2. AI implementation
      3. Review and iterate
      4. AI writes tests
      5. Review tests

7. Cost and effectiveness of AI assists
   1. Key metrics: tokens and context
      1. What they are
      2. How to monitor
   2. Charging algorithms for LLMs
   3. Speed of response with larger context
   4. Best practices
      1. Summarize and start anew
      2. Concise prompts
      3. Use local LLM

8. Assists for large feature: Part 1
   1. Scope: Requires at least one module
   2. Write specification
   3. Review for: completeness, ambiguities, consistency

9. Assists for large features: Part 2
   1. Write a plan and review
   2. Execute each step of the plan.

10. Direct prompting vs. program  assisted action.

11. Working with multiple harnesses

12. Running AI models locally
    1. LM studio
       1. Overview
       2. Downloading models
       3. Running a local model
    2. Connecting VSCode with LM Studio
    3. Comparing local vs. remote models

13. Introduction to skills.
    1. What is a skill
    2. Why skills are useful for AI assisted coding
    3. First skills example
    4. Second skills example

14. Guidelines for writing skills

15. Integrate subagents into your workflow

16. Introduction to MCP tools

17. Integrating tools into workflow
    1. playright

18. Writing your own tool
