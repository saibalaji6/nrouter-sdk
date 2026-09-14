package main

type ChatRequest struct {
	Model string
}

func main() {
	req := ChatRequest{
		Model: "claude-sonnet-4-5",
	}
	_ = req
}
