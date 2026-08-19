import pandas as pd

from agents.gold_agent import _build_gold_transactions
from agents.profiler import _infer_semantic_meaning
from agents.sttm_generator import _standardize_name


def test_infer_semantic_meaning():
    assert _infer_semantic_meaning("product_id") == "identifier"
    assert _infer_semantic_meaning("transaction_date") == "date/time"
    assert _infer_semantic_meaning("unit_price") == "monetary value"


def test_standardize_name():
    assert _standardize_name(" Order Qty ") == "order_qty"


def test_build_gold_transactions_joins_on_shared_id():
    sales = pd.DataFrame({"product_id": ["P1", "P2"], "store_id": ["S1", "S1"], "total_amount": [10.0, 20.0]})
    products = pd.DataFrame({"product_id": ["P1", "P2"], "category": ["A", "B"]})
    tables = {"sales_data": sales, "products": products}

    joined = _build_gold_transactions(tables)
    assert "category" in joined.columns
    assert len(joined) == 2
