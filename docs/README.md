# XKNX website

This is the source for the [XKNX website](http://xknx.io).

# Site preview

Run

```bash
bundle install
bundle exec jekyll build
bundle exec jekyll serve

```

and open [http://127.0.0.1:4000](http://127.0.0.1:4000)

# Deployment

The site is built and deployed by Netlify from this directory; the
Netlify configuration lives in `netlify.toml`.

`.ruby-version` pins the Ruby version Netlify's build image ships
preinstalled (Ruby 3.3.6 on the Ubuntu Noble 24.04 image). Any other
version has to be installed by rvm during the build - which only has
prebuilt binaries for a handful of versions and otherwise compiles Ruby
from source, so the build only succeeds when a build cache with that
Ruby happens to be around. `Gemfile.lock` is locked with the Bundler
version that Ruby ships. When bumping `.ruby-version`, check that the
version is preinstalled on Netlify's current build image and re-lock
with that Ruby's Bundler.

Builds are skipped when nothing in `docs/` changed since the last
successful deploy - see the `ignore` command in `netlify.toml`.
