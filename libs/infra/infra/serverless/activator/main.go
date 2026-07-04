package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
)

var (
	coldStartTriggerTotal = prometheus.NewCounter(prometheus.CounterOpts{
		Name: "cold_start_trigger_total",
		Help: "Total number of cold start triggers (scale from 0 to 1)",
	})

	coldStartLatencyHistogram = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "cold_start_latency_seconds",
		Help:    "Histogram of cold start latency in seconds",
		Buckets: prometheus.ExponentialBuckets(0.1, 2, 10), // 0.1s to ~51s
	})
)

func init() {
	prometheus.MustRegister(coldStartTriggerTotal)
	prometheus.MustRegister(coldStartLatencyHistogram)
}

type Activator struct {
	client         *kubernetes.Clientset
	targetService  string
	deploymentName string
	namespace      string
	idleTTL        time.Duration
	proxy          *httputil.ReverseProxy

	mu              sync.Mutex
	lastRequestTime time.Time
}

func NewActivator() (*Activator, error) {
	config, err := rest.InClusterConfig()
	if err != nil {
		return nil, fmt.Errorf("failed to get in-cluster config: %w", err)
	}

	client, err := kubernetes.NewForConfig(config)
	if err != nil {
		return nil, fmt.Errorf("failed to create kubernetes client: %w", err)
	}

	targetService := getEnv("TARGET_SERVICE", "test-app-cold:80")
	deploymentName := getEnv("DEPLOYMENT_NAME", "test-app-cold")
	namespace := getEnv("NAMESPACE", "default")
	idleTTLStr := getEnv("IDLE_TTL", "30s")

	idleTTL, err := time.ParseDuration(idleTTLStr)
	if err != nil {
		return nil, fmt.Errorf("invalid IDLE_TTL: %w", err)
	}

	targetURL, err := url.Parse("http://" + targetService)
	if err != nil {
		return nil, fmt.Errorf("invalid TARGET_SERVICE: %w", err)
	}

	proxy := httputil.NewSingleHostReverseProxy(targetURL)
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		log.Printf("Proxy error: %v", err)
		http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
	}

	return &Activator{
		client:          client,
		targetService:   targetService,
		deploymentName:  deploymentName,
		namespace:       namespace,
		idleTTL:         idleTTL,
		proxy:           proxy,
		lastRequestTime: time.Now(),
	}, nil
}

func (a *Activator) getCurrentReplicas(ctx context.Context) (int32, error) {
	scale, err := a.client.AppsV1().Deployments(a.namespace).GetScale(ctx, a.deploymentName, metav1.GetOptions{})
	if err != nil {
		return 0, err
	}
	return scale.Spec.Replicas, nil
}

func (a *Activator) scaleDeployment(ctx context.Context, replicas int32) error {
	scale, err := a.client.AppsV1().Deployments(a.namespace).GetScale(ctx, a.deploymentName, metav1.GetOptions{})
	if err != nil {
		return err
	}

	scale.Spec.Replicas = replicas
	_, err = a.client.AppsV1().Deployments(a.namespace).UpdateScale(ctx, a.deploymentName, scale, metav1.UpdateOptions{})
	return err
}

func (a *Activator) waitForReadyEndpoint(ctx context.Context) error {
	timeout := time.After(60 * time.Second)
	ticker := time.NewTicker(100 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-timeout:
			return fmt.Errorf("timeout waiting for ready endpoint")
		case <-ticker.C:
			endpoints, err := a.client.CoreV1().Endpoints(a.namespace).Get(ctx, a.deploymentName, metav1.GetOptions{})
			if err != nil {
				continue
			}

			for _, subset := range endpoints.Subsets {
				if len(subset.Addresses) > 0 {
					log.Printf("Endpoint ready: %s", subset.Addresses[0].IP)
					return nil
				}
			}
		}
	}
}

func (a *Activator) ensureScaledUp(ctx context.Context) (bool, time.Duration, error) {
	a.mu.Lock()
	defer a.mu.Unlock()

	replicas, err := a.getCurrentReplicas(ctx)
	if err != nil {
		return false, 0, fmt.Errorf("failed to get current replicas: %w", err)
	}

	if replicas > 0 {
		return false, 0, nil
	}

	coldStartStart := time.Now()
	coldStartTriggerTotal.Inc()
	log.Printf("Cold start triggered: scaling %s from 0 to 1", a.deploymentName)

	if err := a.scaleDeployment(ctx, 1); err != nil {
		return true, 0, fmt.Errorf("failed to scale deployment: %w", err)
	}

	if err := a.waitForReadyEndpoint(ctx); err != nil {
		return true, 0, fmt.Errorf("failed waiting for endpoint: %w", err)
	}

	latency := time.Since(coldStartStart)
	coldStartLatencyHistogram.Observe(latency.Seconds())
	log.Printf("Cold start completed in %v", latency)

	return true, latency, nil
}

func (a *Activator) updateLastRequestTime() {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.lastRequestTime = time.Now()
}

func (a *Activator) idleChecker() {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		a.mu.Lock()
		timeSinceLastRequest := time.Since(a.lastRequestTime)
		a.mu.Unlock()

		if timeSinceLastRequest >= a.idleTTL {
			ctx := context.Background()
			replicas, err := a.getCurrentReplicas(ctx)
			if err != nil {
				log.Printf("Error checking replicas: %v", err)
				continue
			}

			if replicas > 0 {
				log.Printf("Scaling down %s to 0 after %v idle", a.deploymentName, timeSinceLastRequest)
				if err := a.scaleDeployment(ctx, 0); err != nil {
					log.Printf("Error scaling down: %v", err)
				}
			}
		}
	}
}

func (a *Activator) proxyHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	a.updateLastRequestTime()

	_, _, err := a.ensureScaledUp(ctx)
	if err != nil {
		log.Printf("Error ensuring scale-up: %v", err)
		http.Error(w, "Failed to activate service", http.StatusServiceUnavailable)
		return
	}

	a.proxy.ServeHTTP(w, r)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func main() {
	port := getEnv("PORT", "8081")
	portNum, err := strconv.Atoi(port)
	if err != nil {
		log.Fatalf("Invalid PORT: %v", err)
	}

	activator, err := NewActivator()
	if err != nil {
		log.Fatalf("Failed to create activator: %v", err)
	}

	go activator.idleChecker()

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.Handle("/metrics", promhttp.Handler())
	mux.HandleFunc("/", activator.proxyHandler)

	addr := fmt.Sprintf(":%d", portNum)
	log.Printf("Starting serverless activator on %s", addr)
	log.Printf("Target service: %s, Deployment: %s, Namespace: %s, Idle TTL: %v",
		activator.targetService, activator.deploymentName, activator.namespace, activator.idleTTL)

	if err := http.ListenAndServe(addr, mux); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}
