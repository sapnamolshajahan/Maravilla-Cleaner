# -*- coding: utf-8 -*-

REPORT_OUTPUT_SELECTION = [
    ("xlsx", "Excel"),
]

ROUNDING_SELECTION = [
    ('none', '0.00 (no rounding)'),
    ('dollars', '0 (dollars)'),
]
ROUNDING_SELECTION_DICT = dict((x[0], x[1]) for x in ROUNDING_SELECTION)

# - Column listings.

REPORT_COLUMN_TYPES = [
    ('actual_period', 'Actual - Period'),
    ('actual_ytd', 'Actual - YTD'),
    ('actual_lytd', 'Actual - LYTD'),
    ('actual_ly', 'Actual - Last Full Year'),
    ('budget_period', 'Budget - Period'),
    ('budget_ytd', 'Budget - YTD'),
    ('budget_year', 'Budget - Full Year'),
    ('budget_lytd', 'Budget - LYTD'),
    ('variance', 'Variance'),
    ('variance-percent', 'Variance %'),
]

REPORT_COLUMN_TYPES_DICT = dict((x[0], x[1]) for x in REPORT_COLUMN_TYPES)

REPORT_COLUMN_VALUES = [
    ("0", "0 Offset"),
    ("-1", "-1 Period Offset"),
    ("-2", "-2 Period offset"),
    ("-3", "-3 Period offset"),
    ("-4", "-4 Period offset"),
    ("-5", "-5 Period offset"),
    ("-6", "-6 Period offset"),
    ("-7", "-7 Period offset"),
    ("-8", "-8 Period offset"),
    ("-9", "-9 Period offset"),
    ("-10", "-10 Period offset"),
    ("-11", "-11 Period offset"),
    ("-12", "-12 Period offset"),
]
REPORT_COLUMN_VALUES_DICT = dict((x[0], x[1]) for x in REPORT_COLUMN_VALUES)

REPORT_RANGE_VALUES = [
    ("0", "End This Month"),
    ("1", "End Last Month"),
    ("2", "Period 2"),
    ("3", "Period 3"),
    ("4", "Period 4"),
    ("5", "Period 5"),
    ("6", "Period 6"),
    ("7", "Period 7"),
    ("8", "Period 8"),
    ("9", "Period 9"),
    ("10", "Period 10"),
    ("11", "Period 11"),
    ("12", "Period 12"),
]
REPORT_RANGE_VALUES_DICT = dict((x[0], x[1]) for x in REPORT_RANGE_VALUES)
