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

        # If the user input is completely different (very low similarity), 
        # show the wrong input in red and the correct in blue
        if len(s_user) == 0:
            # User input is empty or only punctuation
            result = f"<span class='diff-ins'>{correct}</span>"
            return result, s_user, s_correct, ""
        
        # Calculate similarity
        matcher = difflib.SequenceMatcher(None, s_user, s_correct)
        similarity = matcher.ratio()
        
        # If similarity is very low (< 0.3), treat as completely wrong
        if similarity < 0.3:
            # Show user input in red, correct in blue
            result = f"<span class='diff-del'>{user_input}</span><span class='diff-ins'>{correct}</span>"
            return result, s_user, s_correct, ""

        matcher = difflib.SequenceMatcher(None, s_user, s_correct)
        
        # Create a list of operations with their positions
        operations = []
        ui = 0
        ci = 0
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    operations.append(('equal', user_map[ui + k], correct_map[ci + k]))
                ui += (i2 - i1)
                ci += (j2 - j1)
            elif tag == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                    u_idx = user_map[ui + k] if (ui + k) < len(user_map) else None
                    c_idx = correct_map[ci + k] if (ci + k) < len(correct_map) else None
                    operations.append(('replace', u_idx, c_idx))
                ui += (i2 - i1)
                ci += (j2 - j1)
            elif tag == 'insert':
                for k in range(j2 - j1):
                    c_idx = correct_map[ci + k]
                    operations.append(('insert', None, c_idx))
                ci += (j2 - j1)
            elif tag == 'delete':
                for k in range(i2 - i1):
                    u_idx = user_map[ui + k]
                    operations.append(('delete', u_idx, None))
                ui += (i2 - i1)

        # Build the result by walking through the user input and mapping to correct
        result = ''
        correct_segments = []
        u_pos = 0
        c_pos = 0
        op_idx = 0
        
        # Create a mapping of user positions to operations
        user_ops = {}
        for op, u_idx, c_idx in operations:
            if u_idx is not None:
                user_ops[u_idx] = (op, u_idx, c_idx)
        
        # Walk through the user input
        while u_pos < len(user_input):
            ch = user_input[u_pos]
            
            # If it's punctuation/space, just add it
            if is_punct_or_space(ch):
                result += ch
                u_pos += 1
                continue
            
            # Check if there's an operation for this user position
            if u_pos in user_ops:
                op, u_idx, c_idx = user_ops[u_pos]
                
                if op == 'equal':
                    result += ch
                    correct_segments.append(ch)
                elif op == 'replace':
                    c_char = correct[c_idx] if c_idx is not None else ''
                    result += f"<span class='diff-del'>{ch}</span><span class='diff-ins'>{c_char}</span>"
                elif op == 'delete':
                    result += f"<span class='diff-del'>{ch}</span>"
                u_pos += 1
            else:
                # No operation for this position, just add the character
                result += ch
                u_pos += 1
        
        # Handle any insertions (missing characters)
        insert_ops = [(op, u_idx, c_idx) for op, u_idx, c_idx in operations if op == 'insert']
        insert_ops.sort(key=lambda x: x[2])  # Sort by correct position
        
        # Insert missing characters at the appropriate positions
        for op, u_idx, c_idx in insert_ops:
            c_char = correct[c_idx]
            # Find the right position to insert
            # For now, we'll add them at the end, but ideally we'd find the right position
            result += f"<span class='diff-ins'>{c_char}</span>"
        
        return result, s_user, s_correct, ''.join(correct_segments)

