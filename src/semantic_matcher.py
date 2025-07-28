from sentence_transformers import SentenceTransformer, util
import os


def match_to_job_query(candidates, job_query, model_name="intfloat/e5-small-v2", top_k=5):
    """Use semantic similarity to match heading candidates to a job query"""
    
    # Try to use pre-downloaded model from cache (offline mode)
    cache_dir = "/app/models/sentence-transformers"
    model_cache_path = os.path.join(cache_dir, f"models--{model_name.replace('/', '--')}")
    
    if os.path.exists(model_cache_path):
        # Model exists in cache, load it offline
        print(f"Loading model {model_name} from cache (offline mode)")
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
        os.environ['HF_HUB_OFFLINE'] = '1'  # Force offline mode
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
    else:
        # Fallback to default behavior for local development
        print(f"Loading model {model_name} from Hugging Face (online mode)")
        model = SentenceTransformer(model_name)
    candidate_texts = [c["text"] for c in candidates]

    if not candidate_texts:
        return []

    embeddings = model.encode(candidate_texts, convert_to_tensor=True)
    query_embedding = model.encode(job_query, convert_to_tensor=True)

    cos_scores = util.cos_sim(query_embedding, embeddings)[0]
    top_results = cos_scores.topk(k=min(top_k, len(candidate_texts)))

    top_matches = []
    for idx, score in zip(top_results.indices, top_results.values):
        c = candidates[idx]
        top_matches.append({
            "text": c["text"],
            "score": round(float(score), 3),
            "page_num": c["page_num"],
            "y": c["y"]
        })

    return top_matches
