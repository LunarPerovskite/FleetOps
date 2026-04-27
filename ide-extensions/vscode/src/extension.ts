/*
 * FleetOps VS Code Extension
 * Universal agent governance for VS Code, Cursor, and any code editor
 */

import * as vscode from 'vscode';
import * as path from 'path';

// ─── Configuration ───
interface FleetOpsConfig {
    apiUrl: string;
    apiKey?: string;
    agentType: string;
    autoApproveSafe: boolean;
    showNotifications: boolean;
}

// ─── Types ───
interface ApprovalResult {
    canProceed: boolean;
    status: string;
    approvalId?: string;
    dangerLevel?: string;
    message: string;
}

interface ApprovalRequest {
    agentId: string;
    agentName: string;
    action: string;
    arguments?: string;
    filePath?: string;
    environment: string;
    estimatedCost?: number;
}

// ─── FleetOps Client ───
class FleetOpsClient {
    private config: FleetOpsConfig;

    constructor(config: FleetOpsConfig) {
        this.config = config;
    }

    async requestApproval(request: ApprovalRequest): Promise<ApprovalResult> {
        try {
            const response = await fetch(`${this.config.apiUrl}/api/v1/approvals/request`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
                },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            // Fail-safe: if FleetOps is down, allow but warn
            vscode.window.showWarningMessage(
                'FleetOps is unavailable. Proceeding without approval.',
                'Open Settings'
            );
            return {
                canProceed: true,
                status: 'fleetops_unavailable',
                message: 'FleetOps unavailable, proceeding with caution'
            };
        }
    }

    async approve(approvalId: string, scope: string = 'once'): Promise<any> {
        const response = await fetch(`${this.config.apiUrl}/api/v1/approvals/${approvalId}/approve`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
            },
            body: JSON.stringify({ scope })
        });
        return response.json();
    }

    async reject(approvalId: string, comments?: string): Promise<any> {
        const response = await fetch(`${this.config.apiUrl}/api/v1/approvals/${approvalId}/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(this.config.apiKey && { 'Authorization': `Bearer ${this.config.apiKey}` })
            },
            body: JSON.stringify({ comments })
        });
        return response.json();
    }

    async getPending(): Promise<any[]> {
        try {
            const response = await fetch(`${this.config.apiUrl}/api/v1/approvals/pending`, {
                headers: this.config.apiKey ? { 'Authorization': `Bearer ${this.config.apiKey}` } : {}
            });
            const data = await response.json();
            return data.items || [];
        } catch {
            return [];
        }
    }

    async getStatus(): Promise<any> {
        try {
            const response = await fetch(`${this.config.apiUrl}/api/v1/status`, {
                headers: this.config.apiKey ? { 'Authorization': `Bearer ${this.config.apiKey}` } : {}
            });
            return response.json();
        } catch {
            return { status: 'unavailable' };
        }
    }
}

// ─── Status Bar Item ───
let statusBarItem: vscode.StatusBarItem;

function updateStatusBar(client: FleetOpsClient) {
    client.getPending().then(pending => {
        const count = pending.length;
        if (count > 0) {
            statusBarItem.text = `$(warning) FleetOps: ${count} pending`;
            statusBarItem.tooltip = `${count} approvals waiting`;
            statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        } else {
            statusBarItem.text = `$(shield) FleetOps`;
            statusBarItem.tooltip = 'FleetOps connected';
            statusBarItem.backgroundColor = undefined;
        }
        statusBarItem.show();
    });
}

// ─── Approval Panel ───
class ApprovalPanel {
    public static currentPanel: ApprovalPanel | undefined;
    private panel: vscode.WebviewPanel;

    constructor(context: vscode.ExtensionContext, approvals: any[]) {
        this.panel = vscode.window.createWebviewPanel(
            'fleetopsApprovals',
            'FleetOps Approvals',
            vscode.ViewColumn.One,
            { enableScripts: true }
        );

        this.panel.webview.html = this.getHtml(approvals);
    }

    private getHtml(approvals: any[]): string {
        const items = approvals.map(a => `
            <div style="padding: 10px; border: 1px solid #444; margin: 5px; border-radius: 5px;">
                <div style="display: flex; justify-content: space-between;">
                    <strong>${a.agent_name || 'Unknown'}</strong>
                    <span style="color: ${this.getDangerColor(a.danger_level)};">${a.danger_level?.toUpperCase() || 'UNKNOWN'}</span>
                </div>
                <div style="color: #ccc; margin: 5px 0;">${a.action || ''}</div>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button onclick="approve('${a.id}', 'once')" style="background: #4CAF50; color: white; border: none; padding: 5px 15px; cursor: pointer;">Approve Once</button>
                    <button onclick="approve('${a.id}', 'session')" style="background: #2196F3; color: white; border: none; padding: 5px 15px; cursor: pointer;">Approve Session</button>
                    <button onclick="reject('${a.id}')" style="background: #f44336; color: white; border: none; padding: 5px 15px; cursor: pointer;">Reject</button>
                </div>
            </div>
        `).join('');

        return `<!DOCTYPE html>
        <html>
        <head>
            <style>
                body { background: #1e1e1e; color: #d4d4d4; font-family: sans-serif; padding: 20px; }
                h1 { color: #4CAF50; }
                .empty { text-align: center; padding: 50px; color: #666; }
            </style>
        </head>
        <body>
            <h1>🛡️ FleetOps Approvals</h1>
            ${items || '<div class="empty">No pending approvals 🎉</div>'}
            <script>
                const vscode = acquireVsCodeApi();
                function approve(id, scope) {
                    vscode.postMessage({ command: 'approve', id, scope });
                }
                function reject(id) {
                    vscode.postMessage({ command: 'reject', id });
                }
            </script>
        </body>
        </html>`;
    }

    private getDangerColor(level: string): string {
        const colors: Record<string, string> = {
            'safe': '#4CAF50',
            'low': '#FFEB3B',
            'medium': '#FF9800',
            'high': '#f44336',
            'critical': '#9C27B0'
        };
        return colors[level] || '#666';
    }

    public static createOrShow(context: vscode.ExtensionContext, approvals: any[]) {
        if (ApprovalPanel.currentPanel) {
            ApprovalPanel.currentPanel.panel.reveal();
        } else {
            ApprovalPanel.currentPanel = new ApprovalPanel(context, approvals);
        }
    }
}

// ─── Terminal Interceptor ───
class TerminalInterceptor {
    private client: FleetOpsClient;
    private disposables: vscode.Disposable[] = [];

    constructor(client: FleetOpsClient) {
        this.client = client;
    }

    activate() {
        // Intercept terminal creation
        vscode.window.onDidOpenTerminal(terminal => {
            this.interceptTerminal(terminal);
        }, null, this.disposables);
    }

    private interceptTerminal(terminal: vscode.Terminal) {
        // Show warning for new terminals
        const config = vscode.workspace.getConfiguration('fleetops');
        if (config.get<boolean>('interceptTerminals', true)) {
            vscode.window.showInformationMessage(
                `FleetOps: Monitoring terminal "${terminal.name}"`,
                'Disable for this session'
            );
        }
    }

    dispose() {
        this.disposables.forEach(d => d.dispose());
    }
}

// ─── Main Extension Activation ───
export async function activate(context: vscode.ExtensionContext) {
    console.log('FleetOps extension activating...');

    // Load configuration
    const config = vscode.workspace.getConfiguration('fleetops');
    const fleetopsConfig: FleetOpsConfig = {
        apiUrl: config.get<string>('apiUrl', 'http://localhost:8000'),
        apiKey: config.get<string>('apiKey'),
        agentType: config.get<string>('agentType', 'vscode_extension'),
        autoApproveSafe: config.get<boolean>('autoApproveSafe', true),
        showNotifications: config.get<boolean>('showNotifications', true)
    };

    // Create client
    const client = new FleetOpsClient(fleetopsConfig);

    // Create status bar
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'fleetops.showApprovals';
    context.subscriptions.push(statusBarItem);

    // Update status periodically
    updateStatusBar(client);
    setInterval(() => updateStatusBar(client), 30000); // Every 30 seconds

    // ─── Commands ───

    // Show approvals panel
    context.subscriptions.push(
        vscode.commands.registerCommand('fleetops.showApprovals', async () => {
            const pending = await client.getPending();
            ApprovalPanel.createOrShow(context, pending);
        })
    );

    // Approve command
    context.subscriptions.push(
        vscode.commands.registerCommand('fleetops.approve', async () => {
            const id = await vscode.window.showInputBox({ prompt: 'Approval ID:' });
            if (id) {
                const scope = await vscode.window.showQuickPick(
                    ['once', 'session', 'workspace', 'always'],
                    { placeHolder: 'Select approval scope' }
                );
                if (scope) {
                    await client.approve(id, scope);
                    vscode.window.showInformationMessage(`Approved ${id} (${scope})`);
                    updateStatusBar(client);
                }
            }
        })
    );

    // Reject command
    context.subscriptions.push(
        vscode.commands.registerCommand('fleetops.reject', async () => {
            const id = await vscode.window.showInputBox({ prompt: 'Approval ID:' });
            if (id) {
                const comments = await vscode.window.showInputBox({ prompt: 'Reason (optional):' });
                await client.reject(id, comments);
                vscode.window.showInformationMessage(`Rejected ${id}`);
                updateStatusBar(client);
            }
        })
    );

    // Check before execute (for AI agents)
    context.subscriptions.push(
        vscode.commands.registerCommand('fleetops.checkBeforeExecute', async (command: string) => {
            const result = await client.requestApproval({
                agentId: `${fleetopsConfig.agentType}-${vscode.env.machineId}`,
                agentName: 'VS Code Agent',
                action: 'bash',
                arguments: command,
                environment: 'development'
            });

            if (!result.canProceed) {
                vscode.window.showErrorMessage(
                    `FleetOps blocked: ${result.message}`,
                    'View Details'
                );
            }

            return result;
        })
    );

    // Configure FleetOps
    context.subscriptions.push(
        vscode.commands.registerCommand('fleetops.configure', async () => {
            const apiUrl = await vscode.window.showInputBox({
                prompt: 'FleetOps API URL:',
                value: fleetopsConfig.apiUrl
            });
            if (apiUrl) {
                await config.update('apiUrl', apiUrl, true);
            }
        })
    );

    // ─── Terminal Interceptor ───
    const interceptor = new TerminalInterceptor(client);
    interceptor.activate();
    context.subscriptions.push(interceptor);

    // ─── Webview Message Handler ───
    if (ApprovalPanel.currentPanel) {
        ApprovalPanel.currentPanel.panel.webview.onDidReceiveMessage(
            async message => {
                switch (message.command) {
                    case 'approve':
                        await client.approve(message.id, message.scope);
                        vscode.window.showInformationMessage(`Approved ${message.id}`);
                        updateStatusBar(client);
                        break;
                    case 'reject':
                        await client.reject(message.id);
                        vscode.window.showInformationMessage(`Rejected ${message.id}`);
                        updateStatusBar(client);
                        break;
                }
            }
        );
    }

    vscode.window.showInformationMessage('FleetOps extension activated! 🛡️');
}

export function deactivate() {
    console.log('FleetOps extension deactivated');
}
