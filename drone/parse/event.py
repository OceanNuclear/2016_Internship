from glob import iglob
from numpy import empty
from itertools import islice


class Event:
    SPECTRUM_LENGTH = 4096

    def __init__(self, field_data, spectrum):
        self.fields = field_data
        self.spectrum = spectrum


def format_value_with_error(string):
    value_str, err_str = string.split("+-")
    return {'value': float(value_str), 'error': float(err_str)}



# LatLong has uncertainty in meters, value in degrees
FORMATTERS = {'latitude': format_value_with_error,
              'longitude': format_value_with_error,
              'altitude': format_value_with_error,
              'gps_timestamp': format_value_with_error,
              'speed': format_value_with_error,
              'climb': format_value_with_error,
              'prog_timestamp': float,
              'real_time': float,
              'live_time': float,
              'sleep_time': float}


FIELD_KEYS = set(FORMATTERS)


def parse_pattern(pattern):
    return parse_files(iglob(pattern))


def parse_files(filenames):
    for path in filenames:
        with open(path) as f:
            lines = f.readlines()

        spectrum = empty(Event.SPECTRUM_LENGTH)
        field_data = {}

        # Scrape meta info
        for i_line, line in enumerate(lines):
            stripped = line.rstrip()

            if not stripped.startswith("#"):
                break

            name, value_raw = stripped[1:].split("=")

            # Parse meta data_array
            try:
                formatter = FORMATTERS[name]
            except KeyError:
                print("Invalid field '{}'".format(name))
                continue

            field_data[name] = formatter(value_raw)

        else:
            i_line = 0

            # Set element in spectrum array
        for i_spec, line in enumerate(islice(lines, i_line, None)):
            stripped = line.rstrip()
            spectrum[i_spec] = int(stripped)

        # Create Event
        yield Event(field_data, spectrum)
