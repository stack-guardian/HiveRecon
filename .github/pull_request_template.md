name: Pull Request
description: Create a pull request for this project
labels: ["pull request"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to submit a pull request.
  - type: textarea
    id: description
    attributes:
      label: Description
      description: A clear and concise description of what this PR does.
    validations:
      required: true
  - type: textarea
    id: motivation
    attributes:
      label: Motivation
      description: Why did you choose this solution? What problem does it solve?
    validations:
      required: true
  - type: textarea
    id: testing
    attributes:
      label: Testing
      description: How did you test this change?
      placeholder: ex. Added unit tests, manual testing, etc.
    validations:
      required: true
  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: Code follows project guidelines
          required: true
        - label: Self-review completed
          required: true
        - label: Tests added/updated
          required: false
        - label: Documentation updated
          required: false
        - label: No new warnings
          required: true
