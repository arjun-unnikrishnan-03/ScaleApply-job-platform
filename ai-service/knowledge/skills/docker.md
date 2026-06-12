# Docker Knowledge Base

Docker is a platform designed to help developers build, share, and run modern applications. We handle the tedious setup, so you can focus on the code.

## Key Concepts
- **Containers**: Standardized unit of software that allows developers to isolate their app from its environment.
- **Images**: Lightweight, standalone, executable package of software that includes everything needed to run an application.
- **Dockerfile**: A text document that contains all the commands a user could call on the command line to assemble an image.

## Best Practices
- Keep images small (use Alpine Linux where possible).
- Use multi-stage builds.
- Never run containers as root.
- Use `.dockerignore` to exclude files from the build context.
