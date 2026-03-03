from app.schemas import TTSRequest


def test_default_values():
    payload = TTSRequest(text="Привет, мир")
    assert payload.language == "ru"
    assert payload.format == "wav"
    assert payload.voice is None


def test_reject_non_wav():
    try:
        TTSRequest(text="Привет", format="mp3")
        assert False, "Validation must fail"
    except Exception as exc:
        assert "Only 'wav' format is supported in MVP." in str(exc)

