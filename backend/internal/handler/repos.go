package handler

import (
	"cmp"
	"encoding/json"
	"net/http"
	"slices"
	"time"

	"gitstat/internal/aggregator"
	"gitstat/internal/model"
	"gitstat/internal/scanner"
	"gitstat/internal/store"
)

func GetReposListHandler(w http.ResponseWriter, r *http.Request) {
	caches := store.GlobalStore.GetAllCaches()

	infos := make([]model.RepoInfo, 0, len(caches))
	for _, cache := range caches {
		infos = append(infos, model.RepoInfo{
			Path:           cache.Path,
			Name:           cache.Name,
			CurrentBranch:  cache.CurrentBranch,
			BranchCount:    cache.BranchCount,
			FileCount:      cache.FileCount,
			LastCommitTime: cache.LastCommitTime,
			RemoteUrl:      cache.RemoteUrl,
		})
	}

	slices.SortFunc(infos, func(a, b model.RepoInfo) int {
		return cmp.Compare(a.Name, b.Name)
	})

	writeJSON(w, "ReposList", infos)
}

func GetRepoInfoHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")
	if path == "" {
		http.Error(w, "path is required", http.StatusBadRequest)
		return
	}

	cache := store.GlobalStore.GetRepoCache(path)
	if cache == nil {
		http.Error(w, "repo not found", http.StatusNotFound)
		return
	}

	branchCount := cache.BranchCount
	fileCount := cache.FileCount
	remoteUrl := cache.RemoteUrl

	if branchCount == 0 {
		meta, err := scanner.GetRepoMeta(cache.Path)
		if err == nil {
			branchCount = meta.BranchCount
			fileCount = meta.FileCount
			store.GlobalStore.UpdateRepo(cache.Path, func(c *store.RepoCache) {
				c.BranchCount = branchCount
				c.FileCount = fileCount
			})
		}
	}

	if remoteUrl == "" {
		remoteUrl = scanner.GetRemoteUrl(cache.Path)
		cache.RemoteUrl = remoteUrl
	}

	writeJSON(w, "RepoInfo", model.RepoInfo{
		Path:           cache.Path,
		Name:           cache.Name,
		CurrentBranch:  cache.CurrentBranch,
		BranchCount:    branchCount,
		FileCount:      fileCount,
		LastCommitTime: cache.LastCommitTime,
		RemoteUrl:      remoteUrl,
	})
}

func GetRepoStatsHandler(w http.ResponseWriter, r *http.Request) {
	path := r.URL.Query().Get("path")
	if path == "" {
		http.Error(w, "path is required", http.StatusBadRequest)
		return
	}

	cache := store.GlobalStore.GetRepoCache(path)
	if cache == nil {
		http.Error(w, "repo not found", http.StatusNotFound)
		return
	}

	repos := []model.Repository{{
		Path:    cache.Path,
		Name:    cache.Name,
		Commits: cache.Commits,
	}}
	rank := aggregator.AggregateAuthorRank(repos, "", time.Time{}, time.Time{})
	contributors := make([]model.ContributorStat, len(rank))
	for i, item := range rank {
		contributors[i] = model.ContributorStat{
			Author:         item.Author,
			Email:          item.Email,
			CommitCount:    item.Commits,
			Additions:      item.Additions,
			Deletions:      item.Deletions,
			LastCommitDate: item.LastCommitDate,
		}
	}

	recentCommits := cache.Commits
	if len(recentCommits) > 20 {
		recentCommits = recentCommits[len(recentCommits)-20:]
	}
	for i, j := 0, len(recentCommits)-1; i < j; i, j = i+1, j-1 {
		recentCommits[i], recentCommits[j] = recentCommits[j], recentCommits[i]
	}

	var earliestDate string
	var earliestAuthor string
	if !cache.EarliestDate.IsZero() {
		earliestDate = cache.EarliestDate.Format("2006-01-02 15:04:05")
	}
	if len(cache.Commits) > 0 {
		earliest := cache.Commits[0]
		for _, c := range cache.Commits {
			if c.Date.Before(earliest.Date) {
				earliest = c
			}
		}
		earliestAuthor = earliest.Author
	}

	repoSize := cache.RepoSize
	if repoSize == 0 {
		repoSize = scanner.GetRepoSize(path)
		store.GlobalStore.UpdateRepo(path, func(c *store.RepoCache) {
			c.RepoSize = repoSize
		})
	}

	stats := model.RepoStats{
		Path:                 cache.Path,
		Name:                 cache.Name,
		CurrentBranch:        cache.CurrentBranch,
		LastCommitTime:       cache.LastCommitTime,
		EarliestDate:         earliestDate,
		EarliestCommitAuthor: earliestAuthor,
		RepoSize:             repoSize,
		RecentCommits:        recentCommits,
		Contributors:         contributors,
	}

	if cache.Analyzed {
		stats.Analysis = &model.AnalyzeResult{
			Name:        cache.Name,
			Path:        cache.Path,
			BranchCount: cache.BranchCount,
			Branches:    cache.Branches,
			FileCount:   cache.FileCount,
			TotalLines:  cache.TotalLines,
			Languages:   cache.Languages,
		}
	}

	writeJSON(w, "RepoStats", stats)
}

func GetRepoAnalyzeHandler(w http.ResponseWriter, r *http.Request) {
	var req model.AnalyzeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	if req.Path == "" {
		http.Error(w, "Path is required", http.StatusBadRequest)
		return
	}

	if result, ok := store.GlobalStore.GetAnalyzeCache(req.Path); ok {
		writeJSON(w, "RepoAnalyze", result)
		return
	}

	result, err := scanner.AnalyzeRepoDeep(req.Path)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	store.GlobalStore.UpdateRepo(req.Path, func(c *store.RepoCache) {
		c.BranchCount = result.BranchCount
		c.Branches = result.Branches
		c.FileCount = result.FileCount
		c.TotalLines = result.TotalLines
		c.Languages = result.Languages
		c.Analyzed = true
	})
	writeJSON(w, "RepoAnalyze", result)
}
