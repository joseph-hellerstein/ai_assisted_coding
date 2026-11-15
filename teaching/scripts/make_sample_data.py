"""Write two sample surveys, each with five responses.

Run it from the teaching/ folder:  python -m scripts.make_sample_data
"""
import random
from datetime import datetime, timedelta

from src.models import Question, Response, Survey, generate_id
from src.storage import save_response, save_survey

SAMPLE_SURVEYS = [
    ("Workshop feedback", [
        Question(generate_id("q_"), "yesno", "Did you attend the whole workshop?"),
        Question(generate_id("q_"), "checkbox", "Which sessions did you attend?", ["Morning", "Afternoon", "Evening"]),
        Question(generate_id("q_"), "text", "What should we change next time?"),
    ]),
    ("Lab equipment", [
        Question(generate_id("q_"), "checkbox", "Which instruments do you use?", ["Microscope", "Centrifuge", "PCR machine"]),
        Question(generate_id("q_"), "yesno", "Is the booking system easy to use?"),
        Question(generate_id("q_"), "text", "Anything broken or missing?"),
    ]),
]
TEXT_ANSWERS = ["More hands-on time", "Longer breaks please", "Great sessions", "", "More examples"]


def sample_answer(question: Question, rng: random.Random):
    if question.type == "yesno":
        return rng.choice(["Yes", "No"])
    if question.type == "checkbox":
        return rng.sample(question.options, rng.randint(1, len(question.options)))
    return rng.choice(TEXT_ANSWERS)


def main(n_responses: int = 5, seed: int = 0) -> None:
    rng = random.Random(seed)
    start = datetime(2026, 11, 1, 9, 0)
    for title, questions in SAMPLE_SURVEYS:
        survey = Survey(id=generate_id("srv_"), title=title, description="Sample data", questions=questions)
        save_survey(survey)
        for i in range(n_responses):
            answers = {q.id: sample_answer(q, rng) for q in questions}
            save_response(Response(
                id=generate_id("resp_"), survey_id=survey.id,
                submitted_at=(start + timedelta(hours=i)).isoformat(timespec="seconds"),
                respondent_id=f"{rng.randint(0, 99999):05d}",
                answers={qid: a for qid, a in answers.items() if a not in ("", [])},
            ))
        print(f"Saved '{title}' with {n_responses} responses.")


if __name__ == "__main__":
    main()
