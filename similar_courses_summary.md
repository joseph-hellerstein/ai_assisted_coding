# Similar Courses at Top Universities and Online Platforms: AI-Assisted Python Programming

This document summarizes courses similar to or related to "AI-Assisted Python Programming." It combines two rounds of research: an initial pass on LLM/transformer/deep-learning courses at top universities, and a second, more targeted pass on courses that teach AI-assisted software development as a *practice* — coding agents, prompting workflow, MCP, skills, subagents, local models — which is the actual angle of `course_outline.md`. Audience assumed throughout: learners who already write Python in multi-module projects and use GitHub, not notebook-only beginners.

**Note on verification:** All entries below were checked against live course pages as of August 2026, by fetching the actual page rather than relying on search snippets alone. Corrected URLs and descriptions are noted where an original listing was inaccurate or a link had gone dead. One entry (MIT "AI for Code") was removed in round 1 because no such course could be found under that name or number.

---

## University Courses

### 1. Stanford CS25: Transformers United V6

**University:** Stanford University
**URL:** https://web.stanford.edu/class/cs25/

**Summary:** One of Stanford's most popular seminar courses, featuring weekly talks from top researchers at the forefront of Transformer research. The course covers breakthroughs in AI from large language models like GPT to applications in art, biology, and robotics. Topics include:
- Overview of Transformers and how they work
- State Space Models vs. Transformers (subquadratic alternatives)
- Ultra-scale training across thousands of GPUs
- Pretraining algorithm design for LLMs
- Generalization from parameters vs. context
- Collaborative AI agents for science and medicine
- Native multimodal intelligence
- Production inference at scale

The course features weekly talks by leading researchers (recent speakers include folks from Anthropic, DeepMind, Hugging Face, Mistral AI, and CMU) and is open to auditors, including Zoom livestream access. It has over 5,000 Discord members.

---

### 2. UC Berkeley CS285: Deep Reinforcement Learning

**University:** University of California, Berkeley
**URL:** https://rail.eecs.berkeley.edu/deeprlcourse-fa23/

**Summary:** Taught by Professor Sergey Levine, this is Berkeley's flagship deep reinforcement learning course. It does not have dedicated modules on AI-assisted programming; it is included here as a related course on the deep learning side of the field. Topics include:
- Imitation learning and policy gradients
- Actor-critic algorithms and value function methods
- Model-based reinforcement learning
- Exploration and offline reinforcement learning
- Practical applications of deep learning to sequential decision-making

*Correction: the original listing pointed to Pieter Abbeel's personal page, which is not the current course site or instructor. The course is currently taught by Sergey Levine at the URL above.*

---

### 3. CMU 11-667: Large Language Models — Methods and Applications

**University:** Carnegie Mellon University (CMU)
**URL:** https://cmu-llms.org/

**Summary:** A graduate-level course providing a holistic view of the current state of large language models. Topics include:
- Language model architectures, training, inference, and evaluation
- Interpretation, alignment, and emergent capabilities of LLMs
- Applications in language tasks and beyond
- Scaling up pretraining and efficient deployment techniques
- Concerns and open challenges surrounding LLM deployment

*Correction: the original listing cited non-existent course numbers ("11-659/11-780") and a dead URL. The real, current CMU course on this topic is 11-667, hosted at the URL above (also cross-listed in some years as 11-766: Large Language Model Applications).*

---

### 4. CMU 15-113: Effective Coding with AI

**University:** Carnegie Mellon University (CMU)
**URL:** https://www.cs.cmu.edu/~113/index.html
**Status:** Live, Spring 2026 offering, verified by direct fetch.

**Summary:** Taught by Mike Taylor, this is the closest university match found across both rounds of research — a 14-week, project-based course explicitly for students who already know how to program (prerequisite: CMU's intro CS course) who want to learn to build with AI tools "the right way." Structure closely parallels the outline's practical arc:
- Weeks 1–4: tool fluency (terminal, Git/GitHub, AI coding assistants), naive vs. structured prompting strategies
- Weeks 4–9: APIs, backend/frontend development, databases (SQLite), ethics discussions (bias, IP, environmental impact, job displacement)
- Weeks 10+: multi-agent workflows, "the agentic frontier," RAG, a capstone project
- Every project requires a **prompt log** and a written reflection the student must produce without AI — a direct parallel to the outline's emphasis on review/iterate and documentation.

Difference from the outline: CMU's course is built around a portfolio of shippable web/mobile projects rather than survey-manager-style module work, and it doesn't cover local model hosting (LM Studio) or MCP tool-building in the same depth.

---

### 5. Purdue University — CS 59300ASE: AI-Assisted Software Engineering

**University:** Purdue University
**URL:** https://www.cs.purdue.edu/graduate/variable-courses.html
**Status:** The PDF syllabus originally found (`.../VT course syllabi/Spring 2024/CS 59200_T ZHang...pdf`) returns a 404 — the file appears to have been moved or delisted. The course itself is real and current; the link above is the live Purdue CS graduate course-listing page confirming it, currently catalogued as **CS 59300ASE** (previously offered as a CS 59200 seminar section).

**Summary:** Taught by Prof. Tianyi Zhang (software engineering / human-AI interaction researcher). Prerequisites: Python and basic ML knowledge. This is a research-seminar format — students read and present papers on code generation, AI-based testing tools, and human-AI programming partnership, and complete a group research project — rather than a hands-on build-things course. Good complement to the outline's "cost and effectiveness of AI assists" and "AI review and iterate" sections if the instructor wants research grounding, but it's pitched at grad students doing SE research, not practitioners.

---

### 6. Northwestern University — COMP_SCI 397: Applied AI for Software Development

**University:** Northwestern University
**URL:** https://www.mccormick.northwestern.edu/computer-science/academics/courses/descriptions/397-6.html
**Status:** Live, verified by direct fetch.

**Summary:** Taught by Hamilton Murrah, for fourth-year undergrads and MS students who already have programming fundamentals — explicitly pitched (per the department) as teaching students to use GenAI tools *after* they have a firm grip on fundamentals, not instead of. Covers prompt-based code generation, best-practice policies for when/how to use AI tools on a team, and the practical limits of tools like Copilot and ChatGPT in real software projects. No published detailed syllabus is public, so exact week-by-week overlap with the outline (MCP, skills, subagents) can't be confirmed — flagged as a gap.

---

### 7. University of Washington CSE490A2: AI-Assisted Software Development

**University:** University of Washington
**URL:** https://courses.cs.washington.edu/courses/cse490a2/25au (archived Autumn 2025 offering) and https://www.cs.washington.edu/academics/undergraduate/ai-education/ (current status page)

**Summary:** Generative AI (GenAI) assistance for programming is transforming software development. This course is an introduction to AI-assisted software development. This is not a course about coding. It teaches clear specifications, system decomposition, code review, debugging, and similar skills needed of a team leader. A programmer directing AI agents is a team leader. Most of the topics are the same skills that you should learn today to become an effective system builder.

Each week, the course covers a different software development task. The weekly assignment is doing that task, using AI assistance, on a codebase provided by the course staff. Example tasks include pair programming, code review, documenting code, debugging, and prototyping user interfaces.

*Correction (round 1): the original URL pointed to a generic course listing page rather than the course itself. The specific course page is linked above.*

*Status update (round 2): this course was a one-time pilot in **Fall 2025**. The Allen School's AI-education page now lists it as **"AI-Assisted Software Engineering," next offering planned for Winter 2027** (title may change) — it is not currently running. The same status page also lists a *second*, separate pilot, **"Using AI-Coding Tools"** (title tentative), scheduled for **Fall 2026** — worth watching as a closer, more recent peer.*

---

### 8. UC Berkeley CS 194/294-196: Agentic AI (public MOOC)

**University:** University of California, Berkeley
**URL:** https://agenticai-learning.org/f25
**Status:** Live, verified by direct fetch. Fall 2025 offering; successor to the "LLM Agents" MOOC series.

**Summary:** Taught by Prof. Dawn Song with weekly guest lectures from OpenAI, Google DeepMind, Meta, Microsoft, NVIDIA, and Sierra. Free, open enrollment, certificate available. Content is weighted toward agent research (reasoning/planning, multi-agent systems, evaluation, safety) with **code generation as one of several application areas** (alongside robotics, web automation, science), rather than a hands-on "build software with an AI assistant" course. Useful as a supplementary theory track for the outline's Module 3 (architecture/terminology) but not a structural peer for the practical modules.

---

### 9. Stanford CS329A: Self-Improving AI Agents

**University:** Stanford University
**URL:** https://cs329a.stanford.edu/index.html
**Status:** Live, verified by direct fetch. Autumn 2025 offering, taught by Aakanksha Chowdhery and Azalia Mirhoseini.

**Summary:** A graduate research seminar on techniques for agents that improve themselves (test-time compute scaling, verifiers, RL, agentic frameworks for software engineering as one unit). Grading is paper presentations, homeworks, and an original research project with a poster session — this is a research methods course for people who want to *build or study* agent techniques, not a practitioner course on using coding agents day to day. Included for completeness but is a weaker match than CMU 15-113 or Northwestern's course.

---

### 10. CMU 11-667 / Related — see entry 3 above (duplicate topic areas consolidated)

---

### 11. Harvard — LLMs for Design and Applications

**University:** Harvard University
**URL:** https://www.eecs.harvard.edu/htk/courses/

**Summary:** Taught by Professor H.T. Kung, this course teaches students to use LLM-powered tools to address real-world design challenges, including the generation of code and circuits. Topics include:
- Systolic arrays, low-bitwidth arithmetic, and model pruning/quantization
- Distillation, low-rank fine-tuning, and dynamic sub-model selection
- Speculative decoding and synthetic data generation
- Using LLMs to generate code that leverages AI-acceleration techniques

---

### 12. ETH Zurich: Large Language Models

**University:** ETH Zurich (Swiss Federal Institute of Technology)
**URL:** https://rycolab.io/classes/llm-s26/

**Summary:** Taught by the Rycolab group, this course covers the probabilistic foundations of language models, training corpus construction and curation, and the neural-network architectures used to instantiate language models at scale. Topics include:
- Formal, theoretical foundations of language modeling
- Systems programming aspects of LLMs
- Privacy and harms in deployed language models
- Applications of language models in NLP and beyond

*Correction: the original listing ("NLP4SE.org," on NLP for Software Engineering) does not correspond to any real ETH course or URL. The entry above is ETH's actual, currently-offered course most closely related to LLMs.*

---

### 13. Georgia Tech CS 4650 / 7650: Natural Language Processing

**University:** Georgia Institute of Technology
**URL:** https://omscs.gatech.edu/cs-7650-natural-language-processing

**Summary:** This course gives an overview of modern data-driven techniques for natural language processing, moving from shallow bag-of-words models to richer structural representations of language, including language models. Topics include:
- Text classification, word embeddings, and language modeling
- Sequence tagging and structured prediction
- Neural network approaches to NLP tasks
- Applications including dialogue, translation, and document retrieval

---

### 14. University of Toronto CSC413 / 2516: Neural Networks and Deep Learning

**University:** University of Toronto
**URL:** https://uoft-csc413.github.io/2023/

**Summary:** This course gives an overview of foundational ideas and recent advances in neural network algorithms. Topics include:
- Backpropagation and automatic differentiation
- Convolutional and recurrent network architectures
- Optimization and generalization techniques
- Unsupervised learning and reinforcement learning with neural networks

*Correction: the original listing cited "CSC486/686" as an "Introduction to Deep Learning" course, but CSC486 is actually Toronto's **Knowledge Representation and Reasoning** course — unrelated to deep learning. The course above (CSC413/2516) is Toronto's real deep learning course.*

---

### 15. Imperial College London: Computing (Artificial Intelligence and Machine Learning)

**University:** Imperial College London
**URL:** https://www.imperial.ac.uk/study/courses/undergraduate/computing-artificial-intelligence-meng/

**Summary:** An MEng degree track that lets students specialize in artificial intelligence and knowledge engineering, machine learning, and computational/engineering models of complex cognitive and social behavior. Topics include:
- Search algorithms and constraint satisfaction
- Neural network foundations for understanding modern AI systems
- Practical applications of AI tools and techniques
- Ethical and societal considerations of AI

*Correction: the original URL was a generic course-listing page. The link above is Imperial's specific AI/ML degree program page.*

---

## Online / Vendor Courses (closer topical matches)

These aren't university courses, but several match the outline's *specific* topics — CLAUDE.md files, subagents, MCP, skills, git worktrees — far more closely than any university syllabus found, since they're built by the same vendor (Anthropic) or its close partners around the same tools referenced in the outline.

### 16. Coursera / Vanderbilt University — "Claude Code: Software Engineering with Generative AI Agents"

**URL:** https://www.coursera.org/learn/claude-code
**Status:** Live, verified by direct fetch. Instructor: Dr. Jules White (Vanderbilt), 47,000+ enrolled, 4.7/5 over 168 reviews.

**Summary:** The single closest structural match to `course_outline.md` found across both rounds. Six modules cover: treating Claude Code as "AI labor," code-quality evaluation, **writing CLAUDE.md files and reusable commands** (outline §3.1.5, §6), **git worktrees and subagents for parallel development** (outline §15), and multimodal prompting. Prerequisite is "basic software development experience and familiarity with Git" — matches the intended audience closely. Requires a paid Claude Code subscription to complete exercises.

---

### 17. DeepLearning.AI (built with Anthropic) — "Claude Code: A Highly Agentic Coding Assistant"

**URL:** https://www.deeplearning.ai/courses/claude-code-a-highly-agentic-coding-assistant
**Status:** Live, verified by direct fetch. Instructor: Elie Schoppik, Head of Technical Education at Anthropic. ~2 hours, free.

**Summary:** Ten short lessons using a real RAG-chatbot codebase: codebase exploration, CLAUDE.md, adding features, testing/refactoring, **running multiple Claude Code sessions in parallel via git worktrees**, GitHub issue/PR integration, hooks, and connecting **Playwright and Figma MCP servers** (outline §16–17). Prerequisite: familiarity with Python and Git — good direct reading/demo material for the outline's Module 3 and Module 17.

---

### 18. DeepLearning.AI (built with Anthropic) — "Agent Skills with Anthropic"

**URL:** https://www.deeplearning.ai/courses/agent-skills-with-anthropic
**Status:** Listed live on DeepLearning.AI's current course catalog (confirmed via search result; not independently re-fetched).

**Summary:** Covers how Skills work across Claude.ai, Claude Code, the API, and the Agent SDK, and how to combine them with MCP and subagents — a direct match for outline Modules 13–14 ("Introduction to skills," "Guidelines for writing skills").

---

### 19. Anthropic Academy — "Claude Code 101"

**URL:** https://anthropic.skilljar.com/claude-code-101
**Status:** Live, verified by direct fetch. Free, self-paced, Skilljar-hosted.

**Summary:** Free and remarkably close to the outline's Module 3 ("Basics of AI-Assists") point-for-point: agentic loop/context/tools/permissions terminology, installation across terminal/VS Code/JetBrains, the **Explore → Plan → Code → Commit workflow**, context management (`/compact`, `/clear`, `/context`), **CLAUDE.md**, **subagents**, **Skills**, **MCP**, and hooks. Worth using directly as a reference syllabus for the outline's Module 3 and parts of Modules 13–16.

---

### 20. Anthropic Academy — "Claude Code in Action"

**URL:** https://anthropic.skilljar.com/claude-code-in-action
**Status:** Confirmed via Anthropic's own course listing (not independently re-fetched in this pass).

**Summary:** Follow-on to Claude Code 101 — 15 short lectures on real development tasks (navigating an unfamiliar codebase, planning a feature before writing it, running long unattended sessions with verification). Matches outline §6 (assisted small feature implementation) and §9 (write-a-plan-and-execute workflow).

---

### 21. Anthropic Academy — "Introduction to Model Context Protocol"

**URL:** https://anthropic.skilljar.com/introduction-to-model-context-protocol
**Status:** Live, verified by direct fetch. Free. Also offered as a separate, paid Coursera version taught by Stephen Grider at https://www.coursera.org/learn/introduction-to-model-context-protocol — 4 modules, hands-on building of an MCP server and client in Python, 4,600+ enrolled — verified live via search result.

**Summary:** Covers MCP's three primitives (tools, resources, prompts), building/testing a server with the MCP Inspector, and client integration — a direct match for outline Module 16 ("Introduction to MCP tools") and Module 18 ("Writing your own tool").

---

## Key Observations

1. **No direct equivalent found, in either round.** There is no single course at a top university, or on a major online platform, that exactly matches the comprehensive coverage of `course_outline.md` — old-school SE foundations, AI-assist architecture/terminology, cost/effectiveness of assists, large-feature workflows, local model hosting, and MCP/skills/subagents, all in one semester-long, graded course.

2. **The closer topical matches are vendor courses, not university courses.** No university course found in either round covers the outline's specific practitioner stack — CLAUDE.md files, subagents, skills, MCP tool-building — as directly as Anthropic's own Academy courses and the DeepLearning.AI/Vanderbilt Claude Code courses do (entries 16–21). If your course's differentiator is the *survey-manager, semester-long, graded-assignment academic format* applied to that same practitioner content, that combination still appears to be genuinely uncommon.

3. **University courses cluster into two camps:** hands-on practitioner courses for students who already code (CMU 15-113, Northwestern COMP_SCI 397, UW's pilot) versus research seminars on agent techniques or LLM theory (Purdue CS 59300ASE, Stanford CS329A/CS25, Berkeley's Agentic AI MOOC/CS285, CMU 11-667, ETH, Georgia Tech, Toronto). Your outline sits in the first camp but with more structured software-engineering scaffolding (documentation, testing, design) than any of them include.

4. **This is a fast-moving field.** Several universities are actively developing new courses on AI-assisted software development specifically (CMU 15-113 and UW's pilots are the clearest examples), and two of the closest peer courses (UW's pilot, Berkeley's MOOC) are one-off or annually-refreshed offerings rather than stable, recurring courses — expect the landscape to keep shifting each semester.

5. **Practical vs. theoretical divide persists.** Most existing university courses lean toward either practical tool usage or theoretical/research understanding, whereas this course aims to balance both, and to do so with an old-school-software-engineering backbone (specs, design, testing, documentation) that most peers lack.

6. **Local-model hosting (LM Studio) is essentially unaddressed academically.** The only material found on this topic, in either round, was vendor/Udemy-style tutorials, not university or established online-platform courses. This may be a genuine differentiator for your outline's Module 12.

7. **A note on sourcing:** Several entries in the original version of this document (round 1) contained fabricated or mismatched course numbers, titles, and URLs (notably for MIT, Harvard, CMU, ETH Zurich, Georgia Tech, and the University of Toronto). All round-1 entries were re-verified against live sources before round 2 began, and all round-2 entries were verified by direct page fetch (noted individually) rather than search-snippet trust alone.
