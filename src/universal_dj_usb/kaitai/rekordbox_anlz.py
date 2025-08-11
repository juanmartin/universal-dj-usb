# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO
from enum import Enum
import struct


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class RekordboxAnlz(KaitaiStruct):
    """These files are created by rekordbox when analyzing audio tracks
    to facilitate DJ performance. They include waveforms, beat grids
    (information about the precise time at which each beat occurs),
    time indices to allow efficient seeking to specific positions
    inside variable bit-rate audio streams, and lists of memory cues
    and loop points. They are used by Pioneer professional DJ
    equipment.
    
    The format has been reverse-engineered to facilitate sophisticated
    integrations with light and laser shows, videos, and other musical
    instruments, by supporting deep knowledge of what is playing and
    what is coming next through monitoring the network communications
    of the players.
    
    .. seealso::
       Source - https://reverseengineering.stackexchange.com/questions/4311/help-reversing-a-edb-database-file-for-pioneers-rekordbox-software
    """

    class CueEntryStatus(Enum):
        disabled = 0
        enabled = 1
        active_loop = 4

    class CueListType(Enum):
        memory_cues = 0
        hot_cues = 1

    class MoodHighPhrase(Enum):
        intro = 1
        up = 2
        down = 3
        chorus = 5
        outro = 6

    class TrackBank(Enum):
        default = 0
        cool = 1
        natural = 2
        hot = 3
        subtle = 4
        warm = 5
        vivid = 6
        club_1 = 7
        club_2 = 8

    class CueEntryType(Enum):
        memory_cue = 1
        loop = 2

    class SectionTags(Enum):
        cues_2 = 1346588466
        cues = 1346588482
        path = 1347441736
        beat_grid = 1347507290
        song_structure = 1347638089
        vbr = 1347830354
        wave_preview = 1347895638
        wave_tiny = 1347900978
        wave_scroll = 1347900979
        wave_color_preview = 1347900980
        wave_color_scroll = 1347900981
        wave_3band_preview = 1347900982
        wave_3band_scroll = 1347900983

    class TrackMood(Enum):
        high = 1
        mid = 2
        low = 3

    class MoodMidPhrase(Enum):
        intro = 1
        verse_1 = 2
        verse_2 = 3
        verse_3 = 4
        verse_4 = 5
        verse_5 = 6
        verse_6 = 7
        bridge = 8
        chorus = 9
        outro = 10

    class MoodLowPhrase(Enum):
        intro = 1
        verse_1 = 2
        verse_1b = 3
        verse_1c = 4
        verse_2 = 5
        verse_2b = 6
        verse_2c = 7
        bridge = 8
        chorus = 9
        outro = 10
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.magic = self._io.read_bytes(4)
        if not self.magic == b"\x50\x4D\x41\x49":
            raise kaitaistruct.ValidationNotEqualError(b"\x50\x4D\x41\x49", self.magic, self._io, u"/seq/0")
        self.len_header = self._io.read_u4be()
        self.len_file = self._io.read_u4be()
        self._unnamed3 = self._io.read_bytes((self.len_header - self._io.pos()))
        self.sections = []
        i = 0
        while not self._io.is_eof():
            self.sections.append(RekordboxAnlz.TaggedSection(self._io, self, self._root))
            i += 1


    class Wave3bandScrollTag(KaitaiStruct):
        """The minimalist CDJ-3000 waveform image suitable for scrolling along
        as a track plays on newer high-resolution hardware.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_entry_bytes = self._io.read_u4be()
            self.len_entries = self._io.read_u4be()
            self._unnamed2 = self._io.read_u4be()
            self.entries = self._io.read_bytes((self.len_entries * self.len_entry_bytes))


    class PhraseMid(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = KaitaiStream.resolve_enum(RekordboxAnlz.MoodMidPhrase, self._io.read_u2be())


    class PathTag(KaitaiStruct):
        """Stores the file path of the audio file to which this analysis
        applies.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_path = self._io.read_u4be()
            if self.len_path > 1:
                self.path = (self._io.read_bytes((self.len_path - 2))).decode(u"utf-16be")



    class WavePreviewTag(KaitaiStruct):
        """Stores a waveform preview image suitable for display above
        the touch strip for jumping to a track position.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_data = self._io.read_u4be()
            self._unnamed1 = self._io.read_u4be()
            if self._parent.len_tag > self._parent.len_header:
                self.data = self._io.read_bytes(self.len_data)



    class BeatGridTag(KaitaiStruct):
        """Holds a list of all the beats found within the track, recording
        their bar position, the time at which they occur, and the tempo
        at that point.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_u4be()
            self._unnamed1 = self._io.read_u4be()
            self.num_beats = self._io.read_u4be()
            self.beats = []
            for i in range(self.num_beats):
                self.beats.append(RekordboxAnlz.BeatGridBeat(self._io, self, self._root))



    class SongStructureBody(KaitaiStruct):
        """Stores the rest of the song structure tag, which can only be
        parsed after unmasking.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.mood = KaitaiStream.resolve_enum(RekordboxAnlz.TrackMood, self._io.read_u2be())
            self._unnamed1 = self._io.read_bytes(6)
            self.end_beat = self._io.read_u2be()
            self._unnamed3 = self._io.read_bytes(2)
            self.raw_bank = self._io.read_u1()
            self._unnamed5 = self._io.read_bytes(1)
            self.entries = []
            for i in range(self._parent.len_entries):
                self.entries.append(RekordboxAnlz.SongStructureEntry(self._io, self, self._root))


        @property
        def bank(self):
            """The stylistic bank which can be assigned to the track in rekordbox Lighting mode, if raw_bank has a legal value.
            """
            if hasattr(self, '_m_bank'):
                return self._m_bank

            if self.raw_bank < 9:
                self._m_bank = KaitaiStream.resolve_enum(RekordboxAnlz.TrackBank, self.raw_bank)

            return getattr(self, '_m_bank', None)


    class WaveColorPreviewTag(KaitaiStruct):
        """A larger, colorful waveform preview image suitable for display
        above the touch strip for jumping to a track position on newer
        high-resolution players.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_entry_bytes = self._io.read_u4be()
            self.len_entries = self._io.read_u4be()
            self._unnamed2 = self._io.read_u4be()
            self.entries = self._io.read_bytes((self.len_entries * self.len_entry_bytes))


    class PhraseHigh(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = KaitaiStream.resolve_enum(RekordboxAnlz.MoodHighPhrase, self._io.read_u2be())


    class WaveScrollTag(KaitaiStruct):
        """A larger waveform image suitable for scrolling along as a track
        plays.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_entry_bytes = self._io.read_u4be()
            self.len_entries = self._io.read_u4be()
            self._unnamed2 = self._io.read_u4be()
            self.entries = self._io.read_bytes((self.len_entries * self.len_entry_bytes))


    class SongStructureTag(KaitaiStruct):
        """Stores the song structure, also known as phrases (intro, verse,
        bridge, chorus, up, down, outro).
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_entry_bytes = self._io.read_u4be()
            self.len_entries = self._io.read_u2be()
            self._raw__raw_body = self._io.read_bytes_full()
            self._raw_body = KaitaiStream.process_xor_many(self._raw__raw_body, (self.mask if self.is_masked else b"\x00"))
            _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
            self.body = RekordboxAnlz.SongStructureBody(_io__raw_body, self, self._root)

        @property
        def c(self):
            if hasattr(self, '_m_c'):
                return self._m_c

            self._m_c = self.len_entries
            return getattr(self, '_m_c', None)

        @property
        def mask(self):
            if hasattr(self, '_m_mask'):
                return self._m_mask

            self._m_mask = struct.pack('19b', (203 + self.c), (225 + self.c), (238 + self.c), (250 + self.c), (229 + self.c), (238 + self.c), (173 + self.c), (238 + self.c), (233 + self.c), (210 + self.c), (233 + self.c), (235 + self.c), (225 + self.c), (233 + self.c), (243 + self.c), (232 + self.c), (233 + self.c), (244 + self.c), (225 + self.c))
            return getattr(self, '_m_mask', None)

        @property
        def raw_mood(self):
            """This is a way to tell whether the rest of the tag has been masked. The value is supposed
            to range from 1 to 3, but in masked files it will be much larger.
            """
            if hasattr(self, '_m_raw_mood'):
                return self._m_raw_mood

            _pos = self._io.pos()
            self._io.seek(6)
            self._m_raw_mood = self._io.read_u2be()
            self._io.seek(_pos)
            return getattr(self, '_m_raw_mood', None)

        @property
        def is_masked(self):
            if hasattr(self, '_m_is_masked'):
                return self._m_is_masked

            self._m_is_masked = self.raw_mood > 20
            return getattr(self, '_m_is_masked', None)


    class CueExtendedEntry(KaitaiStruct):
        """A cue extended list entry. Can either describe a memory cue or a
        loop.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x50\x43\x50\x32":
                raise kaitaistruct.ValidationNotEqualError(b"\x50\x43\x50\x32", self.magic, self._io, u"/types/cue_extended_entry/seq/0")
            self.len_header = self._io.read_u4be()
            self.len_entry = self._io.read_u4be()
            self.hot_cue = self._io.read_u4be()
            self.type = KaitaiStream.resolve_enum(RekordboxAnlz.CueEntryType, self._io.read_u1())
            self._unnamed5 = self._io.read_bytes(3)
            self.time = self._io.read_u4be()
            self.loop_time = self._io.read_u4be()
            self.color_id = self._io.read_u1()
            self._unnamed9 = self._io.read_bytes(7)
            self.loop_numerator = self._io.read_u2be()
            self.loop_denominator = self._io.read_u2be()
            if self.len_entry > 43:
                self.len_comment = self._io.read_u4be()

            if self.len_entry > 43:
                self.comment = (self._io.read_bytes(self.len_comment)).decode(u"utf-16be")

            if (self.len_entry - self.len_comment) > 44:
                self.color_code = self._io.read_u1()

            if (self.len_entry - self.len_comment) > 45:
                self.color_red = self._io.read_u1()

            if (self.len_entry - self.len_comment) > 46:
                self.color_green = self._io.read_u1()

            if (self.len_entry - self.len_comment) > 47:
                self.color_blue = self._io.read_u1()

            if (self.len_entry - self.len_comment) > 48:
                self._unnamed18 = self._io.read_bytes(((self.len_entry - 48) - self.len_comment))



    class VbrTag(KaitaiStruct):
        """Stores an index allowing rapid seeking to particular times
        within a variable-bitrate audio file.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._unnamed0 = self._io.read_u4be()
            self.index = []
            for i in range(400):
                self.index.append(self._io.read_u4be())



    class SongStructureEntry(KaitaiStruct):
        """A song structure entry, represents a single phrase.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.index = self._io.read_u2be()
            self.beat = self._io.read_u2be()
            _on = self._parent.mood
            if _on == RekordboxAnlz.TrackMood.high:
                self.kind = RekordboxAnlz.PhraseHigh(self._io, self, self._root)
            elif _on == RekordboxAnlz.TrackMood.mid:
                self.kind = RekordboxAnlz.PhraseMid(self._io, self, self._root)
            elif _on == RekordboxAnlz.TrackMood.low:
                self.kind = RekordboxAnlz.PhraseLow(self._io, self, self._root)
            else:
                self.kind = RekordboxAnlz.PhraseMid(self._io, self, self._root)
            self._unnamed3 = self._io.read_bytes(1)
            self.k1 = self._io.read_u1()
            self._unnamed5 = self._io.read_bytes(1)
            self.k2 = self._io.read_u1()
            self._unnamed7 = self._io.read_bytes(1)
            self.b = self._io.read_u1()
            self.beat2 = self._io.read_u2be()
            self.beat3 = self._io.read_u2be()
            self.beat4 = self._io.read_u2be()
            self._unnamed12 = self._io.read_bytes(1)
            self.k3 = self._io.read_u1()
            self._unnamed14 = self._io.read_bytes(1)
            self.fill = self._io.read_u1()
            self.beat_fill = self._io.read_u2be()


    class CueEntry(KaitaiStruct):
        """A cue list entry. Can either represent a memory cue or a loop.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.magic = self._io.read_bytes(4)
            if not self.magic == b"\x50\x43\x50\x54":
                raise kaitaistruct.ValidationNotEqualError(b"\x50\x43\x50\x54", self.magic, self._io, u"/types/cue_entry/seq/0")
            self.len_header = self._io.read_u4be()
            self.len_entry = self._io.read_u4be()
            self.hot_cue = self._io.read_u4be()
            self.status = KaitaiStream.resolve_enum(RekordboxAnlz.CueEntryStatus, self._io.read_u4be())
            self._unnamed5 = self._io.read_u4be()
            self.order_first = self._io.read_u2be()
            self.order_last = self._io.read_u2be()
            self.type = KaitaiStream.resolve_enum(RekordboxAnlz.CueEntryType, self._io.read_u1())
            self._unnamed9 = self._io.read_bytes(3)
            self.time = self._io.read_u4be()
            self.loop_time = self._io.read_u4be()
            self._unnamed12 = self._io.read_bytes(16)


    class BeatGridBeat(KaitaiStruct):
        """Describes an individual beat in a beat grid.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.beat_number = self._io.read_u2be()
            self.tempo = self._io.read_u2be()
            self.time = self._io.read_u4be()


    class CueExtendedTag(KaitaiStruct):
        """A variation of cue_tag which was introduced with the nxs2 line,
        and adds descriptive names. (Still comes in two forms, either
        holding memory cues and loop points, or holding hot cues and
        loop points.) Also includes hot cues D through H and color assignment.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.type = KaitaiStream.resolve_enum(RekordboxAnlz.CueListType, self._io.read_u4be())
            self.num_cues = self._io.read_u2be()
            self._unnamed2 = self._io.read_bytes(2)
            self.cues = []
            for i in range(self.num_cues):
                self.cues.append(RekordboxAnlz.CueExtendedEntry(self._io, self, self._root))



    class PhraseLow(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.id = KaitaiStream.resolve_enum(RekordboxAnlz.MoodLowPhrase, self._io.read_u2be())


    class UnknownTag(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            pass


    class TaggedSection(KaitaiStruct):
        """A type-tagged file section, identified by a four-byte magic
        sequence, with a header specifying its length, and whose payload
        is determined by the type tag.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.fourcc = KaitaiStream.resolve_enum(RekordboxAnlz.SectionTags, self._io.read_s4be())
            self.len_header = self._io.read_u4be()
            self.len_tag = self._io.read_u4be()
            _on = self.fourcc
            if _on == RekordboxAnlz.SectionTags.wave_color_scroll:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.WaveColorScrollTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.wave_scroll:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.WaveScrollTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.vbr:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.VbrTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.wave_3band_scroll:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.Wave3bandScrollTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.cues_2:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.CueExtendedTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.cues:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.CueTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.song_structure:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.SongStructureTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.beat_grid:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.BeatGridTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.wave_preview:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.WavePreviewTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.wave_3band_preview:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.Wave3bandPreviewTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.wave_color_preview:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.WaveColorPreviewTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.path:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.PathTag(_io__raw_body, self, self._root)
            elif _on == RekordboxAnlz.SectionTags.wave_tiny:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.WavePreviewTag(_io__raw_body, self, self._root)
            else:
                self._raw_body = self._io.read_bytes((self.len_tag - 12))
                _io__raw_body = KaitaiStream(BytesIO(self._raw_body))
                self.body = RekordboxAnlz.UnknownTag(_io__raw_body, self, self._root)


    class Wave3bandPreviewTag(KaitaiStruct):
        """The minimalist CDJ-3000 waveform preview image suitable for display
        above the touch strip for jumping to a track position.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_entry_bytes = self._io.read_u4be()
            self.len_entries = self._io.read_u4be()
            self.entries = self._io.read_bytes((self.len_entries * self.len_entry_bytes))


    class WaveColorScrollTag(KaitaiStruct):
        """A larger, colorful waveform image suitable for scrolling along
        as a track plays on newer high-resolution hardware. Also
        contains a higher-resolution blue/white waveform.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.len_entry_bytes = self._io.read_u4be()
            self.len_entries = self._io.read_u4be()
            self._unnamed2 = self._io.read_u4be()
            self.entries = self._io.read_bytes((self.len_entries * self.len_entry_bytes))


    class CueTag(KaitaiStruct):
        """Stores either a list of ordinary memory cues and loop points, or
        a list of hot cues and loop points.
        """
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.type = KaitaiStream.resolve_enum(RekordboxAnlz.CueListType, self._io.read_u4be())
            self._unnamed1 = self._io.read_bytes(2)
            self.num_cues = self._io.read_u2be()
            self.memory_count = self._io.read_u4be()
            self.cues = []
            for i in range(self.num_cues):
                self.cues.append(RekordboxAnlz.CueEntry(self._io, self, self._root))




