'''
  timestamp.py

  Implements Timestamp class for encapsulating timestamp.

  Mutability: This class is immutable.

  Internally, in the TAL codebase, the Timestamp class is only way to represent
  and pass around timestamp. Thus this class normalizes across multiple
  different ways to represent timestamp.

  At the TAL API boundary this class is first used to wrap any caller supplied
  timestamp formats and converted into the normalized form. The normalized form
  is the storing timestamp as an integer value (i.e. time since epoch).

  Currently, even on the boundary only the normalized form is supported.
'''

from enum import Enum
from . import exceptions as excp

class Timestamp(object):
  def __init__(self, timestamp):
    try:
      self.__timestamp = int(timestamp)
    except:
      raise excp.InvalidTimestampFormat("Invalid timestamp %s" % timestamp)

    if self.__timestamp < 0:
      raise excp.NegativeTimestamp("Timestamp cannnot be %d" % self.__timestamp)

  def __eq__(self, other):
    if isinstance(other, Timestamp):
        return self.value == other.value
    return False

  def __str__(self):
    return str(self.value)

  @property
  def value(self):
    return self.__timestamp
