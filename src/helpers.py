'''Helper functions for the survey app.'''

import src.constants as cn
from src.storage import (  # type: ignore
    save_survey, load_survey, list_surveys, save_response, load_responses, delete_survey,
    delete_response, save_draft, load_draft, list_drafts, delete_draft,
)

#A2#def get_draft_info() -> tuple[str, int, int]:   #2#
#A2#    """   #2#
#A2#    Get information about the current draft.   #2#
#A2#       #2#
#A2#    Returns:   #2#
#A2#        A tuple containing the   #2#
#A2#            survey title   #2#
#A2#            number of questions   #2#
#A2#            number of responses   #2#
#A2#    """   #2#
#A2#    # Get the survey ids   #2#
#A2#    survey_title = ""   #2#
#A2#    num_question = 0   #2#
#A2#    num_completed = 0   #2#
#A2#    for survey_info in list_surveys():   #2#
#A2#        survey_id = survey_info[cn.L_ID]   #2#
#A2#        drafts = list_drafts(survey_id)   #2#
#A2#        if len(drafts) == 0:   #2#
#A2#            continue   #2#
#A2#        survey_title = survey_info[cn.L_TITLE]   #2#
#A2#        draft = drafts[0]  # Assuming only one draft per survey   #2#
#A2#        import pdb; pdb.set_trace()  # Debugging breakpoint   #2#
#A2#        num_question = draft['total_questions']   #2#
#A2#        num_completed = draft['questions_completed' ]   #2#
#A2#        break   #2#
#A2#    return survey_title, num_question, num_completed   #2#