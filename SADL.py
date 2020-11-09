# Ported from: https://github.com/pleonex/tinke by Cervi for Team Top Hat

from SoundBase import *
from binaryedit.binreader import *
from binaryedit.binwriter import *
from Compression.IMA_ADPCM import ImaAdpcm
from Compression.Procyon import Procyon
from Helper import Helper
from cint.cint import I32
import sys


class Coding:
    EMPTY = 0
    INT_IMA = 0x70
    NDS_PROCYON = 0xB0


class SADLStruct:
    def __init__(self):
        self.id_ = bytes()
        self.file_size = 0
        self.loop_flag = 0
        self.loop_offset = 0
        self.channel = 0
        self.coding = Coding.EMPTY
        self.sample_rate = 0
        self.num_samples = 0
        self.interleave_block_size = 0


class SADL(SoundBase):
    def __init__(self, file: str, id_: int):
        SoundBase.__init__(self, file, id_, "SADL", "vgmstream", True)
        self.sadl = SADLStruct()
        self._ignore_loop = True

    def read_file(self) -> bytearray:
        br = BinaryReader(open(self._sound_file, "rb"))

        self.sadl.id_ = br.read_chars(4)

        br.seek(0x31)
        self.sadl.loop_flag = br.read_byte()
        self.sadl.channel = br.read_byte()

        coding = br.read_byte()
        self.sadl.coding = coding & 0xf0
        print("SADL coding: {}".format(self.sadl.coding))

        if coding & 0x06 == 4:
            self.sadl.sample_rate = 32728
        elif coding & 0x06 == 2:
            self.sadl.sample_rate = 16364

        br.seek(0x40)
        self.sadl.file_size = br.read_uint32()

        start_offset = 0x100
        if self.sadl.coding == Coding.INT_IMA:
            self.sadl.num_samples = int((self.sadl.file_size - start_offset) / self.sadl.channel * 2)
        elif self.sadl.coding == Coding.NDS_PROCYON:
            self.sadl.num_samples = int((self.sadl.file_size - start_offset) / self.sadl.channel / 16 * 30)

        self.sadl.interleave_block_size = 0x10

        br.seek(0x54)
        if self.sadl.loop_flag != 0:
            if self.sadl.coding == Coding.INT_IMA:
                self.sadl.loop_offset = int((br.read_uint32() - start_offset) / self.sadl.channel * 2)
            elif self.sadl.coding == Coding.NDS_PROCYON:
                self.sadl.loop_offset = int((br.read_uint32() - start_offset) / self.sadl.channel / 16 * 30)

        self._total_samples = self.sadl.num_samples
        self._sample_rate = self.sadl.sample_rate
        self._channels = self.sadl.channel
        self._block_size = self.sadl.interleave_block_size
        self._sample_bit_depth = 4

        self._loop_enabled = bool(self.sadl.loop_flag != 0)
        self._loop_begin_sample = self.sadl.loop_offset
        self._loop_end_sample = self.sadl.num_samples

        br.seek(0)
        buffer = br.read_bytearray(br.length())

        br.close()

        return buffer

    def decode(self, encoded: bytearray, loop_enabled: bool) -> bytearray:
        if self.sadl.coding == Coding.NDS_PROCYON:
            return self.decode_procyon(encoded)

        start_offset = I32(0x100)
        pos = 0

        if not self._loop_enabled:
            pos = start_offset
        else:
            pos = start_offset + self._loop_begin_sample * 2 * self._block_size

        left_channel = bytearray()
        right_channel = bytearray()
        data = bytearray()

        while pos < len(encoded):
            if self.sadl.channel == 2:  # Stereo
                buffer = encoded[pos:pos + self.sadl.interleave_block_size]
                pos += len(buffer)
                left_channel.extend(buffer)

                buffer = encoded[pos:pos + self.sadl.interleave_block_size]
                pos += len(buffer)
                right_channel.extend(buffer)
            else:  # Mono
                buffer = encoded[pos:pos + self.sadl.interleave_block_size * 2]
                pos += len(buffer)
                data.extend(buffer)

        # Decompress channels
        if self.sadl.coding == Coding.INT_IMA:
            if self.sadl.channel == 2:
                d_left_channel = ImaAdpcm.decompress(left_channel)

                d_right_channel = ImaAdpcm.decompress(right_channel)

                data.extend(Helper.merge_channels(d_left_channel, d_right_channel))
            else:
                data = ImaAdpcm.decompress(data)

        return data

    def decode_procyon(self, encoded: bytearray) -> bytearray:
        start_offset = I32(0x100)

        buffer = []
        hist = []
        length = []
        offset = []

        for i in range(0, self._channels):
            offset.append(start_offset + self._block_size * i)
            buffer.append(bytearray())
            length.append(I32(0))
            hist.append([I32(0), I32(0)])

        samples_written = I32(0)

        print("")

        while samples_written < self.number_samples:
            sys.stdout.write("\r{}/{} {:.2f}%".format(samples_written, self.number_samples,
                                                     int(samples_written) / int(self.number_samples) * 100))
            samples_to_do = I32(30)
            if samples_written + samples_to_do > self.number_samples:
                samples_to_do = self._total_samples - samples_written

            for chan in range(0, self._channels):
                temp = Procyon.decode(encoded, offset[chan],
                                      samples_to_do, self._channels, hist[chan])

                buffer[chan].extend(temp)
                length[chan] += len(temp)

                offset[chan] += int(self._block_size * self._channels)

            samples_written += samples_to_do

        if self._channels == 1:
            mus = buffer[0]
        else:
            mus = Helper.merge_channels(buffer[0], buffer[1])

        return mus

    def __encode(self, data: bytearray) -> bytearray:
        # TODO: Implement stereo
        if self.channels != 1:
            raise NotImplementedError("Only mono implemented")

        # TODO: Implement sample rate converter
        if self.sample_rate != 16362 and self.sample_rate != 32728:
            raise NotImplementedError("Only implemented sample rate 16364 and 32728.\n" +
                                      "This audio has {}. Please convert it.".format(self.sample_rate))

        # TODO: Implement sample bit converter
        if self.sample_bit_depth != 16:
            raise NotImplementedError("Only sample of 16 bits is allowed.\n" +
                                      "This audio has {}. Please convert it.".format(self.sample_bit_depth))

        # Force to use IMA ADPCM encoding since Procyon encoding has not been implemented yet.
        self.sadl.coding = Coding.INT_IMA
        encoded = ImaAdpcm.compress(data)

        self._block_size = self.sadl.interleave_block_size
        rest = len(encoded) % (self.sadl.interleave_block_size * 2)
        if rest != 0:
            encoded.extend(b"\x00"*((self.sadl.interleave_block_size * 2) - rest))

        return encoded

    def write_file(self, file_out: str, data: bytearray):
        bw = BinaryWriter(open(file_out, "wb"))
        br = BinaryReader(open(self._sound_file, "rb"))

        # Copy header from original file
        bw.write_bytearray(br.read_bytearray(0x100))

        # Write encoded data
        bw.write_bytearray(data)

        # Update header values
        # .. update file size
        bw.seek(0x40)
        bw.write_uint32(bw.length())

        # .. update channels
        bw.seek(0x32)
        bw.write_byte(self.channels)

        # ..update encoding and sample rate values
        bw.seek(0x33)
        br.seek(0x33)
        cod = br.read_byte()
        cod &= 0x09
        cod |= self.sadl.coding
        if self.sample_rate == 16364:
            cod |= 2
        else:
            cod |= 4
        bw.write_byte(cod)

        br.close()
        bw.close()
