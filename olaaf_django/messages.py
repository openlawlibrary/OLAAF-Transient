# TODO: i18n
from .utils import format_date

VALID_OUTDATED_DOC_MSG = """
Document was valid between {start_date} and {end_date}.
"""

VALID_CURRENT_DOC_MSG = """
Document is valid since {start_date}.
"""


def format_message(template, **kwargs):
  """
  Format parameters that have `date` keyword in their names and return populated template.
  """
  for arg_name, arg_value in kwargs.items():
    if 'date' in arg_name:
      kwargs[arg_name] = format_date(arg_value)

  return template.format(**kwargs).strip()
