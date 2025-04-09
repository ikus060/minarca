# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# This script is used to generate openapi.json file offline.
#
# Did not find an alternative to generate markdown or rst from my spec file.
# Either the solution is obsolete or failing
# So let use this quick and simple solution.
import json
import os

import cherrypy
from minarca_server.app import MinarcaApplication
from minarca_server.config import parse_args
from rdiffweb.controller.api_openapi import OpenAPI

# Change location of cwd for script location.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Generate spec file.
cfg = parse_args(
    args=['--database-uri', 'sqlite://', '--minarca-user-dir-owner', 'nobody', '--minarca-user-dir-group', 'nogroup']
)
app = cherrypy.request.app = MinarcaApplication(cfg)
api_spec = OpenAPI()._generate_spec(app.root)
with open("_static/openapi.json", 'w') as fp:
    json.dump(api_spec, fp)


def generate_markdown_for_path(path, methods):
    md_content = []
    for method, details in methods.items():
        md_content.append(f"\n### {method.upper()} {path}")

        if "description" in details:
            md_content.append(f"**Description:**\n{details['description']}\n")

        # Parameters
        parameters = details.get("parameters", [])
        if parameters:
            md_content.append("**Parameters:**")
            for param in parameters:
                param_name = param.get('name', 'Unnamed')
                param_in = param.get('in', 'unknown')
                param_required = " Required" if param.get('required', False) else ""
                param_default = f" Default: {param.get('default')}" if "default" in param else ""
                md_content.append(f"- **{param_name}** (in {param_in}){param_required}{param_default}")
            md_content.append("")

        # Responses
        md_content.append("**Responses:**")
        for status, response in details.get("responses", {}).items():
            md_content.append(f"- **{status}**: {response.get('description', 'No description')}")
            content = response.get("content", {})
            if content:
                md_content.append("  - **Content:** " + ", ".join(content.keys()))

    return md_content


def generate_markdown_from_openapi(openapi_json, output_file):
    """
    Generate a Markdown file from an OpenAPI JSON specification.

    :param openapi_json: Path to the OpenAPI JSON file.
    :param output_file: Path to the output Markdown file.
    """
    with open(openapi_json, "r", encoding="utf-8") as f:
        spec = json.load(f)

    md_content = []

    # Separate API and non-API endpoints
    md_content.append("# All Endpoints")

    md_content.append("## REST API Endpoints")

    for path in sorted(spec.get("paths", [])):
        if path.startswith('/api'):
            md_content.extend(generate_markdown_for_path(path, spec["paths"][path]))

    md_content.append("## Other Endpoints")

    for path in sorted(spec.get("paths", [])):
        if not path.startswith('/api'):
            md_content.extend(generate_markdown_for_path(path, spec["paths"][path]))

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"Markdown documentation generated: {output_file}")


# Example usage
generate_markdown_from_openapi("_static/openapi.json", "endpoints.md")
