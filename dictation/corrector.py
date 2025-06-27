import unicodedata, difflib

class Corrector:
    def strip(self, text):
        return ''.join(ch for ch in text if not unicodedata.category(ch).startswith('P') and not ch.isspace())

    def levenshtein(self, s1, s2):
        dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
        for i in range(len(s1) + 1): dp[i][0] = i
        for j in range(len(s2) + 1): dp[0][j] = j
        for i in range(1, len(s1) + 1):
            for j in range(1, len(s2) + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
        return dp[-1][-1]

    def compare(self, user_input, correct):
        s_user = self.strip(user_input)
        s_correct = self.strip(correct)
        matcher = difflib.SequenceMatcher(None, s_user, s_correct)
        result, ui, ci = "", 0, 0
        correct_segments = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                equal_text = correct[ci:j2]
                result += equal_text
                correct_segments.append(equal_text)
            elif tag == 'replace':
                for k in range(j2 - j1):
                    u = user_input[ui + k] if ui + k < len(user_input) else ""
                    c = correct[ci + k] if ci + k < len(correct) else ""
                    result += f"<span class='diff-del'><del>{u}</del></span><span class='diff-ins'>{c}</span>"
            elif tag == 'insert':
                result += f"<span class='diff-ins'>{correct[ci:j2]}</span>"
            elif tag == 'delete':
                result += f"<span class='diff-del'><del>{user_input[ui:i2]}</del></span>"
            ui += (i2 - i1)
            ci += (j2 - j1)
        return result, s_user, s_correct, "".join(correct_segments)

