from typing import Counter, cast
from .api_constants import base_url
from requests import get
from pprint import pprint

def get_question_ids(app_key: str, poll_id: str) -> list[str]:
    """
    Return a list of filtered question ids, they are
        filtered according to whether or not they
        can be used in statistical calculations.
    """
    questions_resp = get(f"{base_url}/form/{poll_id}/questions",
                         params={"apiKey": app_key})
    if isinstance(resp := questions_resp.json(), dict):
        resp = cast(dict, resp)
        # After we get the questions, exract content.
        questions: dict[str, dict[str, int]] = resp.get("content", {})
        # And then filter the question IDs.
        return [qid for qid in questions if questions[qid].get("type", "") in 
                                            ("control_radio", "control_checkbox")]
    else:
        return []


def get_answer_stats(submissions: list[dict], question_ids: list[str]) -> dict[str, dict[str, int]]:
    """
    Given a list of submissions and a list of valid
        question IDs, return the total number of
        each answers given in every submission
        tot each question.
    """
    question_answers: dict[str, list[str]] = dict.fromkeys(question_ids)  # This will hold our answers.
    for qid in question_answers:  # We cannot populate the list in fromkeys
        question_answers[qid] = []  # Since that results in all arrays being the same array.
    for submission in submissions:
        answers = submission.get("answers", {})
        # Filter answers to only the filtered Qids.
        filtered_answers = [(qid, answers.get(qid, None)) for qid in question_ids]
        for qid, answer in filtered_answers:
            if answer is None:
                continue # Filter out Nones.
            if answer.get("type") == "control_radio":
                # Since radio has single text.
                question_answers[qid].append(answer.get("prettyFormat")) 
            else:
                # Since checkbox has a list.
                question_answers[qid].extend(answer.get("answer", []))  
    # Now count each of the answers and return the tally.
    return {qid : Counter(answer for answer in question_answers[qid] if answer != None) for qid in question_answers}