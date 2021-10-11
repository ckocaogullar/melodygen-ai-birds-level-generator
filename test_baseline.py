import unittest
import baseline
from baseline import all_tone_check, tonal_tone_check, double_note_check,\
    rest_check, durat_normalizer, freq_normalizer, find_freq_ceil

class TestBaseline(unittest.TestCase):
    
    def test_all_tone_check(self):
        baseline.is_minor = False
        baseline.is_major = False
        baseline.is_atonal = False
        self.assertRaises(ValueError, all_tone_check)
        
    def test_tonal_tone_check(self):
        baseline.is_minor = True
        baseline.is_major = True
        self.assertRaises(ValueError, tonal_tone_check)
        
    
    def test_double_note_check(self):
        baseline.double_prob_percentage = -1
        self.assertRaises(ValueError, double_note_check)
        
        baseline.double_prob_percentage = 101
        self.assertRaises(ValueError, double_note_check)
        
    def test_rest_check(self):
        baseline.rest_percentage = 15
        self.assertRaises(ValueError, rest_check)
        
        baseline.rest_percentage = -1
        self.assertRaises(ValueError, rest_check)
        
        baseline.rest_percentage = 101
        self.assertRaises(ValueError, rest_check)
        
        
    def test_durat_normalizer(self):
        self.assertRaises(ValueError, durat_normalizer, -1)
        
    def test_freq_normalizer(self):
        self.assertEqual(0, freq_normalizer(0, 0))
        self.assertIsInstance(freq_normalizer([0, 1], 0), list)
        self.assertIsInstance(freq_normalizer(1, 0), float)
        