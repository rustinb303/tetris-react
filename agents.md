Agent Development Protocol
This document outlines the essential coding standards and development procedures for the agent. Adherence to these guidelines is mandatory for all tasks to ensure code quality, consistency, and reliability.

1. Code Style Conventions
All generated code must conform to the following style conventions.

Commenting
Code must be heavily commented. The goal is to make the code's purpose, logic, and functionality understandable to a human developer with minimal effort.

Function/Method Headers: Every function must have a comment block explaining what it does, its parameters, and what it returns.

Complex Logic: Inline comments should be used to clarify complex or non-obvious sections of code.

File Headers: Each file should begin with a comment describing its overall purpose and contents.

Naming Conventions
Functions: All function names must use camelCase.

Example: calculateTotalAmount, getUserData

Constants: All constant variables must be UPPERCASE_SNAKE_CASE. A constant is a variable whose value should not be changed after it is assigned.

Example: const API_KEY = '...';, const MAX_RETRIES = 3;

Variables: Standard variables should use camelCase.

Example: let itemCount = 0;

Classes: Class names must use PascalCase (also known as UpperCamelCase).

Example: class UserSession { ... }

2. Development & Verification Workflow
Before marking any task as complete, the agent must always attempt to build the application and run its associated tests. This is a critical step to verify that the changes are valid and do not introduce regressions.

Step 1: Build the Application
First, run the build process to ensure all dependencies are resolved and the application compiles successfully.

Build Instructions:

# Install dependencies if they haven't been installed yet
npm install

# Run the build script
npm run build

Step 2: Run Tests
Use playwright to run and render and test the app to verify it appears to be working 
