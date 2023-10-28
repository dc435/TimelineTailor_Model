# -----------------------------
# Main logic for event getter
# Calls SpaCy model and identifies all "DATE" entities in text
# Returns sorted event list
# -----------------------------

from shared_classes import ModelEvent
from logging import Logger
from spacy.language import Language
import spacy

def get_all_events(
        nlp: Language,
        original_text: str,
        max_context_chars: int,
        jobid: str,
        delimiter: str,
        log: Logger
    ) -> list[ModelEvent]:

    log.info("'event_builder' called. Loading Spacy. Job:" + jobid)

    from event_builder.text_preprocessing import get_text_list
    text_list = get_text_list(original_text=original_text,delimiter=delimiter)
    try:
        spacy.require_gpu()
    except:
        spacy.prefer_gpu()
    docs = list(nlp.pipe(text_list))

    from event_builder.event_getter import get_events
    all_events = []
    for doc in docs:
        date_entities = list(ent for ent in doc.ents if ent.label_=="DATE")
        all_events.extend(get_events(date_entities, max_context_chars=max_context_chars, jobid=jobid, delimiter=delimiter))
    all_events.sort(key=lambda e: e.ent_text)
    all_events.sort(key=lambda e: e.date_formatted)

    return all_events

