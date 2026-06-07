package scanner

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"gitstat/internal/model"
)

var extLangMap = map[string]string{
	".rs":      "Rust",
	".go":      "Go",
	".py":      "Python",
	".js":      "JavaScript",
	".jsx":     "React (JSX)",
	".ts":      "TypeScript",
	".tsx":     "React (TSX)",
	".vue":     "Vue",
	".svelte":  "Svelte",
	".java":    "Java",
	".kt":      "Kotlin",
	".kts":     "Kotlin",
	".scala":   "Scala",
	".c":       "C",
	".h":       "C/C++ Header",
	".cpp":     "C++",
	".cxx":     "C++",
	".hpp":     "C++ Header",
	".cs":      "C#",
	".rb":      "Ruby",
	".php":     "PHP",
	".swift":   "Swift",
	".m":       "Objective-C",
	".mm":      "Objective-C++",
	".r":       "R",
	".dart":    "Dart",
	".lua":     "Lua",
	".elixir":  "Elixir",
	".ex":      "Elixir",
	".exs":     "Elixir",
	".hs":      "Haskell",
	".zig":     "Zig",
	".pl":      "Perl",
	".pm":      "Perl",
	".sql":     "SQL",
	".sh":      "Shell",
	".bash":    "Shell",
	".zsh":     "Shell",
	".fish":    "Shell",
	".ps1":     "PowerShell",
	".css":     "CSS",
	".scss":    "SCSS",
	".less":    "Less",
	".html":    "HTML",
	".htm":     "HTML",
	".xml":     "XML",
	".yaml":    "YAML",
	".yml":     "YAML",
	".toml":    "TOML",
	".json":    "JSON",
	".jsonc":   "JSON",
	".md":      "Markdown",
	".rst":     "reStructuredText",
	".tex":     "LaTeX",
	".dockerfile": "Dockerfile",
	".makefile":   "Makefile",
	".cmake":      "CMake",
	".gradle":     "Gradle",
	".proto":      "Protobuf",
	".graphql":    "GraphQL",
	".gql":        "GraphQL",
}

var exactNameMap = map[string]string{
	"Dockerfile": "Dockerfile",
	"Makefile":   "Makefile",
	"CMakeLists.txt": "CMake",
}

func GetRepoMeta(repoPath string) (model.RepoInfo, error) {
	currentBranch, _ := gitExec(repoPath, "rev-parse", "--abbrev-ref", "HEAD")

	branchCount := 0
	out, err := gitExec(repoPath, "for-each-ref", "refs/heads", "--format=%(refname:short)")
	if err == nil && out != "" {
		branchCount = len(strings.Split(out, "\n"))
	}

	fileCount := 0
	out, err = gitExec(repoPath, "ls-tree", "-r", "HEAD", "--name-only")
	if err == nil && out != "" {
		fileCount = len(strings.Split(out, "\n"))
	}

	var lastCommitTime string
	out, err = gitExec(repoPath, "log", "-1", "--format=%ci")
	if err == nil {
		if t, e := time.Parse("2006-01-02 15:04:05 -0700", out); e == nil {
			lastCommitTime = t.Format("2006-01-02 15:04:05")
		}
	}

	return model.RepoInfo{
		Path:           repoPath,
		Name:           filepath.Base(repoPath),
		CurrentBranch:  currentBranch,
		BranchCount:    branchCount,
		FileCount:      fileCount,
		LastCommitTime: lastCommitTime,
	}, nil
}

func AnalyzeRepoDeep(repoPath string) (model.AnalyzeResult, error) {
	currentBranch, _ := gitExec(repoPath, "rev-parse", "--abbrev-ref", "HEAD")

	branchCount := 0
	var branchNames []string
	out, err := gitExec(repoPath, "for-each-ref", "refs/heads", "--format=%(refname:short)")
	if err == nil && out != "" {
		branches := strings.Split(out, "\n")
		branchCount = len(branches)
		var others []string
		for _, b := range branches {
			b = strings.TrimSpace(b)
			if b == "" {
				continue
			}
			if b == currentBranch {
				branchNames = append(branchNames, b+" (current)")
			} else {
				others = append(others, b)
			}
		}
		sort.Strings(others)
		branchNames = append(branchNames, others...)
	}
	if len(branchNames) == 0 {
		branchNames = []string{currentBranch + " (current)"}
	}

	type fileInfo struct {
		path  string
		lines int
		lang  string
	}
	var files []fileInfo

	out, err = gitExec(repoPath, "ls-tree", "-r", "HEAD", "--name-only", "-z")
	if err != nil {
		return model.AnalyzeResult{}, fmt.Errorf("ls-tree: %w", err)
	}
	filePaths := strings.Split(strings.TrimSuffix(out, "\x00"), "\x00")

	for _, rel := range filePaths {
		rel = strings.TrimSpace(rel)
		if rel == "" {
			continue
		}
		ext := strings.ToLower(filepath.Ext(rel))
		base := filepath.Base(rel)

		var lang string
		if v, ok := exactNameMap[base]; ok {
			lang = v
		} else if v, ok := extLangMap[ext]; ok {
			lang = v
		} else {
			lang = "Other"
		}

		fullPath := filepath.Join(repoPath, rel)
		lines := 0
		f, err := os.Open(fullPath)
		if err == nil {
			lines = countLines(f)
			f.Close()
		}

		files = append(files, fileInfo{rel, lines, lang})
	}

	langMap := make(map[string]*model.LanguageStat)
	totalLines := 0
	for _, f := range files {
		totalLines += f.lines
		if _, ok := langMap[f.lang]; !ok {
			langMap[f.lang] = &model.LanguageStat{Name: f.lang}
		}
		langMap[f.lang].FileCount++
		langMap[f.lang].Lines += f.lines
	}

	var languages []model.LanguageStat
	for _, ls := range langMap {
		if totalLines > 0 {
			ls.Percentage = float64(ls.Lines) / float64(totalLines) * 100
		}
		languages = append(languages, *ls)
	}
	sort.Slice(languages, func(i, j int) bool {
		return languages[i].Lines > languages[j].Lines
	})

	return model.AnalyzeResult{
		Name:        filepath.Base(repoPath),
		Path:        repoPath,
		BranchCount: branchCount,
		Branches:    branchNames,
		FileCount:   len(files),
		TotalLines:  totalLines,
		Languages:   languages,
	}, nil
}

func GetRemoteUrl(repoPath string) string {
	out, err := gitExec(repoPath, "remote", "get-url", "origin")
	if err != nil {
		return ""
	}
	return out
}

func GetRepoSize(repoPath string) int64 {
	out, err := gitExec(repoPath, "ls-tree", "-r", "-l", "HEAD")
	if err != nil || out == "" {
		return 0
	}
	var total int64
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		// 100644 blob <hash> <size>\t<path>
		tabIdx := strings.IndexByte(line, '\t')
		if tabIdx < 0 {
			continue
		}
		meta := strings.Fields(line[:tabIdx])
		if len(meta) < 4 || meta[1] != "blob" {
			continue
		}
		if n, e := strconv.ParseInt(meta[3], 10, 64); e == nil {
			total += n
		}
	}
	return total
}

func countLines(reader io.Reader) int {
	scanner := bufio.NewScanner(reader)
	lines := 0
	for scanner.Scan() {
		lines++
	}
	return lines
}
