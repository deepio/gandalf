from io import BytesIO

import attr
from lxml import etree
import music21

from gandalf.base import (
  GandalfObject,
  NoteObject,
  RestObject,
  TimeSignatureObject,
  KeySignatureObject,
  ClefObject)
from gandalf.result_objects import (
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
from gandalf.extra import (
  __return_root_path,
  return_char_except
)
from gandalf.sequence_alignment import (
  AffineNeedlemanWunsch,
  AdvancedAffineNeedlemanWunsch
)


def xml_validator(musicxml_filepath, schema_filepath=__return_root_path() + "/tests/xml/musicxml.xsd"):
  """
  Return if the provided musicxml file is valid against the current musicxml schema.

  Args:
    schema_filepath (string): a filepath to the musicxml schema.

    musicxml_filepath (string): a filepath to the musicxml file to be validated.

  Returns:
    bool
  """
  with open(musicxml_filepath, "rb") as xml_file:
    test = BytesIO(xml_file.read())

  try:
    xml_schema = etree.XMLSchema(etree.parse(schema_filepath))
  except etree.XMLSyntaxError:
    xml_schema = etree.DTD(schema_filepath)

  return xml_schema.validate(etree.parse(test))


def xml_type_finder(musicxml_filepath):
  """
  Check if the xml file is written in a partwise or timewise fashion.
  """
  with open(musicxml_filepath, "r") as xml_file:
    for line in xml_file:
      if "score-partwise" in line.lower():
        return "Partwise"
      elif "score-timewise" in line.lower():
        return "Timewise"
    raise Exception("File has neither time-wise or part-wise tags")


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
      clefs=clefs,
      parts=parts_index,
      error_description={},
    )

  def __iter__(self):
    return iter(self.ret())


class Compare(GandalfObject):
  """
  This is a simple class for comparing Gandalf Objects.
  """
  def __init__(self, true_filepath, test_filepath, sorting_algorithm="basic"):
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

    # Parse both files
    self.true_data = ParseMusic21.from_filepath(true_filepath)
    self.test_data = ParseMusic21.from_filepath(test_filepath)

    self.error_description = {}

    if sorting_algorithm == "basic":
      # Using a "dumb" alignment
      self._object_split()
    elif sorting_algorithm == "anw":
      # Using a simple version of Affine-Needleman-Wunsch
      self.sequence_alignment()

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
    """
    Compare two Gandalf Objects.

      - If the sequence alignment believes there is an extra note in the OMR output, simply deleting the extra note
        should be the solution. Removing each wrong element individually and finally removing the note is not how a
        human would fix this type of error.

      - Then check for each parameter available in the type of marking, count an error for each wrong element and a
        right for every correct. This function should works for all Gandalf objects.
    """
    # If object is missaligned
    try:
      true_part = true_object.part
      true_onset = true_object.onset
      true_mu21_obj = true_object._music21_object
    except AttributeError:
      true_part = "_"
      true_onset = ""
      true_mu21_obj = ""

    # If object is missaligned
    try:
      test_part = test_object.part
      test_onset = test_object.onset
      test_mu21_obj = test_object._music21_object
    except AttributeError:
      test_part = "_"
      test_onset = ""
      test_mu21_obj = ""

    # If there is an extra object in the test data, it's better to just delete the note. + 1 wrong to the total
    if true_object == "_":
      self.__getattribute__(f"{test_object.asname()}_total").wrong += 1
      self.error_description[f"part{true_part}_{true_onset}_{true_mu21_obj}"] = f"part{test_part}_{test_onset}_{test_mu21_obj}"
    else:
      for param in self._return_parameter_names(true_object.asname()):
        try:
          if true_object.__getattribute__(param.split("_")[-1]) == test_object.__getattribute__(param.split("_")[-1]):
            self.__getattribute__(param).right += 1
          else:
            self.__getattribute__(param).wrong += 1
            self.error_description[f"part{true_part}_{true_onset}_{true_mu21_obj}"] = f"part{test_part}_{test_onset}_{test_mu21_obj}"  # noqa
        except AttributeError:
          # If the object needs to be created, each parameter needs to be added individually, +1 error each.
          self.__getattribute__(param).wrong += 1
          self.error_description[f"part{true_part}_{true_onset}_{true_mu21_obj}"] = f"part{test_part}_{test_onset}_{test_mu21_obj}"  # noqa

  def _object_split(self):
    """
    Align Objects together by comparing voice, measure and onset.
    """
    for obj in self._return_object_names():
      for true_object in self.true_data.__getattribute__(obj):
        for test_object in self.test_data.__getattribute__(obj):
          if true_object == test_object:
            self._compare(true_object, test_object)

  def _total(self):
    """
    Automatically add the number of right/wrong attributes to the total of each param (notes, rests).
    """
    for obj in self._return_object_names():
      for params in self._return_parameter_names(obj):
        # Add the detailed results to the list of objects
        self.__getattribute__(obj).append(self.__getattribute__(params))
        self.__getattribute__(f"{obj}_total").right += self.__getattribute__(params).right
        self.__getattribute__(f"{obj}_total").wrong += self.__getattribute__(params).wrong

      self.__getattribute__(obj).append(self.__getattribute__(f"{obj}_total"))

  def _rebuild(self, aligned_data, unaligned_data):
    """
    Rebuild the list of items according to how the AffineNeedlemanWunsch aligned them.
    """
    output = []
    track = 0
    for entry in aligned_data:
      if entry != "_" and entry != " ":
        output.append(unaligned_data[track])
        track += 1
      else:
        output.append("_")

    return output

  def sequence_alignment(self):
    """
    Align each note object with each other. Understandably this is not the best, but it
    serves more as a proof-of-concept or a placeholder to be built later.

    - Notes           are aligned by pitch names
    - Restes          are aligned by measure number as a single char
    - TimeSignatures  are aligned by measure number as a single char
    - KeySignatures   are aligned by measure number as a single char
    - Clefs           are aligned by measure number as a single char
    """

    # Notes
    true_notes = [item.pitch for item in self.true_data.notes]
    test_notes = [item.pitch for item in self.test_data.notes]
    notes_anw = AffineNeedlemanWunsch(true_notes, test_notes)

    true_note_objects = self._rebuild(notes_anw.aligned_true_data, self.true_data.notes)
    test_note_objects = self._rebuild(notes_anw.aligned_test_data, self.test_data.notes)
    for index, objects in enumerate(true_note_objects):
      self._compare(objects, test_note_objects[index])

    # Rests
    true_rests = [return_char_except(item.measure) for item in self.true_data.rests]
    test_rests = [return_char_except(item.measure) for item in self.test_data.rests]
    rests_anw = AffineNeedlemanWunsch(true_rests, test_rests)

    true_rest_objects = self._rebuild(rests_anw.aligned_true_data, self.true_data.rests)
    test_rest_objects = self._rebuild(rests_anw.aligned_test_data, self.test_data.rests)
    for index, objects in enumerate(true_rest_objects):
      self._compare(objects, test_rest_objects[index])

    # Time Signature
    true_timeSignatures = [return_char_except(item.measure) for item in self.true_data.timeSignatures]
    test_timeSignatures = [return_char_except(item.measure) for item in self.test_data.timeSignatures]
    timeSignatures_anw = AffineNeedlemanWunsch(true_timeSignatures, test_timeSignatures)

    true_timeSignature_objects = self._rebuild(timeSignatures_anw.aligned_true_data, self.true_data.timeSignatures)
    test_timeSignature_objects = self._rebuild(timeSignatures_anw.aligned_test_data, self.test_data.timeSignatures)
    for index, objects in enumerate(true_timeSignature_objects):
      self._compare(objects, test_timeSignature_objects[index])

    # Key Signature
    true_keySignatures = [return_char_except(item.measure) for item in self.true_data.keySignatures]
    test_keySignatures = [return_char_except(item.measure) for item in self.test_data.keySignatures]
    keySignatures_anw = AffineNeedlemanWunsch(true_keySignatures, test_keySignatures)

    true_keySignature_objects = self._rebuild(keySignatures_anw.aligned_true_data, self.true_data.keySignatures)
    test_keySignature_objects = self._rebuild(keySignatures_anw.aligned_test_data, self.test_data.keySignatures)
    for index, objects in enumerate(true_keySignature_objects):
      self._compare(objects, test_keySignature_objects[index])

    # Clefs
    true_clefs = [return_char_except(item.measure) for item in self.true_data.clefs]
    test_clefs = [return_char_except(item.measure) for item in self.test_data.clefs]
    clef_anw = AffineNeedlemanWunsch(true_clefs, test_clefs)

    true_clef_objects = self._rebuild(clef_anw.aligned_true_data, self.true_data.clefs)
    test_clef_objects = self._rebuild(clef_anw.aligned_test_data, self.test_data.clefs)
    for index, objects in enumerate(true_clef_objects):
      self._compare(objects, test_clef_objects[index])
