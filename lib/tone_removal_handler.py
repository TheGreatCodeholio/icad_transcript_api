from icad_tone_detection import tone_detect
from pydub import AudioSegment

def apply_agc_with_silence_detection(audio_segment, target_peak=-1.0, silence_threshold=-45.0):
    """
    Apply Automatic Gain Control (AGC) to an audio segment to normalize its volume, while ignoring silent sections.

    :param audio_segment: The audio segment to process.
    :param target_peak: The target peak in dBFS that we want to amplify up to but not exceed.
    :param silence_threshold: The dBFS value below which a segment is considered silent.
    :return: The processed AudioSegment with AGC applied selectively, ignoring silent segments.
    """
    segments = split_audio(audio_segment, chunk_length=1000)  # Split into chunks, e.g., every 1000ms.
    processed_segments = []

    for segment in segments:
        segment_peak_dBFS = segment.dBFS  # Get the current peak amplitude of the segment in dBFS.

        # Determine if the segment is silent.
        is_silent = segment_peak_dBFS < silence_threshold

        if not is_silent:
            gain_needed = target_peak - segment_peak_dBFS  # Calculate how much gain is needed.

            # Only apply gain if it's positive, indicating the segment is quieter than the target peak.
            if gain_needed > 0:
                amplified_segment = segment.apply_gain(gain_needed)
                processed_segments.append(amplified_segment)
            else:
                processed_segments.append(segment)
        else:
            # For silent segments, append them unmodified.
            processed_segments.append(segment)

    # Concatenate all the processed segments back together.
    processed_audio = sum(processed_segments[1:], processed_segments[0])

    return processed_audio


def split_audio(audio_segment, chunk_length=1000):
    """
    Splits an audio segment into chunks of a specified length.

    :param audio_segment: The AudioSegment to split.
    :param chunk_length: The length of each chunk in milliseconds.
    :return: A list of AudioSegment objects.
    """
    return [audio_segment[i:i + chunk_length] for i in range(0, len(audio_segment), chunk_length)]

def detect_tones_in_audio(audio_segment):
    try:
        tone_detect_result = tone_detect(audio_segment)
        detected_tones = {
            "two_tone": tone_detect_result.two_tone_result,
            "long_tone": tone_detect_result.long_result,
            "warble_tone": tone_detect_result.hi_low_result
        }
        return detected_tones
    except Exception as e:
        print(f"Failed To Detect Tones: {e}")
        return None


def cut_tones_from_audio(detected_tones, audio_segment, pre_cut_length=0.5, post_cut_length=0.5):
    try:
        # Initialize a new, empty audio segment to build the processed audio
        processed_audio = AudioSegment.empty()

        # Gather all tone information in one list and sort them by their start time
        all_tones = sorted(
            detected_tones.get('two_tone', []) +
            detected_tones.get('warble_tone', []) +
            detected_tones.get('long_tone', []),
            key=lambda x: x['start']
        )

        last_end_ms = 0
        audio_length_ms = len(audio_segment)

        for tone in all_tones:
            # Adjust the start and end times with pre_cut_length and post_cut_length, ensuring they stay within the audio bounds
            start_ms = max(0, int(tone['start'] * 1000) - int(pre_cut_length * 1000))
            end_ms = min(audio_length_ms, int(tone['end'] * 1000) + int(post_cut_length * 1000))

            # Add the audio segment before the tone to the processed audio
            processed_audio += audio_segment[last_end_ms:start_ms]

            # Create a silent audio segment for the duration of the tone and add it
            silence_duration = max(0, end_ms - start_ms)  # Ensure non-negative duration
            silence = AudioSegment.silent(duration=silence_duration)
            processed_audio += silence

            # Update the last_end_ms to the end of the current tone
            last_end_ms = end_ms

        # After processing all tones, add the remaining audio segment
        processed_audio += audio_segment[last_end_ms:]

        # Ensure the processed audio is the same length as the input audio
        if len(processed_audio) > audio_length_ms:
            processed_audio = processed_audio[:audio_length_ms]
        elif len(processed_audio) < audio_length_ms:
            silence_padding = AudioSegment.silent(duration=audio_length_ms - len(processed_audio))
            processed_audio += silence_padding



        return processed_audio

    except Exception as e:
        print(f"An error occurred while processing the audio: {e}")
        return None