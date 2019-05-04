from gandalf.extra import boundary_search
from gandalf.extra import handle_backups
from gandalf.extra import note_and_measure_offset
from gandalf.extra import track_moved_notes
from gandalf.extra import track_moved_measures


def test_boundary_search():
  string = "\u0001\u0002\u0003\u0004\u0005\u0006\u0007\b\u000e\u000f\u0010\u0011\u0012\u0013\u0014\u0015\u0016\u0017\u0018\u0019\u001a\u001b\u001c\u001d\u001e\u001f" # noqa E501
  assert boundary_search("\u001a", "\u001e", string)             == ['\x1b\x1c\x1d'] # noqa E221


def test_handle_backups():
  string = """<note>
  <chord/>
  <pitch>
    <step>E</step>
    <octave>5</octave>
  </pitch>
  <duration>80</duration>
  <instrument id="P1-S0V0"/>
  <voice>1</voice>
  <type>quarter</type>
  <stem>down</stem>
<backup>
  <vertical-alignment>80</vertical-alignment>
</backup>
</note>
"""
  assert handle_backups("tests/xml/backup-test.xml")           == string # noqa E221


def test_note_and_measure_offset():
  assert note_and_measure_offset("inst_1.measure_1.note_1", 1, 1) == "inst_1.measure_2.note_2" # noqa E221


def test_track_moved_notes():
  assert track_moved_notes("a.bb.c.eee")                          == "a.bb.c" # noqa E221


def test_track_moved_measures():
  assert track_moved_measures("a.bb.c.eee")                       == "a.bb" # noqa E221