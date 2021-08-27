from typing import Counter, cast

from fastapi.exceptions import HTTPException
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


def get_submissions(poll_id: str, app_key: str) -> list[dict]:
    """
    Get all of the submissions of a poll with a given app key.
    
    :param poll_id: Form ID of the JotForm form.
    :param app_key: Unique identifier of the user/app pair.
    :return A list of submissions. 
    :raise HTTPException if the poll is not found.
    """
    submissions = []
    offset = 0
    while True: # Until the content returns empty
        reply = get(f"https://api.jotform.com/form/" # Generate URL
                + f"{poll_id}/submissions" # And fetch a batch of submissions.
                + f"?apiKey={app_key}"
                + "&limit=1000"  # Each batch is at max 1000 long.
                + f"&offset={offset}"  # Offset is from the last batch.
                + '&filter={"status:ne":"DELETED"}')  # And ignored deleted, of course.
        try:
            json = reply.json()
        except:
            raise HTTPException(404, "Poll not found.")
        fetched_submissions: list[dict] = json.get("content")  # Get the new submissions.
        submissions.extend(fetched_submissions)  # Add them to main submissions.
        if len(fetched_submissions) < 1000:  # If less than limit was fetched
            break  # This was the last batch, so break.
        offset += 1000  # Otherwise get ready to fetch the next batch.
    return submissions  # Finally, return all of the submissions.