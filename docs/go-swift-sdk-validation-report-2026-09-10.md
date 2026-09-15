# Go and Swift SDK Validation Report - 2026-09-10

## Scope

This report covers the Go and Swift SDK validation work on branch `sdk-validation`.

<!-- nrouter-doc-wire: messages -->

Sample validation agents were added:

- `examples/go/sdk_validation_agent.go`
- `examples/swift/sdk_validation_agent.swift`

The agents use matching scenario names, models, prompts, and request shapes so gateway/dashboard results can be compared across SDKs.

## Go SDK Test Results

| Check | Result | Notes |
|---|---:|---|
| `go test ./...` | PASS | Go unit suite passed |
| `go vet ./...` | PASS | No vet findings |
| Go validation agent dry-run | PASS | All scenarios render without network |
| Go validation agent live run | PASS/PARTIAL | Core SDK calls work; provider/config cases listed below |

## Latest Go Live Request Results

| Scenario | Model | Result | Request ID | Evidence |
|---|---|---:|---|---|
| models | - | PASS | `f4d5f337-4f2d-4e04-9a59-b2da1e48b716` | `/models` returned 2xx |
| chat | `gpt-4o-mini` | PASS | `7670b0be-9a67-45f7-9d00-6566725cd447` | exact cost, token counts, guardrails pass |
| messages | `claude-haiku-4-5-20251001` | PASS | `869687d2-6b98-403c-ae2a-8d9cce218916` | Anthropic messages wire works |
| responses | `gpt-4o-mini` | PASS | `97d85124-e652-47cb-b82e-7dc233398aa7` | responses wire works |
| embeddings | `text-embedding-3-small` | PASS | `b36243e1-7c49-402c-9f57-95c1b9509399` | exact cost, token count |
| image | `gpt-image-1-mini` | PASS/PARTIAL | `daaf7a10-64f2-4eac-9eed-e2ebc5ac32e1` | image generation succeeded, but cost was unpriced |
| video | `sora-2` | FAIL | `8f38d276-edf5-46d8-82f9-da9c98303207` | gateway returned provider malformed request |
| audio speech | `tts-1` | PASS | `c3fa1682-b959-4712-88af-b9e979a97e77` | returned audio bytes and exact cost |
| audio transcription | `whisper-1` | BLOCKED | `d37ba054-2290-4359-b01b-f4e34eb55c24` | org guardrail blocked deferred audio inspection |
| invalid model | `definitely-invalid-model-go-cross-sdk` | PASS | `99595087-5cd3-4320-b020-eca99b050da5` | SDK typed as `not_found` with request ID |
| guardrail control | `gpt-4o-mini` | PASS | `e4feac41-712e-4e08-bddf-1e051c92573f` | guardrails pass |
| PII guardrail | `gpt-4o-mini` | PASS | `ecfb0159-1446-4236-9fa2-318555742f12` | SDK typed as `guardrail_blocked` |
| jailbreak guardrail | `gpt-4o-mini` | PASS | `7b1eb4ca-2bf3-4e5c-95c9-6dd0c9bc3a88` | SDK typed as `guardrail_blocked` |
| cache first | `gpt-4o-mini` | PASS | `712ff7b1-7879-40b9-a2ff-5f7cd34e90bd` | normal cached-capable request |
| cache repeat | `gpt-4o-mini` | PASS/PARTIAL | `a7973ca7-d154-4dfe-8b55-2c9455ee0667` | succeeded, but no cache-hit metadata exposed |
| cache bypass | `gpt-4o-mini` | PASS | `d79c5f3e-b0ff-4d14-9b19-9acd5a753430` | response included `cache=bypass` |
| `nrsmart` router | `nrsmart` | FAIL | `688ab156-c963-4336-9c8c-8153cea13ad1` | alias not enabled on this account |
| `nrouter-auto` router | `nrouter-auto` | FAIL | `459fe576-a50b-461d-af3c-04e5a76ad293` | alias not enabled on this account |
| stream | `gpt-4o-mini` | PASS/PARTIAL | `5db0ef4c-b8b4-4228-b8d1-baf1ce077bfb` | stream works, cost status was unpriced |

## Confirmed Issues and Blockers

### 1. Video request reaches nRouter but is rejected as malformed by provider path

Classification: gateway/provider/schema

Evidence:

```text
video | LIVE | sora-2 | 400 | 8f38d276-edf5-46d8-82f9-da9c98303207 | ... | nrouter: the provider rejected this request as malformed
```

Impact:

The Go SDK can call the video endpoint and captures the request ID correctly, but the currently used sample body is not accepted by the live provider route.

Recommended action:

Verify the expected video request body for `sora-2` at the gateway/provider layer, then update SDK examples if the request shape needs different fields.

### 2. Audio transcription is blocked by current org guardrail policy

Classification: configuration/guardrail

Evidence:

```text
audio-transcription | LIVE | whisper-1 | 400 | d37ba054-2290-4359-b01b-f4e34eb55c24 | ... | request blocked by a guardrail: part of this request cannot be inspected (audio.upload.deferred_to_transcript)
```

Impact:

The SDK sends the multipart transcription request and captures the guardrail error correctly. The request is blocked before transcription because the organization guardrail policy blocks or redacts uninspectable audio uploads.

Recommended action:

For live transcription validation, temporarily use a key/org policy where deferred audio inspection is warn/log instead of block/redact, or send transcribed text through text endpoints for guardrail testing.

### 3. Cache repeat succeeds but does not show cache-hit metadata

Classification: dashboard/gateway/configuration

Evidence:

```text
cache-first  | 2xx | no response cache header
cache-repeat | 2xx | no response cache header
cache-bypass | 2xx | cache=bypass
```

Impact:

The SDK exposes cache metadata when the gateway sends it. The bypass request proves metadata parsing works, but the repeated request did not produce a visible cache hit.

Recommended action:

Check whether response cache is enabled for this key/model and whether the dashboard logs the first/repeat/bypass requests as expected.

### 4. Router aliases are not enabled for this account

Classification: configuration

Evidence:

```text
nrsmart      | 404 | unknown model: nrsmart is not a served model, and it is not an enabled router alias on this account
nrouter-auto | 404 | unknown model: nrouter-auto is not a served model, and it is not an enabled router alias on this account
```

Impact:

The SDK correctly preserves 404 request IDs and classifies the failures. Router behavior cannot be validated with this key until aliases are enabled.

Recommended action:

Enable the router aliases for the API key/account or provide the exact alias IDs exposed by `/models`.

### 5. Image generation succeeds but returns unpriced cost metadata

Classification: gateway/billing metadata

Evidence:

```text
image | LIVE | gpt-image-1-mini | 2xx | daaf7a10-64f2-4eac-9eed-e2ebc5ac32e1 | unpriced | in=15,out=4160,total=4175
```

Impact:

The SDK successfully calls image generation and captures token metadata, but dashboard cost reconciliation cannot be exact for this image request because `x-nr-request-cost` was absent/unpriced.

Recommended action:

Check billing metadata generation for image routes in the gateway/dashboard.

## Cross-SDK Parity Notes

Go and Swift both expose the same core surfaces:

- chat completions
- messages
- responses
- embeddings
- models/model lookup
- streaming
- images
- video create/retrieve/download
- audio speech/transcription/translation
- metadata helpers
- typed errors
- guardrail metadata
- cache metadata
- budget warning metadata
- prompt helpers
- memory helpers
- sampling helpers

## Commands Used

```powershell
cd D:\nrouter-sdk\sdks\go
go test ./...
go vet ./...
go run ..\..\examples\go\sdk_validation_agent.go
```

Live run:

```powershell
cd D:\nrouter-sdk\sdks\go
Get-Content ..\..\.env | Where-Object { $_ -match '^\s*[^#][^=]+=.*' } | ForEach-Object {
  $parts = $_ -split '=', 2
  $name = $parts[0].Trim()
  $value = $parts[1].Trim().Trim('"').Trim("'")
  [Environment]::SetEnvironmentVariable($name, $value, 'Process')
}
$env:NROUTER_VALIDATION_IMAGE_MODEL='gpt-image-1-mini'
$env:NROUTER_VALIDATION_VIDEO_MODEL='sora-2'
go run ..\..\examples\go\sdk_validation_agent.go -live
```

Conformance:

```powershell
$env:PYTHONUTF8='1'
python conformance/check_conformance.py --self-test
python conformance/check_conformance.py
```

## Final Status

Go SDK: healthy for core runtime, metadata, guardrail, cache-bypass, image, speech, and streaming. Video and transcription need gateway/config follow-up.

Swift SDK: statically appears feature-parity ready from the source surface and matching validation-agent request matrix.

Repository conformance: passing with `PYTHONUTF8=1`.
