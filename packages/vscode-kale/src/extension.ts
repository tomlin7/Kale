import * as vscode from 'vscode';
import * as path from 'path';
import * as cp from 'child_process';

let statusBarItem: vscode.StatusBarItem;

export function activate(context: vscode.ExtensionContext): void {
    // Status bar
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    statusBarItem.text = '$(zap) Kale';
    statusBarItem.tooltip = 'Kale Language';
    statusBarItem.command = 'kale.runFile';
    context.subscriptions.push(statusBarItem);

    // Show/hide status bar based on active editor
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(updateStatusBar)
    );
    updateStatusBar(vscode.window.activeTextEditor);

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('kale.runFile', () => runKaleCommand('run')),
        vscode.commands.registerCommand('kale.buildFile', () => runKaleCommand('build')),
        vscode.commands.registerCommand('kale.checkFile', () => runKaleCommand('check')),
        vscode.commands.registerCommand('kale.dumpAst', () => runKaleCommand('dump-ast')),
        vscode.commands.registerCommand('kale.dumpTokens', () => runKaleCommand('dump-tokens')),
        vscode.commands.registerCommand('kale.dumpLlvm', () => runKaleCommand('dump-llvm')),
    );
}

export function deactivate(): void {
    statusBarItem?.dispose();
}

// ─── Helpers ────────────────────────────────────────────────────────────────

function updateStatusBar(editor: vscode.TextEditor | undefined): void {
    const config = vscode.workspace.getConfiguration('kale');
    const show = config.get<boolean>('showStatusBarItem', true);

    if (show && editor && editor.document.languageId === 'kale') {
        statusBarItem.show();
    } else {
        statusBarItem.hide();
    }
}

function getActiveFilePath(): string | undefined {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.languageId !== 'kale') {
        vscode.window.showWarningMessage('Open a Kale (.kl) file first.');
        return undefined;
    }
    return editor.document.uri.fsPath;
}

function getKaleExecutable(): string {
    const config = vscode.workspace.getConfiguration('kale');
    return config.get<string>('executablePath', 'uv run kale');
}

function getWorkspaceRoot(filePath: string): string {
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(filePath));
    return workspaceFolder?.uri.fsPath ?? path.dirname(filePath);
}

function runKaleCommand(subcommand: string): void {
    const filePath = getActiveFilePath();
    if (!filePath) {
        return;
    }

    const executable = getKaleExecutable();
    const cwd = getWorkspaceRoot(filePath);

    // Build command: e.g. "uv run kale run examples/hello.kl"
    // Use a relative path from workspace root for cleaner output
    const relPath = path.relative(cwd, filePath).replace(/\\/g, '/');
    const fullCommand = `${executable} ${subcommand} ${relPath}`;

    // Ensure the terminal panel is visible
    const terminal = getOrCreateTerminal();
    terminal.show(true);
    terminal.sendText(fullCommand);
}

let _terminal: vscode.Terminal | undefined;

function getOrCreateTerminal(): vscode.Terminal {
    // Reuse an existing terminal named "Kale" if available
    const existing = vscode.window.terminals.find(t => t.name === 'Kale');
    if (existing) {
        _terminal = existing;
        return _terminal;
    }

    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    _terminal = vscode.window.createTerminal({ name: 'Kale', cwd });

    // Clean up reference when terminal is closed
    vscode.window.onDidCloseTerminal(t => {
        if (t === _terminal) {
            _terminal = undefined;
        }
    });

    return _terminal;
}
