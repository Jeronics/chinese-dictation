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
        def is_punct_or_space(ch):
            return unicodedata.category(ch).startswith('P') or ch.isspace()

        def strip_and_map(text):
            stripped = []
            mapping = []
            for idx, ch in enumerate(text):
                if not is_punct_or_space(ch):
                    stripped.append(ch)
                    mapping.append(idx)
            return ''.join(stripped), mapping

        s_user, user_map = strip_and_map(user_input)
        s_correct, correct_map = strip_and_map(correct)
        n, m = len(s_user), len(s_correct)
        # DP table for Levenshtein
        dp = [[0] * (m+1) for _ in range(n+1)]
        for i in range(n+1): dp[i][0] = i
        for j in range(m+1): dp[0][j] = j
        for i in range(1, n+1):
            for j in range(1, m+1):
                if s_user[i-1] == s_correct[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j],    # deletion
                                       dp[i][j-1],    # insertion
                                       dp[i-1][j-1])  # substitution
        # Backtrack to get alignment
        i, j = n, m
        ops = []
        while i > 0 or j > 0:
            if i > 0 and j > 0 and s_user[i-1] == s_correct[j-1]:
                ops.append(('equal', i-1, j-1))
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                ops.append(('replace', i-1, j-1))
                i -= 1
                j -= 1
            elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
                ops.append(('insert', None, j-1))
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + 1:
                ops.append(('delete', i-1, None))
                i -= 1
        ops = ops[::-1]
        # Build result with correct sentence's punctuation/space
        result = ''
        correct_segments = []
        u_ptr = 0
        c_ptr = 0
        op_ptr = 0
        # Map from stripped to original indices
        while c_ptr < len(correct):
            if is_punct_or_space(correct[c_ptr]):
                result += correct[c_ptr]
                c_ptr += 1
                continue
            # Find op for this char
            if op_ptr < len(ops):
                op, u_idx, c_idx = ops[op_ptr]
                if c_idx is not None and correct_map[c_idx] != c_ptr:
                    # This op is for a later char, so just output correct char
                    result += correct[c_ptr]
                    c_ptr += 1
                    continue
                if op == 'equal':
                    result += f"<span class='diff-correct'>{user_input[user_map[u_idx]]}</span>"
                    correct_segments.append(user_input[user_map[u_idx]])
                    u_ptr = user_map[u_idx] + 1
                    c_ptr += 1
                elif op == 'replace':
                    result += f"<span class='diff-del'>{user_input[user_map[u_idx]]}</span>"
                    result += f"<span class='diff-ins'>{correct[c_ptr]}</span>"
                    u_ptr = user_map[u_idx] + 1
                    c_ptr += 1
                elif op == 'insert':
                    result += f"<span class='diff-ins'>{correct[c_ptr]}</span>"
                    c_ptr += 1
                elif op == 'delete':
                    result += f"<span class='diff-extra'>{user_input[user_map[u_idx]]}</span>"
                    u_ptr = user_map[u_idx] + 1
                op_ptr += 1
            else:
                # No more ops, just output remaining correct chars
                result += correct[c_ptr]
                c_ptr += 1
        return result, s_user, s_correct, ''.join(correct_segments)

