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
        # Helper to check if a char is punctuation or space
        def is_punct_or_space(ch):
            return unicodedata.category(ch).startswith('P') or ch.isspace()

        # Build stripped versions and mapping to original indices
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

        matcher = difflib.SequenceMatcher(None, s_user, s_correct)
        # Build a list of (type, user_idx, correct_idx, user_char, correct_char)
        diff_ops = []
        ui = 0
        ci = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    diff_ops.append(('equal', user_map[ui], correct_map[ci], user_input[user_map[ui]], correct[correct_map[ci]]))
                    ui += 1
                    ci += 1
            elif tag == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                    u_idx = user_map[ui + k] if (ui + k) < len(user_map) else None
                    c_idx = correct_map[ci + k] if (ci + k) < len(correct_map) else None
                    u_char = user_input[u_idx] if u_idx is not None else ''
                    c_char = correct[c_idx] if c_idx is not None else ''
                    diff_ops.append(('replace', u_idx, c_idx, u_char, c_char))
                ui += (i2 - i1)
                ci += (j2 - j1)
            elif tag == 'insert':
                for k in range(j2 - j1):
                    c_idx = correct_map[ci + k]
                    c_char = correct[c_idx]
                    diff_ops.append(('insert', None, c_idx, '', c_char))
                ci += (j2 - j1)
            elif tag == 'delete':
                for k in range(i2 - i1):
                    u_idx = user_map[ui + k]
                    u_char = user_input[u_idx]
                    diff_ops.append(('delete', u_idx, None, u_char, ''))
                ui += (i2 - i1)

        # Now, build the output, walking through the correct sentence and inserting highlights only for Hanzi/letters/numbers
        result = ''
        correct_segments = []
        op_idx = 0
        c_len = len(correct)
        c_pos = 0
        while c_pos < c_len:
            ch = correct[c_pos]
            if is_punct_or_space(ch):
                result += ch
                c_pos += 1
                continue
            # Find the next diff_op that matches this correct char position
            if op_idx < len(diff_ops):
                op, u_idx, c_idx, u_char, c_char = diff_ops[op_idx]
                if c_idx == c_pos:
                    if op == 'equal':
                        result += ch
                        correct_segments.append(ch)
                    elif op == 'replace':
                        # Show user wrong char in red, correct char in blue
                        result += f"<span class='diff-del'>{u_char}</span><span class='diff-ins'>{c_char}</span>"
                    elif op == 'insert':
                        # Missing char in blue
                        result += f"<span class='diff-ins'>{c_char}</span>"
                    # For delete, nothing to add here (handled below)
                    op_idx += 1
                    c_pos += 1
                else:
                    # This char is not part of the diff (shouldn't happen), just add it
                    result += ch
                    c_pos += 1
            else:
                # No more diff_ops, just add the rest
                result += ch
                c_pos += 1
        # Handle any trailing deletes (extra chars at end of user input)
        while op_idx < len(diff_ops):
            op, u_idx, c_idx, u_char, c_char = diff_ops[op_idx]
            if op == 'delete':
                result += f"<span class='diff-del'>{u_char}</span>"
            op_idx += 1
        return result, s_user, s_correct, ''.join(correct_segments)

