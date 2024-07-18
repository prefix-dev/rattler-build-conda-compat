## Small guide to releasing

Release new version:

1. Update `pyproject.toml` and `pixi.toml`
2. Run `pixi install`
3. Add lock and toml files to commit. 
4. Push to remote and see if CI is green.
5. Build an sdist using `pixi r build_sdist`
6. Create a tag `git tag v{version}` `git push --tags`.
7. Create the release on github and generate release notes.
