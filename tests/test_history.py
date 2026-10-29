from freeflow.history import History


def test_add_recent_search_and_stats(tmp_path):
    h = History(tmp_path / "history.db")
    h.add("dictate", "um hello world", "Hello world.", app="Slack", audio_seconds=1.5)
    h.add("command", "make it formal", "Dear Sir or Madam,", audio_seconds=1.0)
    recent = h.recent()
    assert [e.mode for e in recent] == ["command", "dictate"]
    assert h.last().final_text == "Dear Sir or Madam,"
    assert [e.app for e in h.recent(search="hello")] == ["Slack"]
    stats = h.stats()
    assert stats.sessions == 2
    assert stats.words == 6
    assert stats.words_today == 6
    assert round(stats.wpm) == 144
    h.clear()
    assert h.recent() == [] and h.last() is None
