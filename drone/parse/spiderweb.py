from math import pi, degrees, radians, cos, sin
from re import compile
from os import path, listdir
from collections import namedtuple


REGEX_MATCH_NAME = compile("(N|NE|E|SE|S|SW|W|NW|C)([0-9]+)_([0-9]+)(_([0-9]+))?.txt$")

direction_to_deg = dict(N=90, NE=45, E=0, SE=-45, S=-90, SW=-135, W=180, NW=135)
direction_to_rad = {d: radians(a) for d, a in direction_to_deg.items()}


Event = namedtuple("Event", "fields spectrum")


def parse_files(directory):
    for filename in listdir(directory):
        result = REGEX_MATCH_NAME.match(filename)

        if result is None:
            continue

        groups = result.groups()

        if len(groups) == 5:
            direction, height_str, length_str, _, filenumber_str = groups
            length = int(length_str) * 1e-2
            fields = dict(length=length)

        # C FILES
        else:
            assert len(groups) == 3
            direction, height_str, filenumber_str = groups
            fields = dict()

        fields['direction'] = direction
        fields['height'] = int(height_str) * 1e-2

        with open(path.join(directory, filename)) as f:
            spectrum = [int(x) for x in f]

        yield Event(fields, spectrum)