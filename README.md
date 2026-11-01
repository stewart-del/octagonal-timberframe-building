# octagonal-timberframe-building
Octagonal timberframe building approx 600sq ft

## Viewer and review

The recovered NAV-04 viewer is in [`index.html`](index.html). It is a self-contained HTML application with the complete 104-member prototype geometry embedded. Open it locally, or serve this directory with `python3 -m http.server 8000` and visit `http://localhost:8000`.

The [project status](docs/PROJECT_STATUS.md) and [source and review notes](docs/SOURCE-AND-REVIEW.md) explain what is preserved, what was tested, and which joinery decisions remain unresolved. This prototype is not a construction-approved cutting plan.

### Checks

```sh
python3 tests/validate_model.py
node tests/viewer-regression.cjs index.html
```

The model-integrity check and 24 browserless viewer logic assertions passed. Real browser/WebGL rendering and mobile layout have not been verified in this continuation.
