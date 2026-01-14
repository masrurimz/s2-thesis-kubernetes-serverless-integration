package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	backendName = getEnv("BACKEND_NAME", "unknown")

	httpRequestDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "HTTP request duration in seconds",
			Buckets: []float64{0.01, 0.05, 0.1, 0.2, 0.5, 1},
		},
		[]string{"method", "path", "status"},
	)

	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "path", "status"},
	)
)

func init() {
	prometheus.MustRegister(httpRequestDuration)
	prometheus.MustRegister(httpRequestsTotal)
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func fib(n int) int {
	if n <= 1 {
		return n
	}
	return fib(n-1) + fib(n-2)
}

func instrumentHandler(path string, handler http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
		handler(rw, r)
		duration := time.Since(start).Seconds()
		status := strconv.Itoa(rw.statusCode)
		httpRequestDuration.WithLabelValues(r.Method, path, status).Observe(duration)
		httpRequestsTotal.WithLabelValues(r.Method, path, status).Inc()
	}
}

type responseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "ok",
		"backend": backendName,
	})
}

func fibHandler(w http.ResponseWriter, r *http.Request) {
	nStr := r.URL.Query().Get("n")
	n, err := strconv.Atoi(nStr)
	if err != nil || n < 0 {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(map[string]string{"error": "invalid n parameter"})
		return
	}

	start := time.Now()
	result := fib(n)
	duration := time.Since(start)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"n":           n,
		"result":      result,
		"duration_ms": duration.Milliseconds(),
		"backend":     backendName,
	})
}

func main() {
	port := getEnv("PORT", "8080")

	http.HandleFunc("/health", instrumentHandler("/health", healthHandler))
	http.HandleFunc("/fib", instrumentHandler("/fib", fibHandler))
	http.Handle("/metrics", promhttp.Handler())

	log.Printf("Starting server on :%s (backend: %s)", port, backendName)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
