# Stage 1: Build stage
FROM rust:1.80.1-alpine AS build

# Install dependencies for building in Alpine
RUN apk add --no-cache musl-dev binutils

WORKDIR /app

# Copy source code and build
COPY . .
RUN cargo build --release

# Strip the binary to reduce size
RUN strip /app/target/release/v1-basic

# Stage 2: Final image
FROM alpine:3.18 AS final

# Install runtime dependencies and binutils for stripping
RUN apk add --no-cache ca-certificates

# Copy the binary from the build stage
COPY --from=build /app/target/release/v1-basic /v1-basic

EXPOSE 8080

# Set binary as the entry point
ENTRYPOINT ["/v1-basic"]