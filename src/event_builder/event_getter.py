# ----------------------------
# Takes the list of date entities in, returns a list of event objects
# Each event object is built from the date text, neighbouring (context) text, a parsed date and other attributes
# ----------------------------


from spacy.tokens import Span
from shared_classes import ModelEvent, DateFormat
from datetime import date
import dateutil.parser as date_parser
from dateutil.parser import ParserError
import re

class Context:
    left: str    
    right: str

class ParsedDate:

    success: bool
    formatted: date 
    format: DateFormat
    
    def __init__(self, success=False, formatted=date.today(), format=DateFormat.UNKNOWN):
        self.success=success
        self.formatted=formatted
        self.format=format

# Main method for event getting
def get_events(
        date_entities: list[Span],
        max_context_chars: int,
        jobid: str,
        delimiter: str
    ) -> list[ModelEvent]:
    
    events = []
    from event_builder.pattern_list import get_patterns
    patterns = get_patterns()

    for ent in date_entities:
        
        e = ModelEvent()
        e.jobid = jobid
        e.ent_text = ent.text
        e.delimiter = delimiter

        pd = get_parsed_date(ent.text,patterns)
        e.date_success = pd.success
        e.date_formatted = pd.formatted
        e.date_format = pd.format

        context = get_context(ent, max_context_chars)
        e.context_left = context.left
        e.context_right = context.right
        
        e.description = ""

        events.append(e)
     
    return events


# Returns parsed date in python date format, from plain date text:
# See DateEntityParser for stand-alone repo: https://github.com/dc435/DateEntityParser
def get_parsed_date(source_text, patterns):
    
    clean_text= get_clean_text(source_text)
    default_date=date(9999,12,31)
    format=DateFormat.UNKNOWN

    pd = ParsedDate(formatted=default_date)

    has_year = re.search(r"\d{4}", source_text)
    if not has_year:
        return pd

    from pyparsing import ParseException

    for p in patterns:
        try:
            result = p.pattern.parseString(clean_text)
            day_txt = result["day"] if "day" in result.keys() else ""
            month_txt = result["month"] if "month" in result.keys() else ""
            year_txt = result["year"] if "year" in result.keys() else "" 
            clean_text = f"{day_txt} {month_txt} {year_txt}".strip()
            default_date = p.default_date
            format = p.format
            break
        except ParseException:
            pass

    try:
        pd.formatted = date_parser.parse(clean_text, default=default_date, dayfirst=True)
        pd.success = True
        pd.format = DateFormat.Y if format == DateFormat.UNKNOWN else format
    except (ParserError, TypeError):
        pd.formatted = default_date
        pd.success = False
        pd.format = DateFormat.UNKNOWN

    return pd

# Helper function for date parsing
def get_clean_text(source_text):

    clean_text = source_text
    clean_text = clean_text.replace("."," ")
    clean_text = clean_text.replace("["," ")
    clean_text = clean_text.replace("]"," ")
    clean_text = clean_text.strip()

    return clean_text

# Returns left and right context text from span in which date entity exists:
def get_context(ent, max_context_chars):

    ent_text = ent.text
    left_text = ent.doc[ent.sent.start:ent.start].text
    right_text = ent.doc[ent.end:ent.sent.end].text
    full_text = left_text + " " + ent_text + " " + right_text
    start = ent.sent.start
    end = ent.sent.end
    go_left = True
    go_right = True

    while go_left or go_right:

        if go_left:
            if start != 0:
                next_sent = ent.doc[start - 1].sent
                if (len(next_sent.text) + len(full_text) < max_context_chars):
                    left_text = next_sent.text + " " + left_text
                    start = next_sent.start
                    full_text = left_text + " " + ent_text + " " + right_text
                else:
                    go_left = False
            else:
                go_left = False

        if go_right:
            if end < len(ent.doc) - 1:
                next_sent = ent.doc[end + 1].sent
                if (len(next_sent.text) + len(full_text) < max_context_chars):
                    right_text = right_text + " " + next_sent.text
                    end = next_sent.end
                    full_text = left_text + " " + ent_text + " " + right_text
                else:
                    go_right = False
            else:
                go_right = False     

    context = Context()
    context.left = left_text
    context.right = right_text

    return context
