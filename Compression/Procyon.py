# Ported from: https://github.com/pleonex/tinke by Cervi for Team Top Hat

from Helper import Helper
from Compression.PCM import BitConverter


class Procyon:
    PROC_COEF = [bytearray(b"\x00\x00"),
                 bytearray(b"\x3c\x00"),
                 bytearray(b"\x73\xcc"),
                 bytearray(b"\x62\xc9"),
                 bytearray(b"\x7a\xc4")]

    @staticmethod
    def decode(decoded: bytearray, offset: int, samples_to_do: int, channels: int, hist: list) -> tuple:
        buffer = bytearray()

        first_sample = 0

        framesin = int(first_sample / 30)

        pos = framesin * 16 + 15 + offset
        header = decoded[pos]
        header = header ^ 80
        scale = 12 - (header & 0xf)
        coef_index = (header >> 4) & 0xf
        hist1 = hist[0]
        hist2 = hist[1]

        if coef_index > 4:
            coef_index = 0
        coef1 = Procyon.PROC_COEF[coef_index][0]
        coef2 = Procyon.PROC_COEF[coef_index][1]
        first_sample = first_sample % 30

        sample_count = 0
        for i in range(first_sample, first_sample + samples_to_do):
            pos = int(framesin * 16 + offset + i / 2)
            sample_byte = decoded[pos] ^ 0x80

            if i & 1 != 0:
                sample = Helper.get_high_nibble_signed(sample_byte)
            else:
                sample = Helper.get_low_nibble_signed(sample_byte)

            if scale < 0:
                sample <<= -scale
            else:
                sample >>= scale

            sample = (hist1 * coef1 + hist2 * coef2 + 32) / 64 + (sample * 64)
            hist2 = hist1
            hist1 = sample

            clamp = Helper.clamp16((sample + 32) / 64) / 64 * 64
            buffer.extend(BitConverter.get_bytearray(clamp))

            sample_count += channels

        return buffer, [hist1, hist2]
