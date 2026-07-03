import argparse
import json
import os
from src.config.env import get_settings
from src.config.schema import ReportConfig
from src.report.assembler import assemble_report
from src.utils.logger import log_info, log_success, log_error, log_warning
from src.utils.spinner import spinner_context

def main():
    parser = argparse.ArgumentParser(
        description="Relationship Compatibility Report Engine. Orchestrates astronomical data calculations and Gemini insights."
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default="sample/input.json",
        help="Path to the JSON configuration input file (default: sample/input.json)"
    )
    args = parser.parse_args()

    log_info("Starting Relationship Compatibility Report Engine...")

    # 1. Load and Validate Environment Variables
    try:
        settings = get_settings()
        log_success("Environment variables loaded and validated.")
    except Exception as e:
        log_error(f"Failed to load environment variables: {e}")
        return

    # 2. Read and Validate Configuration JSON file
    if not os.path.exists(args.config):
        log_error(f"Configuration file not found at: {args.config}")
        return

    try:
        log_info(f"Loading configuration from: {args.config}")
        with open(args.config, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        config = ReportConfig(**config_data)
        log_success("Configuration parsed and validated successfully.")
    except Exception as e:
        log_error(f"Configuration validation failed: {e}")
        return

    # 3. Assemble the Report (Geocoding, VedAstro calculations, Mapping, Gemini call)
    try:
        with spinner_context("Generating cosmic compatibility report... This may take a moment.") as sp:
            report_md, context = assemble_report(
                primary=config.primary,
                secondary=config.secondary,
                opencage_api_key=settings.opencage_api_key,
                gemini_api_key=settings.gemini_api_key
            )
    except Exception as e:
        log_error(f"An error occurred during report generation: {e}")
        return

    # 4. Save Output Files
    try:
        os.makedirs(config.outputDir, exist_ok=True)
        
        # Define output filenames
        p_name = config.primary.name.lower().replace(" ", "_")
        s_name = config.secondary.name.lower().replace(" ", "_")
        
        report_path = os.path.join(config.outputDir, f"{p_name}_{s_name}_report.md")
        context_path = os.path.join(config.outputDir, f"{p_name}_{s_name}_context.json")
        
        log_info(f"Writing output files to: {config.outputDir}")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)
            
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(context, f, indent=2)
            
        log_success(f"Relationship compatibility report successfully saved to: {report_path}")
        log_success(f"Astrological calculations context successfully saved to: {context_path}")
    except Exception as e:
        log_error(f"Failed to save output files: {e}")

if __name__ == "__main__":
    main()
