# ------------------------------------
# Logic for running t5 transformer model to generate description summary
# ------------------------------------


from shared_classes import ModelEvent
from logging import Logger
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer


# Main method:
def add_descriptions(
        model: AutoModelForSeq2SeqLM,
        tokenizer: AutoTokenizer,
        device: str,
        events: list[ModelEvent], 
        max_t5_tokens: int,
        log: Logger,
        jobid: str
    ) -> list[ModelEvent]:

    log.info("'event_processor' called, on " + str(len(events)) + " events. Loading torch. Job:" + jobid)

    total_size = len(events) - 1
    batch_size = 128
    MIN_BATCH_SIZE = 8

    try:

        batch_process(model, tokenizer, events, batch_size, total_size, max_t5_tokens, device, log)

    except RuntimeError as e:

        if str(e).startswith('CUDA out of memory.'):

            log.info('CUDA Memory error using batch size ' + str(batch_size))
            batch_size = MIN_BATCH_SIZE
            import gc, torch
            gc.collect()
            torch.cuda.empty_cache()
            log.info('start again with reduced batch size: ' + str(batch_size))
            batch_process(model, tokenizer, events, batch_size, total_size, max_t5_tokens, device, log)

        else:

            raise e

    return events

# Get input text for generator model:
def get_input_text(left, right):

    placeholder = "^^DATE^^"
    question = "What happened on " + placeholder + "?"
    context = left + " " + placeholder + " " + right
    input_text = "question: {question} context: {context}".format(question = question, context = context)

    return input_text

# Split into batches:
def batch_process(model, tokenizer, events, batch_size, total_size, max_t5_tokens, device, log):

    start = 0
    end = min(batch_size - 1, total_size)

    log.info("start generation loops, batch size:" + str(batch_size))
    loop = 0

    while start < total_size:

        loop += 1

        input_texts = []
        for e in events[start:end + 1]:
            input_text = get_input_text(e.context_left, e.context_right)
            input_texts.append(input_text)

        input_texts_tokenized = tokenizer(input_texts, padding=True, truncation=True, max_length=max_t5_tokens, return_tensors="pt").to(device).input_ids
        outputs_tokenized = model.generate(input_texts_tokenized, max_length=max_t5_tokens)
        decoded_outputs = tokenizer.batch_decode(outputs_tokenized, skip_special_tokens=True)                                                                       

        for i, do in enumerate(decoded_outputs):
            description = do[:1].upper() + do[1:]
            events[start + i].description = description

        start = end + 1
        end = min(end + batch_size, total_size)

