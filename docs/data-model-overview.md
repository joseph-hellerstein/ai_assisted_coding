# Survey Manager: Key Data at a Glance

A survey holds its questions. Responses and drafts belong to one survey and
hold answers keyed by question id. A draft is a response that isn't finished
yet. See [data-model.md](data-model.md) for every field and how each is stored.

```mermaid
erDiagram
    SURVEY ||--|{ QUESTION : "contains"
    SURVEY ||--o{ RESPONSE : "has submitted"
    SURVEY ||--o{ DRAFT : "has in progress"
    RESPONSE }o..o{ QUESTION : "answers"
    DRAFT }o..o{ QUESTION : "partially answers"

    SURVEY {
        string id PK
        string title "the survey's name"
    }
    QUESTION {
        string id PK
        string text
        string type "text, yesno, likert, matrix, ..."
    }
    RESPONSE {
        string id PK "internal, e.g. resp_482913"
        string survey_id FK
        string respondent_id "5-digit ID the taker enters"
        dict answers "question id to answer"
    }
    DRAFT {
        string id PK "internal"
        string survey_id FK
        string respondent_id "5-digit ID the taker enters"
        dict answers "question id to answer, partial"
    }
```

**How to read it:** `||--|{` means one survey contains one or more questions.
`||--o{` means one survey has zero or more responses, and zero or more drafts.
The dotted lines mean responses and drafts point to questions by putting each
question's id in their `answers` keys.
