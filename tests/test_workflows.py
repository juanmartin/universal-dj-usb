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


def test_workflow_integration():
    """Test that build and release workflows are properly integrated."""
    build_file = Path(__file__).parent.parent / ".github" / "workflows" / "build.yml"
    release_file = Path(__file__).parent.parent / ".github" / "workflows" / "release.yml"
    
    with open(build_file) as f:
        build_workflow = yaml.safe_load(f)
    
    with open(release_file) as f:
        release_workflow = yaml.safe_load(f)
    
    # Both workflows should trigger on version tags
    build_on = build_workflow[True]  # "on" key becomes True
    release_on = release_workflow[True]  # "on" key becomes True
    
    assert "push" in build_on
    assert "push" in release_on
    assert "tags" in build_on["push"]  
    assert "tags" in release_on["push"]
    assert build_on["push"]["tags"] == ["v*"]
    assert release_on["push"]["tags"] == ["v*"]
    
    # Release workflow should wait for build workflow
    release_steps = release_workflow["jobs"]["create-release"]["steps"]
    wait_step = None
    download_step = None
    
    for step in release_steps:
        if "Wait for build workflow" in step.get("name", ""):
            wait_step = step
        elif "Download build artifacts" in step.get("name", ""):
            download_step = step
    
    # Verify wait step configuration
    assert wait_step is not None
    assert wait_step["uses"] == "ahmadnassri/action-workflow-run-wait@v1"
    assert wait_step["with"]["workflow"] == "build.yml"
    
    # Verify download step configuration
    assert download_step is not None  
    assert download_step["uses"] == "dawidd6/action-download-artifact@v3"
    assert download_step["with"]["workflow"] == "build.yml"
    assert download_step["with"]["workflow_conclusion"] == "success"