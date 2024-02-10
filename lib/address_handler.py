import re


def build_address_regex(include_intersections: bool = True):
    street_suffix = r"(Road|Street|Ave|Avenue|Boulevard|Drive|Lane|Terrace|Place|Court|Parkway|Circle|Trail|Way|Turnpike|Heights|Loop|Path|Trace|Crossing|Cove|Bend|Landing|Pass|Ridge)?"
    ordinal = r"(1st|2nd|3rd|[0-9]+th|[0-9]+)"
    spelled_out_ordinal = r"(First|Second|Third|[A-Z][a-z]*(th|st|nd|rd)|One Hundred and (First|Second|Third|[A-Z][a-z]*(th|st|nd|rd)))"
    street_name = rf"((?:[A-Z][a-z.-]+(?:\s|$))+|(?:{ordinal})|(?:{spelled_out_ordinal})|(?:Route|Highway|Interstate|I|State Route|State Road|County Route|SR) [0-9]+)"
    direction = r"(North|South|East|West)?"
    street_number = r"([0-9]+(?:-[0-9]+)*)"
    unit = r"(?:Apartment|Unit|Suite|Apartment Number)? ?(?:#? ?[0-9A-Z]+)?"
    intersection_phrases = r"(?:cross street of|cross streets|in the intersection near|at the intersection of|between|and)"
    intersection = rf"({street_name} {street_suffix}? {intersection_phrases} {street_name} {street_suffix}?)"
    address = rf"{street_number} {direction} ?{street_name} ?{street_suffix} ?{unit}"
    regex = rf"({intersection}|{address})" if include_intersections else rf"({address})"
    return regex


def extract_town(text):
    pattern = r'''
            \b
            (
                (?:[Tt]own\s[oO]f|[Vv]illage\s[oO]f|[Cc]ity\s[oO]f)\s([A-Z][A-Za-z\s-]+)|  # Town of/Village of/City of ... (name follows, capitalized)
                ([A-Z][A-Za-z\s-]+)(?:[Tt]ownship|[Bb]orough|[Bb]oro|[Cc]ity)  # ... Township/Borough/Boro/City (name precedes, capitalized)
            )
            |
            \b(?:in|near|outside of)\s([A-Z][A-Za-z\s-]+?)(?:,|\.|\b)  # Standalone town name in a specific context (e.g., "in Centerville", requires capitalization)
            \b
            '''
    matches = re.findall(pattern, text, re.VERBOSE)

    cleaned_towns = []
    for match in matches:
        for town in match:
            if town:  # Check if the capturing group captured anything
                town = re.sub(r'\s+', ' ', town.strip())  # Clean up the town name
                if town not in cleaned_towns:
                    cleaned_towns.append(town)
                break  # Break after the first non-empty match to avoid duplicates from the same tuple

    return cleaned_towns


def get_potential_addresses(transcript):
    transcript = transcript.replace(",", "").replace("  ", " ")
    address_regex = re.compile(build_address_regex())
    addresses = address_regex.findall(transcript)

    towns = extract_town(transcript)
    # Assuming extract_town returns a list of towns or an empty list if no towns are found

    valid_suffixes = {'Street', 'St', 'Road', 'Rd', 'Avenue', 'Ave', 'Boulevard', 'Blvd', 'Lane', 'Ln', 'Drive', 'Dr',
                      'Terrace', 'Place', 'Court', 'Parkway', 'Circle', 'Trail', 'Way', 'Turnpike', 'Heights', 'Loop',
                      'Path', 'Trace', 'Crossing', 'Cove', 'Bend', 'Landing', 'Pass', 'Ridge'}

    cleaned_addresses = []
    for address in addresses:
        address_text = address[0].strip().replace("-", "")
        if len(address_text) > 5 and (address_text.split()[-1] in valid_suffixes or address_text.split()[-1].isdigit()):
            full_address = address_text
            if towns:  # If a town is extracted, append it to the address
                full_address += f" in {towns[0]}"  # Assuming we take the first town if there are multiple
            cleaned_addresses.append(full_address)

    # If no addresses were found but a town was, add the town to the results
    if not cleaned_addresses and towns:
        cleaned_addresses.append(towns[0])

    # Remove duplicates by converting the list to a set, then back to a list
    unique_addresses = list(set(cleaned_addresses))

    return unique_addresses
