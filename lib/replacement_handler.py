import csv
import logging
import os
import re

module_logger = logging.getLogger('icad_transcribe.replacement')


def transcript_replacement(transcript, replacements_file_path="/app/etc/transcribe_replacements.csv"):
    if not os.path.exists(replacements_file_path):
        module_logger.warning(f"Replacement file does not exist: {replacements_file_path}")
        return transcript

    try:
        with open(replacements_file_path, "r") as rf:
            csv_reader = csv.DictReader(rf)
            replace_data = [row for row in csv_reader]

            if not replace_data:
                module_logger.warning("Replacement data is empty.")
                return transcript

    except Exception as e:
        module_logger.warning(f"Failed to read or process replacements file: {e}")
        return transcript

    def replace_func(match):
        word = match.group(0)
        for replacement in replace_data:
            if word.lower() == replacement.get("Word", "").lower():
                return replacement.get("Replacement", word)
        return word

    try:
        pattern = '|'.join(
            re.escape(replacement.get("Word")) for replacement in replace_data if replacement.get("Word"))

        transcript = re.sub(pattern, replace_func, transcript, flags=re.IGNORECASE)
    except re.error as e:
        module_logger.warning(f"Regex error: {e}")
        return transcript

    return transcript
