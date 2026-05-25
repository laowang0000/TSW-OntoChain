from backend.services.ontology_service import SAMPLE_CSV_PATH
from backend.services.validation_service import validate_transaction_csv


def test_validation_accepts_sample_csv():
    report = validate_transaction_csv(SAMPLE_CSV_PATH)

    assert report["valid"] is True
    assert report["row_count"] == 9
    assert not report["errors"]


def test_validation_reports_missing_required_column(tmp_path):
    csv_path = tmp_path / "missing_column.csv"
    csv_path.write_text(
        "\n".join(
            [
                "tx_hash,sender,receiver,token,amount,timestamp,contract_address",
                "0xBAD,0xSender,0xReceiver,ETH,10,2026-05-10T09:00:00,0xContract",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_transaction_csv(csv_path)

    assert report["valid"] is False
    assert any(error["field"] == "transaction_type" for error in report["errors"])


def test_validation_reports_non_numeric_amount(tmp_path):
    csv_path = tmp_path / "bad_amount.csv"
    csv_path.write_text(
        "\n".join(
            [
                "tx_hash,sender,receiver,token,amount,timestamp,contract_address,transaction_type",
                "0xBAD,0xSender,0xReceiver,ETH,not-a-number,2026-05-10T09:00:00,0xContract,transfer",
            ]
        ),
        encoding="utf-8",
    )

    report = validate_transaction_csv(csv_path)

    assert report["valid"] is False
    assert any(error["field"] == "amount" and "numeric" in error["message"] for error in report["errors"])
