# Ruby

Required structure:

```text
.ruby-version
Gemfile
Gemfile.lock
lib/
spec/                    # or test/
```

Requirements:

- pin the Ruby runtime in `.ruby-version`;
- declare the compatible Ruby range in the Gemfile or gem specification;
- commit `Gemfile.lock`;
- install through Bundler;
- run RuboCop with committed configuration;
- run either RSpec or Minitest consistently; and
- execute commands with `bundle exec`.

Do not publish a gem from this repository. A reusable library with its own
release lifecycle belongs in a purpose-built repository.
