package server

import (
	"io/fs"
	"log"
	"net/http"
	"strings"
	"time"

	"gitstat/internal/handler"

	"github.com/go-chi/chi/v5"
)

func NewServer() *chi.Mux {
	r := chi.NewRouter()

	r.Use(corsMiddleware)
	r.Use(loggingMiddleware)

	r.Post("/api/scan/path", handler.SetScanPathHandler)
	r.Get("/api/scan/path", handler.GetScanPathHandler)
	r.Get("/api/repositories", handler.GetRepositoriesHandler)
	r.Get("/api/stats/overview", handler.GetOverviewStatsHandler)
	r.Get("/api/stats/daily", handler.GetDailyStatsHandler)
	r.Get("/api/stats/weekly", handler.GetWeeklyStatsHandler)
	r.Get("/api/stats/monthly", handler.GetMonthlyStatsHandler)
	r.Get("/api/stats/yearly", handler.GetYearlyStatsHandler)
	r.Get("/api/stats/authors", handler.GetAuthorRankHandler)
	r.Get("/api/stats/activity-heatmap", handler.GetActivityHeatmapHandler)
	r.Get("/api/stats/repo-comparison", handler.GetRepoComparisonHandler)
	r.Post("/api/export/json", handler.ExportDataHandler)
	r.Get("/api/repos/list", handler.GetReposListHandler)
	r.Get("/api/repos/info", handler.GetRepoInfoHandler)
	r.Get("/api/repos/stats", handler.GetRepoStatsHandler)
	r.Post("/api/repos/analyze", handler.GetRepoAnalyzeHandler)

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("OK"))
	})

	return r
}

func NewServerWithStatic(staticFS fs.FS) *chi.Mux {
	r := NewServer()

	if staticFS == nil {
		return r
	}

	r.Handle("/*", spaHandler(staticFS))

	return r
}

func spaHandler(staticFS fs.FS) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimPrefix(r.URL.Path, "/")
		if path == "" {
			path = "index.html"
		}

		// try to serve the requested static file
		f, err := staticFS.Open(path)
		if err == nil {
			defer f.Close()
			info, err := f.Stat()
			if err == nil && !info.IsDir() {
				http.ServeFileFS(w, r, staticFS, path)
				return
			}
		}

		// fallback to index.html for SPA routing
		_, err = staticFS.Open("index.html")
		if err != nil {
			http.NotFound(w, r)
			return
		}
		http.ServeFileFS(w, r, staticFS, "index.html")
	}
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("[%s] %s %s (%v)", r.Method, r.URL.Path, r.URL.RawQuery, time.Since(start))
	})
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}
