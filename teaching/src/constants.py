"""Settings and component ids shared by the layout and the callbacks."""

PORT = 8052
N_QUESTION_ROWS = 5  # number of question rows in the Survey Maker

# Tabs
MAIN_TABS = "main-tabs"

# Survey Maker
MAKER_TITLE = "maker-title"
MAKER_DESCRIPTION = "maker-description"
MAKER_SAVE = "maker-save"
MAKER_STATUS = "maker-status"
# Each question row's fields have ids like {"type": MAKER_Q_TEXT, "row": 2}
MAKER_Q_TYPE = "maker-q-type"
MAKER_Q_TEXT = "maker-q-text"
MAKER_Q_OPTIONS = "maker-q-options"

# Survey Taker
TAKER_SURVEY_SELECT = "taker-survey-select"
TAKER_FORM = "taker-form"

# Survey Analyzer
ANALYZER_SURVEY_SELECT = "analyzer-survey-select"
ANALYZER_RESULTS = "analyzer-results"
TAKER_RESPONDENT_ID = "taker-respondent-id"
TAKER_SUBMIT = "taker-submit"
TAKER_STATUS = "taker-status"
ANSWER = "answer"  # each answer input's id is {"type": ANSWER, "qid": <question id>}
