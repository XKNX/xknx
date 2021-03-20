"""Generate a markdown table that can be copied to home-assistant.io sensor.knx documentation."""
try:
    from xknx.dpt import DPTBase
except ModuleNotFoundError:
    exit(
        "Add the `xknx` directory to pythons path via `export PYTHONPATH=$HOME/directory/to/xknx`"
    )


# Defines the column order of the printed table.
# ["dpt_number", "value_type", "dpt_size", "unit", "dpt_range"]
COLUMN_ORDER = ["dpt_number", "value_type", "dpt_size", "dpt_range", "unit"]

# Defines the column adjustment of the printed table.
# "left", "right" or "center"
COLUMN_ADJUSTMENT = {
    "value_type": "left",
    "unit": "left",
    "dpt_number": "right",
    "dpt_size": "right",
    "dpt_range": "center",
}


class Row:
    """A row in the table. Table header text is defined in __init__ defaults."""

    column_width = {}

    def __init__(
        self,
        value_type="type",
        unit="unit",
        dpt_number="KNX DPT",
        dpt_size="size in byte",
        dpt_range="range",
    ):
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
        def _format_column_ljust(index):
            content = getattr(self, index)
            return "| " + content.ljust(Row.column_width[index] + 1)

        _row = ""
        for column in COLUMN_ORDER:
            _row += _format_column_ljust(column)
        _row += "|"
        return _row


class DPTRow(Row):
    """A row holding information for a DPT."""

    def __init__(self, dpt_class: DPTBase):
        dpt_range = ""
        if hasattr(dpt_class, "value_min") and hasattr(dpt_class, "value_max"):
            dpt_range = f"{dpt_class.value_min} ... {dpt_class.value_max}"

        dpt_number_str = self._get_dpt_number_from_docstring(dpt_class)
        self.dpt_number_sort = self._dpt_number_sort(dpt_number_str)
        dpt_number = self._dpt_number_str_repr(dpt_number_str)

        super().__init__(
            value_type=dpt_class.value_type,
            unit=dpt_class.unit,
            dpt_number=dpt_number,
            dpt_size=str(dpt_class.payload_length),
            dpt_range=dpt_range,
        )

    def _get_dpt_number_from_docstring(self, dpt_class: DPTBase):
        """Extract dpt number from class docstring."""
        docstring = dpt_class.__doc__
        try:
            for line in docstring.splitlines():
                text = line.strip()
                if text.startswith("DPT"):
                    return text.split()[1]
        except IndexError:
            print("Error: Could not read docstring for: %s" % dpt_class)
        print("Error: Could not find DPT in docstring for: %s" % dpt_class)
        raise ValueError

    def _dpt_number_sort(self, dpt_str: str) -> int:
        """Return dpt number as integer (for sorting). "xxx" is treated as 0."""
        try:
            dpt_major, dpt_minor = dpt_str.split(".")
            if dpt_minor in ("x", "xxx", "*", "***"):
                dpt_minor = -1
            elif dpt_minor in ("?", "???"):
                dpt_minor = 99999
            return (int(dpt_major) * 100000) + int(dpt_minor)
        except ValueError:
            print(
                f"Error: Could not parse dpt_number: '{self.dpt_number}' in  '{self.value_type}'"
            )

    def _dpt_number_str_repr(self, dpt_str: str) -> str:
        dpt_major, dpt_minor = dpt_str.split(".")
        if dpt_minor in ("x", "xxx", "*", "***"):
            return dpt_major
        return dpt_str


def table_delimiter():
    """Build a row of table delimiters."""

    def table_delimiter_ljust(width):
        return "|-" + "-" * width + "-"

    def table_delimiter_center(width):
        return "|:" + "-" * width + ":"

    def table_delimiter_rjust(width):
        return "|-" + "-" * width + ":"

    _row = ""
    for column in COLUMN_ORDER:
        _cell_width = Row.column_width[column]
        if COLUMN_ADJUSTMENT[column] == "left":
            _row += table_delimiter_ljust(_cell_width)
        elif COLUMN_ADJUSTMENT[column] == "right":
            _row += table_delimiter_rjust(_cell_width)
        elif COLUMN_ADJUSTMENT[column] == "center":
            _row += table_delimiter_center(_cell_width)
    _row += "|"
    return _row


def print_table():
    """Read the values and print the table to stdout."""
    rows = []
    for dpt in DPTBase.__recursive_subclasses__():
        if dpt.has_distinct_value_type():
            try:
                row = DPTRow(dpt_class=dpt)
            except ValueError:
                continue
            else:
                rows.append(row)

    rows.sort(key=lambda row: row.dpt_number_sort)

    table_header = Row()
    rows.insert(0, table_header)

    # Insert at last to have correct column_widths.
    rows.insert(1, table_delimiter())

    for row in rows:
        print(row)


if __name__ == "__main__":
    print_table()
