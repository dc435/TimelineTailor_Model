# Split large text block into list of smaller text strings for batch processing:

def get_text_list(original_text, delimiter, max_txt_block_chars=10000):
    
    all_lines = original_text.splitlines()
    delim_string = " " + delimiter + " "
    text_list = []
    line = ""
    for l in all_lines:
        l += delim_string
        if len(line) + len(l) < max_txt_block_chars:
            line += l
        else:
            text_list.append(line)
            line = l
    text_list.append(line)
    
    return text_list