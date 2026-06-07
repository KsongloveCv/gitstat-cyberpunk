package handler

import (
	"bytes"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"gitstat/internal/model"
	"gitstat/internal/store"
)

func parseTimeParams(r *http.Request, defaultRange string) (startDate, endDate time.Time) {
	startDateStr := r.URL.Query().Get("startDate")
	endDateStr := r.URL.Query().Get("endDate")

	if startDateStr != "" && endDateStr != "" {
		startDate, _ = time.ParseInLocation("2006-01-02", startDateStr, time.Local)
		endDate, _ = time.ParseInLocation("2006-01-02", endDateStr, time.Local)
		endDate = endDate.Add(24*time.Hour - time.Second)
	} else {
		timeRange := r.URL.Query().Get("range")
		if timeRange == "" {
			timeRange = defaultRange
		}
		startDate, endDate = ParseTimeRange(timeRange)
	}

	return startDate, endDate
}

func loadRepos(repoPaths []string) []model.Repository {
	repos := store.GlobalStore.GetRepositories()

	if len(repoPaths) > 0 {
		repoMap := make(map[string]bool)
		for _, path := range repoPaths {
			repoMap[path] = true
		}
		filteredRepos := make([]model.Repository, 0)
		for _, repo := range repos {
			if repoMap[repo.Path] {
				filteredRepos = append(filteredRepos, repo)
			}
		}
		repos = filteredRepos
	}

	return repos
}

func resolveUserEmail(repos []model.Repository, email string) string {
	if email != "" {
		return email
	}
	for _, repo := range repos {
		if repo.UserEmail != "" {
			return repo.UserEmail
		}
	}
	return ""
}

func writeJSON(w http.ResponseWriter, tag string, data interface{}) {
	w.Header().Set("Content-Type", "application/json")

	buf := &bytes.Buffer{}
	if err := json.NewEncoder(buf).Encode(data); err != nil {
		log.Printf("[%s] Serialize error: %v", tag, err)
		return
	}

	w.Write(buf.Bytes())
}
