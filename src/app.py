from potassium import Potassium, Request, Response

app = Potassium("my_app")

# @app.init runs at startup, and loads models into the app's context
@app.init
def init():

    DELIMITER = "|"
    MAX_T5_TOKENS = 512

    import platform
    if platform.system() == "Windows":
        T5_MODEL_PATH_EXT = "./model/best" # (FOR LOCAL WINDOWS TESTING)
    if platform.system() == "Linux":
        T5_MODEL_PATH_EXT = "../app/model" # (FOR DEPLOYMENT)

    # Initialise log:
    global log
    import logging
    log = logging.getLogger("app.py")
    log.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.DEBUG)
    c_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s:   %(message)s'))
    log.addHandler(c_handler)

    # 1. Initialize SpaCy model:

    log.info("Initializing Spacy language model.")

    # global nlp
    # global delimiter

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        import spacy

    try:
        spacy.require_gpu()
        log.info("Spacy nlp successfully using GPU.")
    except:
        spacy.prefer_gpu()
        log.warning("Could not require spacy GPU.")
    nlp = spacy.load("en_core_web_trf")
    # Add custom sentence segment pipeline:
    delimiter = DELIMITER
    from spacy.language import Language
    @Language.component("custom_sentencizer")
    def custom_sentencizer(doc):
        for i, token in enumerate(doc[:-2]):
            if token.text == DELIMITER:
                doc[i + 1].is_sent_start = True
        return doc
    nlp.add_pipe("custom_sentencizer", before="parser")
    nlp.add_pipe("merge_entities")

    #  2. Initialise t5 model:

    log.info("Initializing t5 model.")

    # global model
    # global tokenizer
    # global device
    # global max_t5_tokens

    import torch
    device = "cuda:0"
    if torch.cuda.is_available():
        device = "cuda:0"
        log.info("t5 model successfull using GPU. 'device'=" + device)
    else:
        device = "cpu"
        log.warning("Torch unable to use GPU. 'device'=" + device)
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    max_t5_tokens = MAX_T5_TOKENS

    tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=T5_MODEL_PATH_EXT, local_files_only=True, padding=True, truncation=True, model_max_length=max_t5_tokens)
    model = AutoModelForSeq2SeqLM.from_pretrained(pretrained_model_name_or_path=T5_MODEL_PATH_EXT, local_files_only=True).to(device)

    log.info("App init() complete.")

    context = {
        "log": log,
        "model": model,
        "tokenizer": tokenizer,
        "delimiter": DELIMITER,
        "nlp": nlp,
        "device": device,
        "max_t5_tokens":MAX_T5_TOKENS
    }

    return context

# @app.handler runs for every call
@app.handler("/")
def handler(context: dict, request: Request) -> Response:


    model_inputs = request.json

    from shared_classes import NewJob, ModelOutput, ModelEvent
    import warnings

    # global log
    # global nlp
    # global delimiter
    # global model
    # global tokenizer
    # global device
    # global max_t5_tokens

    log = context.get("log")
    model = context.get("model")
    tokenizer = context.get("tokenizer")
    delimiter = context.get("delimiter")
    nlp = context.get("nlp")
    device = context.get("device")
    max_t5_tokens = context.get("max_t5_tokens")

    MAX_CONTEXT_CHARS = 1350

    modelOutput = ModelOutput(
        success = False,
        message = "Default Message.",
        events = [ModelEvent()]
    )

    try:
        newjob = NewJob(**model_inputs)
    except:
        print("error")
        log.error("Could not parse model_inputs.")
        modelOutput.message = "Could not parse model_inputs."
        return Response(
            json = modelOutput.dict(),
            status=400
        )

    log.info("New Job request received. Job:" + newjob.jobid)

    try:

        # 1. identify date entities in text, and return as list of 'event' objects:
        from event_builder.event_builder import get_all_events
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            events = get_all_events(
                nlp,
                newjob.original_text,
                max_context_chars=MAX_CONTEXT_CHARS,
                jobid=newjob.jobid,
                delimiter=delimiter,
                log=log
            )

        # 2. Process each event to generate brief description of what occured on the given event date:
        from event_processor.event_processor import add_descriptions
        events = add_descriptions(
            model,
            tokenizer,
            device,
            events,
            max_t5_tokens = max_t5_tokens,
            log=log,
            jobid=newjob.jobid
        )

        modelOutput.events = events
        modelOutput.message = "Successfully processed new job."
        modelOutput.success = True
        log.info("Model processing done. Returning " + str(len(modelOutput.events)) + " events.")

    except Exception:

        log.error("Could not process events. Job:" + newjob.jobid)
        log.exception("Could not process events")

    finally:

        return Response(
            json = modelOutput.dict(),
            status=200
        )

        # return modelOutput.json()

if __name__ == "__main__":
    app.serve()