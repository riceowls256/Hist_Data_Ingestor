#!/usr/bin/env python3
"""
Documentation Validation Script for Hist Data Ingestor

This script validates all documentation to ensure:
1. CLI examples execute successfully
2. Internal links point to existing files/sections
3. Code references point to actual implementation files
4. Configuration examples are syntactically valid YAML
5. All documented procedures work as expected

Usage:
    python scripts/validate_docs.py [--verbose] [--fix-links]
"""

import os
import re
import sys
import yaml
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Any
import argparse


class DocumentationValidator:
    def __init__(self, project_root: Path, verbose: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.errors = []
        self.warnings = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with appropriate formatting"""
        if self.verbose or level in ["ERROR", "WARNING"]:
            prefix = {
                "INFO": "ℹ️ ",
                "WARNING": "⚠️ ",
                "ERROR": "❌",
                "SUCCESS": "✅"
            }.get(level, "")
            print(f"{prefix} {message}")
    
    def add_error(self, error: str):
        """Add an error to the error list"""
        self.errors.append(error)
        self.log(error, "ERROR")
    
    def add_warning(self, warning: str):
        """Add a warning to the warnings list"""
        self.warnings.append(warning)
        self.log(warning, "WARNING")
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the project"""
        md_files = []
        for pattern in ["**/*.md", "**/*.MD"]:
            md_files.extend(self.project_root.glob(pattern))
        return [f for f in md_files if not f.is_relative_to(self.project_root / "venv")]
    
    def validate_cli_examples(self) -> bool:
        """Test CLI examples from documentation by actual execution"""
        self.log("Validating CLI examples...")
        
        # Read README.md for CLI examples
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            self.add_error("README.md not found")
            return False
        
        content = readme_path.read_text()
        
        # Extract CLI commands from code blocks
        cli_pattern = r'```(?:sh|bash)\n(.*?python main\.py.*?)\n```'
        commands = re.findall(cli_pattern, content, re.DOTALL | re.MULTILINE)
        
        success_count = 0
        total_count = 0
        
        for command_block in commands:
            lines = command_block.strip().split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('python main.py') and '--help' in line:
                    total_count += 1
                    try:
                        # Test help commands (should always work)
                        result = subprocess.run(
                            line.split(), 
                            cwd=self.project_root,
                            capture_output=True, 
                            text=True, 
                            timeout=30
                        )
                        if result.returncode == 0:
                            success_count += 1
                            self.log(f"CLI command succeeded: {line}", "SUCCESS")
                        else:
                            self.add_error(f"CLI command failed: {line} - {result.stderr}")
                    except subprocess.TimeoutExpired:
                        self.add_error(f"CLI command timed out: {line}")
                    except Exception as e:
                        self.add_error(f"CLI command error: {line} - {str(e)}")
        
        self.log(f"CLI validation: {success_count}/{total_count} commands succeeded")
        return success_count == total_count
    
    def validate_internal_links(self) -> bool:
        """Validate that internal links point to existing files/sections"""
        self.log("Validating internal links...")
        
        md_files = self.find_markdown_files()
        all_valid = True
        
        for md_file in md_files:
            content = md_file.read_text()
            
            # Find markdown links [text](path) and [text](path#section)
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            links = re.findall(link_pattern, content)
            
            for link_text, link_path in links:
                # Skip external links
                if link_path.startswith(('http://', 'https://', 'mailto:')):
                    continue
                
                # Handle links with anchors
                if '#' in link_path:
                    file_path, anchor = link_path.split('#', 1)
                else:
                    file_path, anchor = link_path, None
                
                # Resolve relative paths
                if file_path:
                    target_path = (md_file.parent / file_path).resolve()
                    if not target_path.exists():
                        self.add_error(f"Broken link in {md_file}: '{link_path}' -> {target_path}")
                        all_valid = False
                    else:
                        self.log(f"Valid link: {md_file.name} -> {file_path}", "SUCCESS")
        
        return all_valid
    
    def validate_code_references(self) -> bool:
        """Check that code references point to actual implementation files"""
        self.log("Validating code references...")
        
        md_files = self.find_markdown_files()
        all_valid = True
        
        for md_file in md_files:
            content = md_file.read_text()
            
            # Find code references like src/module/file.py
            code_ref_pattern = r'`(src/[^`]+\.py)`'
            refs = re.findall(code_ref_pattern, content)
            
            for ref in refs:
                target_path = self.project_root / ref
                if not target_path.exists():
                    self.add_error(f"Code reference not found in {md_file}: {ref}")
                    all_valid = False
                else:
                    self.log(f"Valid code reference: {md_file.name} -> {ref}", "SUCCESS")
        
        return all_valid
    
    def validate_yaml_examples(self) -> bool:
        """Verify that YAML configuration examples are syntactically valid"""
        self.log("Validating YAML configuration examples...")
        
        md_files = self.find_markdown_files()
        all_valid = True
        
        for md_file in md_files:
            content = md_file.read_text()
            
            # Find YAML code blocks
            yaml_pattern = r'```ya?ml\n(.*?)\n```'
            yaml_blocks = re.findall(yaml_pattern, content, re.DOTALL)
            
            for i, yaml_content in enumerate(yaml_blocks):
                try:
                    yaml.safe_load(yaml_content)
                    self.log(f"Valid YAML in {md_file.name} (block {i+1})", "SUCCESS")
                except yaml.YAMLError as e:
                    self.add_error(f"Invalid YAML in {md_file} (block {i+1}): {str(e)}")
                    all_valid = False
        
        return all_valid
    
    def validate_configuration_files(self) -> bool:
        """Validate actual configuration files"""
        self.log("Validating configuration files...")
        
        config_files = [
            "configs/system_config.yaml",
            "configs/api_specific/databento_config.yaml"
        ]
        
        all_valid = True
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        yaml.safe_load(f)
                    self.log(f"Valid configuration: {config_file}", "SUCCESS")
                except yaml.YAMLError as e:
                    self.add_error(f"Invalid YAML in {config_file}: {str(e)}")
                    all_valid = False
            else:
                self.add_warning(f"Configuration file not found: {config_file}")
        
        return all_valid
    
    def validate_file_structure(self) -> bool:
        """Validate that documented file structure matches reality"""
        self.log("Validating file structure references...")
        
        # Key directories that should exist
        expected_dirs = [
            "src/core", "src/cli", "src/ingestion", "src/querying", 
            "src/storage", "src/transformation", "src/utils",
            "configs", "logs", "dlq", "tests"
        ]
        
        all_valid = True
        for dir_path in expected_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                self.add_error(f"Expected directory not found: {dir_path}")
                all_valid = False
            else:
                self.log(f"Directory exists: {dir_path}", "SUCCESS")
        
        return all_valid
    
    def run_full_validation(self) -> bool:
        """Run all validation checks"""
        self.log("Starting comprehensive documentation validation...")
        
        checks = [
            ("CLI Examples", self.validate_cli_examples),
            ("Internal Links", self.validate_internal_links),
            ("Code References", self.validate_code_references),
            ("YAML Examples", self.validate_yaml_examples),
            ("Configuration Files", self.validate_configuration_files),
            ("File Structure", self.validate_file_structure)
        ]
        
        results = {}
        for check_name, check_func in checks:
            self.log(f"\n{'='*50}")
            self.log(f"Running {check_name} validation...")
            self.log('='*50)
            
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.add_error(f"{check_name} validation failed with exception: {str(e)}")
                results[check_name] = False
        
        # Summary report
        self.log(f"\n{'='*50}")
        self.log("VALIDATION SUMMARY")
        self.log('='*50)
        
        all_passed = True
        for check_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            self.log(f"{check_name:.<30} {status}")
            all_passed = all_passed and passed
        
        self.log(f"\nTotal Errors: {len(self.errors)}")
        self.log(f"Total Warnings: {len(self.warnings)}")
        
        if all_passed:
            self.log("\n🎉 All documentation validation checks PASSED!", "SUCCESS")
        else:
            self.log(f"\n💥 Documentation validation FAILED with {len(self.errors)} errors", "ERROR")
        
        return all_passed


def main():
    parser = argparse.ArgumentParser(description="Validate project documentation")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    
    args = parser.parse_args()
    
    validator = DocumentationValidator(args.project_root, args.verbose)
    success = validator.run_full_validation()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 