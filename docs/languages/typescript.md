# TypeScript and Node.js

TypeScript capsules use nvm for the Node.js runtime and npm for deterministic
dependency installation.

Required structure:

```text
.nvmrc
package.json
package-lock.json
tsconfig.json
eslint.config.mjs
src/
test/
```

Requirements:

- pin one Node.js version in `.nvmrc`;
- declare a compatible `engines.node` range in `package.json`;
- commit `package-lock.json` and install with `npm ci`;
- enable strict TypeScript checking;
- expose `format:check`, `lint`, `typecheck`, `build`, and `test` scripts;
- use ESLint and Prettier with committed configuration;
- avoid globally installed packages; and
- run compiled output or an explicitly pinned TypeScript runtime.

Plain JavaScript examples use the same Node.js and npm requirements and enable
type checking through TypeScript `checkJs` or an equivalent configured checker.
