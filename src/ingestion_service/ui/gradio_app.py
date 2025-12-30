# gradio/gradio_app.py
import os
import requests
import gradio as gr

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")


def submit_ingest(source_type: str, file_obj):
    metadata = {}
    if file_obj:
        metadata["filename"] = file_obj.name

    response = requests.post(
        f"{API_BASE_URL}/v1/ingest",
        json={"source_type": source_type, "metadata": metadata},
        timeout=5,
    )

    if response.status_code != 202:
        return f"Error submitting ingestion: {response.status_code}"

    data = response.json()
    return f"Ingestion accepted.\nID: {data['ingestion_id']}"


def check_status(ingestion_id: str):
    response = requests.get(
        f"{API_BASE_URL}/v1/ingest/{ingestion_id}",
        timeout=5,
    )
    if response.status_code == 404:
        return "Ingestion ID not found"
    data = response.json()
    return f"Status: {data['status']}"


def build_ui():
    with gr.Blocks(title="Agentic RAG Ingestion") as demo:
        gr.Markdown("# Agentic RAG Ingestion (MS2 Demo)")

        with gr.Row():
            source_type = gr.Dropdown(
                choices=["file", "bytes", "uri"],
                value="file",
                label="Source Type",
            )
            file_input = gr.File(label="Upload File")
            submit_btn = gr.Button("Submit Ingestion")

        submission_output = gr.Textbox(label="Submission Result")

        submit_btn.click(
            fn=submit_ingest,
            inputs=[source_type, file_input],
            outputs=[submission_output],
        )

        gr.Markdown("## Check Status")
        ingestion_id_input = gr.Textbox(label="Ingestion ID")
        status_btn = gr.Button("Check Status")
        status_output = gr.Textbox(label="Status")

        status_btn.click(
            fn=check_status,
            inputs=[ingestion_id_input],
            outputs=[status_output],
        )

    return demo


if __name__ == "__main__":
    ui = build_ui()
    ui.launch(server_port=7860, server_name="0.0.0.0")
