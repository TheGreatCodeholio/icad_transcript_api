import csv
import logging
import os
import re

module_logger = logging.getLogger('icad_transcribe.replacement')


def transcript_replacement(transcript_dict, replacements_file_path):
    if not os.path.exists(replacements_file_path):
        module_logger.warning(f"Replacement file does not exist: {replacements_file_path}")
        return transcript_dict

    try:
        with open(replacements_file_path, "r") as rf:
            csv_reader = csv.DictReader(rf)
            replace_data = [row for row in csv_reader]

            if not replace_data:
                module_logger.warning("Replacement data is empty.")
                return transcript_dict

    except Exception as e:
        module_logger.warning(f"Failed to read or process replacements file: {e}")
        return transcript_dict

    def replace_func(match):
        word = match.group(0)
        for replacement in replace_data:
            if word.lower() == replacement.get("Word", "").lower():
                return replacement.get("Replacement", word)
        return word

    try:
        pattern = '|'.join(
            re.escape(replacement.get("Word")) for replacement in replace_data if replacement.get("Word"))

        # Replace in the main transcript text
        if 'transcript' in transcript_dict:
            transcript_dict['transcript'] = re.sub(pattern, replace_func, transcript_dict['transcript'], flags=re.IGNORECASE)

        # Replace in each segment text
        if 'segments' in transcript_dict:
            for segment in transcript_dict['segments']:
                segment['text'] = re.sub(pattern, replace_func, segment['text'], flags=re.IGNORECASE)

    except re.error as e:
        module_logger.warning(f"Regex error: {e}")
        return transcript_dict

    return transcript_dict
