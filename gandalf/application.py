from io import StringIO, BytesIO

import attr
from lxml import etree
import music21

from gandalf.base import GandalfObject
from gandalf.base import NoteObject
from gandalf.base import RestObject
from gandalf.base import TimeSignatureObject
from gandalf.base import KeySignatureObject
from gandalf.base import ClefObject
# Result Objects
from gandalf.base import (
  NotePitchResult,
  NoteDurationResult,
  NoteOctaveResult,
  NoteAccidentalResult,
  NoteStemDirectionResult,
  NoteBeamResult,
  NoteTotalResult,
  RestAccidentalResult,
  RestDurationResult,
  RestTotalResult,
  TimeSignatureNumeratorResult,
  TimeSignatureDenominatorResult,
  TimeSignatureTotalResult,
  KeySignatureStepResult,
  KeySignatureModeResult,
  KeySignatureTotalResult,
  ClefNameResult,
  ClefLineResult,
  ClefOctaveResult,
  ClefTotalResult,
)
from gandalf.extra import __return_root_path


def validate_xml(musicxml_filepath):
  """
  Return if the provided musicxml file is valid against the current musicxml schema.

  Args:
    schema_filepath (string): a filepath to the musicxml schema.

    musicxml_filepath (string): a filepath to the musicxml file to be validated.

  Returns:
    bool
  """
  schema_filepath = __return_root_path() + "/tests/xml/musicxml.xsd"
  with open(schema_filepath, "r") as schema:
    schema = StringIO(schema.read())
  with open(musicxml_filepath, "rb") as xml_file:
    test = BytesIO(xml_file.read())

  xml_schema = etree.XMLSchema(etree.parse(schema_filepath))
  return xml_schema.validate(etree.parse(test))


@attr.s
class ParseMusic21(GandalfObject):
  """
  This is just a simplifying wrapper around Music21, so it can import anything Music21 can.
  """
  @classmethod
  def from_filepath(cls, filepath):
    notes, rests, timeSignatures, keySignatures, clefs = [], [], [], [], []
    for parts_index, parts in enumerate(music21.converter.parseFile(filepath).recurse().getElementsByClass("Part"), 1):  # noqa
      notes += [NoteObject(item, parts_index) for item in parts.recurse().notes if not item.isChord]
      rests += [RestObject(item, parts_index) for item in parts.recurse().notesAndRests if not item.isNote]
      timeSignatures += [TimeSignatureObject(item, parts_index) for item in parts.recurse().getTimeSignatures()]
      keySignatures += [KeySignatureObject(item, parts_index) for item in parts.recurse().getElementsByClass("KeySignature")]  # noqa
      clefs += [ClefObject(item, parts_index) for item in parts.recurse().getElementsByClass("Clef")]
    return cls(
      notes=notes,
      rests=rests,
      timeSignatures=timeSignatures,
      keySignatures=keySignatures,
      clefs=clefs
    )

  def __iter__(self):
    return iter(self.ret())


class Compare(GandalfObject):
  """
  This is a simple class for comparing Gandalf Objects.
  """
  def __init__(self, true_filepath, test_filepath):
    self.true_data = ParseMusic21.from_filepath(true_filepath)
    self.test_data = ParseMusic21.from_filepath(test_filepath)

    # Notes
    self.notes = []
    self.notes_pitch = NotePitchResult()
    self.notes_duration = NoteDurationResult()
    self.notes_octave = NoteOctaveResult()
    self.notes_accidental = NoteAccidentalResult()
    self.notes_stemdirection = NoteStemDirectionResult()
    self.notes_beam = NoteBeamResult()
    self.notes_total = NoteTotalResult()

    # Rests
    self.rests = []
    self.rests_accidental = RestAccidentalResult()
    self.rests_duration = RestDurationResult()
    self.rests_total = RestTotalResult()

    # Time Signatures
    self.timeSignatures = []
    self.timeSignatures_numerator = TimeSignatureNumeratorResult()
    self.timeSignatures_denominator = TimeSignatureDenominatorResult()
    self.timeSignatures_total = TimeSignatureTotalResult()

    # Key Signatures
    self.keySignatures = []
    self.keySignatures_step = KeySignatureStepResult()
    self.keySignatures_mode = KeySignatureModeResult()
    self.keySignatures_total = KeySignatureTotalResult()

    # Clefs
    self.clefs = []
    self.clefs_name = ClefNameResult()
    self.clefs_line = ClefLineResult()
    self.clefs_octave = ClefOctaveResult()
    self.clefs_total = ClefTotalResult()

    self._object_split()
    self._total()

  def _return_object_names(self):
    """
    For a given object, return all fields

    For example:
      ['clefs', 'keySignatures', 'notes', 'rests', 'timeSignatures']
    """
    return [item for item in dir(self) if "_" not in item and item not in ["check", "ret"]]

  def _return_parameter_names(self, field):
    """
    For a specific field, return all items

    For notes:
      ['notes_accidental', 'notes_beam', 'notes_duration', 'notes_octave', 'notes_pitch', 'notes_stemdirection']
    """
    return [item for item in dir(self) if field in item and "_" in item and "total" not in item]

  def _compare(self, true_object, test_object):
    for param in self._return_parameter_names(true_object.asname()):

      if true_object.__getattribute__(param.split("_")[-1]) == test_object.__getattribute__(param.split("_")[-1]):
        self.__getattribute__(param).right += 1
      else:
        self.__getattribute__(param).wrong += 1

  def _object_split(self):
    """
    Align Objects together
    """
    for obj in self._return_object_names():
      for true_object in self.true_data.__getattribute__(obj):
        for test_object in self.test_data.__getattribute__(obj):
          if true_object == test_object:
            self._compare(true_object, test_object)

  def _total(self):
    for obj in self._return_object_names():
      for params in self._return_parameter_names(obj):
        # Add the detailed results to the list of objects
        self.__getattribute__(obj).append(self.__getattribute__(params))
        self.__getattribute__(f"{obj}_total").right += self.__getattribute__(params).right
        self.__getattribute__(f"{obj}_total").wrong += self.__getattribute__(params).wrong

      self.__getattribute__(obj).append(self.__getattribute__(f"{obj}_total"))
