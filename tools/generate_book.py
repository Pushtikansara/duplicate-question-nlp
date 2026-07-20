"""Generate a beautifully formatted DOCX book: Cross Encoders from Zero to Research Level."""

import os

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Cm, Pt, RGBColor

doc = Document()

# ── Page Setup ──────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(2.54)
    section.right_margin = Cm(2.54)

# ── Style Definitions ───────────────────────────────────────────
style = doc.styles["Normal"]
font = style.font
font.name = "Calibri"
font.size = Pt(11)
style.paragraph_format.space_after = Pt(6)
style.paragraph_format.line_spacing = 1.15

for level in range(1, 5):
    h = doc.styles[f"Heading {level}"]
    h.font.name = "Calibri"
    h.font.color.rgb = RGBColor(0x1B, 0x3A, 0x5C)

doc.styles["Heading 1"].font.size = Pt(22)
doc.styles["Heading 2"].font.size = Pt(16)
doc.styles["Heading 3"].font.size = Pt(13)
doc.styles["Heading 4"].font.size = Pt(11)

# Code style
code_style = doc.styles.add_style("Code", WD_STYLE_TYPE.PARAGRAPH)
code_font = code_style.font
code_font.name = "Consolas"
code_font.size = Pt(9)
code_font.color.rgb = RGBColor(0x2D, 0x2D, 0x2D)
code_style.paragraph_format.space_before = Pt(2)
code_style.paragraph_format.space_after = Pt(2)
code_style.paragraph_format.line_spacing = 1.0


# ── Helper Functions ────────────────────────────────────────────
def add_code_block(doc, code_text):
    """Add a code block with light grey background via table."""
    lines = code_text.strip().split("\n")
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    cell = table.cell(0, 0)
    cell.text = ""
    for i, line in enumerate(lines):
        if i > 0:
            cell.add_paragraph("").text = ""
        cell.add_paragraph(line, style="Code")
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
    cell._tc.get_or_add_tcPr().append(shading)
    doc.add_paragraph("")  # spacing after


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.left_indent = Cm(1.27 + level * 0.63)
    return p


def add_table(doc, headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            table.rows[ri + 1].cells[ci].text = str(val)
    doc.add_paragraph("")


def add_separator(doc):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("─" * 60)
    run.font.color.rgb = RGBColor(0xAA, 0xAA, 0xAA)
    run.font.size = Pt(8)


# ══════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════
for _ in range(6):
    doc.add_paragraph("")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("CROSS ENCODERS")
run.font.size = Pt(36)
run.font.color.rgb = RGBColor(0x1B, 0x3A, 0x5C)
run.bold = True

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("From Absolute Beginner to Research Level")
run.font.size = Pt(18)
run.font.color.rgb = RGBColor(0x55, 0x7A, 0x95)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("With Applications to Duplicate Question Detection")
run.font.size = Pt(14)
run.font.color.rgb = RGBColor(0x77, 0x77, 0x77)
run.italic = True

doc.add_paragraph("")
doc.add_paragraph("")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("Om Mistry  •  Disu Makadiya  •  Pushti Kansara")
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (manual)
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Table of Contents", level=1)
toc_items = [
    ("Part 1: Why Cross Encoder Exists", 2),
    ("Part 2: Transformers Recap", 3),
    ("Part 3: Inside a Cross Encoder", 4),
    ("Part 4: Tokenization in Detail", 5),
    ("Part 5: Attention Mathematics", 6),
    ("Part 6: Why Cross Encoder is Different", 7),
    ("Part 7: The [CLS] Token", 8),
    ("Part 8: Classification Head", 9),
    ("Part 9: Training Pipeline", 10),
    ("Part 10: Your Project in Detail", 11),
    ("Part 11: Visualizations", 12),
    ("Part 12: Common Mistakes", 13),
    ("Part 13: Advanced Topics", 14),
    ("Part 14: Research Level", 15),
    ("Part 15: Code Walkthrough", 16),
]
for title, page in toc_items:
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.font.size = Pt(11)
    p.add_run(f"  {'.' * (60 - len(title))}  {page}").font.size = Pt(9)

doc.add_page_break()


# ══════════════════════════════════════════════════════════════════
# PART 1
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 1: Why Cross Encoder Exists", level=1)

doc.add_heading("The Problem: Semantic Similarity", level=2)
doc.add_paragraph(
    "You have two questions:\n\n"
    'Q1: "What is Artificial Intelligence?"\n'
    'Q2: "Explain AI."\n\n'
    "A human instantly knows these are duplicates. They ask the same thing. "
    "But to a computer, these are just strings of characters. The character-level "
    'overlap is minimal: "What is Artificial Intelligence?" ∩ "Explain AI." = { }'
)
doc.add_paragraph(
    "Lexical similarity (matching exact words) gives zero. But semantic similarity — the meaning — is high."
)

doc.add_heading("Bi-Encoder: The First Solution", level=2)
doc.add_paragraph("A Bi-Encoder is a two-tower architecture. Two identical transformers run independently:")
add_code_block(
    doc,
    """Q1 → Transformer → Vector A (768-dim)
Q2 → Transformer → Vector B (768-dim)
Similarity = cosine(A, B)""",
)
doc.add_paragraph(
    "Why Bi-Encoder was invented: To solve the scalability problem. If you have 10 million "
    "questions and want to find duplicates for a new question, you can: (1) encode all 10M "
    "questions once offline, (2) encode the new question fast, (3) compare the new vector "
    "against all 10M with cosine similarity using FAISS."
)
doc.add_paragraph(
    "What Bi-Encoder solves: It makes semantic search feasible at scale by decoupling encoding from comparison."
)
doc.add_paragraph(
    "What Bi-Encoder cannot solve: The two questions never see each other. They are encoded "
    'independently. Each word in Q1 only attends to words in Q1. The word "Explain" in Q2 never '
    'knows that "What is" in Q1 expresses the same intent.'
)

doc.add_heading("Why Cosine Similarity Alone Sometimes Fails", level=2)
add_bullet(doc, 'Homonyms: "What is Python?" could mean snake vs language. Both get the same vector.')
add_bullet(
    doc,
    'Negation: "How to enable notifications" vs "How to disable notifications" — very similar vectors but opposite meanings.',
)
add_bullet(
    doc, 'Fine-grained distinctions: "What is the best GPU for gaming?" vs "What is the best GPU for deep learning?"'
)

doc.add_heading("Cross-Encoder: The Precision Solution", level=2)
doc.add_paragraph("A Cross-Encoder processes both questions together through a single transformer:")
add_code_block(
    doc,
    """[CLS] What is Artificial Intelligence? [SEP] Explain AI. [SEP]
                    ↓
              One Transformer
                    ↓
           Classification Head
                    ↓
           Probability: 0.97""",
)
doc.add_paragraph(
    "Why Cross-Encoder was invented: Because Bi-Encoder loses the interaction between the two "
    "texts. The Cross-Encoder allows every word in Q1 to attend to every word in Q2 through "
    'self-attention. "Explain" can directly attend to "What is" and learn they express the same intent.'
)

doc.add_heading("When Each is Better", level=2)
add_table(
    doc,
    ["Property", "Bi-Encoder", "Cross-Encoder"],
    [
        ["Accuracy", "Good", "Excellent"],
        ["Speed per pair", "Fast (~1ms)", "Slow (10-100ms)"],
        ["Scalability", "Billion-scale", "Thousand-scale"],
        ["Cross-attention", "No", "Yes"],
        ["Training", "Contrastive loss", "Classification loss"],
    ],
)

doc.add_paragraph(
    "In your project, the Cross-Encoder serves as the reranker: the ensemble uses it when "
    "the Bi-Encoders disagree or when the lexical model signals uncertainty."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 2
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 2: Transformers Recap", level=1)
doc.add_paragraph(
    "You need to understand every layer of a Transformer because a Cross-Encoder IS a Transformer "
    'with a classification head on top. There is no architectural difference. The "cross-encoding" '
    "comes from how you format the input."
)

doc.add_heading("2.1 Embedding Layer", level=2)
doc.add_paragraph(
    "Input: token IDs (integers). Each ID maps to a row in a matrix:\n\n"
    "Embedding Matrix: [vocab_size × hidden_dim] = [128000 × 768]\n\n"
    "token_id=101 maps to row 101 of this matrix, giving a 768-dimensional vector. "
    "The embedding layer is a lookup table. It is the only place where tokens become vectors."
)

doc.add_heading("2.2 Tokenization", level=2)
doc.add_paragraph("Tokenization converts text into token IDs:")
add_code_block(
    doc,
    """"What is Artificial Intelligence?"
    ↓ WordPiece/BPE Tokenizer
["What", "is", "Artificial", "Intelligence", "?"]
    ↓
[2054, 2003, 19204, 1385, 1029]""",
)
doc.add_paragraph(
    "DeBERTa-v3 uses SentencePiece (unlike BERT which uses WordPiece). SentencePiece treats "
    "the entire text as a raw byte stream, including spaces. Vocabulary size: ~128,000."
)

doc.add_heading("2.3 Special Tokens", level=2)
add_table(
    doc,
    ["Token", "DeBERTa ID", "BERT ID", "Purpose"],
    [
        ["[CLS]", "1", "101", "Classification token — aggregates sequence info"],
        ["[SEP]", "2", "102", "Separator between sentences"],
        ["[PAD]", "0", "0", "Padding to max length"],
        ["[MASK]", "128000", "103", "Masked token for pre-training"],
    ],
)

doc.add_heading("2.4 Position Embeddings", level=2)
doc.add_paragraph(
    "Transformers have no inherent notion of word order. Position embeddings inject sequence position: "
    'Position 0 → pos_embedding[0] (for [CLS]), Position 1 → pos_embedding[1] (for "What"), etc.\n\n'
    "DeBERTa is different: It uses relative position instead of absolute position. The positions "
    "are encoded in the attention mechanism itself (disentangled attention). This allows the model "
    "to know how far apart two tokens are, not just their absolute positions."
)

doc.add_heading("2.5 The Complete Embedding", level=2)
doc.add_paragraph("final_embedding[i] = token_embedding[token_id[i]] + position_embedding[i]")
doc.add_paragraph(
    "Note: DeBERTa does not use token type (segment) embeddings. It relies on relative position encoding."
)

doc.add_heading("2.6 Attention (Single Head)", level=2)
doc.add_paragraph("The core mechanism. Every token can look at every other token.")
add_code_block(
    doc,
    """Attention(Q, K, V) = softmax(Q × K^T / √d_k) × V

Q = X × W_Q    (Query: What is this token looking for?)
K = X × W_K    (Key: What information does this token have?)
V = X × W_V    (Value: The actual information content)""",
)
doc.add_paragraph(
    'For "Explain" in Q2 to attend to "What is" in Q1:\n'
    '1. "Explain" generates a Query vector\n'
    '2. "What", "is", "Artificial", "Intelligence" generate Key vectors\n'
    "3. Dot product between Query(Explain) and each Key\n"
    "4. High dot product = high attention weight\n"
    '5. Weighted sum of Value vectors gives the context-aware representation of "Explain"\n\n'
    'This is why Cross-Encoder works: "Explain" can directly attend to every word in Q1.'
)

doc.add_heading("2.7 Multi-Head Attention", level=2)
doc.add_paragraph("One head learns one type of relationship. Multiple heads learn different types simultaneously:")
add_code_block(
    doc,
    """MultiHead(Q,K,V) = Concat(head_1, ..., head_h) × W_O
head_i = Attention(Q×W_Q_i, K×W_K_i, V×W_V_i)""",
)
doc.add_paragraph(
    "DeBERTa-v3-base: 12 heads, each with d_k = 64 (12 × 64 = 768 = hidden_dim).\n\n"
    "Each head can specialize:\n"
    "• Head 1: Syntactic relationships (subject-verb)\n"
    '• Head 2: Semantic similarity ("Explain" ↔ "What is")\n'
    '• Head 3: Abbreviation recognition ("AI" ↔ "Artificial Intelligence")\n'
    '• Head 4: Negation detection ("enable" vs "disable")\n'
    "• Heads 5-12: Various linguistic patterns"
)

doc.add_heading("2.8 Feed-Forward Network", level=2)
add_code_block(
    doc,
    """FFN(x) = GELU(x × W_1 + b_1) × W_2 + b_2
W_1: [768 × 3072]   (4× expansion)
W_2: [3072 × 768]""",
)

doc.add_heading("2.9 Residual Connections + LayerNorm", level=2)
add_code_block(
    doc,
    """output = LayerNorm(x + Attention(x))
output = LayerNorm(output + FFN(output))""",
)
doc.add_paragraph(
    "Residual connection (x + ...): Allows gradients to flow directly through the network without vanishing.\n"
    "LayerNorm: Normalizes across the hidden dimension to stabilize training."
)

doc.add_heading("2.10 Encoder Stack", level=2)
doc.add_paragraph(
    "Layer 0: Embedding\n"
    "Layer 1-12: Attention + FFN + Residual + LayerNorm\n\n"
    "Each layer builds on the previous:\n"
    "• Early layers: Capture surface patterns (word pairs, local syntax)\n"
    "• Middle layers: Capture semantic roles\n"
    "• Late layers: Capture high-level meaning and cross-sentence relationships"
)

doc.add_heading("2.11 Contextual Embeddings", level=2)
doc.add_paragraph(
    'Unlike static word embeddings (Word2Vec, GloVe) where "bank" always has the same vector, '
    "contextual embeddings change based on context:\n"
    '• "river bank" → bank attends to river → different vector\n'
    '• "money bank" → bank attends to money\n\n'
    'In your Cross-Encoder, "AI" in Q2 attends to "Artificial Intelligence" in Q1. '
    'The vector for "AI" becomes more similar to "Artificial Intelligence" because attention allows it.'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 3
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 3: Inside a Cross Encoder", level=1)

doc.add_heading("The Complete Pipeline", level=2)
add_code_block(
    doc,
    """Question 1: "What is Artificial Intelligence?"
Question 2: "Explain AI."

         ↓
normalize_question (abbreviation expansion, typo fix, lowercase)
         ↓
Q1': "what is artificial intelligence (artificial intelligence)"
Q2': "explain ai. (artificial intelligence)"
         ↓
Tokenizer (SentencePiece for DeBERTa-v3)
         ↓
[CLS] what is artificial intelligence ( artificial intelligence ) [SEP]
explain ai. ( artificial intelligence ) [SEP]
         ↓
Token IDs: [1, 10534, 322, 16723, 5826, 7, 16723, 5826, 8, 2,
            8192, 365, 5, 7, 16723, 5826, 8, 2]
         ↓
Embedding Matrix (128000 × 768 lookup) → [18 × 768]
         ↓
Layer 1-12: Multi-Head Self-Attention + FFN
    "explain" attends to "what", "is", "artificial intelligence", "ai"
    → contextualized representation for every token
         ↓
Final Hidden State: [18 × 768]
         ↓
Extract [CLS] vector (position 0): [1 × 768]
         ↓
Classification Head: Linear(768 → 2) → logits: [-3.2, 1.8]
Softmax → [0.0067, 0.9933]
         ↓
Probability: 0.9933 (duplicate)""",
)

doc.add_heading("Why This Works", level=2)
doc.add_paragraph(
    "Every token in Q2 attends to every token in Q1 through all 12 layers of self-attention. "
    "The [CLS] token attends to ALL tokens from BOTH questions. The classification head then "
    "reads the [CLS] representation which encodes the relationship between the two questions.\n\n"
    "In a Bi-Encoder:\n"
    "  Q1 → Transformer → [CLS]_1 (only knows Q1)\n"
    "  Q2 → Transformer → [CLS]_2 (only knows Q2)\n"
    "  cosine([CLS]_1, [CLS]_2) → similarity\n\n"
    "The [CLS] vectors never interacted. Each is blind to the other question.\n\n"
    "In a Cross-Encoder:\n"
    "  [CLS] Q1 [SEP] Q2 [SEP] → Transformer → [CLS]_joint (knows both Q1 and Q2)\n"
    "  Linear([CLS]_joint) → logits\n\n"
    '[CLS] pays attention to every word in both questions. It can detect that "What is" and '
    '"Explain" express the same intent, and that "AI" is an abbreviation of "Artificial Intelligence".'
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 4
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 4: Tokenization in Detail", level=1)

doc.add_heading("Step-by-Step with DeBERTa-v3", level=2)
doc.add_paragraph(
    'Raw text after preprocessing: Q1 = "what is artificial intelligence (artificial intelligence)"\n'
    'Q2 = "explain ai. (artificial intelligence)"\n\n'
    "The tokenizer(q1, q2) call automatically formats:\n"
    "[CLS] what is artificial intelligence (artificial intelligence) [SEP] explain ai. (artificial intelligence) [SEP]"
)

doc.add_heading("Approximate Tokenization", level=2)
add_table(
    doc,
    ["Index", "Token ID", "Text"],
    [
        ["0", "1", "[CLS]"],
        ["1", "10534", "what"],
        ["2", "322", "is"],
        ["3", "16723", "artificial"],
        ["4", "5826", "intelligence"],
        ["5", "7", "("],
        ["6", "16723", "artificial"],
        ["7", "5826", "intelligence"],
        ["8", "8", ")"],
        ["9", "2", "[SEP]"],
        ["10", "8192", "explain"],
        ["11", "365", "ai"],
        ["12", "5", "."],
        ["13", "7", "("],
        ["14", "16723", "artificial"],
        ["15", "5826", "intelligence"],
        ["16", "8", ")"],
        ["17", "2", "[SEP]"],
    ],
)

doc.add_heading("Attention Mask", level=2)
doc.add_paragraph(
    "[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, ..., 0]\n"
    "↑ Real tokens (18)                                     ↑ Padding (110)"
)

doc.add_heading("Final Tensors", level=2)
add_code_block(
    doc,
    """input_ids:      torch.Size([1, 128])
  tensor([[    1, 10534,   322, 16723,  5826,     7, 16723,  5826,
               8,     2,  8192,   365,     5,     7, 16723,  5826,
               8,     2,     0,     0,  ...]])

attention_mask: torch.Size([1, 128])
  tensor([[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, ...]])

labels: torch.Size([1])
  tensor([1])  — duplicate""",
)

doc.add_heading("How tokenizer() Produces This", level=2)
add_code_block(
    doc,
    """encoding = tokenizer(
    "what is artificial intelligence (artificial intelligence)",  # q1
    "explain ai. (artificial intelligence)",                      # q2
    max_length=128,
    padding="max_length",
    truncation=True,
    return_tensors="pt",
)""",
)
doc.add_paragraph(
    "Internally:\n1. Adds [CLS] at start\n2. Tokenizes q1 → token IDs\n"
    "3. Adds [SEP]\n4. Tokenizes q2 → token IDs\n5. Adds [SEP]\n"
    "6. If shorter than max_length, pads with [PAD] (ID=0)\n"
    "7. If longer, truncates the longer segment"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 5
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 5: Attention Mathematics", level=1)

doc.add_heading("The Full Attention Computation", level=2)
doc.add_paragraph("Given input sequence X of shape [seq_len × d_model] (18 × 768):")

doc.add_heading("Step 1: Create Q, K, V", level=2)
add_code_block(
    doc,
    """Q = X × W_Q    [18 × 768] × [768 × 64] = [18 × 64]
K = X × W_K    [18 × 768] × [768 × 64] = [18 × 64]
V = X × W_V    [18 × 768] × [768 × 64] = [18 × 64]""",
)
doc.add_paragraph(
    "Each token produces:\n• Query: what it is looking for\n• Key: what information it offers\n• Value: the actual information it shares"
)

doc.add_heading("Step 2-3: Scores and Scaling", level=2)
add_code_block(
    doc,
    """Scores = Q × K^T    [18 × 64] × [64 × 18] = [18 × 18]
Scores = Scores / √d_k = Scores / 8""",
)
doc.add_paragraph(
    "Scores[i][j] = dot product between Query of token i and Key of token j.\n\n"
    'If token 10 ("explain") has a Query similar to the Key of token 1 ("what"), then Scores[10][1] is high.\n\n'
    "Scaling prevents dot products from growing too large, which would push softmax into regions with extremely small gradients."
)

doc.add_heading("Step 4-5: Mask and Softmax", level=2)
add_code_block(
    doc,
    """For each position j where attention_mask[j] == 0:
    Scores[i][j] = -inf   # padding contributes nothing

Attention_weights[i][j] = exp(Scores[i][j]) / Σ_k exp(Scores[i][k])""",
)
doc.add_paragraph(
    "Row-wise softmax. Each row sums to 1. This converts scores into a probability distribution over all tokens."
)

doc.add_heading("Step 6: Weighted Sum", level=2)
add_code_block(doc, """Context_i = Σ_j Attention_weights[i][j] × V[j]""")
doc.add_paragraph(
    "Token i's new representation is a weighted sum of all value vectors. The weight is determined by how much token i should attend to each token j."
)

doc.add_heading('Concrete Example: Attention from "explain"', level=2)
add_table(
    doc,
    ["Token", "Attention Weight"],
    [
        ["[CLS]", "0.02"],
        ['"what"', '0.15 ← "explain" recognizes "what is" as similar intent'],
        ['"is"', "0.12"],
        ['"artificial" (pos 3)', "0.08"],
        ['"intelligence" (pos 4)', "0.08"],
        ['"("', "0.01"],
        ['"artificial" (pos 6)', "0.08"],
        ['"intelligence" (pos 7)', "0.08"],
        ['")"', "0.01"],
        ["[SEP]", "0.02"],
        ['"explain"', "0.20 ← attending to itself"],
        ['"ai"', '0.10 ← recognizes "AI" as the subject'],
        ['"."', "0.01"],
        ['"("', "0.01"],
        ['"artificial" (pos 14)', "0.02"],
        ['"intelligence" (pos 15)', "0.02"],
        ['")"', "0.01"],
        ["[SEP]", "0.02"],
    ],
)

doc.add_paragraph(
    "Through 12 layers of this, the model builds a rich representation where:\n"
    "• Q2 words know about Q1 words\n"
    "• The [CLS] token aggregates information from both\n"
    "• The relationship between the two questions is encoded in [CLS]"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 6
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 6: Why Cross Encoder is Different", level=1)

doc.add_heading("Bi-Encoder: Two Isolated Transformers", level=2)
add_code_block(
    doc,
    """Q1: "What is Artificial Intelligence?" → Tokenize → Transformer → [CLS]_1 = f(Q1)
Q2: "Explain AI." → Tokenize → Transformer → [CLS]_2 = f(Q2)

Similarity = cosine([CLS]_1, [CLS]_2)""",
)
doc.add_paragraph(
    'Information loss: "Explain" never knows that "What is" precedes a definition request. '
    '"AI" never knows that "Artificial Intelligence" was mentioned. The similarity is computed '
    "on two summaries that were created in isolation."
)

doc.add_heading("Cross-Encoder: One Transformer Processing Both", level=2)
add_code_block(
    doc,
    """[CLS] what is artificial intelligence ? [SEP] explain ai . [SEP]
                     ↓
               Transformer
                     ↓
"explain" attends to "what", "is", "artificial", "intelligence"
"ai" attends to "artificial", "intelligence"
[CLS] attends to ALL tokens from both questions
                     ↓
[CLS]_joint = f(Q1, Q2) — encodes the RELATIONSHIP""",
)

doc.add_heading("Why Bi-Encoder Exists Despite Information Loss", level=2)
add_bullet(
    doc,
    "Sub-quadratic retrieval: For N documents, Bi-Encoder does N forward passes once. Cross-Encoder would need O(N²) comparisons.",
)
add_bullet(
    doc, "Pre-computation: Bi-Encoder embeddings can be stored and indexed with FAISS for millisecond retrieval."
)
add_bullet(
    doc,
    "Latency: Bi-Encoder inference for a single query is one forward pass vs one forward pass per pair for Cross-Encoder.",
)

doc.add_heading("Typical Architecture: Two-Stage Retrieval", level=2)
add_code_block(
    doc,
    """Stage 1 (Bi-Encoder):
  10M documents → embeddings → FAISS index
  Query → embedding → nearest neighbors → 100 candidates

Stage 2 (Cross-Encoder):
  Score 100 candidates with Cross-Encoder
  Rerank → return top-10""",
)
doc.add_paragraph(
    "This is exactly what your project's ensemble does: Bi-Encoders (E5, BGE, MPNet) "
    "find candidates, Cross-Encoder reranks them."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 7
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 7: The [CLS] Token", level=1)

doc.add_heading("What [CLS] Actually Learns", level=2)
doc.add_paragraph(
    "The [CLS] token is a special token inserted at position 0. Its initial embedding is just "
    "a learnable vector — it has no semantic content. Through training, [CLS] learns to aggregate "
    "information from the entire sequence.\n\n"
    "Initialization: [CLS]_0 = W_embedding[token_id_of_CLS] = random vector\n\n"
    "After training: [CLS]_final = Attention([CLS] attends to all tokens)\n\n"
    "[CLS] has no input-dependent initial meaning — it is always the same token. But through "
    "self-attention, its final representation becomes a weighted summary of all tokens."
)

doc.add_heading("Why Classification Uses [CLS]", level=2)
doc.add_paragraph(
    "For sentence-pair classification, [CLS] is better than mean pooling because:\n\n"
    "1. [CLS] learns to attend selectively: It can learn attention patterns that emphasize "
    "words important for the classification task and ignore irrelevant words.\n\n"
    "2. [CLS] captures relationships: Through layers of attention, [CLS] can encode that "
    '"What is AI" and "Explain AI" are the same intent, even though they share few words.\n\n'
    "3. Mean pooling dilutes signal: If you average all 128 token vectors, the signal from "
    '"AI" → "Artificial Intelligence" matching is diluted by 126 other tokens.'
)

doc.add_heading("How [CLS] Becomes the Joint Representation", level=2)
doc.add_paragraph(
    "Through each attention layer:\n\n"
    "Layer 1: [CLS] attends to nearby tokens → captures local syntax\n"
    'Layer 2-3: [CLS] attends to key entities → "AI", "Artificial Intelligence"\n'
    'Layer 4-6: [CLS] attends to intent-marking words → "What is", "Explain"\n'
    "Layer 7-9: [CLS] attends to relationship between entities in Q1 and Q2\n"
    "Layer 10-12: [CLS] refines the joint representation → final classification features"
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 8
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 8: Classification Head", level=1)

doc.add_heading("Architecture", level=2)
add_code_block(
    doc,
    """Final Hidden State [batch × seq_len × 768]
                    ↓
[CLS] Token [batch × 768]
                    ↓
Dropout(p=0.1) — randomly zeroes 10% during training
                    ↓
Linear Layer: 768 → 2
    logits = x × W^T + b
    W: [2 × 768],  b: [2]
                    ↓
Logits: [batch × 2]  e.g., [-3.2, 1.8]
                    ↓
Softmax → [0.0067, 0.9933]
                    ↓
predicted_class = argmax = 1 (duplicate)
probability_duplicate = 0.9933""",
)

doc.add_heading("Linear Layer", level=2)
doc.add_paragraph(
    "logits[i] = Σ_j (x[j] × W[j][i]) + b[i]\n\n"
    "Each column of W is a template. Column 0 = non-duplicate template, "
    "Column 1 = duplicate template. The dot product measures similarity between "
    "[CLS] and each template."
)

doc.add_heading("Dropout", level=2)
doc.add_paragraph(
    "During training, each dimension has a 10% chance of being set to 0. This prevents "
    "the classifier from relying too much on any single dimension. During inference, "
    "dropout is disabled."
)

doc.add_heading("Softmax", level=2)
doc.add_paragraph(
    "softmax(logits_i) = exp(logits_i) / Σ_j exp(logits_j)\n\n"
    "For logits = [-3.2, 1.8]:\n"
    "softmax[0] = exp(-3.2) / (exp(-3.2) + exp(1.8)) = 0.0067\n"
    "softmax[1] = exp(1.8) / (exp(-3.2) + exp(1.8)) = 0.9933"
)

doc.add_heading("Threshold", level=2)
doc.add_paragraph(
    "predicted = probability_duplicate >= threshold\n\n"
    "Default threshold: 0.5. But imbalanced datasets shift the optimal threshold. "
    "Your code finds it via scan on validation set:"
)
add_code_block(
    doc,
    """best_f1 = 0
best_thresh = 0.5
for thresh in np.linspace(0.1, 0.9, 81):
    preds = (probs >= thresh).astype(int)
    f1 = f1_score(true_labels, preds)
    if f1 > best_f1:
        best_f1 = f1
        best_thresh = thresh""",
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 9
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 9: Training Pipeline", level=1)

doc.add_heading("9.1 Dataset Creation", level=2)
doc.add_paragraph("Your dataset (Quora duplicate questions) has (q1, q2, label) where label=1 if duplicate, 0 if not.")
add_table(
    doc,
    ["Split", "Ratio", "Purpose"],
    [
        ["Train", "80%", "Model training"],
        ["Validation", "10%", "Hyperparameter tuning, checkpoint selection"],
        ["Test", "10%", "Final evaluation (held out)"],
    ],
)

doc.add_heading("9.2 Positive, Negative & Hard Negative Pairs", level=2)
doc.add_paragraph("Positive pairs: Questions that Quora users marked as duplicates.")
add_code_block(
    doc,
    """Q1: "How to learn Python?"
Q2: "What's the best way to learn Python?"
Label: 1""",
)
doc.add_paragraph("Negative pairs: Random non-duplicate pairs (easy).")
add_code_block(
    doc,
    """Q1: "How to learn Python?"
Q2: "What is the capital of France?"
Label: 0""",
)
doc.add_paragraph("Hard negatives: Share many words but differ in critical detail.")
add_code_block(
    doc,
    """Q1: "How to install TensorFlow on Windows?"
Q2: "How to install TensorFlow on Mac?"
Label: 0""",
)

doc.add_heading("9.3 Loss Function: Cross-Entropy", level=2)
add_code_block(
    doc,
    """CrossEntropyLoss = -Σ_c y_c × log(p_c)

For binary with true label = 1:
Loss = -log(p_1) = -log(0.9933) = 0.0068

Class-weighted variant:
class_weights = [1.0, n_neg / n_pos]
loss = F.cross_entropy(logits, labels, weight=class_weights)""",
)

doc.add_heading("9.4 Backpropagation", level=2)
doc.add_paragraph("The gradient flows backward through every layer:")
add_code_block(
    doc,
    """Loss → Softmax → Linear → Dropout → [CLS] → Layer 12 → ... → Layer 1 → Embeddings

dL/dW[:,1] = (p_1 - y) × [CLS]      # gradient for classification head
dL/d[CLS] = W[:,1] × (p_1 - y)      # gradient into transformer
...                                    # backprop through 12 layers""",
)
doc.add_paragraph("Every parameter gets updated: ~184M parameters (DeBERTa-v3-base) + ~1,538 (classification head).")

doc.add_heading("9.5 Optimizer: AdamW", level=2)
add_code_block(
    doc,
    """from torch.optim import AdamW
optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01,
                  fused=(device.type == "cuda"))""",
)
doc.add_paragraph(
    "AdamW = Adam + decoupled weight decay.\n"
    "• m_t = β₁×m_{t-1} + (1-β₁)×g_t  (momentum)\n"
    "• v_t = β₂×v_{t-1} + (1-β₂)×g_t² (velocity)\n"
    "• θ_t = θ_{t-1} - lr × m_t / (√v_t + ε)  (adaptive update)\n\n"
    "fused=True: Uses fused CUDA kernel (2-3x faster on GPU)."
)

doc.add_heading("9.6 Learning Rate Schedule: Linear Warmup", level=2)
add_code_block(
    doc,
    """total_steps = len(train_loader) * num_epochs // gradient_accumulation_steps
warmup_steps = int(total_steps * 0.1)
scheduler = get_linear_schedule_with_warmup(
    optimizer, num_warmup_steps=warmup_steps,
    num_training_steps=total_steps
)""",
)
doc.add_paragraph(
    "Warmup phase (first 10%): LR increases linearly from 0 to 2e-5.\n"
    "Decay phase (remaining 90%): LR decreases linearly to 0.\n\n"
    "Why warmup? At the start, parameters are far from optimal (pre-trained on MLM, not classification). "
    "Large updates early on destabilize training. Warmup lets the model gradually adjust."
)

doc.add_heading("9.7 Training Loop Summary", level=2)
doc.add_paragraph(
    "200k samples, batch_size=16, gradient_accumulation_steps=2:\n"
    "• 12,500 steps per epoch\n"
    "• 6,250 actual parameter updates per epoch\n"
    "• 3 epochs → ~18,750 parameter updates"
)

doc.add_heading("9.8 Validation and Checkpointing", level=2)
doc.add_paragraph(
    "After each epoch:\n"
    "• model.eval() — disable dropout\n"
    "• torch.no_grad() — no gradient computation\n"
    "• Compute accuracy, F1, precision, recall, ROC-AUC\n\n"
    "Only save when validation F1 improves:\n"
    "if val_f1 > best_val_f1: save_pretrained()"
)

doc.add_heading("9.9 Early Stopping", level=2)
doc.add_paragraph(
    "patience=2: If validation F1 does not improve for 2 consecutive epochs, stop training.\n\n"
    "Prevents overfitting: if validation metrics stop improving, further training only memorizes training data."
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 10
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 10: Your Project in Detail", level=1)

doc.add_heading("Dataset Flow", level=2)
add_code_block(
    doc,
    """data/cleaned_quora.parquet
  ↓
get_quora_splits() → 80/10/10 stratified split
  ↓
train_df: ~320k pairs
val_df:   ~40k pairs
test_df:  ~40k pairs
  ↓
normalize_question() for each q1, q2:
  - Lowercase
  - Expand abbreviations: "AI" → "AI (Artificial Intelligence)"
  - Fix typos: "artifical" → "artificial"
  - Normalize whitespace, punctuation
  ↓
QuoraPairDataset:
  - tokenizer(q1, q2, max_length=128, padding="max_length", truncation=True)
  - returns {input_ids, attention_mask, labels}
  ↓
Pre-tokenize (for GPU efficiency): TensorDataset
  ↓
DataLoader (batch_size=16, shuffle=True, num_workers=4)""",
)

doc.add_heading("Gradient Flow for One Training Example", level=2)
add_code_block(
    doc,
    """Step 1: Batch of 16 pairs → GPU
  input_ids: [16, 128], attention_mask: [16, 128], labels: [16]

Step 2: Forward pass
  model(input_ids, attention_mask) → logits [16, 2]

Step 3: Loss
  loss_fn(logits, labels) → scalar = 0.68

Step 4: Backward pass
  loss.backward()  → gradients flow through ALL layers

Step 5: Optimizer step
  optimizer.step()  → AdamW update
  scheduler.step()  → adjust learning rate

Step 6: Accumulate (every 2 batches = 32 pairs → one update)""",
)

doc.add_heading("How Duplicate Probability is Learned", level=2)
doc.add_paragraph(
    "Initially: Classification head randomly initialized → outputs ~0.5 for all pairs.\n\n"
    "After 1,000 batches: Model learns high word overlap → duplicate.\n\n"
    "After 10,000 batches:\n"
    '• Head 3: Abbreviation detection ("ML" → "Machine Learning")\n'
    '• Head 7: Negation detection ("enable" vs "disable")\n'
    '• Head 11: Entity comparison ("Python" in Q1 vs "Python" in Q2)\n'
    "• [CLS] aggregates signals from specialized heads\n\n"
    "After training (3 epochs, ~18,750 updates):\n"
    "• Classification head weights have converged\n"
    "• Model can distinguish subtle duplicates from non-duplicates"
)

doc.add_heading("Why Each Hyperparameter Matters", level=2)

doc.add_heading("max_length", level=3)
doc.add_paragraph(
    "Your default = 128. Average Quora question is ~40 characters. "
    "If too small (64): long questions truncated, information lost. "
    "If too large (512): 4x GPU memory, more padding waste."
)

doc.add_heading("batch_size", level=3)
doc.add_paragraph(
    "Your default = 16 (effective 32 with gradient_accumulation_steps=2).\n"
    "Small batch (4-8): Noisy gradients, more iterations needed.\n"
    "Large batch (64-128): Stable but can converge to sharp minima.\n"
    "16 is standard for DeBERTa-v3-base fine-tuning."
)

doc.add_heading("learning_rate", level=3)
doc.add_paragraph(
    "2e-5 is the sweet spot for fine-tuning DeBERTa-v3-base.\n"
    "Too high (5e-4): Destroys pre-trained knowledge, loss diverges.\n"
    "Too low (1e-6): Barely learns the new task."
)

doc.add_heading("Why Preprocessing Matters", level=2)
add_bullet(doc, 'Lowercase: "AI" and "ai" → same token. Without it, model treats them as different words.')
add_bullet(
    doc,
    'Abbreviation expansion: "AI" → "AI (Artificial Intelligence)". Lets model match "AI" to "Artificial Intelligence" across questions.',
)
add_bullet(
    doc,
    'Typo fixing: "artifical" → "artificial". Without it, mistyped words split into subwords, creating fragmented representations.',
)
add_bullet(doc, 'Punctuation: "What is AI?" and "What is AI???" → same representation.')

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 11
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 11: Visualizations", level=1)

doc.add_heading("Training Pipeline", level=2)
add_code_block(
    doc,
    """                  CLEANED DATA
          data/cleaned_quora.parquet
                    │
          get_quora_splits()
          ┌─────────┼─────────┐
          │         │         │
        TRAIN      VAL      TEST
       (80%)     (10%)     (10%)
          │
    normalize_question()
          │
    QuoraPairDataset (tokenize)
          │
    Pre-tokenize → TensorDataset
          │
    DataLoader(batch=16, shuffle)
          │
    ┌──────┴──────┐     ┌──────────────┐
    │  GPU LOOP   │     │ VALIDATION   │
    │ forward()   │     │ model.eval() │
    │ loss()      │     │ metrics      │
    │ backward()  │     │ save if best │
    │ optimizer   │     └──────────────┘
    │ scheduler   │
    └─────────────┘
          │
    BEST MODEL SAVED
    models/cross-encoder-quora/""",
)

doc.add_heading("Inference Pipeline", level=2)
add_code_block(
    doc,
    """        USER INPUT: q1, q2
              │
    normalize_question(q1)
    normalize_question(q2)
              │
    tokenizer(q1, q2, max_length=128)
              │
    input_ids, attention_mask → GPU
              │
    model(input_ids, attention_mask)
              │
    logits: [non_dup_logit, dup_logit]
              │
    softmax → [prob_non, prob_dup]
              │
    prob_dup >= threshold? → prediction
              │
    Return: {"prediction": "Duplicate",
             "prob_duplicate": 0.97}""",
)

doc.add_heading("[CLS] Flow Through Layers", level=2)
doc.add_paragraph(
    "Layer 0: [CLS] = token_embedding + position_embedding (random initialization)\n"
    "Layer 1: [CLS] attends to all tokens → begins aggregating\n"
    'Layer 2: [CLS] attends to "what", "is" → knows it is a question\n'
    'Layer 3: [CLS] attends to "ai" in both questions → knows entity\n'
    "Layer 4: [CLS] encodes that both ask about AI\n"
    "...\n"
    "Layer 12: [CLS] = rich representation of the pair relationship"
)

doc.add_heading("Classification Computation", level=2)
add_code_block(
    doc,
    """[CLS] Layer 12 Output: [768]
         │
         │   W_classifier: [2 × 768]
         │
         ├──Σ (x[0:768] × W[0,0:768]) + b[0] = non_dup_logit = -3.2
         │
         └──Σ (x[0:768] × W[1,0:768]) + b[1] = dup_logit = 1.8
         │
         softmax(-3.2, 1.8) = (0.0067, 0.9933)
         │
         predicted = argmax = 1 (Duplicate)""",
)

doc.add_heading("Loss Calculation Visualization", level=2)
add_table(
    doc,
    ["", "Predicted Non-Dup", "Predicted Dup"],
    [
        ["Actual Non-Dup (0)", "TN (loss=0.01)", "FP (loss=4.61)"],
        ["Actual Dup (1)", "FN (loss=4.61)", "TP (loss=0.01)"],
    ],
)

doc.add_heading("Checkpoint Strategy", level=2)
add_code_block(
    doc,
    """After Epoch 1: Val F1 = 0.82 → best → save
After Epoch 2: Val F1 = 0.84 → best → save (overwrites)
After Epoch 3: Val F1 = 0.83 → not best → don''t save
              (Epoch 2 checkpoint is kept)""",
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 12
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 12: Common Mistakes", level=1)

doc.add_heading("Overfitting", level=2)
doc.add_paragraph(
    "Symptom: Training loss decreases, validation loss increases.\n\n"
    "Epoch 1: Train Loss=0.45, Val F1=0.82\n"
    "Epoch 2: Train Loss=0.28, Val F1=0.84\n"
    "Epoch 3: Train Loss=0.12, Val F1=0.83 ← overfitting\n\n"
    "Fix: Use more data, increase weight decay, increase dropout, use early stopping."
)

doc.add_heading("Underfitting", level=2)
doc.add_paragraph(
    "Symptom: Both training and validation loss stay high.\n\n"
    "Fix: Increase epochs, increase learning rate, decrease weight decay, use larger model."
)

doc.add_heading("Threshold Tuning on Test Set", level=2)
doc.add_paragraph(
    "Your code finds optimal threshold on test set (line 484-491). This leaks test information!\n\n"
    "Proper approach: Tune threshold on validation set, then evaluate ONCE on test."
)

doc.add_heading("Data Leakage", level=2)
add_bullet(doc, "Splitting before deduplication: Same question in train and test → model memorizes.")
add_bullet(
    doc, "Leaking labels through preprocessing: If expansion depends on external knowledge that changes over time."
)

doc.add_heading("Validation Leakage", level=2)
doc.add_paragraph(
    "Using validation metrics to decide when to stop, then reporting that metric as final performance.\n"
    "Best val F1: 0.84 (epoch 2). Test F1: 0.83. The true performance is 0.83, not 0.84."
)

doc.add_heading("Wrong Preprocessing", level=2)
doc.add_paragraph(
    "If training uses normalize_question(expand_abbrevs=True) but inference uses expand_abbrevs=False, "
    "the token distributions differ. Performance drops by 10-20%."
)

doc.add_heading("Wrong Tokenizer", level=2)
doc.add_paragraph(
    "Loading a different tokenizer for training vs inference:\n"
    'Training: AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")\n'
    'Inference: AutoTokenizer.from_pretrained("bert-base-uncased")  ← WRONG!\n\n'
    'Token ID mappings differ between models. Token ID 101 means [CLS] in BERT but is a subword "am" in DeBERTa.'
)

doc.add_heading("Wrong Checkpoint", level=2)
doc.add_paragraph(
    "Loading the pre-trained model instead of the fine-tuned one:\n"
    'model = AutoModelForSequenceClassification.from_pretrained("microsoft/deberta-v3-base")  ← loads UNFINE-TUNED model\n\n'
    'Fix: model = AutoModelForSequenceClassification.from_pretrained("models/cross-encoder-quora")'
)

doc.add_heading("Wrong Inference Mode", level=2)
doc.add_paragraph(
    "Forgetting model.eval() and torch.no_grad() during inference causes:\n"
    "• Dropout active → different outputs each run\n"
    "• Gradient computation → 2x memory usage\n\n"
    "Fix:\n"
    "model.eval()\n"
    "with torch.no_grad():\n"
    "    outputs = model(input_ids, attention_mask)"
)

doc.add_heading("Impact Summary", level=2)
add_table(
    doc,
    ["Mistake", "Performance Impact", "Why"],
    [
        ["Overfitting", "-5% F1", "Model memorizes, does not generalize"],
        ["Threshold on test", "+1-2% reported F1", "Optimistic evaluation"],
        ["Data leakage", "+5-10% reported F1", "Model sees test during training"],
        ["Wrong preprocessing", "-10-20% F1", "Token distributions do not match"],
        ["Wrong tokenizer", "Model breaks", "Completely different vocabulary"],
        ["Wrong checkpoint", "-3-10% F1", "Using pre-trained instead of fine-tuned"],
        ["Wrong inference mode", "-1-3% F1", "Dropout randomness"],
    ],
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 13
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 13: Advanced Topics", level=1)

doc.add_heading("13.1 Layer-wise Learning Rate Decay", level=2)
doc.add_paragraph(
    "Different layers need different learning rates:\n\n"
    "• Layer 0 (Embedding): lr × 0.1 (almost frozen, well pre-trained)\n"
    "• Layer 1-6: lr × 0.5 (low layers capture syntax)\n"
    "• Layer 7-11: lr × 0.9 (higher layers more task-specific)\n"
    "• Layer 12: lr × 1.0 (task-specific features)\n"
    "• Classification Head: lr × 10.0 (randomly initialized)"
)
add_code_block(
    doc,
    """def get_layerwise_lr(model, base_lr=2e-5):
    opt_params = []
    named_params = list(model.named_parameters())
    cls_params = [p for n, p in named_params if "classifier" in n]
    opt_params.append({"params": cls_params, "lr": base_lr * 10})
    for i in reversed(range(12)):
        layer_p = [p for n, p in named_params if f"layer.{i}" in n]
        lr = base_lr * (0.95 ** (11 - i))
        opt_params.append({"params": layer_p, "lr": lr})
    emb_p = [p for n, p in named_params if "embeddings" in n]
    opt_params.append({"params": emb_p, "lr": base_lr * 0.1})
    return AdamW(opt_params, weight_decay=0.01)""",
)

doc.add_heading("13.2 Mixed Precision (FP16)", level=2)
doc.add_paragraph(
    "Stores weights in FP16 during forward/backward, keeps FP32 copy for updates.\n"
    "Benefits: ~40% less memory, 2-3x speedup on Tensor Cores.\n\n"
    "Key components:\n"
    "• torch.amp.autocast: Automatic mixed precision context\n"
    "• GradScaler: Prevents gradient underflow (gradients < 6e-8 become 0 in FP16)"
)

doc.add_heading("13.3 Gradient Checkpointing", level=2)
doc.add_paragraph(
    "Trades computation for memory: forward activations are not stored but recomputed during backward.\n"
    "Memory: ~50% reduction. Speed: ~20% slower."
)

doc.add_heading("13.4 Exponential Moving Average (EMA)", level=2)
doc.add_paragraph(
    "Maintains a moving average of model weights: shadow[k] = decay × shadow[k] + (1-decay) × v\n\n"
    "The moving average smooths the weight trajectory, converging to a flatter minimum "
    "that generalizes better. Often outperforms final checkpoint by 0.5-1% F1."
)

doc.add_heading("13.5 Temperature Scaling", level=2)
doc.add_paragraph(
    "Calibration technique: softmax(logits / T)\n\n"
    "T > 1: Softer probabilities (overconfident model becomes more uncertain)\n"
    "T < 1: Sharper probabilities (underconfident model becomes more certain)\n\n"
    "T is learned on the validation set by optimizing NLL."
)

doc.add_heading("13.6 Label Smoothing", level=2)
doc.add_paragraph(
    "Replaces hard labels (0, 1) with soft labels (0.1, 0.9):\n\n"
    "Label 1 → target = [0.05, 0.95] (instead of [0, 1])\n"
    "Label 0 → target = [0.95, 0.05] (instead of [1, 0])\n\n"
    "Prevents overconfidence and improves calibration."
)

doc.add_heading("13.7 Hard Negative Mining", level=2)
doc.add_paragraph(
    "Strategies to augment training with challenging non-duplicate pairs:\n\n"
    "1. BM25 hard negatives: Retrieve top-100 BM25 matches (lexically similar but not duplicates)\n"
    "2. Bi-Encoder hard negatives: Use fine-tuned E5 to find high-similarity non-duplicates\n"
    "3. Cross-Encoder hard negatives: Use current model mistakes as additional training data\n\n"
    "Without hard negatives, the model cheats by memorizing that high word overlap = duplicate."
)

doc.add_heading("13.8 Knowledge Distillation", level=2)
doc.add_paragraph(
    "Train a smaller student model to mimic a larger teacher model:\n\n"
    "Teacher: DeBERTa-v3-large (304M params, accurate but slow)\n"
    "Student: MiniLM-L6 (80M params, fast)\n\n"
    "Loss = α × CE(student, true_label) + (1-α) × KL(student_logits/T, teacher_logits/T)\n\n"
    "Soft labels contain more information about the decision boundary than hard 0/1 labels."
)

doc.add_heading("13.9 Cross-Encoder Reranking Architecture", level=2)
add_code_block(
    doc,
    """User Query → Stage 1: Bi-Encoder Retrieval (FAISS)
  10M questions → 100 candidates (50ms)
  ↓
Stage 2: Cross-Encoder Reranking
  100 candidates scored → top-10 (100ms)
  ↓
Stage 3: Return top-10 to user""",
)

doc.add_heading("13.10 When to Use Each Technique", level=2)
add_table(
    doc,
    ["Technique", "When to Use", "Expected Gain"],
    [
        ["Layer-wise LR decay", "Fine-tuning large models", "+1-2% F1"],
        ["Mixed precision", "GPU with Tensor Cores (RTX 30xx+)", "2x speedup"],
        ["Gradient checkpointing", "GPU memory limited (< 8GB)", "Enable larger batch"],
        ["EMA", "Always at end of training", "+0.5-1% F1"],
        ["Temperature scaling", "Poorly calibrated probabilities", "Better reliability"],
        ["Label smoothing", "Overconfident model", "+0.5-1% F1"],
        ["Hard negative mining", "Model misses subtle distinctions", "+2-5% F1"],
        ["Knowledge distillation", "Need fast inference", "10x speedup, -1-2% F1"],
    ],
)

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 14
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 14: Research Level — Production Usage at Major Companies", level=1)

doc.add_heading("14.1 Google", level=2)
doc.add_paragraph(
    "Two-stage system for search:\n"
    "1. Retrieval: Lightweight Bi-Encoder retrieves 1000 candidates from index\n"
    "2. Reranking: Large Cross-Encoder (T5 or PaLM) scores the 1000 candidates\n\n"
    "Key innovation: Training on user click data rather than hand-labeled data. "
    'If a user searches "What is AI" and clicks on "Artificial Intelligence explained", that is a positive pair.'
)

doc.add_heading("14.2 Microsoft (DeBERTa)", level=2)
doc.add_paragraph(
    "DeBERTa (Decoding-enhanced BERT with Disentangled Attention):\n\n"
    "Disentangled attention — the key innovation:\n"
    "Standard: A_ij = (H_i × W_Q) × (H_j × W_K)^T\n"
    "DeBERTa: A_ij = content_attention + relative_position_attention\n\n"
    "Attention weight depends on BOTH content AND relative distance. "
    "Crucial for Cross-Encoders because tokens at distance 9 can still have strong attention "
    "if they ask the same thing.\n\n"
    "DeBERTa-v3 (your model): Uses ELECTRA-style pre-training (replaced token detection) "
    "making it more parameter-efficient than BERT/RoBERTa."
)

doc.add_heading("14.3 OpenAI", level=2)
doc.add_paragraph(
    "Uses Cross-Encoders for:\n"
    "• Content filtering: (user_query, safety_policy) → violation score\n"
    "• Reward modeling: (prompt, response) → helpfulness score for RLHF\n"
    "• Quality evaluation: (instruction, completion) → quality score"
)

doc.add_heading("14.4 Meta (Facebook)", level=2)
doc.add_paragraph(
    "Recommendation system:\n"
    "[CLS] User watching Python video [SEP] Recommended ML video [SEP]\n"
    "→ Cross-Encoder scores likelihood of user watching recommended content\n\n"
    "Trained on engagement data (clicks, watch time, likes) rather than explicit labels."
)

doc.add_heading("14.5 Anthropic", level=2)
doc.add_paragraph(
    "Constitutional AI uses Cross-Encoders for preference modeling:\n"
    "[CLS] Assistant response [SEP] Constitutional principle [SEP]\n"
    "→ Cross-Encoder scores alignment with principles"
)

doc.add_heading("14.6 Production Architecture", level=2)
add_code_block(
    doc,
    """                  ┌─────────────────────────────┐
                  │        LOAD BALANCER         │
                  └──────────┬──────────────────┘
                             │
                  ┌──────────┴──────────┐
                  │   QUERY PARSER      │
                  │ (normalize, expand) │
                  └──────────┬──────────┘
                             │
              ┌──────────────┴──────────────┐
              │         RETRIEVAL           │
              │  (Bi-Encoder + FAISS)       │
              │  (BM25 lexical fallback)    │
              │  10M → 100 candidates       │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │       CROSS-ENCODER         │
              │         RERANKER            │
              │  100 candidates → top-10    │
              │  Deployed on 4×A100 GPUs    │
              │  Batch inference: 50ms/tier │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │      ENSEMBLE RERANK        │
              │  (optional, high-stakes)    │
              │  Average 3 Cross-Encoders   │
              └──────────────┬──────────────┘
                             │
              ┌──────────────┴──────────────┐
              │         RESULTS             │
              │  Top-10 ranked by CE score  │
              └─────────────────────────────┘""",
)

doc.add_heading("Inference Optimizations", level=2)
add_bullet(doc, "Batching: Process 100 candidates in one forward pass")
add_bullet(doc, "KV-cache: Cache intermediate representations for real-time reranking")
add_bullet(doc, "ONNX/TensorRT: Convert to optimized inference format (2-5x speedup)")
add_bullet(doc, "INT8 Quantization: 4x memory reduction with <1% accuracy loss")

doc.add_page_break()

# ══════════════════════════════════════════════════════════════════
# PART 15
# ══════════════════════════════════════════════════════════════════
doc.add_heading("Part 15: Code Walkthrough", level=1)
doc.add_paragraph("Complete line-by-line explanation of scripts/train_cross_encoder.py")

doc.add_heading("15.1 Imports and Setup", level=2)
add_code_block(
    doc,
    '''"""Train a Cross-Encoder on Quora duplicate questions dataset."""

from __future__ import annotations  # Enables forward reference type hints
import sys, time, json, argparse
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from torch.optim import AdamW
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, confusion_matrix,
)''',
)
doc.add_paragraph(
    "Key imports:\n"
    "• AutoTokenizer: Loads DeBERTa-v3 tokenizer from HuggingFace hub\n"
    "• AutoModelForSequenceClassification: Loads DeBERTa-v3 with classification head\n"
    "• AdamW: Optimizer with decoupled weight decay\n"
    "• get_linear_schedule_with_warmup: LR scheduler\n"
    "• sklearn.metrics: Evaluation metrics"
)

doc.add_heading("15.2 Path Configuration", level=2)
add_code_block(
    doc,
    """SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from duplicate_question_app._dataset.loader import get_quora_splits
from duplicate_question_app._preprocessing import normalize_question

RESULTS_DIR = Path(__file__).resolve().parents[1] / "outputs" / "embedding_models"
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MODEL_NAME = "cross-encoder-quora"
MODEL_PATH = MODELS_DIR / MODEL_NAME""",
)
doc.add_paragraph(
    "Adds src/ to Python path so we can import project modules. "
    "Configures output paths for results JSON and saved model weights."
)

doc.add_heading("15.3 QuoraPairDataset", level=2)
add_code_block(
    doc,
    """class QuoraPairDataset(Dataset):
    def __init__(self, q1s, q2s, labels, tokenizer, max_length=128):
        self.q1s = q1s; self.q2s = q2s; self.labels = labels
        self.tokenizer = tokenizer; self.max_length = max_length

    def __len__(self): return len(self.labels)

    def __getitem__(self, idx):
        q1, q2, label = self.q1s[idx], self.q2s[idx], self.labels[idx]
        encoding = self.tokenizer(
            q1, q2,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(label, dtype=torch.long),
        }""",
)
doc.add_paragraph(
    "The key method is __getitem__ which takes a question pair and returns tokenized tensors. "
    "The tokenizer(q1, q2) call creates [CLS] q1 [SEP] q2 [SEP] format. "
    "squeeze(0) removes the batch dimension (tokenizer returns [1, seq_len])."
)

doc.add_heading("15.4 Data Preparation", level=2)
add_code_block(
    doc,
    """def prepare_data(max_train_samples=200000, sample_val=True, val_size=5000):
    train_df, val_df, test_df = get_quora_splits()
    if max_train_samples and len(train_df) > max_train_samples:
        train_df = train_df.sample(n=max_train_samples, random_state=42)

    train_q1s = [normalize_question(q, expand_abbrevs=True) for q in train_df["q1"]]
    train_q2s = [normalize_question(q, expand_abbrevs=True) for q in train_df["q2"]]
    train_labels = train_df["label"].tolist()
    # ... same for val ...

    tokenizer = AutoTokenizer.from_pretrained("microsoft/deberta-v3-base")
    train_dataset = QuoraPairDataset(train_q1s, train_q2s, train_labels, tokenizer)
    val_dataset = QuoraPairDataset(val_q1s, val_q2s, val_labels, tokenizer)
    return train_dataset, val_dataset, test_df""",
)
doc.add_paragraph(
    "Preprocessing is critical: normalize_question with expand_abbrevs=True ensures "
    '"AI" becomes "AI (Artificial Intelligence)", enabling the model to match abbreviations.'
)

doc.add_heading("15.5 Main Training Function", level=2)
add_code_block(
    doc,
    """def train_cross_encoder(
    model_name="microsoft/deberta-v3-base",
    output_path=MODEL_PATH,
    max_train_samples=200000,
    num_epochs=3,
    batch_size=16,
    learning_rate=2e-5,
    weight_decay=0.01,
    warmup_ratio=0.1,
    use_gpu=False,
    gradient_accumulation_steps=2,
    max_length=128,
    fp16=False,
) -> Path:""",
)
doc.add_paragraph("All hyperparameters as explicit parameters. No hidden configuration.")

doc.add_heading("15.6 GPU Setup", level=2)
add_code_block(
    doc,
    """if use_gpu is None:
    use_gpu = torch.cuda.is_available()
device = torch.device("cuda" if use_gpu and torch.cuda.is_available() else "cpu")
use_fp16 = (fp16 if fp16 is not None else True) and device.type == "cuda"

if device.type == "cuda":
    torch.backends.cudnn.benchmark = True          # Auto-tune cuDNN
    torch.backends.cuda.matmul.allow_tf32 = True   # Enable TF32
    torch.backends.cudnn.allow_tf32 = True
    torch.set_float32_matmul_precision('high')     # Use tensor cores""",
)
doc.add_paragraph(
    "Auto-detects GPU. TF32 is an NVIDIA Ampere+ feature providing ~2x faster matmul "
    "with negligible accuracy loss. Without these: 20-40% slower on RTX 4060."
)

doc.add_heading("15.7 Pre-tokenization (GPU Bottleneck Fix)", level=2)
add_code_block(
    doc,
    """train_input_ids, train_attention_masks, train_labels_list = [], [], []
for i in range(len(train_dataset)):
    item = train_dataset[i]
    train_input_ids.append(item["input_ids"])
    train_attention_masks.append(item["attention_mask"])
    train_labels_list.append(item["labels"])

train_tensor_dataset = TensorDataset(
    torch.stack(train_input_ids),
    torch.stack(train_attention_masks),
    torch.tensor(train_labels_list),
)""",
)
doc.add_paragraph(
    "Pre-tokenizes all data into memory. Without this, each epoch would re-tokenize "
    "200k pairs (CPU bottleneck). With pre-tokenization, the bottleneck shifts to GPU. "
    "Training is 2-3x faster."
)

doc.add_heading("15.8 DataLoader", level=2)
add_code_block(
    doc,
    """num_cpus = torch.multiprocessing.cpu_count()
data_num_workers = min(8, num_cpus // 2)

train_loader = DataLoader(
    train_tensor_dataset,
    batch_size=batch_size,
    shuffle=True,
    num_workers=data_num_workers,
    pin_memory=device.type == "cuda",
    persistent_workers=data_num_workers > 0,
    prefetch_factor=2 if data_num_workers > 0 else None,
)""",
)
doc.add_paragraph(
    "Uses half the available CPUs for data loading (max 8). pin_memory enables faster "
    "CPU→GPU transfer. persistent_workers keeps workers alive between epochs. "
    "Without these optimizations: GPU stalls waiting for data, throughput drops 20-40%."
)

doc.add_heading("15.9 Model and Loss", level=2)
add_code_block(
    doc,
    """raw_model = AutoModelForSequenceClassification.from_pretrained(
    model_name, num_labels=2, torch_dtype=torch.float32
).to(device)
model = raw_model

# Class-weighted loss for imbalance
n_pos, n_neg = count_labels(train_labels)
weight_pos = n_neg / n_pos
class_weights = torch.tensor([1.0, weight_pos]).to(device)
loss_fn = CrossEntropyLoss(weight=class_weights)""",
)
doc.add_paragraph(
    "num_labels=2 adds a linear layer mapping 768→2. Class weighting counteracts "
    "imbalance: if 37% duplicates, weight_pos = 1.70. Errors on positives penalized 1.7x more."
)

doc.add_heading("15.10 Optimizer and Scheduler", level=2)
add_code_block(
    doc,
    """optimizer = AdamW(model.parameters(), lr=2e-5, weight_decay=0.01,
                  fused=(device.type == "cuda"))
total_steps = len(train_loader) * num_epochs // gradient_accumulation_steps
warmup_steps = int(total_steps * 0.1)
scheduler = get_linear_schedule_with_warmup(
    optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
)""",
)
doc.add_paragraph(
    "fused=True: 2-3x faster AdamW on GPU. Warmup for 10% of steps, "
    "then linear decay to 0. With 200k samples, batch_size=16, acc_steps=2: "
    "total_steps = 200k/16/2 × 3 = 18,750, warmup = 1,875."
)

doc.add_heading("15.11 Training Loop", level=2)
add_code_block(
    doc,
    """for epoch in range(num_epochs):
    model.train()
    optimizer.zero_grad()
    for step, batch in enumerate(train_loader):
        input_ids, attention_mask, labels = [x.to(device) for x in batch]

        with torch.amp.autocast(device_type=device.type) if use_fp16 else nullcontext():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, labels) / gradient_accumulation_steps

        if use_fp16:
            scaler.scale(loss).backward()
        else:
            loss.backward()

        if (step + 1) % gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            if use_fp16:
                scaler.step(optimizer); scaler.update()
            else:
                optimizer.step()
            scheduler.step()
            optimizer.zero_grad()""",
)
doc.add_paragraph(
    "Gradient accumulation simulates larger batch size. Gradient clipping at 1.0 prevents "
    "destabilizing large gradients. FP16 uses GradScaler to prevent underflow."
)

doc.add_heading("15.12 Validation", level=2)
add_code_block(
    doc,
    """model.eval()
with torch.no_grad():
    for batch in val_loader:
        input_ids, attention_mask, labels = [x.to(device) for x in batch]
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        probs = torch.softmax(outputs.logits, dim=1)
        all_preds.extend(torch.argmax(probs, dim=1).cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

val_f1 = f1_score(all_labels, all_preds)
if val_f1 > best_val_f1:
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)""",
)
doc.add_paragraph(
    "model.eval() disables dropout. torch.no_grad() prevents gradient computation (2x memory savings). "
    "Only saves when validation F1 improves."
)

doc.add_heading("15.13 Test Evaluation and Threshold Search", level=2)
add_code_block(
    doc,
    """for thresh in np.linspace(0.1, 0.9, 81):
    preds = (np.array(test_probs) >= thresh).astype(int)
    f1 = f1_score(test_labels, preds)
    if f1 > best_test_f1:
        best_test_f1 = f1; best_thresh = thresh

results = {
    "model": "deberta-v3-cross-encoder-quora",
    "threshold": float(best_thresh),
    "f1": float(test_f1),
    "roc_auc": float(test_roc),
    # ...
}
with open(results_path, "w") as f:
    json.dump(results, f, indent=2)""",
)
doc.add_paragraph(
    "Scans 81 thresholds from 0.1 to 0.9. Saves metrics to outputs/embedding_models/ for the Streamlit dashboard."
)

doc.add_heading("15.14 CLI Entry Point", level=2)
add_code_block(
    doc,
    """if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-samples", type=int, default=200000)
    parser.add_argument("--max-length", type=int, default=128)
    args = parser.parse_args()

    output = train_cross_encoder(
        model_name="microsoft/deberta-v3-base",
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_train_samples=args.max_samples,
        max_length=args.max_length,
    )
    print(f"Model saved to: {output}")""",
)
doc.add_paragraph("Command-line usage: python scripts/train_cross_encoder.py --epochs 5 --batch-size 16 --lr 3e-5")

# ══════════════════════════════════════════════════════════════════
# APPENDIX
# ══════════════════════════════════════════════════════════════════
doc.add_page_break()
doc.add_heading("Appendix: Quick Reference", level=1)

doc.add_heading("Key Equations", level=2)
add_code_block(
    doc,
    """Attention(Q,K,V) = softmax(Q×K^T/√d_k)×V

MultiHead(Q,K,V) = Concat(head_1,...,head_h)×W_O

FFN(x) = GELU(x×W_1+b_1)×W_2+b_2

LayerNorm(x) = γ×(x-μ)/√(σ²+ε) + β

CrossEntropy = -Σ y×log(p)

AdamW: θ_t = θ_{t-1} - lr×m_t/(√v_t+ε) - lr×weight_decay×θ_{t-1}""",
)

doc.add_heading("Recommended Hyperparameters for DeBERTa-v3-base", level=2)
add_table(
    doc,
    ["Parameter", "Recommended Value", "Notes"],
    [
        ["Learning rate", "2e-5", "1e-5 to 5e-5 range"],
        ["Batch size", "16-32", "Effective with gradient accumulation"],
        ["Epochs", "3-5", "Stop early if val F1 plateaus"],
        ["Warmup ratio", "0.1", "10% of total steps"],
        ["Weight decay", "0.01", "L2 regularization strength"],
        ["Max length", "128", "Quora average = ~40 tokens"],
        ["Dropout", "0.1", "Classification head only"],
        ["Gradient clipping", "1.0", "Prevents gradient explosion"],
    ],
)

doc.add_heading("Tracking Training Progress", level=2)
doc.add_paragraph(
    "Expected loss trajectory:\n"
    "• Start: ~0.69 (random, equivalent to ln(2))\n"
    "• After 1 epoch: ~0.35-0.45\n"
    "• After 3 epochs: ~0.15-0.25\n\n"
    "Expected F1 for Quora duplicate detection:\n"
    "• Bi-Encoder (E5/BGE/MPNet): 0.79-0.82\n"
    "• Cross-Encoder (DeBERTa-v3): 0.84-0.88\n"
    "• Ensemble: 0.86-0.90"
)

# ── Save ────────────────────────────────────────────────────────
output_path = os.path.join(os.path.dirname(__file__), "..", "Cross_Encoders_Complete_Guide.docx")
doc.save(output_path)
print(f"Document saved to: {output_path}")
