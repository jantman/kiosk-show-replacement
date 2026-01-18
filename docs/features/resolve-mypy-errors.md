# Resolve All Mypy Type Errors

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

The `nox -s type_check` session currently fails with 110 mypy errors across 15 source files. The CLAUDE.md mentions an acceptable baseline of 11 errors (due to missing SQLAlchemy/Flask-Migrate stubs), but the error count has grown significantly.

This feature involves:
- Analyzing all current mypy errors
- Adding proper type annotations where missing
- Fixing type mismatches and incompatible assignments
- Adding appropriate type stubs or `# type: ignore` comments only where truly necessary (e.g., library issues)
- Reducing the error count to the acceptable baseline or ideally zero
- Updating CLAUDE.md if the acceptable baseline changes
