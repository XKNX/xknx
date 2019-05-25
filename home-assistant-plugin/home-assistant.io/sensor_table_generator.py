"""Generate a markdown table that can be copied to home-assistant.io sensor.knx documentation."""
try:
    from xknx.devices.remote_value_sensor import RemoteValueSensor
    from xknx.knx.dpt import DPTBase
except ModuleNotFoundError:
    exit("Add the `xknx` directory to pythons path via `export PYTHONPATH=$HOME/directory/to/xknx`")


class Row():
    """A row in the table. Table header text is defined in __init__ defaults."""
    column_width = {}

    def __init__(self,
                 value_type="type",
                 unit="unit",
                 dpt_number="KNX DPT",
                 dpt_size="size in byte",
                 dpt_range="range"):
        self.value_type = value_type
        self._update_column_width("value_type", value_type)
        self.unit = unit
        self._update_column_width("unit", unit)
        self.dpt_number = dpt_number
        self._update_column_width("dpt_number", dpt_number)
        self.dpt_size = dpt_size
        self._update_column_width("dpt_size", dpt_size)
        self.dpt_range = dpt_range
        self._update_column_width("dpt_range", dpt_range)

    def _update_column_width(self, index, text: str):
        try:
            Row.column_width[index] = max(Row.column_width[index], len(text))
        except KeyError:
            # index is not yet available
            Row.column_width[index] = len(text)

    def __repr__(self):
        def _format_column_ljust(content, index):
            return "| " + content.ljust(Row.column_width[index] + 1)

        return (_format_column_ljust(self.value_type, "value_type") +
                _format_column_ljust(self.unit, "unit") +
                _format_column_ljust(self.dpt_number, "dpt_number") +
                _format_column_ljust(self.dpt_size, "dpt_size") +
                # _format_column_ljust(self.dpt_range, "dpt_range") +
                "|")


class DPTRow(Row):
    """A row holding information for a DPT."""

    def __init__(self,
                 value_type: str,
                 dpt_class: DPTBase):
        dpt_range = ""
        if hasattr(dpt_class, "value_min") and hasattr(dpt_class, "value_max"):
            dpt_range = "%s ... %s" % (dpt_class.value_min, dpt_class.value_max)

        super().__init__(value_type=value_type,
                         unit=dpt_class.unit,
                         dpt_number=self._get_dpt_number_from_docstring(dpt_class),
                         dpt_size=str(dpt_class.payload_length),
                         dpt_range=dpt_range)

    def _get_dpt_number_from_docstring(self, dpt_class: DPTBase):
        """Extract dpt number from class docstring."""
        docstring = dpt_class.__doc__
        try:
            for line in docstring.splitlines():
                text = line.strip()
                if text.startswith("DPT"):
                    return text.split()[1]
        except IndexError:
            print("Error: Can't read docstring for: %s" % dpt_class)
        return None

    def dpt_number_int(self):
        """Return dpt number as integer (for sorting). "xxx" is treated as 0."""
        try:
            dpt_major, dpt_minor = self.dpt_number.split(".")
            if dpt_minor in ("x", "xxx", "*", "***"):
                dpt_minor = 0
            return (int(dpt_major) * 1000) + int(dpt_minor)
        except ValueError:
            print("Error: Can't parse dpt_number: %s" % self.dpt_number)


def table_delimiter():
    """Build a row of table delimiters."""
    def table_delimiter_ljust(width):
        return "|-" + "-" * width + "-"

    def table_delimiter_center(width):
        return "|:" + "-" * width + ":"

    def table_delimiter_rjust(width):
        return "|-" + "-" * width + ":"

    return (table_delimiter_ljust(Row.column_width["value_type"]) +
            table_delimiter_ljust(Row.column_width["unit"]) +
            table_delimiter_rjust(Row.column_width["dpt_number"]) +
            table_delimiter_rjust(Row.column_width["dpt_size"]) +
            # table_delimiter_center(Row.column_width["dpt_range"]) +
            "|")


def print_table():
    """Read the values and print the table to stdout."""
    rows = []
    for key, dpt in RemoteValueSensor.DPTMAP.items():
        rows.append(DPTRow(value_type=key, dpt_class=dpt))

    rows.sort(key=lambda row: row.dpt_number_int())

    table_header = Row()
    rows.insert(0, table_header)

    # Insert at last to have correct column_widths.
    rows.insert(1, table_delimiter())

    for row in rows:
        print(row)


if __name__ == "__main__":
    print_table()
