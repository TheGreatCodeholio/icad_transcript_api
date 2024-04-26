
def associate_segments_with_src(segments, src_list):
    if not src_list:
        # If there is no src_list provided, return segments with default src
        return [{
            "pos": 0,
            "src": 0,
            "tag": "Speaker"
        }]

    # Sort srcList by 'pos' to ensure it is in the correct order
    src_list_sorted = sorted(src_list, key=lambda x: x['pos'])

    # Append a large number to handle segments beyond the last src position
    src_list_sorted.append({'pos': float('inf'), 'src': -1, 'tag': ''})

    src_index = 0

    for segment in segments:
        segment_start, segment_end = segment['start'], segment['end']
        src_for_segment = None

        # Move the src_index to the correct src covering the segment_start
        while src_index < len(src_list_sorted) - 1 and src_list_sorted[src_index + 1]['pos'] <= segment_start:
            src_index += 1

        # Check the current src covers the segment
        if src_list_sorted[src_index]['pos'] <= segment_end:
            current_src = src_list_sorted[src_index]
            if current_src.get('tag'):
                src_for_segment = current_src['tag']
            else:
                src_for_segment = current_src['src'] if current_src['src'] != -1 else 0
        else:
            # If no valid src is found, you might set a default or handle it accordingly
            src_for_segment = 0

        segment['unit_tag'] = src_for_segment

    return segments
