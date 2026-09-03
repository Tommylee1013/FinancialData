# Fed Policy Probability

FedWatch-style FOMC decision probabilities using CBOT 30-Day Federal Funds Futures (`ZQ`) and EFFR.

- Meeting dates come from `macro.macro_data` symbol `FDTR`.
- Raw OHLC data is stored in `fed_policy.fed_funds_futures` and `fed_policy.effective_fed_funds_rate`.
- Long-form scenario probabilities are stored in `fed_policy.meeting_probabilities`.
- Every stored series includes `base_date`, `release_date`, `time`, and `time_zone`.

```bash
python -m src.fed_policy.job --start 2024-01-01
python -m src.fed_policy.job --start 2024-01-01 --meeting 2026-09-16
```

Future meetings not yet present in `FDTR` can be supplied with repeatable `--meeting` arguments.
