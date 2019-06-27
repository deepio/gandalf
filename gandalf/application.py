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
from gandalf.base import Result
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
    self.notes_pitch = Result("notes_pitch")
    self.notes_duration = Result("notes_duration")
    self.notes_octave = Result("notes_octave")
    self.notes_accidental = Result("notes_accidental")
    self.notes_stemdirection = Result("notes_stemdirection")
    self.notes_beam = Result("notes_beam")
    self.notes_total = Result("notes_total")

    # Rests
    self.rests = []
    self.rests_accidental = Result("rests_accidental")
    self.rests_duration = Result("rests_duration")
    self.rests_total = Result("rests_total")

    # Time Signatures
    self.timeSignatures = []
    self.timeSignatures_numerator = Result("timeSignatures_numerator")
    self.timeSignatures_denominator = Result("timeSignatures_denominator")
    self.timeSignatures_total = Result("timeSignatures_total")

    # Key Signatures
    self.keySignatures = []
    self.keySignatures_step = Result("keySignatures_step")
    self.keySignatures_mode = Result("keySignatures_mode")
    self.keySignatures_total = Result("keySignatures_total")

    # Clefs
    self.clefs = []
    self.clefs_name = Result("clefs_name")
    self.clefs_line = Result("clefs_line")
    self.clefs_octave = Result("clefs_octave")
    self.clefs_total = Result("clefs_total")

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

  def _object_split(self, func, true_objects, test_objects):
    """
    Align Objects together
    """
    for index, true_object in enumerate(true_objects):
      for index2, test_object in enumerate(test_objects):
        if true_object == test_object:
          func(true_object, test_object)

  def _compare_notes(self, true_data, test_data):
    # TODO: Refactor _compare_notes and _compare together for all objects.
    attributes = [item.split("_")[1] for item in self._param_finder("notes")]

    for obj in self._object_finder():
      for attribute in attributes:
        if true_data.__getattribute__(attribute) == test_data.__getattribute__(attribute):
          self.__getattribute__(f"{obj}_{attribute}").right += 1
        else:
          self.__getattribute__(f"{obj}_{attribute}").wrong += 1

  def _compare(self):
    # Compare NoteObjects
    self._object_split(self._compare_notes, self.true_data.ret()[0], self.test_data.ret()[0])

  def _total(self):
    # 
    for obj in self._object_finder():
      # For each parameter
      for parameter in self._param_finder(obj):
        self.notes.right += self.__getattribute__(parameter).right
        self.notes.wrong += self.__getattribute__(parameter).wrong
