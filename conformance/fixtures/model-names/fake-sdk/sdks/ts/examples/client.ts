import { NRouter } from "nrouter";

export async function main() {
  const client = new NRouter();
  await client.chat({
    model: "claude-sonnet-4-5",
  });
}
