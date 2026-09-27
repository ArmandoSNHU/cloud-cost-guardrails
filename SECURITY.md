# Security boundaries

Author: Armando Gomez

This is a local inventory analyzer. It does not authenticate to cloud providers, verify supplied inventory against live infrastructure, or perform remediation. Use synthetic examples in public contributions. Resource names, tags and findings can contain business information; do not publish operational inventories or reports.

Input validation rejects unknown fields, invalid ports, non-finite or negative costs, and values that pretend to be booleans. CLI input failures return a generic error without echoing the supplied value. These controls do not make an inventory trustworthy or constitute a cloud security audit.

Main requires pull requests and all Python matrix checks, including for administrators. Force pushes and branch deletion are disabled. GitHub secret scanning, push protection, vulnerability alerts and automatic security fixes are enabled. Actions are pinned, CI permissions are read-only, and checkout credentials are not retained. Weekly Dependabot checks track Actions and the Python manifest; there are currently no third-party runtime dependencies. Use a supported, patched Python runtime.

Report sensitive issues privately to the repository owner through an established private channel. Do not put credentials, account data or customer inventories in public issues. If a credential is published, revoke or rotate it; deleting the file does not remove historical copies. Secret scanning cannot detect every secret or private datum.
