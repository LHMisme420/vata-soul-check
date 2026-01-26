# features.py (hardened with deeper analysis)
import ast
import re
from tree_sitter import Language, Parser
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModel
import torch
import nltk
from nltk.corpus import stopwords
import networkx as nx

nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

# Load once
PYTHON_LANGUAGE = Language('build/my-languages.so', 'python')  # Build tree-sitter lang first
parser = Parser()
parser.set_language(PYTHON_LANGUAGE)
tokenizer = AutoTokenizer.from_pretrained("Salesforce/codegen-350M-mono")
model = AutoModelForCausalLM.from_pretrained("Salesforce/codegen-350M-mono")
codebert_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
codebert_model = AutoModel.from_pretrained("microsoft/codebert-base")

def extract_features(code: str, language="python") -> dict:
    features = {}

    # Basic stats
    lines = code.splitlines()
    features["line_count"] = len(lines)
    features["char_count"] = len(code)
    features["avg_line_length"] = features["char_count"] / max(1, features["line_count"])

    # Comment ratio & style (enhanced with relevance)
    comments = re.findall(r'#.*', code)  # Python-style; adjust per lang
    comment_text = ' '.join(comments).lower()
    code_text = re.sub(r'#.*', '', code).lower()  # Code without comments
    comment_words = set(re.findall(r'\b\w+\b', comment_text)) - stop_words
    code_words = set(re.findall(r'\b\w+\b', code_text)) - stop_words
    features["comment_ratio"] = len(comments) / max(1, len(lines))
    features["has_todo"] = 1 if any("TODO" in c.upper() for c in comments) else 0
    features["comment_entropy"] = len(set("".join(comments))) / max(1, len("".join(comments)))  # Low = repetitive = AI-ish
    features["comment_relevance"] = len(comment_words & code_words) / max(1, len(comment_words))  # Overlap; low if fake/dumped

    # AST-based (deeper: depth, branching, graph complexity)
    try:
        tree = parser.parse(bytes(code, "utf8"))
        ast_node = ast.parse(code)
        features["ast_node_count"] = len(list(ast.walk(ast_node)))
        # Depth and branching
        def ast_depth(node, depth=0):
            if not hasattr(node, 'body'): return depth
            return max(ast_depth(child, depth + 1) for child in ast.iter_child_nodes(node)) if ast.iter_child_nodes(node) else depth
        features["ast_max_depth"] = ast_depth(ast_node)
        # Simple graph: nodes as AST elements, edges as parent-child
        G = nx.DiGraph()
        def build_graph(node, parent=None):
            G.add_node(id(node), type=type(node).__name__)
            if parent: G.add_edge(id(parent), id(node))
            for child in ast.iter_child_nodes(node):
                build_graph(child, id(node))
        build_graph(ast_node)
        features["ast_branching_factor"] = np.mean([d for n, d in G.degree() if d > 0]) if G.nodes else 0
    except:
        features["ast_node_count"] = features["ast_max_depth"] = features["ast_branching_factor"] = 0

    # Perplexity proxy (AI code often lower perplexity = more predictable)
    inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs, labels=inputs["input_ids"])
        loss = outputs.loss
    features["perplexity"] = torch.exp(loss).item() if loss is not None else 1.0

    # Variable name entropy + pattern detection (templated = gaming)
    var_names = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
    if var_names:
        counts = np.unique(var_names, return_counts=True)[1]
        probs = counts / len(var_names)
        features["var_name_entropy"] = -np.sum(probs * np.log2(probs))
        # Pattern: high if many follow 'varX' template
        features["var_pattern_ratio"] = sum(1 for v in var_names if re.match(r'\w+\d+', v)) / len(var_names)

    # CodeBERT embedding mean (for style invariance)
    inputs = codebert_tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        embeddings = codebert_model(**inputs).last_hidden_state.mean(dim=1).squeeze().numpy()
    features["codebert_mean"] = np.mean(embeddings)  # Simple scalar; could expand to more dims

    return features