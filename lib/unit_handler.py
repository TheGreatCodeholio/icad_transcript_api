

def associate_segments_with_src(segments, src_list):
    if len(src_list) == 0:
        src_list = [{
                "pos": 0,
                "src": 0,
                "tag": "Speaker"
            }]

    # Sort srcList by 'pos' to ensure it is in the correct order
    src_list_sorted = sorted(src_list, key=lambda x: x['pos'])

    for segment in segments:
        # Find the src for the start of the segment
        segment_start = segment['start']
        src_for_segment = None

        for src in src_list_sorted:
            if segment_start >= src['pos']:
                if src.get('tag') != '':
                    src_for_segment = src.get("tag")
                else:
                    src_for_segment = src['src']
            else:
                break

        # Assign the found src to the entire segment
        segment['unit_tag'] = src_for_segment

    return segments