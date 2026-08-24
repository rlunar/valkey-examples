# PHP

Required structure:

```text
composer.json
composer.lock
src/
tests/
phpunit.xml
phpstan.neon
```

Requirements:

- declare the PHP runtime requirement and `config.platform.php` in
  `composer.json`;
- commit `composer.lock`;
- use PSR-4 autoloading;
- run `composer validate --strict`;
- install with non-interactive, locked Composer settings;
- run a configured formatter or coding-standard check;
- run PHPStan at the repository-approved level; and
- run PHPUnit.

Pin the local PHP runtime through the capsule's immutable container image when
no project-approved local version manager exists.
