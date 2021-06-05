# A file for querying various statistics
from app.models import SeekerProfile, LocationCoordinates, CompanyProfile, JobPost


def get_coordinate_info(table, describe=False, merge=False):
    """
    Gets the coordinates from the locations of each entry in the given table.
    If `describe` is true, will also append the location name.
    If `merge` is true, will combine entries of the location and append the count.
    """
    entries = table.query.all()
    counts = dict()
    # first get all info - coordinates, names, and counts
    for entry in entries:
        try:
            lat, lng = LocationCoordinates.get(entry.city, entry.state, False)
            name = f"{entry.city}, {entry.state}"
            # could not find one or the other; just replace with unknown for city and 'USA' for state
            if name.startswith("None"):
                name = name.replace("None", "Unknown", 1)
            if "None" in name:  # state is unknown
                name = name.replace("None", "USA")

        except ValueError:
            try:
                lat, lng = LocationCoordinates.get(state=entry.state, fallback=False)
                name = entry.state
            except ValueError:
                lat, lng = LocationCoordinates.get(None, None, True)
                name = "Unknown"
        key = (lat, lng, name)
        counts[key] = counts.setdefault(key, 0) + 1

    # then extract content based on arguments
    if merge:
        # append count to the tuple, slicing to remove the name if it's not wanted
        return [(*k, v) if True else (*k[:-1], v) for k, v in counts.items()]
    # get and unpack the duplicated entries (repeated v times)
    # slice tuple if not wanting the location description
    i = 3 if describe else 2
    return [x for y in [[k[:i] for _ in range(v)] for k, v in counts.items()] for x in y]

