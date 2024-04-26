def get_closest_src(src_list, segment):
    def closest_source(src):
        return abs(src['pos'] - segment['start'])

    closest_src = min(src_list, key=closest_source)
    return closest_src


def associate_segments_with_src(segments, src_list):

    for segment in segments:
        # Finding the closest source based on the segment start time
        closest_src = get_closest_src(src_list, segment)

        # Applying the rules for unit_tag
        if closest_src['src'] != -1:
            if closest_src['tag']:
                segment['unit_tag'] = closest_src['tag']
            else:
                segment['unit_tag'] = closest_src['src']
        else:
            segment['unit_tag'] = 0

    return segments
