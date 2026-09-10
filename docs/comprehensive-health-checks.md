# Comprehensive SDK Health Checks

This repository separates SDK health checks by cost and purpose.

| When | Workflow | What it checks | Uses nRouter credits? |
| --- | --- | --- | --- |
| Daily | `SDK live health` | Real authentication and low-cost core gateway routes in all ten SDKs | Yes, low-cost text requests only |
| Daily | `CI` | Installation, build, unit tests, contract tests, conformance, and dependency-security audit | No |
| On SDK changes | `SDK media contract` | Image, speech, transcription, and video request compatibility without generating paid media | No |
| Manual | `Live media smoke` | One real image, short speech clip, and optional four-second video through the JavaScript SDK | Yes; video is off by default |

## What a green run means

- The live check proves every SDK can use the dedicated test key and receive a valid response from nRouter.
- CI proves the SDKs build, their local tests pass, and their public contract agrees with `spec/nrouter-sdk-spec.json`.
- The media contract checks request shape only. It does not claim that a paid image, audio, or video generation succeeded.

## Failure response

1. Open the failed GitHub Actions job and read its step log.
2. Download the `sdk-live-health-summary` artifact for a live-health run.
3. Use the request ID in the failing log to inspect nRouter Logs.
4. Retry once for a possible provider/network outage. If it fails again, open an SDK issue with the SDK, route, request ID, error, and run link.

## Deliberate limits

- Do not schedule image, speech, or video generation: they are paid requests.
- Do not put a real API key in source code. The workflows use the `NROUTER_SDK_HEALTH_API_KEY` GitHub secret.
- The JavaScript manual media test is one representative real-media route. All ten SDKs receive free media contract coverage.
