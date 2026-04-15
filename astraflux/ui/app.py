# -*- coding: utf-8 -*-

import gradio as gr
from astraflux.definitions.constants import *

from astraflux.ui.components.common import COMMON_CSS, create_side_nav_menu
from astraflux.ui.pages.service_manage import create_service_manage_page
from astraflux.ui.pages.task_manage import create_task_manage_page
from astraflux.ui.pages.ai_tool import create_ai_tool_page


class WebApp:

    def __init__(self, logger, config):
        self.logger = logger
        self.config = config

        self.prot = config.get(WEB.CONFIG.PORT.value, WEB.DEFAULT.PORT.value)
        self.server_name = config.get(WEB.CONFIG.SERVER_NAME.value, WEB.DEFAULT.SERVER_NAME.value)
        self.username = config.get(WEB.CONFIG.USERNAME.value, WEB.DEFAULT.USERNAME.value)
        self.password = config.get(WEB.CONFIG.PASSWORD.value, WEB.DEFAULT.PASSWORD.value)

    def check_login(self, username, password):
        """Verify username and password, return login status"""
        if username == self.username and password == self.password:
            return gr.update(visible=False), gr.update(visible=True), "Login successful! Redirecting to homepage..."
        else:
            return gr.update(visible=True), gr.update(visible=False), "Incorrect username or password, please try again"

    @staticmethod
    def show_service_page():
        """Show Service Management page and activate corresponding button"""
        return (
            gr.update(visible=True),  # Service Management page
            gr.update(visible=False),  # Task Management page
            gr.update(visible=False),  # AI Tools page
            gr.update(variant="primary"),  # Activate Service button
            gr.update(variant="secondary"),  # Deactivate Task button
            gr.update(variant="secondary")  # Deactivate AI button
        )

    @staticmethod
    def show_task_page():
        """Show Task Management page and activate corresponding button"""
        return (
            gr.update(visible=False),  # Service Management page
            gr.update(visible=True),  # Task Management page
            gr.update(visible=False),  # AI Tools page
            gr.update(variant="secondary"),  # Deactivate Service button
            gr.update(variant="primary"),  # Activate Task button
            gr.update(variant="secondary")  # Deactivate AI button
        )

    @staticmethod
    def show_ai_page():
        """Show AI Tools page and activate corresponding button"""
        return (
            gr.update(visible=False),  # Service Management page
            gr.update(visible=False),  # Task Management page
            gr.update(visible=True),  # AI Tools page
            gr.update(variant="secondary"),  # Deactivate Service button
            gr.update(variant="secondary"),  # Deactivate Task button
            gr.update(variant="primary")  # Activate AI button
        )

    def web_launch(self):

        with gr.Blocks() as demo:
            # Global state: control visibility of login page/homepage
            login_panel = gr.Column(visible=True, elem_classes="login-container")
            main_panel = gr.Column(visible=False)

            # -------------------- Login Page --------------------
            with login_panel:
                gr.Markdown("# System Login")
                username = gr.Textbox(label="Username", placeholder="Please enter your username")
                password = gr.Textbox(label="Password", type="password", placeholder="Please enter your password")
                login_btn = gr.Button("Login", variant="primary")
                login_msg = gr.Markdown("", elem_id="login-msg")

            # -------------------- Main Page (displayed after login) --------------------
            with main_panel:
                # Left menu + right content layout (add main-row class to ensure full width)
                with gr.Row(elem_classes="main-row", height="90vh"):
                    # Left navigation menu
                    service_btn, task_btn, ai_tool_btn = create_side_nav_menu()

                    # Right content area (80% width)
                    with gr.Column(elem_classes="main-content"):
                        # Service Management page container (displayed by default)
                        service_page = gr.Column(visible=True)
                        with service_page:
                            create_service_manage_page()

                        # Task Management page container (hidden by default)
                        task_page = gr.Column(visible=False)
                        with task_page:
                            create_task_manage_page()

                        # AI Tools page container (hidden by default)
                        ai_page = gr.Column(visible=False)
                        with ai_page:
                            create_ai_tool_page()

            # -------------------- Event Binding --------------------
            # Login verification
            login_btn.click(
                fn=self.check_login,
                inputs=[username, password],
                outputs=[login_panel, main_panel, login_msg]
            )

            # Left menu navigation - Service Management (sync button active state)
            service_btn.click(
                fn=self.show_service_page,
                outputs=[service_page, task_page, ai_page, service_btn, task_btn, ai_tool_btn]
            )

            # Left menu navigation - Task Management (sync button active state)
            task_btn.click(
                fn=self.show_task_page,
                outputs=[service_page, task_page, ai_page, service_btn, task_btn, ai_tool_btn]
            )

            # Left menu navigation - AI Tools (sync button active state)
            ai_tool_btn.click(
                fn=self.show_ai_page,
                outputs=[service_page, task_page, ai_page, service_btn, task_btn, ai_tool_btn]
            )

        # Launch application (Gradio 6.x specification)
        demo.launch(
            server_name=self.server_name,
            server_port=self.prot,
            debug=True,
            share=False,
            css=COMMON_CSS
        )
