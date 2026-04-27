/*
 * FleetOps JetBrains Plugin
 * Works with IntelliJ IDEA, PyCharm, WebStorm, Rider, etc.
 */

package com.fleetops.intellij;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.wm.StatusBar;
import com.intellij.openapi.wm.StatusBarWidget;
import com.intellij.openapi.wm.WindowManager;
import com.intellij.util.Consumer;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.*;
import java.awt.event.MouseEvent;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/**
 * FleetOps status bar widget for JetBrains IDEs
 */
public class FleetOpsStatusBarWidget implements StatusBarWidget, StatusBarWidget.IconPresentation {
    
    private final HttpClient httpClient = HttpClient.newHttpClient();
    private String apiUrl = "http://localhost:8000";
    private int pendingCount = 0;
    
    public FleetOpsStatusBarWidget() {
        // Load configuration
        this.apiUrl = System.getProperty("fleetops.apiUrl", "http://localhost:8000");
    }
    
    @Override
    @NotNull
    public String ID() {
        return "FleetOpsStatusBarWidget";
    }
    
    @Override
    @Nullable
    public Icon getIcon() {
        return pendingCount > 0 
            ? AllIcons.General.Warning 
            : AllIcons.Actions.IntentionBulb;
    }
    
    @Override
    @Nullable
    public String getTooltipText() {
        return pendingCount > 0 
            ? String.format("FleetOps: %d pending approvals", pendingCount)
            : "FleetOps connected";
    }
    
    @Override
    @Nullable
    public Consumer<MouseEvent> getClickConsumer() {
        return event -> {
            // Open approvals panel on click
            showApprovalsPanel();
        };
    }
    
    private void showApprovalsPanel() {
        // Show approvals tool window
        // Implementation would open a FleetOps tool window
    }
    
    public void updatePendingCount(int count) {
        this.pendingCount = count;
    }
    
    @Override
    public void install(@NotNull StatusBar statusBar) {
        // Start polling for updates
        startPolling();
    }
    
    @Override
    public void dispose() {
        // Cleanup
    }
    
    private void startPolling() {
        // Poll FleetOps API every 30 seconds
        // Implementation would use ScheduledExecutorService
    }
    
    /**
     * Check if an action should proceed
     */
    public boolean checkBeforeExecute(String tool, String command, String filePath) {
        try {
            String json = String.format(
                "{\"agentId\":\"jetbrains-%s\",\"agentName\":\"JetBrains IDE\",\"action\":\"%s\",\"arguments\":\"%s\",\"filePath\":\"%s\"}",
                System.getProperty("user.name"),
                tool,
                command.replace("\"", "\\\""),
                filePath != null ? filePath : ""
            );
            
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(apiUrl + "/api/v1/approvals/request"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();
            
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            
            if (response.statusCode() == 200) {
                // Parse response - check if canProceed
                return response.body().contains("\"can_proceed\":true");
            }
        } catch (IOException | InterruptedException e) {
            // Fail-safe: allow if FleetOps unavailable
            return true;
        }
        
        return false;
    }
}
