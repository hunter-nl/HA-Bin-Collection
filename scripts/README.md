# Diagnostic scripts

`debug_mijnafvalwijzer_response.py` saves the full MijnAfvalwijzer API response
to a local file for provider investigation. It redacts API credentials and
household information before writing the file.

```sh
uv run python scripts/debug_mijnafvalwijzer_response.py \
  --postcode 1234AB \
  --house-number 1 \
  --output mijnafvalwijzer-response.redacted.json
```

The response is not written to the Home Assistant log. Review the generated
file locally and share it only after verifying its contents.
