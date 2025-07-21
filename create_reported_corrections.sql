DROP TABLE IF EXISTS reported_corrections;
CREATE TABLE reported_corrections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid,
    user_email text,
    input_sentence text NOT NULL, -- what the user typed
    correct_sentence text NOT NULL, -- the reference answer
    corrected_sentence text NOT NULL, -- the HTML-corrected version
    pinyin text,
    translation text, -- the English sentence
    created_at timestamptz NOT NULL DEFAULT now(),
    correction_html text NOT NULL
); 