"""
Unit tests for the spatialmedia CLI tool.

# Test inputs are generated with
ffmpeg -y -f lavfi -i testsrc -vf scale=320:240 -vcodec libx264 -t 0.05 data/testsrc_320x240_h264.mp4
ffmpeg -y -f lavfi -i testsrc -vf scale=320:240 -vcodec libvpx-vp9 -t 0.05 data/testsrc_320x240_vp9.mp4
ffmpeg -y -f lavfi -i testsrc -vf scale=32:24 -vcodec prores -t 0.05 data/testsrc_32x24_prores.mov

"""
import unittest
import os

from spatialmedia.__main__ import main
from spatialmedia import metadata_utils

_OUTPUT_DIR = 'test_output'

def append_contents(contents):
    def append(x):
        contents = contents + x
    return append

class TestAdd(unittest.TestCase):

    def inject_metadata(self, args):
        self.assertIsNone(main(args))

        contents = []
        metadata_utils.parse_metadata(args[-1],
                                      lambda x: contents.append(x))
        try:
            os.remove(args[-1])
        except:
            return ''
        return '\n'.join(contents[2:])

    def test_inject_v1_equirect_mono(self):
        contents = self.inject_metadata(['-i',
                                         '--projection', 'equirectangular',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono_v1.mp4'])

        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find("ProjectionType = equirectangular") > 0)

    def test_inject_v1_rectangular_left_right(self):
        contents = self.inject_metadata(['-i',
                                         '--stereo', 'left-right',
                                         '--projection', 'none',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/rectangular_left_right_v1.mp4'])

        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertFalse(contents.find("ProjectionType = equirectangular") > 0)
        self.assertTrue(contents.find("ProjectionType = rectangular") > 0)
        self.assertTrue(contents.find("Spherical = false") > 0)

    def test_inject_v2_equirect_mono(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--projection', 'equirectangular',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono.mp4'])
        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Bounds Top: 0') >= 0)
        self.assertTrue(contents.find('Bounds Bottom: 0') >= 0)
        self.assertTrue(contents.find('Bounds Left: 0') >= 0)
        self.assertTrue(contents.find('Bounds Right: 0') >= 0)

    def test_inject_v2_equirect_mono_with_bounds(self):
        contents = self.inject_metadata(['-i',
                                         '--v2',
                                         '--bounds', '0x1:-2:0x7FFFFFFF:32',
                                         '--projection', 'equirectangular',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono.mp4'])
        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Bounds Top: 1') >= 0)
        self.assertTrue(contents.find('Bounds Bottom: 0') >= 0)
        self.assertTrue(contents.find('Bounds Left: 2147483647') >= 0)
        self.assertTrue(contents.find('Bounds Right: 32') >= 0)

    def test_inject_v2_equirect_mono_vp9(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--projection', 'equirectangular',
                                         'data/testsrc_320x240_vp9.mp4',
                                         f'{_OUTPUT_DIR}/equirect_mono_vp9.mp4'])

        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)

    def test_inject_v2_equirect_mono_prores(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--projection', 'equirectangular',
                                         'data/testsrc_32x24_prores.mov',
                                         f'{_OUTPUT_DIR}/equirect_mono_prores.mov'])
        self.assertTrue(contents.find('SV3D') >= 0)
        self.assertTrue(contents.find('PRHD') >= 0)
        self.assertTrue(contents.find('EQUI') >= 0)
        self.assertFalse(contents.find('ST3D') >= 0)


    def test_inject_v2_rectangular_left_right(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--stereo', 'left-right',
                                         '--projection', 'none',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/rectangular_left_right.mp4'])
        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertTrue(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Stereo Mode: 2') >= 0)

    def test_inject_v2_rectangular_top_bottom(self):
        contents = self.inject_metadata(['-i',
                                         '--v2', '--stereo', 'top-bottom',
                                         '--projection', 'none',
                                         'data/testsrc_320x240_h264.mp4',
                                         f'{_OUTPUT_DIR}/rectangular_top_bottom.mp4'])

        self.assertFalse(contents.find('SV3D') >= 0)
        self.assertFalse(contents.find('PRHD') >= 0)
        self.assertFalse(contents.find('EQUI') >= 0)
        self.assertTrue(contents.find('ST3D') >= 0)
        self.assertTrue(contents.find('Stereo Mode: 1') >= 0)


if __name__ == '__main__':
    try:
        os.mkdir('test_output')
    except:
        pass
    unittest.main()
