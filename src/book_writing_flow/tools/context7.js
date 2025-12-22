#!/usr/bin/env node

const readline = require("readline");
const { Configuration, OpenAIApi } = require("openai");

const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY
});

const openai = new OpenAIApi(configuration);

async function getDocs(libraryName, topic, tokens) {
  const prompt = topic
    ? `Explain the '${topic}' functionality of ${libraryName}. Include examples where appropriate.`
    : `Provide a concise, structured technical overview of ${libraryName}, its use cases, and primary capabilities.`;

  const response = await openai.createChatCompletion({
    model: "gpt-4",
    messages: [{ role: "user", content: prompt }],
    max_tokens: tokens || 800,
    temperature: 0.4
  });

  return response.data.choices[0].message.content.trim();
}

async function handleRequest(inputLine) {
  try {
    const req = JSON.parse(inputLine);
    const { tool, args } = req;

    if (!tool || typeof args !== "object") {
      throw new Error("Malformed request: missing 'tool' or 'args'");
    }

    let result;

    if (tool === "resolve-library-id") {
      // passthrough — no fake ID mapping
      result = args.libraryName;
    } else if (tool === "get-library-docs") {
      const { context7CompatibleLibraryID, topic, tokens } = args;
      result = await getDocs(context7CompatibleLibraryID, topic, tokens);
    } else {
      throw new Error(`Unknown tool: ${tool}`);
    }

    process.stdout.write(JSON.stringify({ result }) + "\n");
  } catch (err) {
    process.stderr.write(`[Context7 ERROR]: ${err.message}\n`);
    process.stdout.write(JSON.stringify({ error: err.message }) + "\n");
  }
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on("line", handleRequest);
