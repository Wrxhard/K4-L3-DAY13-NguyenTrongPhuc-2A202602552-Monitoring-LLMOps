from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd_and_credit_card_formats() -> None:
    for value, marker in (
        ("001234567890", "REDACTED_CCCD"),
        ("4111 1111 1111 1111", "REDACTED_CREDIT_CARD"),
        ("4111-1111-1111-1111", "REDACTED_CREDIT_CARD"),
    ):
        out = scrub_text(f"Identifier: {value}")
        assert out == f"Identifier: [{marker}]"


def test_scrub_extended_contact_and_identifier_formats() -> None:
    for value, marker in (
        ("student+lab@vinuni.edu.vn", "REDACTED_EMAIL"),
        ("+84 (0)90 123 4567", "REDACTED_PHONE_VN"),
        ("001 234 567 890", "REDACTED_CCCD"),
        ("4111.1111.1111.1111", "REDACTED_CREDIT_CARD"),
    ):
        out = scrub_text(f"Identifier: {value}")
        assert out == f"Identifier: [{marker}]"
