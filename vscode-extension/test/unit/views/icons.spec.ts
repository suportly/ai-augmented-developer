import { expect } from 'chai';

import { makeStatusIcon } from '../../../src/views/icons';

/**
 * Stub doubles for `vscode.ThemeIcon` / `vscode.ThemeColor`. The real classes
 * cannot be imported from unit tests because `vscode` is provided by the host
 * at runtime and externalised by esbuild at build time. The stubs are
 * deliberately structurally compatible (id + optional color) but not nominally
 * typed against the `vscode` declaration — hence the `as any` at the
 * `makeStatusIcon` call site.
 */
class StubThemeIcon {
  constructor(public id: string, public color?: StubThemeColor) {}
}
class StubThemeColor {
  constructor(public id: string) {}
}

const statusIcon = makeStatusIcon({
  // Stubs are structurally compatible; cast bypasses nominal type-checking.
  ThemeIcon: StubThemeIcon as any,
  ThemeColor: StubThemeColor as any,
});

describe('statusIcon', () => {
  it('maps pending to circle-outline with no color', () => {
    const icon = statusIcon('pending') as StubThemeIcon;
    expect(icon).to.be.instanceOf(StubThemeIcon);
    expect(icon.id).to.equal('circle-outline');
    expect(icon.color).to.be.undefined;
  });

  it('maps in_progress to sync~spin tinted with charts.blue', () => {
    const icon = statusIcon('in_progress') as StubThemeIcon;
    expect(icon).to.be.instanceOf(StubThemeIcon);
    expect(icon.id).to.equal('sync~spin');
    expect(icon.color).to.be.instanceOf(StubThemeColor);
    expect(icon.color!.id).to.equal('charts.blue');
  });

  it('maps blocked to error tinted with errorForeground', () => {
    const icon = statusIcon('blocked') as StubThemeIcon;
    expect(icon).to.be.instanceOf(StubThemeIcon);
    expect(icon.id).to.equal('error');
    expect(icon.color).to.be.instanceOf(StubThemeColor);
    expect(icon.color!.id).to.equal('errorForeground');
  });

  it('maps done to check tinted with charts.green', () => {
    const icon = statusIcon('done') as StubThemeIcon;
    expect(icon).to.be.instanceOf(StubThemeIcon);
    expect(icon.id).to.equal('check');
    expect(icon.color).to.be.instanceOf(StubThemeColor);
    expect(icon.color!.id).to.equal('charts.green');
  });

  it('maps unknown to question with no color', () => {
    const icon = statusIcon('unknown') as StubThemeIcon;
    expect(icon).to.be.instanceOf(StubThemeIcon);
    expect(icon.id).to.equal('question');
    expect(icon.color).to.be.undefined;
  });
});
