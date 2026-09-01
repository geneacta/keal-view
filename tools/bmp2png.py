#!/usr/bin/env python3
"""bmp2png.py — turn a frame keal-view rendered offscreen into a PNG.

`kvSaveBmp` writes a BMP because a BMP is a header and the rows, and the
runtime has no business linking a compressor. This turns one into a PNG for
looking at, using nothing but the standard library.
"""
import struct, sys, zlib

def convert(src, dst):
    d = open(src, 'rb').read()
    off, = struct.unpack_from('<I', d, 10)
    w, h = struct.unpack_from('<ii', d, 18)
    bpp, = struct.unpack_from('<H', d, 28)
    if bpp != 32:
        raise SystemExit(f'{src}: expected 32 bits per pixel, found {bpp}')
    flip = h > 0                      # a positive height means bottom-up rows
    h = abs(h)
    rows = []
    for y in range(h):
        sy = (h - 1 - y) if flip else y
        r = d[off + sy * w * 4: off + (sy + 1) * w * 4]
        # BGRA in the file (little-endian 0xAARRGGBB) -> RGBA for the PNG
        rows.append(b'\x00' + bytes(v for i in range(w)
                                    for v in (r[i*4+2], r[i*4+1], r[i*4+0], 255)))
    raw = zlib.compress(b''.join(rows), 9)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c))

    png = (b'\x89PNG\r\n\x1a\n'
           + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
           + chunk(b'IDAT', raw) + chunk(b'IEND', b''))
    open(dst, 'wb').write(png)
    print(f'{dst}  {w}x{h}')

if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: bmp2png.py in.bmp out.png')
    convert(sys.argv[1], sys.argv[2])
