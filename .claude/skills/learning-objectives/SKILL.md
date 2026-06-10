---
name: writing-learning-objectives
description: Use when writing, reviewing, or improving learning objectives for course episodes or modules. Applies to any course content, especially AI-assisted coding or technical courses. Triggers on requests to write objectives, check objectives quality, or structure what learners will be able to do.
---

# Writing Learning Objectives

## Overview

Learning objectives specify exactly what learners will be able to DO after an episode — not what will be taught. Each objective is a single, measurable, observable behavior anchored to an appropriate Bloom's cognitive level.

## Standard Format

```
By the end of this episode, learners will be able to [ACTION VERB] [OBJECT] [CONDITION/CONTEXT].
```

**Scope:** 3–5 objectives per episode. More means the episode is too broad.

## Bloom's Taxonomy Quick Reference

Match the verb to the intended cognitive level. For introductory technical courses, most objectives land at Apply or below.

| Level | What it means | Strong verbs | Avoid |
|-------|--------------|--------------|-------|
| **Remember** | Recall facts | list, identify, name, define | know, learn |
| **Understand** | Explain concepts | explain, describe, summarize, distinguish | understand, appreciate |
| **Apply** | Use in new situations | use, run, configure, execute, write, demonstrate | be familiar with |
| **Analyze** | Break down / examine | compare, diagnose, examine, differentiate | understand deeply |
| **Evaluate** | Judge / critique | assess, evaluate, justify, select | understand well |
| **Create** | Produce something new | design, build, generate, compose | — |

## Quality Checklist

Before finalizing each objective, verify:

- [ ] Uses a single, measurable action verb (not "understand", "know", or "appreciate")
- [ ] Covers exactly ONE behavior — not two joined with "and"
- [ ] Observable: could a reviewer watch a learner do this?
- [ ] Achievable within the episode's scope and duration
- [ ] Aligns with actual episode content (if objective can't be taught in the episode, cut it)
- [ ] Learner-centered (what the learner does, not what the instructor covers)

## Common Mistakes

| Mistake | Example | Fix |
|---------|---------|-----|
| Vague verb | "Understand prompting strategies" | "Distinguish effective from ineffective prompts" |
| Compound objective | "Install Claude Code **and** configure it" | Split into two objectives |
| Instructor focus | "This episode covers the interface" | "Navigate the Claude Code interface to open a project" |
| Too broad | "Become proficient with Claude Code" | One specific skill per objective |
| Untestable | "Appreciate the value of AI tools" | "Evaluate whether a Claude Code response requires refinement" |

## Example: Well-Formed Objectives

**Episode: Using Claude Code for the First Time**

By the end of this episode, learners will be able to:

1. Install Claude Code and verify it runs successfully in their terminal.
2. Open a project directory and submit their first prompt to Claude Code.
3. Identify the main components of a Claude Code response (code, explanation, proposed changes).
4. Accept or reject a proposed file change and confirm the result in their editor.

Note: "Install... and verify" is acceptable here because install-then-verify is a single workflow step; the verification is not a separate skill. When in doubt, split.
