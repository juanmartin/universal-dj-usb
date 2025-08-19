"""Tests for GitHub Actions workflow files."""

import pytest
import yaml
from pathlib import Path


def test_workflow_yaml_syntax():
    """Test that all workflow YAML files have valid syntax."""
    workflows_dir = Path(__file__).parent.parent / ".github" / "workflows"
    
    workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
    assert len(workflow_files) > 0, "No workflow files found"
    
    for workflow_file in workflow_files:
        try:
            with open(workflow_file) as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax in {workflow_file}: {e}")


def test_release_workflow_structure():
    """Test that the release workflow has the expected structure."""
    release_file = Path(__file__).parent.parent / ".github" / "workflows" / "release.yml"
    
    with open(release_file) as f:
        workflow = yaml.safe_load(f)
    
    # Check basic structure
    assert "name" in workflow
    assert True in workflow  # "on" gets parsed as boolean True in YAML
    assert "jobs" in workflow
    
    # Check that it triggers on tags
    on_config = workflow[True]  # "on" key becomes True
    assert "push" in on_config
    assert "tags" in on_config["push"]
    assert on_config["push"]["tags"] == ["v*"]
    
    # Check that the create-release job exists
    assert "create-release" in workflow["jobs"]
    
    job = workflow["jobs"]["create-release"]
    step_names = [step.get("name", "") for step in job["steps"]]
    
    # Check for key steps
    assert any("Wait for build workflow" in name for name in step_names)
    assert any("Download build artifacts" in name for name in step_names)  
    assert any("Create Release" in name for name in step_names)


def test_build_workflow_structure():
    """Test that the build workflow has the expected structure."""
    build_file = Path(__file__).parent.parent / ".github" / "workflows" / "build.yml"
    
    with open(build_file) as f:
        workflow = yaml.safe_load(f)
    
    # Check basic structure
    assert "name" in workflow
    assert workflow["name"] == "Build"
    assert True in workflow  # "on" gets parsed as boolean True in YAML
    assert "jobs" in workflow
    
    # Check that it has test and build jobs
    assert "test" in workflow["jobs"]
    assert "build" in workflow["jobs"]
    
    # Check that build job has matrix strategy
    build_job = workflow["jobs"]["build"]
    assert "strategy" in build_job
    assert "matrix" in build_job["strategy"]