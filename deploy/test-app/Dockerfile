FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o test-app .

FROM scratch

COPY --from=builder /app/test-app /test-app

EXPOSE 8080
ENTRYPOINT ["/test-app"]
