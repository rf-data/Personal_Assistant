## retrieval_metrics.py
# import


def precision_k():
    """
    = relevant_doc / all_docs
    """

    return


def recall_k():
    """
    = relevant_doc / all_relevant_docs
    """

    return


def hit_rate_k():
    """
    if at least one relevant_doc --> 1
    else --> 0
    """

    return


def mrr():
    """mean reciprocal rank

    ???? mrr = 1/N * sum(1/rank_1st_relevant_doc)
    """
    return


def map():
    """mean average precision

    MAP = 1/N * sum(1 / query_ap)
    """

    return


def ndcg():
    """normalized discounted cumulative gain

    NDCG@K = DCG@K / IDCG@K
    """

    return


def coverage():
    """coverage

    coverage = unique_relevant_info_retrieved / total_relevant_info
    """

    return
