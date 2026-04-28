import { expect } from 'chai';

describe('extension bootstrap', () => {
  it('exposes activate as a function from the built bundle', () => {
    // The assertion is intentionally on the BUILT artefact (out/extension.js),
    // not the TS source — this test fails until `npm run build` has run.
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const built = require('../../out/extension.js');
    expect(built).to.have.property('activate');
    expect(built.activate).to.be.a('function');
    expect(built).to.have.property('deactivate');
    expect(built.deactivate).to.be.a('function');
  });
});
