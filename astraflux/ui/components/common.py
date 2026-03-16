# -*- coding: utf-8 -*-
import gradio as gr

# Global styles (adapted for left sidebar + small buttons + active state)
COMMON_CSS = """
/* Left sidebar style - width set to 1/10 of the page */
.side-nav {
    width: 10% !important;  /* 1/10 of the page */
    min-width: 120px;       /* Minimum width to avoid being too narrow */
    max-width: 180px;       /* Maximum width to avoid being too wide */
    padding: 10px;
    border-right: 1px solid #e5e7eb;
}
/* Small button style - reduce height */
.nav-btn {
    width: 100%;
    margin: 3px 0 !important;  /* Reduce vertical margin */
    padding: 6px 8px !important;/* Reduce padding to lower height */
    font-size: 14px !important; /* Reduce font size */
    height: auto !important;    /* Auto height adaptation */
}
/* Login page container */
.login-container {
    max-width: 400px;
    margin: 50px auto;
}
/* Main content area */
.main-content {
    width: 90% !important;  /* Remaining 9/10 width for content area */
    padding: 20px;
    flex: 1;
}
/* Main page row layout - ensure sidebar + content fill full width */
.main-row {
    width: 100% !important;
    display: flex;
}
"""


def create_side_nav_menu():
    """Create left vertical navigation menu (displayed after login)"""
    with gr.Column(elem_classes="side-nav"):
        gr.Markdown("### Function Menu")
        # Define small buttons, activate Service Management by default
        service_btn = gr.Button("Service Management", variant="primary", elem_classes="nav-btn")
        task_btn = gr.Button("Task Management", variant="secondary", elem_classes="nav-btn")
        ai_tool_btn = gr.Button("AI Tools", variant="secondary", elem_classes="nav-btn")
    return service_btn, task_btn, ai_tool_btn
