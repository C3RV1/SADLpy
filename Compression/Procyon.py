# Ported from: https://github.com/pleonex/tinke by Cervi for Team Top Hat

from cint.cint import I16, I32, I8
from Helper import Helper
from Compression.PCM import BitConverter


class Procyon:
    PROC_COEF = [bytearray(b"\x00\x00"),
                 bytearray(b"\x3c\x00"),
                 bytearray(b"\x73\xcc"),
                 bytearray(b"\x62\xc9"),
                 bytearray(b"\x7a\xc4")]

    @staticmethod
    def decode(decoded: bytearray, offset: int, samples_to_do: int, channels: int, hist: list) -> bytearray:
        buffer = bytearray()

        first_sample = I32(0)

        framesin = I32(first_sample // 30)

        pos = framesin * 0x10 + offset + 15
        header = I32(decoded[pos])
        header = header ^ 0x80
        scale = 12 - (header & 0xf)
        coef_index = (header >> 4) & 0xf
        hist1 = I32(hist[0])
        hist2 = I32(hist[1])

        if coef_index > 4:
            coef_index = 0
        coef1 = I8(Procyon.PROC_COEF[coef_index][0])
        coef2 = I8(Procyon.PROC_COEF[coef_index][1])
        first_sample = first_sample % 30

        for i in range(first_sample, first_sample + samples_to_do):
            pos = I32(framesin * 16 + offset + i // 2)
            sample_byte = I8(decoded[int(pos)] ^ 0x80)

            if i & 1 != 0:
                sample = I32(Helper.get_high_nibble_signed(int(sample_byte))) * 64 * 64
            else:
                sample = I32(Helper.get_low_nibble_signed(int(sample_byte))) * 64 * 64

            if scale < 0:
                sample <<= -scale
            else:
                sample >>= scale

            sample = I32(((hist1 * coef1 + hist2 * coef2 + 32) // 64) + (sample * 64))
            hist2 = hist1
            hist1 = sample

            clamp = I16(Helper.clamp16((sample + 32) // 64) // 64 * 64)

            buffer.extend(BitConverter.get_bytearray(clamp))

        hist[0] = hist1
        hist[1] = hist2

        return buffer
