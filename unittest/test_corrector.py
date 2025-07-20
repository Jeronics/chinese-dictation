import unittest
from dictation.corrector import Corrector

class TestCorrector(unittest.TestCase):
    def setUp(self):
        self.corrector = Corrector()

    def check(self, user_input, correct, expected_html):
        correction, *_ = self.corrector.compare(user_input, correct)
        self.assertEqual(correction, expected_html)

    def test_perfect_match(self):
        self.check('很久以前，有一个皇帝。', '很久以前，有一个皇帝。', '很久以前，有一个皇帝。')

    def test_missing_character(self):
        self.check('很久以前，有一个皇', '很久以前，有一个皇帝。', "很久以前，有一个皇<span class='diff-ins'>帝</span>")

    def test_extra_character(self):
        self.check('很久以前，有一个皇帝帝。', '很久以前，有一个皇帝。', "很久以前，有一个皇帝<span class='diff-del'>帝</span>。")

    def test_wrong_character(self):
        self.check('很久以前，有一个皇狗。', '很久以前，有一个皇帝。', "很久以前，有一个皇<span class='diff-del'>狗</span><span class='diff-ins'>帝</span>。")

    def test_missing_punctuation(self):
        self.check('很久以前有一个皇帝', '很久以前，有一个皇帝。', '很久以前，有一个皇帝。')

    def test_different_punctuation_type(self):
        self.check('很久以前,有一个皇帝。', '很久以前，有一个皇帝。', '很久以前，有一个皇帝。')

    def test_mismatched_punctuation(self):
        self.check('很，久以前有一个皇帝。', '很久以前，有一个皇帝。', '很久以前，有一个皇帝。')

    def test_extra_space(self):
        self.check('很久 以前，有一个皇帝。', '很久以前，有一个皇帝。', '很久以前，有一个皇帝。')

    def test_multiple_errors(self):
        self.check('很久以前有一个狗', '很久以前，有一个皇帝。', "很久以前，有一个<span class='diff-del'>狗</span><span class='diff-ins'>皇</span>帝。")

    def test_all_highlights(self):
        self.check('很久以前有一个狗帝帝', '很久以前，有一个皇帝。', "很久以前，有一个<span class='diff-del'>狗</span><span class='diff-ins'>皇</span>帝<span class='diff-del'>帝</span>。")


if __name__ == '__main__':
    unittest.main() 