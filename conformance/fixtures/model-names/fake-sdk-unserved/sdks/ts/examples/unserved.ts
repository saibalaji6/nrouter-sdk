import { NRouter } from "nrouter";

export async function main() {
  const client = new NRouter();
  await client.chat({
    model: "unserved-ts-model",
  });
}
