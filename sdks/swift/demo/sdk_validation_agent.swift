import Foundation
import NRouter

// Uses the same scenario names, models, prompts, and JSON bodies as the Go
// validation agent. Dry-run is the default; pass --live for gateway traffic.
struct Scenario {
    let name: String
    let model: String
    let body: [String: Any]
}

func env(_ key: String, _ fallback: String = "") -> String {
    ProcessInfo.processInfo.environment[key] ?? fallback
}

func errorText(_ error: Error) -> String {
    error.localizedDescription.replacingOccurrences(of: "\n", with: " ")
}

let chatModel = env("NROUTER_VALIDATION_CHAT_MODEL", "gpt-4o-mini")
let messagesModel = env("NROUTER_VALIDATION_MESSAGES_MODEL", "claude-haiku-4-5-20251001")
let embeddingModel = env("NROUTER_VALIDATION_EMBEDDING_MODEL", "text-embedding-3-small")
let imageModel = env("NROUTER_VALIDATION_IMAGE_MODEL")
let videoModel = env("NROUTER_VALIDATION_VIDEO_MODEL")
let scenarios = [
    Scenario(name: "chat", model: chatModel, body: ["model": chatModel, "messages": [["role": "user", "content": "SDK-CROSS-001 Reply exactly OK"]], "max_tokens": 16]),
    // nrouter-doc-wire: messages
    Scenario(name: "messages", model: messagesModel, body: ["model": messagesModel, "max_tokens": 16, "messages": [["role": "user", "content": "SDK-CROSS-002 Reply exactly OK"]]]),
    Scenario(name: "responses", model: chatModel, body: ["model": chatModel, "input": "SDK-CROSS-003 Reply exactly OK", "max_output_tokens": 16]),
    Scenario(name: "embeddings", model: embeddingModel, body: ["model": embeddingModel, "input": "SDK-CROSS-004"]),
    Scenario(name: "image", model: imageModel, body: ["model": imageModel, "prompt": "SDK-CROSS-005 a plain white square", "n": 1, "size": "1024x1024"]),
    Scenario(name: "video", model: videoModel, body: ["model": videoModel, "prompt": "SDK-CROSS-006 a plain white square", "seconds": 1, "size": "1280x720"]),
]

print("SCENARIO | MODE | MODEL | STATUS | REQUEST_ID | COST | ERROR")
if !CommandLine.arguments.contains("--live") {
    for s in scenarios { print("\(s.name) | DRY-RUN | \(s.model) | - | - | - | would call gateway") }
    print("stream | DRY-RUN | \(chatModel) | - | - | - | would call gateway")
} else {
    do {
        let client = try NRouter()
        let modelResult = try await client.models()
        print("models | LIVE | - | \(modelResult.statusCode) | \(modelResult.meta.requestID ?? "-") | \(modelResult.meta.cost.map(String.init) ?? "unpriced") | -")
        for s in scenarios {
            if s.model.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty { print("\(s.name) | SKIPPED | - | - | - | - | model env not set"); continue }
            do {
                let result: NRouter.Response
                switch s.name {
                case "chat": result = try await client.chatCompletions(s.body)
                case "messages": result = try await client.messages(s.body)
                case "responses": result = try await client.responses(s.body)
                case "embeddings": result = try await client.embeddings(s.body)
                case "image": result = try await client.imagesGenerations(s.body)
                case "video": result = try await client.createVideo(s.body)
                default: continue
                }
                print("\(s.name) | LIVE | \(s.model) | \(result.statusCode) | \(result.meta.requestID ?? "-") | \(result.meta.cost.map(String.init) ?? "unpriced") | -")
            } catch { print("\(s.name) | LIVE | \(s.model) | - | - | - | \(errorText(error))") }
        }
        let stream = try await client.chatCompletionsStream(scenarios[0].body)
        var text = ""
        for try await chunk in stream.chunks { text += chunk.delta }
        print("stream | LIVE | \(chatModel) | \(stream.statusCode) | \(stream.meta.requestID ?? "-") | \(stream.meta.cost.map(String.init) ?? "unpriced") | text=\(text.count)chars")
    } catch { print("setup | LIVE | - | - | - | - | \(errorText(error))") }
}
