## Small guide to releasing

Release new version:

1. Create a branch `release/v{version}` and do the following:
2. Update `pyproject.toml` and `pixi.toml`
3. Run `pixi install`
4. Add lock and toml files to commit.
5. Push to remote and see if CI is green. *if not*: either make changes in a separate PR (if big), or here (if small).
7. Merge to main.
8. Build an sdist using `pixi r build_sdist`. This needs to succeed.
9. Create a tag `git tag v{version}` `git push --tags`.
10. Create the release on github and generate release notes, upload the generated sdist.
