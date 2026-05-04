import * as path from 'path';

// At runtime the compiled file lives at `out/test/integration/suite/`,
// so four `..` segments bring us back to the extension root where
// `package.json` lives. Source layout (`test/integration/suite/`) needs
// the same depth, so this resolves correctly under both ts-node and the
// compiled extension-host run.
const manifestPath = path.resolve(__dirname, '..', '..', '..', '..', 'package.json');
const manifest = require(manifestPath) as { publisher: string; name: string };

export const EXTENSION_ID = `${manifest.publisher}.${manifest.name}`;
