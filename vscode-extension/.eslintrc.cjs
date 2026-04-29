/* eslint config for the aiadev Spec Explorer VS Code extension. */
module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 2022,
    sourceType: 'module',
    project: false,
  },
  plugins: ['@typescript-eslint'],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  env: {
    node: true,
    es2022: true,
  },
  rules: {
    'no-console': 'error',
    '@typescript-eslint/no-explicit-any': 'error',
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    '@typescript-eslint/no-inferrable-types': 'off',
    'prefer-const': 'error',
  },
  ignorePatterns: [
    'out/',
    'node_modules/',
    'test/',
    '.mocharc.json',
    'esbuild.mjs',
    '.eslintrc.cjs',
  ],
};
