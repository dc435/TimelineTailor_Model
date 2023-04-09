# TimelineTailor_Model

This is the backend model repo for Timeline Tailor. The front end and main logic can be found at https://github.com/dc435/TimelineTailor.

The code on this repo is deployed on a serverless GPU with Banana Dev (https://www.banana.dev/) and called via API from TimelineTailor.

## How does it work?

The model API receives a block of raw text, originally provided by the user through the web interface. A job number has already been assigned for reference.

The model processes the text through a pipeline in two stages, as follows.

## Stage 1: SpaCy NER and date string parsing

The first stage uses a SpaCy transformer and Named Entity Recognition to identify all date entities in the text (see https://spacy.io/usage/embeddings-transformers).

For each date entity, a python 'Event' object is created. Various processing of the event object and its surrounding context text assigns values to the Event variables.

A list of 'Event' objects is returned from this first pipeline stage.

## Stage 2: T5 Transformer

The list of Event objects is sent to the T5 transformer. This is a sequence to sequence model (https://huggingface.co/docs/transformers/model_doc/t5).

It takes as input the left-context and right-context text surrounding the date entity and returns a concise description of the event being described.

The T5 model has been fine-tuned by me using a custom-built training set. The description output is added to the event object variable.


## Example:


### Original Text (with \*\*target date\*\* in asterixed):


    Roosevelt instructed the WSA to negotiate a cut in the UK Import Program for December 1944, January 1945 and February 1945 with the British, asked the Office of War Mobilization and Reconversion to investigate the labor situation at the shipyards, and told the JCS to get the theaters to break up the pools of idle shipping and improve turnaround times.[49]
    COMZ managed to unload 115 ships in November. The port commanders improved the discharge rate from 327 long tons (332 t) per ship per day in October to 457 long tons (464 t) per ship per day in   **November 1944**   by offering incentives such as extra leave to their best performing hatch crews.[50] On 6 December, the JCS prohibited selective unloading and directed that shipping requirements be modified to match actual discharge capacities. Each theater was ordered to establish a shipping control agency that would ensure compliance with these directives.[49] In the ETO, the shipping control agency consisted of the Chief of Staff of COMZ, Major General Royal B. Lord; his Assistant Chief of Staff (G-4) at COMZ, Brigadier General James H. Stratton; and Franklin.[41] Somervell ordered 25 of the 35 Liberty ships that had been engaged in the cross-Channel service and ships that had been sitting idle with non-urgent supplies after being partially unloaded to return to the United States.

### Event object:


    'jobid': 'qwertyuiop1234567890asdfghjkl', 

    'ent_text': 'November 1944', 

    'description': 'The port commanders improved the discharge rate from 327 long tons (332 t) per ship per day to 457 long tons (464 t) per ship per day by offering incentives such as extra leave to their best performing hatch crews', 

    'date_success': False, 

    'date_formatted': '1944-11-01', 

    'date_format': 1, 

    'context_left': 'Roosevelt instructed the WSA to negotiate a cut in the UK Import Program for December 1944, January 1945 and February 1945 with the British, asked the Office of War Mobilization and Reconversion to investigate the labor situation at the shipyards, and told the JCS to get the theaters to break up the pools of idle shipping and improve turnaround times.[49] |   | COMZ managed to unload 115 ships in November. The port commanders improved the discharge rate from 327 long tons (332 t) per ship per day in October to 457 long tons (464 t) per ship per day in', 

    'context_right': 'by offering incentives such as extra leave to their best performing hatch crews.[50] On 6 December, the JCS prohibited selective unloading and directed that shipping requirements be modified to match actual discharge capacities. Each theater was ordered to establish a shipping control agency that would ensure compliance with these directives.[49] In the ETO, the shipping control agency consisted of the Chief of Staff of COMZ, Major General Royal B. Lord; his Assistant Chief of Staff (G-4) at COMZ, Brigadier General James H. Stratton; and Franklin.[41] Somervell ordered 25 of the 35 Liberty ships that had been engaged in the cross-Channel service and ships that had been sitting idle with non-urgent supplies after being partially unloaded to return to the United States.', 

    'delimiter': '|'



## Return object

The list of events is then converted to a json object and returned via the Banana interface.

