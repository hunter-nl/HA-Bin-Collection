# Diagnostic scripts

`debug-provider-response.sh` saves raw responses from any provider currently
included in this integration. It supports `mijnafvalwijzer` and `acv` today,
and accepts only the provider names that the integration supports. It redacts
API credentials and household information before writing the file.

```sh
scripts/debug-provider-response.sh \
  --provider mijnafvalwijzer \
  --postcode 1234AB \
  --house-number 1 \
  --output mijnafvalwijzer-response.redacted.json
```

For ACV, the saved file includes both its address response and its calendar
response:

```sh
scripts/debug-provider-response.sh \
  --provider acv \
  --postcode 1234AB \
  --house-number 1
```

The response is not written to the Home Assistant log. Review the generated
file locally and share it only after verifying its contents.
