import { expect } from 'chai';
import * as fs from 'node:fs';
import * as path from 'node:path';

const manifestPath = path.resolve(__dirname, '../../package.json');
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8')) as Record<string, unknown>;

describe('manifest', () => {
  it('declares activationEvents for the spec explorer view', () => {
    expect((manifest as any).activationEvents).to.deep.equal(['onView:aiadev.specExplorer']);
  });

  it('declares untrustedWorkspaces capability as supported', () => {
    expect((manifest as any).capabilities.untrustedWorkspaces).to.deep.equal({ supported: true });
  });

  it('declares an activitybar viewsContainer for aiadev', () => {
    const containers = (manifest as any).contributes.viewsContainers.activitybar;
    expect(containers).to.be.an('array').with.lengthOf(1);
    const entry = containers[0];
    expect(entry.id).to.equal('aiadev');
    expect(entry.title).to.equal('aiadev');
    expect(entry.icon).to.be.a('string');
  });

  it('points the activitybar icon at a file that exists on disk', () => {
    const iconRel = (manifest as any).contributes.viewsContainers.activitybar[0].icon as string;
    const iconAbs = path.resolve(__dirname, '../..', iconRel);
    expect(fs.existsSync(iconAbs), `icon missing at ${iconAbs}`).to.equal(true);
  });

  it('declares the spec explorer view inside the aiadev container', () => {
    const views = (manifest as any).contributes.views;
    expect(views.aiadev).to.deep.equal([
      { id: 'aiadev.specExplorer', name: 'Spec Explorer' },
    ]);
  });

  it('declares the configuration property aiadev.specExplorer.specsRoot', () => {
    expect((manifest as any).contributes.configuration).to.deep.equal({
      title: 'aiadev Spec Explorer',
      properties: {
        'aiadev.specExplorer.specsRoot': {
          type: 'string',
          default: 'specs',
          scope: 'resource',
          description: 'Root directory under each workspace folder where aiadev specs live.',
        },
      },
    });
  });

  it('declares the refresh command', () => {
    const commands = (manifest as any).contributes.commands as any[];
    const refresh = commands.find((c) => c.command === 'aiadev.specExplorer.refresh');
    expect(refresh).to.deep.equal({
      command: 'aiadev.specExplorer.refresh',
      title: 'Refresh',
      category: 'aiadev',
      icon: '$(refresh)',
    });
  });

  it('binds the refresh command to the spec explorer view title menu', () => {
    const menus = (manifest as any).contributes.menus['view/title'] as any[];
    const entry = menus.find(
      (m) => m.command === 'aiadev.specExplorer.refresh' && m.when === 'view == aiadev.specExplorer',
    );
    expect(entry).to.deep.equal({
      command: 'aiadev.specExplorer.refresh',
      when: 'view == aiadev.specExplorer',
      group: 'navigation',
    });
  });
});
