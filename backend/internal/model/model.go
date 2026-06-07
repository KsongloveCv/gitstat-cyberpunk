package model

import "time"

type Repository struct {
	Path           string   `json:"path"`
	Name           string   `json:"name"`
	CurrentBranch  string   `json:"currentBranch"`
	LastCommitTime string   `json:"lastCommitTime"`
	UserEmail      string   `json:"userEmail"`
	Commits        []Commit `json:"commits"`
}

type Commit struct {
	Hash      string    `json:"hash"`
	Author    string    `json:"author"`
	Email     string    `json:"email"`
	Date      time.Time `json:"date"`
	Message   string    `json:"message"`
	Additions int       `json:"additions"`
	Deletions int       `json:"deletions"`
}

type OverviewStats struct {
	TotalCommits    int              `json:"totalCommits"`
	TotalAdditions  int              `json:"totalAdditions"`
	TotalDeletions  int              `json:"totalDeletions"`
	ActiveAuthors   int              `json:"activeAuthors"`
	RepositoryCount int              `json:"repositoryCount"`
	Authors         []AuthorRankItem `json:"authors,omitempty"`
}

type AuthorDailyStats struct {
	Author    string          `json:"author"`
	Email     string          `json:"email"`
	Commits   int             `json:"commits"`
	Additions int             `json:"additions"`
	Deletions int             `json:"deletions"`
	IsMe      bool            `json:"isMe"`
	DailyData []DayCommitData `json:"dailyData,omitempty"`
}

type DayCommitData struct {
	Date      string `json:"date"`
	Commits   int    `json:"commits"`
	Additions int    `json:"additions"`
	Deletions int    `json:"deletions"`
}

type RepositoryDailyStats struct {
	RepoName       string             `json:"repoName"`
	RepoPath       string             `json:"repoPath"`
	CurrentBranch  string             `json:"currentBranch"`
	LastCommitTime string             `json:"lastCommitTime"`
	Authors        []AuthorDailyStats `json:"authors"`
}

// 周期聚合数据结构 (周/月/年)
type PeriodCommitData struct {
	Period    string `json:"date"`
	Commits   int    `json:"commits"`
	Additions int    `json:"additions"`
	Deletions int    `json:"deletions"`
}

type AuthorPeriodStats struct {
	Author     string            `json:"author"`
	Email      string            `json:"email"`
	Commits    int               `json:"commits"`
	Additions  int               `json:"additions"`
	Deletions  int               `json:"deletions"`
	IsMe       bool              `json:"isMe"`
	PeriodData []PeriodCommitData `json:"dailyData,omitempty"`
}

type RepositoryPeriodStats struct {
	RepoName       string             `json:"repoName"`
	RepoPath       string             `json:"repoPath"`
	CurrentBranch  string             `json:"currentBranch"`
	LastCommitTime string             `json:"lastCommitTime"`
	Authors        []AuthorPeriodStats `json:"authors"`
}

type ApiResponse struct {
	Code    int         `json:"code"`
	Data    interface{} `json:"data,omitempty"`
	Message string      `json:"message,omitempty"`
}

// 开发者排行榜项
type AuthorRankItem struct {
	Author        string  `json:"author"`
	Email         string  `json:"email"`
	Commits       int     `json:"commits"`
	Additions     int     `json:"additions"`
	Deletions     int     `json:"deletions"`
	NetChange     int     `json:"netChange"` // 新增-删除
	IsMe          bool    `json:"isMe"`
	AvgCommitSize float64 `json:"avgCommitSize"` // 平均提交大小
	LastCommitDate string `json:"lastCommitDate,omitempty"` // 最后提交时间
}

// 活动热力图数据点
type ActivityHeatmapPoint struct {
	DayOfWeek   int `json:"dayOfWeek"` // 0=周日, 1=周一...6=周六
	Hour        int `json:"hour"`      // 0-23
	CommitCount int `json:"commitCount"`
}

// 仓库列表项（快数据）
type RepoInfo struct {
	Path           string `json:"path"`
	Name           string `json:"name"`
	CurrentBranch  string `json:"currentBranch"`
	BranchCount    int    `json:"branchCount"`
	FileCount      int    `json:"fileCount"`
	LastCommitTime string `json:"lastCommitTime"`
	RemoteUrl      string `json:"remoteUrl"`
}

// 语言统计
type LanguageStat struct {
	Name       string  `json:"name"`
	FileCount  int     `json:"fileCount"`
	Lines      int     `json:"lines"`
	Percentage float64 `json:"percentage"`
}

// 深度分析结果
type AnalyzeResult struct {
	Name          string        `json:"name"`
	Path          string        `json:"path"`
	BranchCount   int           `json:"branchCount"`
	Branches      []string      `json:"branches"`
	FileCount     int           `json:"fileCount"`
	TotalLines    int           `json:"totalLines"`
	Languages     []LanguageStat `json:"languages"`
}

// 深度分析请求
type AnalyzeRequest struct {
	Path string `json:"path"`
}

// 贡献者统计
type ContributorStat struct {
	Author         string `json:"author"`
	Email          string `json:"email"`
	CommitCount    int    `json:"commitCount"`
	Additions      int    `json:"additions"`
	Deletions      int    `json:"deletions"`
	LastCommitDate string `json:"lastCommitDate"`
}

// 仓库统计（计算字段）
type RepoStats struct {
	Path                 string            `json:"path"`
	Name                 string            `json:"name"`
	CurrentBranch        string            `json:"currentBranch"`
	LastCommitTime       string            `json:"lastCommitTime"`
	EarliestDate         string            `json:"earliestDate"`
	EarliestCommitAuthor string            `json:"earliestCommitAuthor"`
	RepoSize             int64             `json:"repoSize"`
	RecentCommits        []Commit          `json:"recentCommits"`
	Contributors         []ContributorStat `json:"contributors"`
	Analysis             *AnalyzeResult    `json:"analysis,omitempty"`
}

// 仓库对比数据
type RepoComparison struct {
	RepoName         string  `json:"repoName"`
	RepoPath         string  `json:"repoPath"`
	Commits          int     `json:"commits"`
	Authors          int     `json:"authors"`
	Additions        int     `json:"additions"`
	Deletions        int     `json:"deletions"`
	LastCommitTime   string  `json:"lastCommitTime"`
	ActiveDays       int     `json:"activeDays"`       // 活跃天数
	AvgCommitsPerDay float64 `json:"avgCommitsPerDay"` // 日均提交数
}
