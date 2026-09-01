from cashgraph.extract import extract_cashtags


def test_extracts_common_and_class_tickers():
    text = "Buying $AAPL $NVDA $BRK.B and $BTC-USD but not $123.45 cash"
    tags = extract_cashtags(text)
    assert "AAPL" in tags
    assert "NVDA" in tags
    assert "BRK.B" in tags
    assert "BTC-USD" in tags
    assert "123" not in tags
    assert "45" not in tags


def test_dedupes_and_uppercases():
    assert extract_cashtags("$nvda then $NVDA") == ["NVDA"]
