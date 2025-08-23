#!/usr/bin/env python3
"""
OBSERVATORIO ETS Deployment Script
Increments version, commits changes, and pushes to remote repository.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        if result.stdout:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        sys.exit(1)

def get_current_version():
    """Read current version from VERSION file."""
    version_file = Path("VERSION")
    if version_file.exists():
        return version_file.read_text().strip()
    return "1.0.0"

def increment_version(version, bump_type="patch"):
    """Increment version number."""
    major, minor, patch = map(int, version.split('.'))
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1
    
    return f"{major}.{minor}.{patch}"

def update_version_in_files(new_version):
    """Update version in dashboard template."""
    template_file = Path("templates/dashboard.html")
    if template_file.exists():
        content = template_file.read_text()
        # Find and replace version in template
        import re
        content = re.sub(
            r'<span class="version-badge">v[\d.]+</span>',
            f'<span class="version-badge">v{new_version}</span>',
            content
        )
        template_file.write_text(content)
        print(f"Updated version in dashboard template to v{new_version}")

def main():
    """Main deployment function."""
    print("🚀 OBSERVATORIO ETS Deployment")
    print("=" * 40)
    
    # Check if we're in a git repository
    result = run_command("git status", check=False)
    if result.returncode != 0:
        print("Error: Not in a git repository")
        sys.exit(1)
    
    # Get deployment type from command line argument
    bump_type = "patch"  # default
    if len(sys.argv) > 1:
        if sys.argv[1] in ["major", "minor", "patch"]:
            bump_type = sys.argv[1]
        else:
            print("Usage: python deploy.py [major|minor|patch]")
            sys.exit(1)
    
    # Get current version and increment
    current_version = get_current_version()
    new_version = increment_version(current_version, bump_type)
    
    print(f"Current version: v{current_version}")
    print(f"New version: v{new_version} ({bump_type} bump)")
    
    # Update VERSION file
    Path("VERSION").write_text(new_version)
    print(f"Updated VERSION file to {new_version}")
    
    # Update version in dashboard template
    update_version_in_files(new_version)
    
    # Git operations
    print("\n📦 Git operations:")
    
    # Add all changes
    run_command("git add .")
    
    # Check if there are changes to commit
    result = run_command("git diff --staged --quiet", check=False)
    if result.returncode == 0:
        print("No changes to commit")
        return
    
    # Commit with version tag
    commit_message = f"🚀 Deploy v{new_version} - {bump_type} release"
    run_command(f'git commit -m "{commit_message}"')
    
    # Create git tag
    run_command(f"git tag -a v{new_version} -m 'Release v{new_version}'")
    
    # Push to remote
    print("\n🌐 Pushing to remote:")
    run_command("git push origin")
    run_command("git push origin --tags")
    
    print(f"\n✅ Successfully deployed v{new_version}!")
    print("🔗 Dashboard deployed and running")

if __name__ == "__main__":
    main()