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

The site is built and deployed by Netlify from this directory.
`.ruby-version` pins the Ruby version Netlify's build image ships
preinstalled, so the build doesn't have to compile Ruby from source;
`Gemfile.lock` is locked with the Bundler version that Ruby ships.
When bumping `.ruby-version`, check that the version is preinstalled
on Netlify's current build image and re-lock with that Ruby's Bundler.
