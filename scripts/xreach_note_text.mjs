#!/usr/bin/env node
/**
 * Return fuller X Note Tweet text from xreach's authenticated GraphQL client.
 *
 * xreach-cli currently exposes legacy.full_text, which is capped for Note
 * Tweets even though the GraphQL response contains note_tweet text. This
 * adapter deliberately emits only tweet ids and public tweet text; it never
 * prints or persists the xreach session.
 */
import { execFileSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { pathToFileURL } from "node:url";

function fail(message) {
  console.error(`xreach_note_text: ${message}`);
  process.exit(2);
}

function parseArgs(argv) {
  const ids = [];

  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--ids") {
      while (argv[index + 1] && !argv[index + 1].startsWith("--")) {
        ids.push(argv[index + 1]);
        index += 1;
      }
    } else {
      fail(`unknown argument ${value}`);
    }
  }

  if (!ids.length) {
    fail("pass --ids <tweet ids...>");
  }
  return [...new Set(ids)];
}

function mergeReplyPrefix(legacyText, noteText) {
  const probe = noteText.slice(0, Math.min(noteText.length, 80));
  const position = probe ? legacyText.indexOf(probe) : -1;
  return position > 0 ? `${legacyText.slice(0, position)}${noteText}` : noteText;
}

function attachNoteText(client) {
  const parseTweet = client.parseTweet.bind(client);
  client.parseTweet = (result) => {
    const tweet = result.tweet || result;
    const parsed = parseTweet(result);
    const noteText = tweet.note_tweet?.note_tweet_results?.result?.text;
    if (typeof noteText === "string" && noteText.length) {
      parsed.noteText = mergeReplyPrefix(parsed.text || "", noteText);
    }
    return parsed;
  };
}

function addExpandedText(output, tweet) {
  if (tweet?.id && typeof tweet.noteText === "string" && tweet.noteText.length > (tweet.text || "").length) {
    output[tweet.id] = tweet.noteText;
  }
}

function loadClient() {
  let xreachBin;
  try {
    xreachBin = execFileSync("which", ["xreach"], { encoding: "utf8" }).trim();
  } catch {
    fail("xreach is not installed or is not on PATH");
  }

  const entryUrl = pathToFileURL(realpathSync(xreachBin));
  return import(new URL("./commands/shared.js", entryUrl));
}

async function main() {
  const ids = parseArgs(process.argv.slice(2));
  const { getClient } = await loadClient();
  const client = await getClient({});
  attachNoteText(client);
  const expanded = {};

  let nextIndex = 0;
  async function worker() {
    while (nextIndex < ids.length) {
      const id = ids[nextIndex++];
      try {
        addExpandedText(expanded, await client.getTweet(id));
      } catch (error) {
        console.error(`xreach_note_text: ${id}: ${error.message}`);
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(4, ids.length) }, worker));

  process.stdout.write(`${JSON.stringify(expanded)}\n`);
}

main().catch((error) => fail(error.message));
