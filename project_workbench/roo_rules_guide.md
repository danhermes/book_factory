# Creating Roo Rules

This guide explains how to create custom configurations for the Roo AI assistant.

## 1. Custom Modes

Custom modes allow you to define specific behaviors and capabilities for Roo. They can be configured in two locations:

1. **Globally** via `c:\Users\dan\AppData\Roaming\Cursor\User\globalStorage\rooveterinaryinc.roo-cline\settings\custom_modes.json`
2. **Per-workspace** via a `.roomodes` file in your workspace root directory

When modes with the same slug exist in both files, the workspace-specific version takes precedence.

## 2. Creating a Custom Mode

To create a custom mode, you need to define a JSON configuration with the following structure:

```json
{
 "customModes": [
   {
     "slug": "your-mode-name", 
     "name": "Your Mode Display Name", 
     "roleDefinition": "Detailed description of the mode's role and capabilities",
     "whenToUse": "Description of when this mode should be used", 
     "groups": [
       "read",
       "edit",
       "browser",
       "command",
       "mcp"
     ],
     "customInstructions": "Additional instructions for the mode" 
   }
 ]
}
```

### Required Fields:

- **slug**: A unique identifier using lowercase letters, numbers, and hyphens
- **name**: The display name for the mode
- **roleDefinition**: A detailed description of the mode's role and capabilities
- **groups**: Array of allowed tool groups (can be empty)

### Optional Fields:

- **whenToUse**: Description of when this mode should be used
- **customInstructions**: Additional instructions for how the mode should operate

### File Access Restrictions

You can restrict file access for specific groups by using:

```json
["edit", { "fileRegex": "\\.md$", "description": "Markdown files only" }]
```

## Example Custom Mode

Here's an example of a custom mode for a technical writer:

```json
{
 "customModes": [
   {
     "slug": "tech-writer",
     "name": "📝 Technical Writer",
     "roleDefinition": "You are Roo, a technical writing expert specializing in clear documentation and tutorials. Your expertise includes:\n- Creating user-friendly documentation\n- Explaining complex technical concepts\n- Structuring information for maximum clarity\n- Following documentation best practices",
     "whenToUse": "Use this mode when creating or editing documentation, README files, or technical guides.",
     "groups": [
       "read",
       ["edit", { "fileRegex": "\\.md$", "description": "Markdown files only" }],
       "browser"
     ],
     "customInstructions": "Always prioritize clarity over technical jargon. Use examples where appropriate."
   }
 ]
}
```

To use this configuration, either add it to the global custom_modes.json file or create a `.roomodes` file in your project root with this content.

## 3. Example .roomodes File

Here's an example of a complete `.roomodes` file you could create in your project root:

```json
{
  "customModes": [
    {
      "slug": "book-writer",
      "name": "📚 Book Writer",
      "roleDefinition": "You are Roo, an expert book author specializing in creating engaging and informative content. Your expertise includes:\n- Crafting compelling narratives\n- Organizing complex information into digestible chapters\n- Maintaining consistent voice and style throughout long-form content\n- Creating educational content that keeps readers engaged",
      "whenToUse": "Use this mode when writing book chapters, organizing book structure, or editing book content.",
      "groups": [
        "read",
        "edit",
        "browser",
        "command"
      ],
      "customInstructions": "Focus on creating content that flows naturally between sections. Use storytelling techniques to illustrate complex concepts. Maintain a conversational but authoritative tone."
    },
    {
      "slug": "tech-editor",
      "name": "🔍 Technical Editor",
      "roleDefinition": "You are Roo, a meticulous technical editor with an eye for detail and consistency. Your expertise includes:\n- Identifying and correcting technical inaccuracies\n- Ensuring consistent terminology throughout documents\n- Improving clarity without changing meaning\n- Following style guides and documentation standards",
      "whenToUse": "Use this mode when reviewing and editing technical content, checking for errors, or ensuring consistency across documents.",
      "groups": [
        "read",
        "edit"
      ],
      "customInstructions": "Always verify technical accuracy. Suggest improvements for clarity while preserving the author's voice. Flag potential inconsistencies between sections."
    }
  ]
}
```

## 4. Tool Groups Reference

The `groups` field in a custom mode defines which tools the mode can access:

- **read**: Tools for reading files and information (read_file, fetch_instructions, search_files, list_files, list_code_definition_names)
- **edit**: Tools for modifying files (apply_diff, write_to_file)
- **browser**: Tools for browser interaction (browser_action)
- **command**: Tools for executing commands (execute_command)
- **mcp**: Tools for MCP operations (use_mcp_tool, access_mcp_resource)

## 5. Best Practices

1. **Be Specific**: Define clear role definitions and custom instructions
2. **Limit Access**: Only grant access to tool groups the mode actually needs
3. **Use File Restrictions**: When appropriate, limit which files a mode can edit
4. **Create Specialized Modes**: Create different modes for different tasks rather than one general-purpose mode
5. **Test Your Modes**: After creating a mode, test it to ensure it behaves as expected