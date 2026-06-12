# Participant User Guide

This guide explains how to prepare and upload your hackathon submission to this public repository.

## 1. Before You Start
- Confirm you are registered for the hackathon:
  - https://www.cqtacanada.com/hackathon-registration
- Review the event page:
  - https://www.cqtacanada.com/events/cqta/quality-engineering-hackathon-june-2026
- Make sure you have:
  - A GitHub account
  - Git installed
  - Your project code and presentation materials ready

## 2. Submission Folder Naming
Create exactly one top-level folder in submissions/ using one of these formats:
- individual-firstname-lastname
- team-teamname

Examples:
- individual-jane-doe
- team-quality-guardians

Use lowercase letters, numbers, and hyphens only.

## 3. Required Files And Folders
Inside your folder, include:
- README.md (required)
- src/ (recommended)
- presentation/ (required if presenting slides)
- docs/ (optional supporting content)

Recommended structure:

```text
submissions/<your-folder>/
|-- README.md
|-- src/
|-- presentation/
`-- docs/
```

## 4. What To Put In README.md
At minimum include:
- Project title
- Participant name(s)
- Problem statement
- Solution summary
- Tech stack
- Setup and run instructions
- Demo steps
- Links to presentation and optional demo video

You can copy templates/SUBMISSION_README_TEMPLATE.md.

## 5. Upload Workflow

Important:
- Do not commit directly to main.
- All submissions must come through a pull request.

### Option A: GitHub Web
1. Fork this repository.
2. Create a new branch in your fork.
3. In your branch, add your folder under submissions/.
4. Commit your changes.
5. Open a pull request to this repository (target: main).

### Option B: Git CLI
1. Fork and clone your fork.
2. Create a branch.
3. Add your submission files.
4. Commit and push.
5. Open a pull request to main.

## 6. Pull Request Title Format
Use:
- submission: <your-folder-name>

Example:
- submission: team-quality-guardians

## 7. File Size And Content Guidance
- Keep repository size reasonable.
- Avoid very large binaries when possible.
- Link to external recordings if video files are large.
- Never upload secrets or credentials.
- Only include assets you have rights to share.

## 8. Final Pre-Submission Check
Run through docs/SUBMISSION_CHECKLIST.md before opening your pull request.

## 9. After Submission
- Watch your pull request for feedback from organizers.
- Respond quickly to requested fixes.
- Ensure your latest commit is in the pull request before cutoff time.
