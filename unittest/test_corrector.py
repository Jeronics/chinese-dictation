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
        self.check('很久以前有一个皇帝', '很久以前，有一个皇帝。', '很久以前有一个皇帝')

    def test_misplaced_punctuation(self):
        self.check('很久以前,有一个皇帝。', '很久以前，有一个皇帝。', '很久以前,有一个皇帝。')

    def test_multiple_errors(self):
        self.check('很久以前有一个狗', '很久以前，有一个皇帝。', "很久以前有一个<span class='diff-del'>狗</span><span class='diff-ins'>皇</span>")

    def test_all_highlights(self):
        self.check('很久以前有一个狗帝帝', '很久以前，有一个皇帝。', "很久以前有一个<span class='diff-del'>狗</span><span class='diff-ins'>皇</span>帝<span class='diff-del'>帝</span>")

    # Latin alphabet tests
    def test_latin_perfect_match(self):
        self.check('Hello world!', 'Hello world!', 'Hello world!')

    def test_latin_missing_character(self):
        self.check('Hello wrld', 'Hello world!', "Hello wrld<span class='diff-ins'>o</span>")

    def test_latin_wrong_character(self):
        self.check('Hello wold', 'Hello world!', "Hello wold<span class='diff-ins'>r</span>")

    def test_latin_extra_character(self):
        self.check('Hello worldd!', 'Hello world!', "Hello world<span class='diff-del'>d</span>!")

    def test_latin_missing_punctuation(self):
        self.check('Hello world', 'Hello world!', 'Hello world')

    def test_latin_extra_punctuation(self):
        self.check('Hello world!!', 'Hello world!', 'Hello world!!')

    def test_latin_numbers(self):
        self.check('I have 3 cats', 'I have 4 cats', "I have <span class='diff-del'>3</span><span class='diff-ins'>4</span> cats")

    def test_latin_pinyin(self):
        self.check('Ni hao', 'Ni hao!', 'Ni hao')

if __name__ == '__main__':
    unittest.main() 