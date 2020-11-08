# Ported from: https://github.com/pleonex/tinke by Cervi for Team Top Hat


class SoundBase:
    def __init__(self, sound_file: str, id_: int, format_: str, copyright_: str, editable: bool):
        self._sound_file = sound_file
        self._id = id_
        self._format = format_
        self._copyright = copyright_
        self._editable = editable

        self._pcm16 = bytearray()
        self._pcm16_loop = bytearray()

        self._loop_enabled = True
        self._loop_begin_sample = 0
        self._loop_end_sample = 0

        self._total_samples = 0
        self._sample_rate = 0
        self._channels = 0
        self._block_size = 0
        self._sample_bit_depth = 0

    @property
    def sound_file(self):
        return self._sound_file

    @property
    def format(self):
        return self._format

    @property
    def id(self):
        return self._id

    @property
    def copyright(self):
        return self._copyright

    @property
    def can_edit(self):
        return self._editable

    @property
    def can_loop(self):
        return self._loop_enabled

    @property
    def loop_begin(self):
        return self._loop_begin_sample

    @property
    def loop_end(self):
        return self._loop_end_sample

    @property
    def number_samples(self):
        return self._total_samples

    @property
    def sample_rate(self):
        return self._sample_rate

    @property
    def channels(self):
        return self._channels

    @property
    def block_size(self):
        return self._block_size

    @property
    def sample_bit_depth(self):
        return self._sample_bit_depth

    def initialize(self):
        encoded = self.read_file()

        self._pcm16 = self.decode(encoded, False)
        if self._loop_enabled:
            self._pcm16_loop = self.decode(encoded, True)

    # Abstract
    def read_file(self) -> bytearray:
        raise NotImplementedError("read_file not implemented")

    # Abstract
    def decode(self, encoded: bytearray, loop_enabled: bool) -> bytearray:
        raise NotImplementedError("decode not implemented")

    def write_file(self, file_out: str, data: bytearray):
        raise NotImplementedError("write_file not implemented")

    def encode(self) -> bytearray:
        return self.__encode(self._pcm16)

    def __encode(self, data: bytearray) -> bytearray:
        raise NotImplementedError("encode not implemented")

    # TODO: public Stream Get_Stream()
