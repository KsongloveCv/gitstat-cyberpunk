package scanner

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"gitstat/internal/model"
)

func gitExec(repoPath string, args ...string) (string, error) {
	cmd := exec.Command("git", args...)
	cmd.Dir = repoPath
	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("git %v in %s: %w", args, repoPath, err)
	}
	return strings.TrimRight(string(out), "\n\r "), nil
}

func scanSingleRepo(path string, startDate, endDate time.Time) (model.Repository, error) {
	currentBranch, _ := gitExec(path, "rev-parse", "--abbrev-ref", "HEAD")
	userEmail, _ := gitExec(path, "config", "user.email")

	commits, err := runGitLog(path, startDate, endDate)
	if err != nil {
		return model.Repository{}, err
	}

	var lastCommitTime string
	for _, c := range commits {
		if !c.Date.IsZero() {
			lastCommitTime = c.Date.Format("2006-01-02 15:04:05")
			break
		}
	}
	if lastCommitTime == "" {
		out, err := gitExec(path, "log", "-1", "--format=%ci")
		if err == nil {
			if t, e := time.Parse("2006-01-02 15:04:05 -0700", out); e == nil {
				lastCommitTime = t.Format("2006-01-02 15:04:05")
			}
		}
	}

	return model.Repository{
		Path:           path,
		Name:           filepath.Base(path),
		CurrentBranch:  currentBranch,
		LastCommitTime: lastCommitTime,
		UserEmail:      userEmail,
		Commits:        commits,
	}, nil
}

func runGitLog(repoPath string, since, until time.Time) ([]model.Commit, error) {
	args := []string{"log", "--format=---GITSTAT_COMMIT---%n%H%n%an%n%ae%n%ci%n%s", "--numstat"}
	if !since.IsZero() {
		args = append(args, "--since="+since.Format("2006-01-02 15:04:05"))
	}
	if !until.IsZero() {
		args = append(args, "--until="+until.Format("2006-01-02 15:04:05"))
	}

	cmd := exec.Command("git", args...)
	cmd.Dir = repoPath
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("git log in %s: %w", repoPath, err)
	}

	return parseGitLog(string(out))
}

func parseGitLog(text string) ([]model.Commit, error) {
	lines := strings.Split(text, "\n")
	if len(lines) == 0 {
		return nil, nil
	}

	var commits []model.Commit
	const commitMarker = "---GITSTAT_COMMIT---"

	i := 0
	// skip leading lines until first marker
	for i < len(lines) && lines[i] != commitMarker {
		i++
	}

	for i < len(lines) {
		if lines[i] != commitMarker {
			i++
			continue
		}
		i++ // skip marker

		if i+4 >= len(lines) {
			break
		}

		hash := strings.TrimSpace(lines[i]); i++
		author := strings.TrimSpace(lines[i]); i++
		email := strings.TrimSpace(lines[i]); i++
		dateStr := strings.TrimSpace(lines[i]); i++
		subject := strings.TrimSpace(lines[i]); i++

		commitTime, _ := time.Parse("2006-01-02 15:04:05 -0700", dateStr)
		if commitTime.IsZero() {
			commitTime, _ = time.Parse("2006-01-02 15:04:05", dateStr)
		}

		var additions, deletions int
		for i < len(lines) && lines[i] != commitMarker {
			line := strings.TrimSpace(lines[i])
			i++
			if line == "" {
				continue
			}
			parts := strings.Split(line, "\t")
			if len(parts) >= 2 {
				add, errA := strconv.Atoi(parts[0])
				del, errD := strconv.Atoi(parts[1])
				if errA == nil {
					additions += add
				}
				if errD == nil {
					deletions += del
				}
			}
		}

		commits = append(commits, model.Commit{
			Hash:      hash,
			Author:    author,
			Email:     email,
			Date:      commitTime,
			Message:   subject,
			Additions: additions,
			Deletions: deletions,
		})
	}

	return commits, nil
}

func ScanCommitsByRange(repoPath string, startDate, endDate time.Time) ([]model.Commit, error) {
	return runGitLog(repoPath, startDate, endDate)
}
func DiscoverRepos(rootPath string) ([]model.Repository, error) {
	var repos []model.Repository

	gitPath := filepath.Join(rootPath, ".git")
	if _, err := os.Stat(gitPath); err == nil {
		meta, err := ScanMetadata(rootPath)
		if err == nil {
			repos = append(repos, meta)
		}
	}

	entries, err := os.ReadDir(rootPath)
	if err != nil {
		return nil, err
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		repoPath := filepath.Join(rootPath, entry.Name())
		if _, err := os.Stat(filepath.Join(repoPath, ".git")); os.IsNotExist(err) {
			continue
		}
		meta, err := ScanMetadata(repoPath)
		if err != nil {
			continue
		}
		repos = append(repos, meta)
	}
	return repos, nil
}

func ScanMetadata(repoPath string) (model.Repository, error) {
	currentBranch, _ := gitExec(repoPath, "rev-parse", "--abbrev-ref", "HEAD")
	userEmail, _ := gitExec(repoPath, "config", "user.email")

	var lastCommitTime string
	out, err := gitExec(repoPath, "log", "-1", "--format=%ci")
	if err == nil {
		if t, e := time.Parse("2006-01-02 15:04:05 -0700", out); e == nil {
			lastCommitTime = t.Format("2006-01-02 15:04:05")
		}
	} else {
		_ = err
	}

	return model.Repository{
		Path:           repoPath,
		Name:           filepath.Base(repoPath),
		CurrentBranch:  currentBranch,
		UserEmail:      userEmail,
		LastCommitTime: lastCommitTime,
	}, nil
}
