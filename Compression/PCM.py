# Ported from: https://github.com/pleonex/tinke by Cervi for Team Top Hat

import struct


class BitConverter:
    @staticmethod
    def to_int_16(bytearray_: bytearray, b: int) -> int:
        return struct.unpack("h", bytearray_[b:b+2])[0]

    @staticmethod
    def get_bytearray(short) -> bytearray:
        return bytearray(struct.pack("h", short))


class PCM:
    @staticmethod
    def pcm8signed_to_pcm16(data: bytearray) -> bytearray:
        results = bytearray()
        data = PCM.bit8_to_bit16(data)

        for i in range(0, len(data), 2):
            sample = BitConverter.to_int_16(data, i)
            pcm16 = sample & 0x7f
            pcm16 <<= 8
            if sample >> 7 != 0:
                pcm16 -= 0x7fff

            results += BitConverter.get_bytearray(pcm16)

        return results

    @staticmethod
    def pcm8unsigned_to_pcm16(data: bytearray) -> bytearray:
        results = bytearray()
        data = PCM.bit8_to_bit16(data)

        for i in range(0, len(data), 2):
            sample = BitConverter.to_int_16(data, i)
            pcm16 = sample & 0xff
            pcm16 <<= 8
            pcm16 += 0x7fff

            results += BitConverter.get_bytearray(pcm16)

        return results

    @staticmethod
    def pcm16_to_pcm8(data: bytearray) -> bytearray:
        results = bytearray()

        for i in range(0, len(data), 2):
            pcm16 = BitConverter.to_int_16(data, i)
            negative = bool(pcm16 < 0)
            if negative:
                pcm16 += 0x7fff
            pcm16 >>= 8
            if negative:
                pcm16 += 0x80
            results += pcm16

        return results

    @staticmethod
    def bit8_to_bit16(data: bytearray) -> bytearray:
        results = bytearray()

        for i in range(0, len(data)):
            results += BitConverter.get_bytearray(data[i])

        return results
