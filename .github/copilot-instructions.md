When performing a code review, check if the guidelines stated in the CONTRIBUTING.md file are being followed. If any guidelines are not being followed, provide constructive feedback to help the contributor align with the project's standards.
When performing a code review, Specifically focus on the following aspects:
- Release notes were added
- Every app class has a @supported_version annotation. .github/scripts/publish_app_tags.py uses it to find the apps to tag on a release

