# Contributing

Thanks for your interest. This is a small analysis project, and issues, corrections and
suggestions are welcome.

## Ground rules

- **Public or synthetic data only.** Never add real patient, incident, ambulance or
  household data, or real field-collected submissions. Start points are synthetic.
- **Assumptions live in `config/`.** Facility capabilities, travel speeds and target
  times are editable assumptions. Change them by editing the CSV files in `config/` and
  stating a source or reason in the pull request. Do not hard-code them in scripts.
- **Record provenance.** Any new input needs a row in `data/README.md` (source, licence,
  retrieval date) and an entry in `data/source-manifest.json`.
- **Not for real emergencies.** Do not describe outputs as verified or as safe to act on.

## Workflow

1. Open an issue first for anything larger than a small fix.
2. Branch from `main` (`phase-eX-<name>` for roadmap phases, `fix-...` or `docs-...`
   otherwise).
3. Keep commits small: one logical change each, with an imperative message
   ("Add travel scenario table").
4. Run `make test` before opening a pull request.
5. Open a pull request using the template. CI must pass.

## Running locally

```sh
make setup   # create .venv and install requirements
make test    # run the tests
```

AccessMod itself runs in Docker; see `docs/ROADMAP.md` and `docs/accessmod-notes.md`.

## Code of conduct

Participation is covered by the [Code of Conduct](CODE_OF_CONDUCT.md).
