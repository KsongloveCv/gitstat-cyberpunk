package main

import (
	"embed"
	"encoding/json"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"os/exec"
	"runtime"

	"gitstat/internal/scanner"
	"gitstat/internal/server"
	"gitstat/internal/store"
)

var Version = "dev"

//go:embed web/dist/*
var embeddedDist embed.FS

func main() {
	if len(os.Args) < 2 {
		runDebug()
		return
	}

	switch os.Args[1] {
	case "serve":
		runServe(os.Args[2:])
	case "--version", "-v":
		fmt.Println(Version)
	case "--help", "-h", "help":
		printHelp()
	default:
		fmt.Fprintf(os.Stderr, "Unknown command: %s\n\n", os.Args[1])
		printHelp()
		os.Exit(1)
	}
}

func runDebug() {
	defaultPath := "D:/work"
	repos, err := scanner.DiscoverRepos(defaultPath)
	if err != nil {
		log.Printf("Warning: Failed to discover repos in %s: %v", defaultPath, err)
	} else {
		store.GlobalStore.RegisterRepos(repos)
		log.Printf("Registered %d repos from %s", len(repos), defaultPath)
	}

	r := server.NewServer()

	r.HandleFunc("/api/version", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"version": Version})
	})

	fmt.Println("GitStat server starting on :12580...")
	log.Fatal(http.ListenAndServe(":12580", r))
}

func runServe(args []string) {
	serveCmd := flag.NewFlagSet("serve", flag.ExitOnError)
	port := serveCmd.Int("port", 12580, "Port number")
	serveCmd.Parse(args)

	// 获取扫描目录：位置参数优先，否则使用当前工作目录
	var scanPath string
	positionalArgs := serveCmd.Args()
	if len(positionalArgs) > 0 {
		scanPath = positionalArgs[0]
	} else {
		var err error
		scanPath, err = os.Getwd()
		if err != nil {
			log.Printf("Warning: Failed to get working directory: %v", err)
		}
	}

	// 自动注册扫描目录下的仓库元数据
	if scanPath != "" {
		repos, err := scanner.DiscoverRepos(scanPath)
		if err != nil {
			log.Printf("Warning: Failed to discover repos in %s: %v", scanPath, err)
		} else {
			store.GlobalStore.SetScanPath(scanPath)
			store.GlobalStore.RegisterRepos(repos)
			log.Printf("Registered %d repos from %s", len(repos), scanPath)
		}
	}

	distFS, err := fs.Sub(embeddedDist, "web/dist")
	if err != nil {
		log.Printf("Warning: Failed to load embedded static files: %v", err)
		log.Println("Server will start with API only.")
	}

	r := server.NewServerWithStatic(distFS)

	r.HandleFunc("/api/version", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{"version": Version})
	})

	addr := fmt.Sprintf(":%d", *port)
	url := fmt.Sprintf("http://localhost:%d", *port)
	fmt.Println("GitStat Web Server")
	if scanPath != "" {
		fmt.Printf("Scan directory: %s\n", scanPath)
	}
	fmt.Printf("Listening on %s\n", url)
	fmt.Println("Open in browser to view analytics")

	go openBrowser(url)

	log.Fatal(http.ListenAndServe(addr, r))
}

func printHelp() {
	fmt.Println("GitStat - Git Repository Statistics Analyzer")
	fmt.Println()
	fmt.Println("Usage:")
	fmt.Println("  gitstat                     Start in debug mode (API only, :12580)")
	fmt.Println("  gitstat serve [directory]   Start web server with embedded UI")
	fmt.Println("  gitstat --version           Show version")
	fmt.Println("  gitstat --help              Show this help")
	fmt.Println()
	fmt.Println("Serve Options:")
	fmt.Println("  --port number       Port number (default: 12580)")
	fmt.Println()
	fmt.Println("Serve Arguments:")
	fmt.Println("  directory           Scan directory (default: current working directory)")
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("cmd", "/c", "start", url)
	case "darwin":
		cmd = exec.Command("open", url)
	default:
		cmd = exec.Command("xdg-open", url)
	}
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Run()
}
