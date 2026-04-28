import * as vscode from 'vscode';

/**
 * Thin abstraction over the file-system operations the spec-explorer needs.
 *
 * The production implementation (`VsCodeFileSystem`) wraps the VS Code API so
 * tests can swap in an in-memory fake without booting an extension host.
 */
export interface FileSystem {
  /**
   * List all files matching a glob pattern relative to a folder URI
   * (e.g. "specs/*\/spec.md"). Returns absolute fs paths.
   */
  findFiles(folderFsPath: string, pattern: string): Promise<string[]>;

  /** Read a file as UTF-8 text. */
  readFileText(absoluteFsPath: string): Promise<string>;

  /** Test whether a file exists (no follow-symlink concerns at our layer). */
  exists(absoluteFsPath: string): Promise<boolean>;
}

/** Production `FileSystem` backed by `vscode.workspace`. */
export class VsCodeFileSystem implements FileSystem {
  async findFiles(folderFsPath: string, pattern: string): Promise<string[]> {
    const folderUri = vscode.Uri.file(folderFsPath);
    const relative = new vscode.RelativePattern(folderUri, pattern);
    const uris = await vscode.workspace.findFiles(relative);
    return uris.map((uri) => uri.fsPath);
  }

  async readFileText(absoluteFsPath: string): Promise<string> {
    const uri = vscode.Uri.file(absoluteFsPath);
    const bytes = await vscode.workspace.fs.readFile(uri);
    return Buffer.from(bytes).toString('utf-8');
  }

  async exists(absoluteFsPath: string): Promise<boolean> {
    const uri = vscode.Uri.file(absoluteFsPath);
    try {
      await vscode.workspace.fs.stat(uri);
      return true;
    } catch (err) {
      if (
        err instanceof vscode.FileSystemError &&
        err.code === 'FileNotFound'
      ) {
        return false;
      }
      // Other stat failures (permissions, IO) propagate so callers can react.
      throw err;
    }
  }
}
