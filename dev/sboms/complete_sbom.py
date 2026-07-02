#!/usr/bin/env python3
"""
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0

Complete and correct CycloneDX SBOM files for a better compliance with BSI TR-03183-2 version 2.1

1. Reads a syft-generated CycloneDX JSON SBOM file
2. filters it to only the project's own dependencies (removing system packages)
3. add required metadata fields
4. removes unneeded metadata fields
"""

import argparse
import json
import sys

MANUFACTURER = {
    "name": "CSAF Tools Development Community",
    "url": ["https://github.com/csaf-tools/provider-online-check"],
}

VCS_URL = "https://github.com/csaf-tools/provider-online-check.git"

LICENSE = [{"license": {"id": "Apache-2.0"}}]

# Package types
# removes: binary (httpd), apk, deb
IN_SCOPE_PACKAGE_TYPES = {"python", "npm", "go-module"}

# syft cataloger names
# removes: binary-classifier-cataloger, apk-db-cataloger, dpkg-db-cataloger
IN_SCOPE_CATALOGERS = {
    "python-installed-package-cataloger",  # backend
    "javascript-package-cataloger",  # frontend
    "go-module-binary-cataloger",  # csaf_checker in backend
}

# syft purl types
# removes: pkg:generic, pkg:apk, pkg:deb
IN_SCOPE_PURL = {
    "pkg:pypi/",  # backend
    "pkg:npm/",  # frontend
    "pkg:golang/",  # csaf_checker in backend
}

def get_syft_prop(component: dict, name: str) -> str:
    for prop in component.get("properties", []):
        if prop["name"] == name:
            return prop["value"]
    return ""


def is_in_scope(component: dict) -> bool:
    pkg_type = get_syft_prop(component, "syft:package:type")
    if pkg_type in IN_SCOPE_PACKAGE_TYPES:
        return True
    found_by = get_syft_prop(component, "syft:package:foundBy")
    if found_by in IN_SCOPE_CATALOGERS:
        return True
    for scheme in IN_SCOPE_PURL:
        if component.get("purl", "").startswith(scheme):
            return True
    return False


def strip_syft_noise(component: dict) -> dict:
    """Remove syft-internal properties that serve no purpose

    Removes:
      syft:package:type, syft:package:foundBy, syft:package:language,
      syft:package:metadataType, syft:location:N:...,
      syft:cpe23, syft:metadata:..., etc.
    """
    component["properties"] = [
        p for p in component.get("properties", [])
        if not p["name"].startswith("syft:")
    ]
    if not component["properties"]:
        del component["properties"]
    return component


def complete_sbom(sbom: dict, component_name: str, version: str) -> dict:
    # Metadata
    meta = sbom.setdefault("metadata", {})

    meta["manufacturer"] = MANUFACTURER
    meta["supplier"] = MANUFACTURER
    meta["licenses"] = LICENSE

    # The component itself
    comp = meta.setdefault("component", {})
    comp["type"] = "application"
    comp["name"] = component_name
    comp["version"] = version
    comp["publisher"] = MANUFACTURER["name"]
    comp["supplier"] = MANUFACTURER
    comp["licenses"] = LICENSE
    comp["externalReferences"] = [{"url": VCS_URL, "type": "vcs"}]

    # Replace container image version with application version
    comp["version"] = version

    # Remove syft metadata
    if "properties" in meta:
        meta["properties"] = [
            p for p in meta["properties"]
            if not p["name"].startswith("syft:")
        ]
        if not meta["properties"]:
            del meta["properties"]

    # Remove all entries that are out of scope
    all_components = sbom.get("components", [])
    in_scope = [c for c in all_components if is_in_scope(c)]

    # Remove all syft-internal stuff
    sbom["components"] = [strip_syft_noise(c) for c in in_scope]

    return sbom


def main(sbom_file, component_name: str, version: str) -> None:
    sbom = json.load(sbom_file)

    complete_sbom(sbom, component_name, version)

    sbom_file.seek(0)
    sbom_file.truncate()
    json.dump(sbom, sbom_file, indent=2)
    sbom_file.write("\n")

    in_scope_count = len(sbom["components"])
    print(f"{sbom_file.name}: Rewritten with {in_scope_count} components in-scope", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sbom_file", metavar="sbom file", type=argparse.FileType('r+'),
                        help="Path to the CycloneDX JSON SBOM file (will be modified in place)")
    parser.add_argument("component", help="Component name")
    parser.add_argument("version", help="Application version string")
    args = parser.parse_args()

    main(args.sbom_file, args.component, args.version)
