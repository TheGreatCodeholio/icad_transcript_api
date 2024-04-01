
def associate_segments_with_src(segments, src_list):
    if not src_list:
        return [{
            "pos": 0,
            "src": 0,
            "tag": "Speaker"
        }]

    # Sort srcList by 'pos' to ensure it is in the correct order
    src_list_sorted = sorted(src_list, key=lambda x: x['pos'])

    for segment in segments:
        segment_start, segment_end = segment['start'], segment['end']
        src_for_segment = None

        # Initialize variables to find the closest src before segment start
        closest_src_before_segment_start = None
        min_diff = float('inf')

        for src in src_list_sorted:
            src_pos = src['pos']

            # Ensure the src starts before the segment ends
            if src_pos <= segment_end:
                diff = segment_start - src_pos

                # Check if this src is closer to the segment start than previous ones
                if 0 <= diff < min_diff:
                    closest_src_before_segment_start = src
                    min_diff = diff
            else:
                # Since src_list is sorted, break the loop once we pass segment_end
                break

        if closest_src_before_segment_start:
            # Assign the found src to the entire segment
            if closest_src_before_segment_start.get('tag') != '':
                src_for_segment = closest_src_before_segment_start.get("tag")
            else:
                src_for_segment = closest_src_before_segment_start['src'] if closest_src_before_segment_start['src'] != -1 else 0

        segment['unit_tag'] = src_for_segment

    return segments
